"""Post-trade review (review.py): process graded apart from outcome, from the journal only."""

import importlib.util
import json
from decimal import Decimal as D
from pathlib import Path

from conftest import offline_ccxt

from economia_trader import Journal, KillSwitch, Mode, PaperBroker, TradeProposal, Trader
from economia_trader.cli import main
from economia_trader.exchanges import CcxtSpot
from economia_trader.review import review
from economia_trader.safety import ENV_ALLOW_TESTNET

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _paper(tmp_path, limits):
    return Trader(
        CcxtSpot("bybit", client=offline_ccxt("bybit")),
        mode=Mode.PAPER,
        limits=limits,
        journal=Journal(tmp_path / "j.jsonl"),
        broker=PaperBroker("1000"),
        kill_switch=KillSwitch(tmp_path / "KILL", env={}),
        env={},
    )


def test_paper_stop_exit_is_a_clean_loss_measured_in_r(tmp_path, limits):
    trader = _paper(tmp_path, limits)
    trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000", proposer="t@v1"))
    trader.check_stops({"BTCUSDT": D("48900")})
    out = review(tmp_path / "j.jsonl")
    assert out["open"] == [] and out["orphan_sells"] == 0
    (t,) = out["trades"]
    assert t["mode"] == "paper" and t["proposers"] == ["t@v1"] and t["exit_by"] == ["stop"]
    assert t["process"]["grade"] == "clean"  # a loss with a clean process is still clean
    assert t["costs"]["entry_slippage_bps"] == "5.0"  # the paper broker's 5 bps, against the mark
    assert D(t["outcome"]["net"]) < 0 and D(t["outcome"]["r"]) < 0
    assert D(t["costs"]["fees"]) > 0 and t["finding"]["type"] == "clean"
    (week,) = out["weeks"].values()
    assert week["closed"] == 1 and week["hit_rate"] == 0.0 and week["process"] == {"clean": 1}


def test_testnet_smoke_cycle_is_protected_on_the_exchange(tmp_path):
    spec = importlib.util.spec_from_file_location("smoke_testnet", EXAMPLES / "smoke_testnet.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    env = {ENV_ALLOW_TESTNET: "1", "BYBIT_API_KEY": "k", "BYBIT_API_SECRET": "s"}
    assert mod.smoke(
        "bybiteu",
        "BTCUSDT",
        "0.0002",
        EXAMPLES / "limits.example.json",
        tmp_path,
        client=offline_ccxt("bybiteu"),
        env=env,
    )
    (t,) = review(tmp_path / "journal.jsonl")["trades"]
    assert t["mode"] == "testnet" and t["exit_by"] == ["smoke"]
    assert t["process"]["protection"]["where"] == "exchange"
    assert t["process"]["protection"]["gap_s"] <= 60 and t["process"]["grade"] == "clean"
    assert t["outcome"]["r"] is not None and D(t["outcome"]["risk_1r"]) > 0


def _exchange_trade(journal, *, sell_price, mismatch=False, stop_placed=True):
    """The journal lines a testnet trade leaves, written directly (no exchange involved)."""
    journal.append(
        "proposal",
        {"id": "p1", "symbol": "BTCUSDT", "side": "buy", "qty": "0.001", "stop_loss": "49000", "proposer": "whale@v2"},
    )
    journal.append("assessment", {"proposal_id": "p1", "approved": True, "price": "50000", "loss_at_stop": "1"})
    journal.append("intent", {"mode": "testnet", "client_order_id": "c1", "proposal_id": "p1"})
    journal.append("order", {"order_id": "o1", "client_order_id": "c1", "side": "buy"})
    journal.append(
        "fill",
        {
            "source": "exchange",
            "order_id": "o1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "qty": "0.001",
            "price": "50010",
            "fee": "0.05",
            "stop_order": False,
        },
    )
    if stop_placed:
        journal.append("stop_placed", {"symbol": "BTCUSDT", "order_id": "s1"})
    if mismatch:
        journal.append("reconcile_mismatch", {"symbol": "BTCUSDT", "book": "0.001", "exchange": "0.0005"})
    journal.append(
        "proposal", {"id": "p2", "symbol": "BTCUSDT", "side": "sell", "qty": "0.001", "proposer": "take-profit"}
    )
    journal.append("assessment", {"proposal_id": "p2", "approved": True, "price": str(sell_price)})
    journal.append("intent", {"mode": "testnet", "client_order_id": "c2", "proposal_id": "p2"})
    journal.append("stop_cancelled", {"symbol": "BTCUSDT", "order_id": "s1", "why": "exit by the trader"})
    journal.append("order", {"order_id": "o2", "client_order_id": "c2", "side": "sell"})
    journal.append(
        "fill",
        {
            "source": "exchange",
            "order_id": "o2",
            "symbol": "BTCUSDT",
            "side": "sell",
            "qty": "0.001",
            "price": str(sell_price),
            "fee": "0.05",
            "stop_order": False,
        },
    )


def test_a_winning_trade_with_a_major_break_is_still_a_major_break(tmp_path):
    _exchange_trade(Journal(tmp_path / "j.jsonl"), sell_price=52000, mismatch=True)
    (t,) = review(tmp_path / "j.jsonl")["trades"]
    assert D(t["outcome"]["r"]) > 1  # (2 - 0.01 - 0.1) / 1R
    assert t["process"]["grade"] == "major break"
    assert t["finding"] == {"type": "break", "stage": "reconcile", "detail": "book 0.001 vs exchange 0.0005"}
    assert t["costs"]["entry_slippage_bps"] == "2.0" and t["exit_by"] == ["take-profit"]


def test_a_position_without_any_stop_is_a_major_break(tmp_path):
    _exchange_trade(Journal(tmp_path / "j.jsonl"), sell_price=50500, stop_placed=False)
    (t,) = review(tmp_path / "j.jsonl")["trades"]
    assert t["process"]["protection"]["where"] == "none"
    assert t["process"]["grade"] == "major break" and t["finding"]["stage"] == "protection"


def test_week_summary_expectancy_and_hit_rate(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    for i, (entry, exit_) in enumerate([("100", "120"), ("100", "90")]):  # +2R and -1R (1R = 10)
        j.append(
            "proposal",
            {"id": f"b{i}", "symbol": "ETHUSDT", "side": "buy", "qty": "1", "stop_loss": "90", "proposer": "grid@v1"},
        )
        j.append("assessment", {"proposal_id": f"b{i}", "approved": True, "price": entry, "loss_at_stop": "10"})
        j.append("intent", {"mode": "paper", "client_order_id": f"cb{i}", "proposal_id": f"b{i}"})
        j.append(
            "fill",
            {"client_order_id": f"cb{i}", "symbol": "ETHUSDT", "side": "buy", "qty": "1", "price": entry, "fee": "0"},
        )
        j.append("proposal", {"id": f"s{i}", "symbol": "ETHUSDT", "side": "sell", "qty": "1", "proposer": "exit"})
        j.append("assessment", {"proposal_id": f"s{i}", "approved": True, "price": exit_})
        j.append("intent", {"mode": "paper", "client_order_id": f"cs{i}", "proposal_id": f"s{i}"})
        j.append(
            "fill",
            {"client_order_id": f"cs{i}", "symbol": "ETHUSDT", "side": "sell", "qty": "1", "price": exit_, "fee": "0"},
        )
    out = review(tmp_path / "j.jsonl")
    assert [t["outcome"]["r"] for t in out["trades"]] == ["2.00", "-1.00"]
    (week,) = out["weeks"].values()
    assert week["hit_rate"] == 0.5 and week["expectancy_r"] == "0.50"
    assert week["avg_win_r"] == "2.00" and week["avg_loss_r"] == "-1.00" and week["largest_loss"] == "-10.0000"
    assert review(tmp_path / "j.jsonl", since="2999-01-01")["trades"] == []


def test_open_position_and_orphan_sell_are_reported_not_reviewed(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    j.append("fill", {"client_order_id": "x", "symbol": "ETHUSDT", "side": "sell", "qty": "1", "price": "1"})
    j.append("fill", {"client_order_id": "y", "symbol": "BTCUSDT", "side": "buy", "qty": "1", "price": "1"})
    out = review(tmp_path / "j.jsonl")
    assert out["trades"] == [] and out["open"] == ["BTCUSDT"] and out["orphan_sells"] == 1


def test_cli_review(tmp_path, capsys):
    _exchange_trade(Journal(tmp_path / "j.jsonl"), sell_price=50500)
    assert main(["review", "--journal", str(tmp_path / "j.jsonl")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["trades"][0]["process"]["grade"] == "clean" and len(out["weeks"]) == 1
