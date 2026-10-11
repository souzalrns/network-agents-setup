import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits, verify
from economia_trader.exchanges.base import ExchangeError, Ticker
from economia_trader.flow import FlowPrint, JsonFileFlowSource, StaticFlowSource
from economia_trader.report import report
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode
from economia_trader.screen import ScreenConfig, screen

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
AS_OF = "2026-10-10T12:00:00+00:00"
T0 = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def fp(
    id,
    ticker="ACME",
    sentiment="bullish",
    premium="60000",
    volume=100,
    oi=1000,
    dte=30,
    ivr="85",
    cap="3000000000",
    avail="2026-10-10T11:00:00+00:00",
    earnings=None,
):
    return FlowPrint(
        id, ticker, sentiment, D(premium), volume, oi, dte, D(ivr), D(cap), "2026-10-09T20:00:00+00:00", avail, earnings
    )


# ---- screen ----


def test_example_file_screen():
    prints = JsonFileFlowSource(EXAMPLES / "flow.example.json").prints(AS_OF)
    res = screen(prints, ScreenConfig(), AS_OF)
    assert [c.ticker for c in res.candidates] == ["ACME"]
    assert res.dropped == {"MEGA": ["market cap out of range"], "BETA": ["earnings in 4d (blocked)"]}
    assert res.candidates[0].print_ids == ("f1", "f2")


def test_filters_and_reasons():
    prints = [
        fp("a1", "LOWIV", ivr="50"),
        fp("b1", "MIXED"),
        fp("b2", "MIXED", sentiment="bearish", premium="60000"),
        fp("c1", "NEWPOS", volume=5000, oi=1000),
        fp("d1", "SMALL", premium="5000"),  # order-level noise: silently ignored
        fp("e1", "SHORTDTE", dte=3),
        fp("f1", "OK"),
    ]
    res = screen(prints, ScreenConfig(), AS_OF)
    assert [c.ticker for c in res.candidates] == ["OK"]
    assert res.dropped["LOWIV"] == ["iv_rank 50 < 80"]
    assert res.dropped["MIXED"] == ["bullish 50% < 70%"]
    assert res.dropped["NEWPOS"][0].startswith("vol/oi 5.00 >= 0.5")
    assert "SMALL" not in res.dropped and "SHORTDTE" not in res.dropped


def test_vol_oi_inverted_hypothesis():
    cfg = ScreenConfig(vol_oi_max=None, vol_oi_min=D("1"))
    res = screen([fp("x", "NEWPOS", volume=5000, oi=1000), fp("y", "OLD", volume=100, oi=1000)], cfg, AS_OF)
    assert [c.ticker for c in res.candidates] == ["NEWPOS"]
    assert res.dropped["OLD"][0].startswith("vol/oi 0.10 <= 1")


def test_no_lookahead_and_earnings_flag_only():
    future = fp("z", "LATE", avail="2026-10-10T13:00:00+00:00")
    assert screen([future], ScreenConfig(), AS_OF).candidates == []
    soon = fp("e", "EARN", earnings="2026-10-13")
    flagged = screen([soon], ScreenConfig(block_earnings_days=None), AS_OF).candidates[0]
    assert flagged.earnings_soon is True


def test_ranking_and_cap():
    prints = [fp(f"p{i}", f"T{i}") for i in range(5)] + [fp("q", "T0", sentiment="bearish", premium="40000")]
    res = screen(prints, ScreenConfig(max_candidates=2), AS_OF)
    assert len(res.candidates) == 2 and "T0" not in [c.ticker for c in res.candidates]
    assert any("ranked below" in r for rs in res.dropped.values() for r in rs)


def test_config_version_and_validation():
    a, b = ScreenConfig(), ScreenConfig(min_iv_rank=D("70"))
    assert a.version != b.version and a.version == ScreenConfig(note="other").version
    assert RunConfig().version != RunConfig(stop_pct=D("0.05")).version
    with pytest.raises(ValueError, match="unknown screen config"):
        ScreenConfig.from_mapping({"min_ivr": 1})
    cfg = RunConfig.from_mapping(json.loads((EXAMPLES / "run.example.json").read_text()))
    assert cfg.screen.vol_oi_min is None and cfg.max_hold_days == 15


# ---- runner ----


class FakeExchange:
    name = "fake"
    supports_testnet = False

    def __init__(self, prices):
        self.prices = prices
        self.down = False

    def ticker(self, symbol):
        if self.down:
            raise ExchangeError("timeout")
        return Ticker(symbol, D(self.prices[symbol]), None, None)


LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))


def _runner(tmp_path, ex, clock, config=None, prints=None):
    return Runner(
        ex,
        StaticFlowSource(prints or [fp("f1", "ACME")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=config or RunConfig(),
        state_dir=tmp_path,
        cash="100",
        env={},
        clock=clock,
    )


def test_entry_then_take_profit_across_restart(tmp_path):
    ex = FakeExchange({"ACME": "20"})
    r = _runner(tmp_path, ex, lambda: T0)
    s = r.run_once()
    assert s["entries"] == [{"ticker": "ACME", "status": "filled", "reasons": []}]
    pos = r.trader.state.positions["ACME"]
    assert pos.qty == D("1.250000") and r.trader.stops["ACME"] == D("18.40")

    ex.prices["ACME"] = "23.5"
    r2 = _runner(tmp_path, ex, lambda: T0 + timedelta(days=1))  # restart: state comes from disk
    assert "ACME" in r2.trader.state.positions
    s2 = r2.run_once()
    assert s2["exits"] == [{"ticker": "ACME", "status": "filled", "why": "take-profit"}]
    rep = report(tmp_path / "journal.jsonl")
    v = rep["by_version"][f"whale-screen@{RunConfig().version}"]
    assert v["entries"] == 1 and v["closed"] == 1 and v["win_rate"] == 1.0 and D(v["pnl"]) > 0
    assert verify(tmp_path / "journal.jsonl") == []


def test_stop_and_time_exits(tmp_path):
    ex = FakeExchange({"ACME": "20"})
    r = _runner(tmp_path, ex, lambda: T0)
    r.run_once()
    ex.prices["ACME"] = "18"
    s = _runner(tmp_path, ex, lambda: T0 + timedelta(days=1), prints=[]).run_once()
    assert s["exits"][0]["why"] == "stop" and s["exits"][0]["status"] == "filled"
    rep = report(tmp_path / "journal.jsonl")
    assert rep["by_version"][f"whale-screen@{RunConfig().version}"]["win_rate"] == 0.0

    ex2 = FakeExchange({"ACME": "20"})
    d2 = tmp_path / "t"
    _runner(d2, ex2, lambda: T0).run_once()
    s = _runner(d2, ex2, lambda: T0 + timedelta(days=16), prints=[]).run_once()
    assert s["exits"] == [{"ticker": "ACME", "status": "filled", "why": "time-exit"}]


def test_auto_kill_on_drawdown_blocks_new_entries(tmp_path):
    ex = FakeExchange({"ACME": "20", "BETA": "10"})
    cfg = RunConfig(max_drawdown_pct=D("0.01"))
    _runner(tmp_path, ex, lambda: T0, config=cfg).run_once()
    ex.prices["ACME"] = "19"  # above the stop, but equity -1.3%
    r = _runner(tmp_path, ex, lambda: T0 + timedelta(hours=4), config=cfg, prints=[fp("b", "BETA")])
    s = r.run_once()
    assert s["auto_kill"].startswith("drawdown")
    assert r.kill_switch.engaged()
    assert s["entries"] == [{"ticker": "BETA", "status": "blocked", "reasons": ["kill_switch"]}]
    assert report(tmp_path / "journal.jsonl")["auto_kills"]


def test_auto_kill_after_errors_in_row(tmp_path):
    ex = FakeExchange({"ACME": "20"})
    _runner(tmp_path, ex, lambda: T0).run_once()  # hold a position so ticks need the exchange
    ex.down = True
    for i in range(3):
        r = _runner(tmp_path, ex, lambda i=i: T0 + timedelta(hours=i + 1))
        s = r.run_once()
        assert s["error"] == "timeout"
    assert r.kill_switch.engaged()
    assert json.loads((tmp_path / "state.json").read_text())["errors_in_row"] == 3


def test_run_forever_ticks(tmp_path):
    ex = FakeExchange({"ACME": "20"})
    slept = []
    n = _runner(tmp_path, ex, lambda: T0).run_forever(60, max_ticks=3, sleep=slept.append)
    assert n == 3 and slept == [60, 60]


def test_cli_screen_and_run_once(tmp_path, monkeypatch, capsys):
    from economia_trader import cli

    assert cli.main(["screen", "--flow-file", str(EXAMPLES / "flow.example.json"), "--as-of", AS_OF]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [c["ticker"] for c in out["candidates"]] == ["ACME"]

    monkeypatch.setattr(cli, "make_exchange", lambda name, mode: FakeExchange({"ACME": "20"}))
    flow = tmp_path / "flow.json"
    flow.write_text((EXAMPLES / "flow.example.json").read_text())
    rc = cli.main(
        [
            "run",
            "--mode",
            "paper",
            "--flow-file",
            str(flow),
            "--limits",
            str(EXAMPLES / "limits.stocks.example.json"),
            "--state-dir",
            str(tmp_path / "st"),
            "--once",
        ]
    )
    assert rc == 0
    capsys.readouterr()
    assert cli.main(["report", "--journal", str(tmp_path / "st" / "journal.jsonl")]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["open_positions"] == ["ACME"]
