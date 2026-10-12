import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

from economia_trader import RiskLimits
from economia_trader.contracts import to_dict
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.monitors import EventStore, news_events
from economia_trader.report import report
from economia_trader.runner import RunConfig, Runner, merge_ideas
from economia_trader.safety import Mode
from economia_trader.signals import (
    Idea,
    insider_clusters,
    insider_events,
    news_sentiment_events,
    sentiment_veto,
    social_sentiment_events,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
AS_OF = T0.isoformat(timespec="seconds")
OBS = "2026-10-12T10:00:00+00:00"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))


def trade(ticker, insider, shares, price, day="2026-10-08", filed="2026-10-09", side="buy"):
    return {
        "ticker": ticker,
        "insider": insider,
        "role": "Director",
        "side": side,
        "shares": shares,
        "price": price,
        "trade_date": day,
        "filed_at": filed,
        "accession": f"{ticker}-{insider}",
    }


def as_rows(events):
    return [to_dict(e) for e in events]


# ---- insiders ----


def test_insider_events_use_filing_time_not_trade_time():
    ev = insider_events([trade("ACME", "Ann", 1000, "50")], observed_at=OBS)[0]
    assert ev.event_at == "2026-10-08T00:00:00+00:00" and ev.published_at == "2026-10-09T00:00:00+00:00"
    assert ev.available_at == OBS and ev.payload["value"] == "50000"


def test_insider_cluster_needs_distinct_insiders_value_window_and_knowledge():
    rows = [
        trade("ACME", "Ann", 1000, "60"),
        trade("ACME", "Bob", 1000, "60"),  # 2 insiders, $120k
        trade("BETA", "Cid", 10000, "50"),  # one insider only
        trade("GAMA", "Dee", 100, "10"),
        trade("GAMA", "Eve", 100, "10"),  # too small
        trade("DELT", "Fay", 1000, "60", side="sell"),
        trade("DELT", "Gus", 1000, "60", side="sell"),
        trade("OLDX", "Hal", 2000, "60", day="2026-09-01"),
        trade("OLDX", "Ivy", 2000, "60", day="2026-09-01"),
    ]
    evs = as_rows(insider_events(rows, observed_at=OBS))
    ideas = insider_clusters(evs, AS_OF)
    assert [i.ticker for i in ideas] == ["ACME"] and ideas[0].source == "insiders"
    assert "2 insiders bought $120,000" in ideas[0].rationale
    assert insider_clusters(evs, "2026-10-12T09:00:00+00:00") == []  # filings not yet known then


def test_merge_ideas_prefers_agreement():
    a = Idea("ACME", "flow", ("p1",), "flow says", D(10))
    b = Idea("ACME", "insiders", ("ev1",), "insiders say", D(5))
    c = Idea("BETA", "flow", ("p2",), "x", D(1000))
    merged = merge_ideas([c, a, b])
    assert merged[0].ticker == "ACME" and merged[0].source == "flow+insiders"
    assert merged[0].evidence_ids == ("ev1", "p1")


# ---- sentiment ----


def _news(title, ticker, pub="2026-10-13T09:00:00Z"):
    return as_rows(news_events([{"date": pub, "title": title, "url": title, "symbols": ticker}], observed_at=OBS))[0]


def test_finbert_events_and_veto():
    news = [_news("ACME misses badly", "ACME"), _news("ACME faces probe", "ACME"), _news("ACME new CEO", "ACME")]
    scorer = lambda texts: [("negative", 0.9), ("negative", 0.8), ("neutral", 0.6)]  # noqa: E731
    scored = as_rows(news_sentiment_events(news, scorer, observed_at="2026-10-13T10:00:00+00:00"))
    assert {s["payload"]["label"] for s in scored} == {"negative", "neutral"}
    assert scored[0]["payload"]["tickers"] == ["ACME"]
    assert sentiment_veto(scored, "ACME", AS_OF) == ["news 67% negative (3 headlines)"]
    assert sentiment_veto(scored, "ACME", AS_OF, max_negative_share=0.9) == []
    assert sentiment_veto(scored, "ACME", "2026-10-13T09:30:00+00:00") == []  # not scored yet then


def test_social_veto_from_adanos_rows():
    rows = [
        {"ticker": "acme", "source": "reddit", "bullish_pct": 20, "buzz_score": 70, "trend": "falling"},
        {"ticker": "ACME", "source": "x", "bullish_pct": 30, "buzz_score": 50},
    ]
    evs = as_rows(social_sentiment_events(rows, observed_at="2026-10-13T11:00:00+00:00"))
    assert sentiment_veto(evs, "ACME", AS_OF) == ["social bullish 25% < 30%"]
    assert sentiment_veto(evs, "BETA", AS_OF) == []


# ---- runner integration ----


class Ex:
    name = "fake"
    supports_testnet = False

    def ticker(self, s):
        return Ticker(s, D({"ACME": "20", "BETA": "10", "GAMA": "5"}[s]), None, None)


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


def _runner(tmp, store, cfg, prints=()):
    return Runner(
        Ex(),
        StaticFlowSource(list(prints)),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=cfg,
        state_dir=tmp,
        cash="100",
        env={},
        clock=lambda: T0,
        events=store,
    )


def test_runner_trades_insider_cluster_and_attributes_it(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    store.add(insider_events([trade("GAMA", "Ann", 10000, "5"), trade("GAMA", "Bob", 20000, "5")], observed_at=OBS))
    cfg = RunConfig(use_flow=False, insider_signal=True, insider_min_value=D("50000"))
    s = _runner(tmp_path, store, cfg).run_once()
    assert s["insiders"] == ["GAMA"] and s["entries"][0]["status"] == "filled"
    rep = report(tmp_path / "journal.jsonl")
    assert f"insiders@{cfg.version}" in rep["by_version"]


def test_runner_sentiment_veto_blocks_flow_idea(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    news = [_news("ACME misses", "ACME")]
    store.add(
        news_events(
            [{"date": "2026-10-13T09:00:00Z", "title": "ACME misses", "url": "ACME misses", "symbols": "ACME"}],
            observed_at=OBS,
        )
    )
    store.add(news_sentiment_events(news, lambda t: [("negative", 0.95)], observed_at="2026-10-13T10:00:00+00:00"))
    cfg = RunConfig(sentiment_veto=True, max_new_per_run=2)
    s = _runner(tmp_path, store, cfg, prints=[fp("a", "ACME"), fp("b", "BETA")]).run_once()
    assert ("ACME", "vetoed") in [(e["ticker"], e["status"]) for e in s["entries"]]
    assert ("BETA", "filled") in [(e["ticker"], e["status"]) for e in s["entries"]]
    page = build_html(tmp_path, now=T0)
    assert "Vetos por sentimento" in page and "100% negative" in page and "negative" in page


def test_new_knobs_are_versioned_and_parsed():
    base = RunConfig()
    for kw in ({"insider_signal": True}, {"sentiment_veto": True}, {"use_flow": False}, {"insider_min_value": D("1")}):
        assert RunConfig(**kw).version != base.version
    cfg = RunConfig.from_mapping({"insider_signal": True, "insider_min_count": 3, "max_negative_news_share": "0.5"})
    assert cfg.insider_signal is True and cfg.insider_min_count == 3 and cfg.max_negative_news_share == D("0.5")
