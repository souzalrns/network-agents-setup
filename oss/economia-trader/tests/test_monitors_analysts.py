import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from economia_trader import RiskLimits
from economia_trader.analysts import TokenUsage, TradingAgentsAnalyst
from economia_trader.exchanges.base import Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.monitors import EventStore, is_high_impact, macro_events, news_events
from economia_trader.report import report
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
OBS = "2026-10-12T10:00:00+00:00"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))


# ---- monitors ----


def test_news_events_four_clocks_and_dedup(tmp_path):
    rows = [
        {
            "date": datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc),
            "title": "ACME beats",
            "url": "u1",
            "symbols": "ACME",
        },
        {"date": "2026-10-12T11:30:00Z", "title": "late", "url": "u2"},  # published after we observed
        {"title": "no date"},
    ]
    evs = news_events(rows, observed_at=OBS)
    assert len(evs) == 2
    assert evs[0].available_at == OBS and evs[0].published_at == "2026-10-12T09:00:00+00:00"
    assert evs[1].available_at == "2026-10-12T11:30:00+00:00"  # never before publication
    store = EventStore(tmp_path / "events.jsonl")
    assert store.add(evs) == 2 and store.add(evs) == 0  # de-duplicated by id


def test_macro_events_eastern_time_and_impact():
    rows = [
        {"event": "Consumer Price Index", "date": "2026-10-14", "time": "08:30", "importance": "high"},
        {"release": "Real Earnings", "date": "2026-10-14"},
    ]
    evs = macro_events(rows, observed_at=OBS)
    cpi = evs[0]
    assert cpi.event_at == "2026-10-14T12:30:00+00:00"  # 08:30 EDT -> 12:30 UTC
    assert cpi.payload["high_impact"] and not evs[1].payload["high_impact"]
    assert is_high_impact("FOMC rate decision") and not is_high_impact("Pulp and paper")


def test_high_impact_window_respects_available_at(tmp_path):
    store = EventStore(tmp_path / "e.jsonl")
    store.add(macro_events([{"event": "Employment Situation", "date": "2026-10-14", "time": "08:30"}], observed_at=OBS))
    assert store.high_impact_within("2026-10-13T20:00:00+00:00", 24)
    assert not store.high_impact_within("2026-10-12T09:00:00+00:00", 72)  # schedule not yet known then
    assert not store.high_impact_within("2026-10-16T12:00:00+00:00", 24)


# ---- analyst ----


def test_analyst_confirms_vetoes_and_budget(tmp_path):
    calls = []

    def fake_propagate(ticker, day):
        calls.append(ticker)
        return {"market_report": "m", "final_trade_decision": f"Rating: {ratings[ticker]}"}, ratings[ticker]

    ratings = {"ACME": "Overweight", "BETA": "Hold", "GAMA": "REVIEW"}
    a = TradingAgentsAnalyst(propagate=fake_propagate, evidence_dir=tmp_path, max_runs_per_day=2)
    ok = a.opinion("ACME", "2026-10-13")
    assert ok.confirms and json.loads(Path(ok.evidence_path).read_text())["reports"]["market_report"] == "m"
    assert not a.opinion("BETA", "2026-10-13").confirms
    over = a.opinion("GAMA", "2026-10-13")
    assert over.rating == "BUDGET" and not over.confirms and calls == ["ACME", "BETA"]  # no LLM call over budget
    assert a.opinion("GAMA", "2026-10-14").rating == "REVIEW"  # new day, new budget; REVIEW never confirms


def test_token_usage_handler_counts():
    u = TokenUsage()
    u.add("claude", 100, 20)
    u.add("claude", 50, 5)
    assert u.by_model == {"claude": {"in": 150, "out": 25, "calls": 2}}


# ---- runner integration ----


class Ex:
    name = "fake"
    supports_testnet = False

    def __init__(self, prices):
        self.prices = prices

    def ticker(self, s):
        return Ticker(s, D(self.prices[s]), None, None)


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


def _runner(tmp_path, *, events=None, analyst=None, cfg=None):
    return Runner(
        Ex({"ACME": "20", "BETA": "10"}),
        StaticFlowSource([fp("a", "ACME"), fp("b", "BETA")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=cfg or RunConfig(),
        state_dir=tmp_path,
        cash="100",
        env={},
        clock=lambda: T0,
        events=events,
        analyst=analyst,
    )


def test_macro_block_skips_entries_but_keeps_exits(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    cpi = {"event": "Consumer Price Index", "date": "2026-10-14", "time": "07:30"}  # 11:30 UTC, 23.5h ahead
    store.add(macro_events([cpi], observed_at=OBS))
    s = _runner(tmp_path, events=store).run_once()
    assert s["macro_block"] == ["Consumer Price Index"] and s["entries"] == []
    assert "exits" in s
    s2 = _runner(tmp_path / "off", events=store, cfg=RunConfig(macro_block_hours=None)).run_once()
    assert "macro_block" not in s2 and s2["entries"][0]["status"] == "filled"


def test_analyst_gate_in_runner(tmp_path):
    ratings = {"ACME": "Hold", "BETA": "Buy"}
    a = TradingAgentsAnalyst(propagate=lambda t, d: ({}, ratings[t]), evidence_dir=tmp_path / "ev")
    cfg = RunConfig(confirm_with="tradingagents", max_new_per_run=2)
    s = _runner(tmp_path, analyst=a, cfg=cfg).run_once()
    assert [(e["ticker"], e["status"]) for e in s["entries"]] == [("ACME", "vetoed"), ("BETA", "filled")]
    kinds = [json.loads(x)["kind"] for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert kinds.count("opinion") == 2
    prop = next(
        json.loads(x)["payload"]
        for x in (tmp_path / "journal.jsonl").read_text().splitlines()
        if json.loads(x)["kind"] == "proposal"
    )
    assert any(e.startswith("opinion:") for e in prop["evidence_ids"])
    assert report(tmp_path / "journal.jsonl")["open_positions"] == ["BETA"]


def test_confirm_without_analyst_is_a_config_error(tmp_path):
    with pytest.raises(ValueError, match="needs an analyst"):
        _runner(tmp_path, cfg=RunConfig(confirm_with="tradingagents"))


def test_version_changes_with_new_knobs():
    base = RunConfig()
    assert base.version != RunConfig(macro_block_hours=None).version
    assert base.version != RunConfig(confirm_with="tradingagents").version
    cfg = RunConfig.from_mapping({"macro_block_hours": None, "confirm_with": "tradingagents"})
    assert cfg.macro_block_hours is None and cfg.confirm_with == "tradingagents"


def test_cli_monitor_with_calendar_file(tmp_path, capsys):
    from economia_trader import cli

    cal = tmp_path / "fomc.json"
    cal.write_text(json.dumps([{"event": "FOMC rate decision", "date": "2026-10-28", "time": "14:00"}]))
    ev = tmp_path / "events.jsonl"
    assert cli.main(["monitor", "--calendar-file", str(cal), "--events", str(ev)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["added"] == {"calendar_file": 1}
    row = json.loads(ev.read_text().splitlines()[0])
    assert row["payload"]["high_impact"] and row["event_at"] == "2026-10-28T18:00:00+00:00"


def test_openbb_record_normalisation():
    from economia_trader.monitors import _records

    model = SimpleNamespace(model_dump=lambda: {"title": "x", "date": "2026-10-12"})
    assert _records(SimpleNamespace(results=[model])) == [{"title": "x", "date": "2026-10-12"}]
    assert _records([{"a": 1}]) == [{"a": 1}]
