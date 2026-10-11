import json
from decimal import Decimal as D

import pytest

from economia_trader.backtest import run_backtest, size_for_risk, sma_cross
from economia_trader.cli import main
from economia_trader.exchanges.base import Kline

HOUR = 3_600_000


def _series():
    # flat, rally, crash: one long entry on the cross up, an exit on the cross down or the stop
    closes = [100] * 35 + [100 + i for i in range(1, 31)] + [130 - 2 * i for i in range(1, 31)]
    bars = []
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c
        bars.append(Kline(i * HOUR, D(o), D(max(o, c)) + 1, D(min(o, c)) - 1, D(c), D(10)))
    return bars


def test_size_for_risk_respects_both_caps(limits):
    qty = size_for_risk(D("100"), D("97"), limits)
    loss = qty * 3 + qty * 100 * limits.fee_rate * 2
    assert loss <= limits.max_loss_per_trade and qty * 100 <= limits.max_order_notional
    assert size_for_risk(D("100"), D("101"), limits) == 0


def test_backtest_no_lookahead_and_round_trip(limits):
    bars = _series()
    run = run_backtest(bars, sma_cross(5, 20), symbol="BTCUSDT", limits=limits, cash="1000")
    buys = [f for f in run.fills if f.side == "buy"]
    sells = [f for f in run.fills if f.side == "sell"]
    assert len(buys) == 1 and len(sells) == 1
    # filled at the *next* bar's open (+5 bps), never at the signal bar's close
    opens = {b.open * (1 + D("0.0005")) for b in bars}
    assert buys[0].price in opens
    s = run.summary()
    assert s["trades_closed"] == 1 and len(run.equity_curve) == len(bars)
    assert D(s["final_equity"]) > 0


def test_cli_backtest_from_file(tmp_path, capsys):
    kfile = tmp_path / "k.json"
    kfile.write_text(
        json.dumps([[b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close), "10"] for b in _series()])
    )
    lfile = tmp_path / "l.json"
    lfile.write_text(
        json.dumps(
            {
                "max_order_notional": "100",
                "max_loss_per_trade": "5",
                "max_daily_loss": "10",
                "allowed_symbols": ["BTCUSDT"],
            }
        )
    )
    assert (
        main(
            [
                "backtest",
                "--symbol",
                "BTCUSDT",
                "--limits",
                str(lfile),
                "--klines-file",
                str(kfile),
                "--fast",
                "5",
                "--slow",
                "20",
            ]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["bars"] == 95 and out["trades_closed"] == 1


def test_cli_kill_gate_and_journal(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ECONOMIA_TRADER_LIVE", raising=False)
    monkeypatch.delenv("ECONOMIA_TRADER_KILL", raising=False)
    assert main(["kill", "--reason", "drill"]) == 0
    capsys.readouterr()
    assert main(["gate", "--mode", "live"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["kill_switch"] is True and rep["live_acknowledged"] is False
    assert main(["unkill"]) == 0

    from economia_trader import Journal

    Journal(tmp_path / "j.jsonl").append("x", {})
    assert main(["verify-journal", str(tmp_path / "j.jsonl")]) == 0


def test_cli_trade_paper(tmp_path, monkeypatch, capsys):
    from conftest import offline_ccxt

    from economia_trader import cli
    from economia_trader.exchanges import CcxtSpot

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ECONOMIA_TRADER_KILL", raising=False)
    monkeypatch.setattr(cli, "make_exchange", lambda name, mode: CcxtSpot("bybit", client=offline_ccxt("bybit")))
    lfile = tmp_path / "l.json"
    lfile.write_text(
        json.dumps(
            {
                "max_order_notional": "100",
                "max_loss_per_trade": "5",
                "max_daily_loss": "10",
                "allowed_symbols": ["BTCUSDT"],
            }
        )
    )
    rc = main(
        ["trade", "--symbol", "BTCUSDT", "--side", "buy", "--qty", "0.001", "--stop", "49000", "--limits", str(lfile)]
    )
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "filled"
    assert (tmp_path / ".economia-trader" / "journal.jsonl").exists()


def test_cli_check_key_needs_non_paper(capsys):
    assert main(["check-key", "--mode", "paper"]) == 2


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0 and "economia-trader" in capsys.readouterr().out
