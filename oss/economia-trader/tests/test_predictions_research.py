import csv
import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.contracts import to_dict
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Kline, Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.monitors import EventStore
from economia_trader.predictions import (
    GAMMA,
    _http_json,
    gamma_markets,
    latest_odds,
    odds_block,
    prediction_events,
    yes_probability,
)
from economia_trader.research import FINRL_COLUMNS, finrl_rows, write_csv
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
AS_OF = T0.isoformat(timespec="seconds")


def market(q, slug, yes, volume="250000.5", outcomes='["Yes", "No"]'):
    # the shape the Gamma API returns: outcomes and prices as stringified lists
    return {
        "question": q,
        "slug": slug,
        "outcomes": outcomes,
        "outcomePrices": json.dumps([str(yes), str(1 - yes)]),
        "volume": volume,
        "endDate": "2026-12-31T00:00:00Z",
    }


ROWS = [
    market("Fed decreases interest rates by 25 bps after December 2026 meeting?", "fed-cut-dec", 0.71),
    market("US recession in 2026?", "us-recession-2026", 0.38),
    market("Will the Federal Reserve hike rates in 2026?", "fed-hike", 0.05),
    market("Will it snow in Lisbon?", "lisbon-snow", 0.01),  # not macro
    market("US recession in 2027?", "us-recession-2027", 0.6, volume="900"),  # too small
    market("Which party wins the Senate?", "senate", 0.5, outcomes='["Dem", "Rep"]'),  # not Yes/No
]


def as_rows(evs):
    return [to_dict(e) for e in evs]


def test_yes_probability_reads_binary_markets_only():
    assert yes_probability(ROWS[0]) == pytest.approx(0.71)
    assert yes_probability(ROWS[-1]) is None
    assert yes_probability({"outcomes": "nope", "outcomePrices": "[]"}) is None


def test_prediction_events_keep_macro_markets_with_volume():
    evs = as_rows(prediction_events(ROWS, observed_at="2026-10-13T10:00:00+00:00"))
    assert [e["payload"]["slug"] for e in evs] == ["fed-cut-dec", "us-recession-2026", "fed-hike"]
    e = evs[1]
    assert e["kind"] == "prediction_market" and e["payload"]["yes_prob"] == 0.38 and e["payload"]["volume"] == 250000
    assert e["available_at"] == "2026-10-13T10:00:00+00:00"
    again = as_rows(prediction_events(ROWS, observed_at="2026-10-13T10:40:00+00:00"))
    assert again[1]["id"] == e["id"]  # one snapshot per market per hour


def test_latest_odds_uses_only_known_and_fresh_snapshots():
    old = as_rows(
        prediction_events(
            [market("US recession in 2026?", "us-recession-2026", 0.2)], observed_at="2026-10-09T10:00:00+00:00"
        )
    )
    now = as_rows(prediction_events(ROWS, observed_at="2026-10-13T10:00:00+00:00"))
    future = as_rows(
        prediction_events(
            [market("US recession in 2026?", "us-recession-2026", 0.9)], observed_at="2026-10-13T13:00:00+00:00"
        )
    )
    odds = {e["payload"]["slug"]: e["payload"]["yes_prob"] for e in latest_odds(old + now + future, AS_OF)}
    assert odds["us-recession-2026"] == 0.38  # not the future 0.9, not the stale 0.2
    assert latest_odds(old, AS_OF) == []  # older than 48h


def test_odds_block_rules():
    evs = as_rows(prediction_events(ROWS, observed_at="2026-10-13T10:00:00+00:00"))
    assert odds_block(evs, AS_OF, [("recession", D("0.5"))]) == []
    assert odds_block(evs, AS_OF, [("recession", D("0.3"))]) == ["US recession in 2026?: 38% >= 30%"]
    assert odds_block([], AS_OF, [("recession", D("0.01"))]) == []  # no data, no block


def test_gamma_markets_pages_and_refuses_other_hosts():
    seen = []

    def fetch(url):
        seen.append(url)
        return [ROWS[0]] * 2 if len(seen) == 1 else [ROWS[1]]

    rows = gamma_markets(limit=2, pages=5, fetch=fetch)
    assert len(rows) == 3 and len(seen) == 2
    assert seen[0].startswith(f"{GAMMA}/markets?") and "closed=false" in seen[0] and "offset=2" in seen[1]
    with pytest.raises(ValueError, match="outside the Gamma API"):
        _http_json("https://evil.example/markets")


# ---- the loop: odds hold new entries ----


class Ex:
    name = "fake"
    supports_testnet = False

    def ticker(self, s):
        return Ticker(s, D("20"), None, None)


def fp(id, ticker):
    return FlowPrint(
        id,
        ticker,
        "bullish",
        D("60000"),
        100,
        1000,
        30,
        D("85"),
        D("3000000000"),
        "2026-10-12T20:00:00+00:00",
        "2026-10-13T11:00:00+00:00",
    )


def test_runner_odds_block_holds_entries_and_is_versioned(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    store.add(prediction_events(ROWS, observed_at="2026-10-13T10:00:00+00:00"))
    cfg = RunConfig.from_mapping({"odds_block": {"recession": "0.3"}})
    assert cfg.odds_block == (("recession", D("0.3")),) and cfg.version != RunConfig().version
    runner = Runner(
        Ex(),
        StaticFlowSource([fp("a", "ACME")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=cfg,
        state_dir=tmp_path,
        cash="100",
        env={},
        clock=lambda: T0,
        events=store,
    )
    s = runner.run_once()
    assert s["entries"] == [] and s["odds_block"] == ["US recession in 2026?: 38% >= 30%"]
    page = build_html(tmp_path, now=T0)
    assert "Probabilidades macro (Polymarket" in page and "71%" in page and "pausa por probabilidades" in page
    with pytest.raises(ValueError, match="odds_block"):
        RunConfig.from_mapping({"odds_block": {"recession": "1.5"}})


# ---- research export (FinRL format) ----


def test_finrl_rows_and_csv(tmp_path):
    day = 86_400_000
    series = {
        "SPY": [Kline(i * day, D(10 + i), D(11 + i), D(9 + i), D("10.5") + i, D(100)) for i in range(2)],
        "QQQ": [Kline(i * day, D(20), D(21), D(19), D("20.5"), D(50)) for i in range(2)],
    }
    rows = finrl_rows(series)
    assert [(r["date"], r["tic"]) for r in rows] == [
        ("1970-01-01", "QQQ"),
        ("1970-01-01", "SPY"),
        ("1970-01-02", "QQQ"),
        ("1970-01-02", "SPY"),
    ]
    out = tmp_path / "data.csv"
    assert write_csv(out, rows) == 4
    with out.open() as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames) == FINRL_COLUMNS
        assert next(reader)["close"] == "20.5"


def test_cli_export_klines(tmp_path, monkeypatch, capsys):
    import economia_trader.cli as cli

    class K:
        def klines(self, symbol, interval, limit):
            return [Kline(0, D(1), D(2), D("0.5"), D("1.5"), D(10))]

    monkeypatch.setattr(cli, "make_exchange", lambda name, mode: K())
    out = tmp_path / "k.csv"
    assert cli.main(["export-klines", "--exchange", "alpaca", "--symbols", "spy,qqq", "--out", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["rows"] == 2
