from decimal import Decimal as D

import pytest
from conftest import offline_ccxt

from economia_trader import (
    EconomicEvent,
    ExecutionBlocked,
    Journal,
    KillSwitch,
    Mode,
    PaperBroker,
    TradeProposal,
    Trader,
    verify,
)
from economia_trader.exchanges import CcxtSpot
from economia_trader.safety import ENV_ALLOW_TESTNET, ENV_LIVE, LIVE_ACK


def _paper(tmp_path, limits, cash="1000"):
    ks = KillSwitch(tmp_path / "KILL", env={})
    journal = Journal(tmp_path / "j.jsonl")
    trader = Trader(
        CcxtSpot("bybit", client=offline_ccxt("bybit")),
        mode=Mode.PAPER,
        limits=limits,
        journal=journal,
        broker=PaperBroker(cash),
        kill_switch=ks,
        env={},
    )
    return trader, journal, ks


def test_paper_buy_then_stop_exit(tmp_path, limits):
    trader, journal, _ = _paper(tmp_path, limits)
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000", proposer="t"))
    assert out.status == "filled" and out.fill.price == D("50025.0000")  # 5 bps slippage
    assert trader.stops == {"BTCUSDT": D("49000")}
    exits = trader.check_stops({"BTCUSDT": D("48900")})
    assert [e.status for e in exits] == ["filled"] and "BTCUSDT" not in trader.state.positions
    assert trader.stops == {}
    kinds = [e["kind"] for e in journal.entries()]
    assert kinds[:4] == ["proposal", "assessment", "intent", "fill"]
    assert verify(journal.path) == []


def test_rejection_is_journaled(tmp_path, limits):
    trader, journal, _ = _paper(tmp_path, limits)
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001"))
    assert out.status == "rejected" and "buy without stop_loss" in out.reasons
    assert journal.entries()[-1]["payload"]["approved"] is False


def test_kill_switch_blocks(tmp_path, limits):
    trader, journal, ks = _paper(tmp_path, limits)
    ks.engage()
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    assert out.status == "blocked" and out.reasons == ["kill_switch"]
    assert journal.entries()[-1]["kind"] == "blocked"


def test_broker_cash_limit(tmp_path, limits):
    trader, _, _ = _paper(tmp_path, limits, cash="10")
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    assert out.status == "rejected" and "insufficient cash" in out.reasons[0]


def test_paper_needs_broker(tmp_path, limits):
    with pytest.raises(ValueError):
        Trader(
            CcxtSpot("bybit", client=offline_ccxt("bybit")),
            mode=Mode.PAPER,
            limits=limits,
            journal=Journal(tmp_path / "j"),
        )


def _testnet(tmp_path, limits, env, mode=Mode.TESTNET, approver=None, perms=None):
    client = offline_ccxt("bybit", perms=perms)
    network = "testnet" if mode is Mode.TESTNET else "mainnet"
    ex = CcxtSpot("bybit", network, client=client, allow_mainnet_orders=mode is Mode.LIVE)
    kw = {"approver": approver} if approver else {}
    trader = Trader(
        ex,
        mode=mode,
        limits=limits,
        journal=Journal(tmp_path / "j.jsonl"),
        kill_switch=KillSwitch(tmp_path / "KILL", env={}),
        env=env,
        **kw,
    )
    return trader, client


def _orders(client):
    return [c for c in client.calls if c[0] == "create_order"]


def test_testnet_order_flow(tmp_path, limits):
    trader, client = _testnet(tmp_path, limits, {ENV_ALLOW_TESTNET: "1"})
    assert "testnet" in str(client.urls["api"])  # real ccxt sandbox URLs
    trader.verify_key()
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    assert out.status == "sent" and out.order["order_id"] == "o-9"
    (_, args, _kw) = _orders(client)[-1]
    assert args[:5] == ("BTC/USDT", "market", "buy", 0.001, None)
    assert args[5]["clientOrderId"].startswith("et")
    assert trader.state.positions["BTCUSDT"].qty == D("0.001")


def test_testnet_without_env_never_calls_order(tmp_path, limits):
    trader, client = _testnet(tmp_path, limits, {})
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    assert out.status == "blocked" and out.reasons == ["testnet_disabled"]
    assert _orders(client) == []


def test_withdraw_key_refused(tmp_path, limits):
    perms = {"Wallet": ["Withdraw"], "Spot": ["SpotTrade"]}
    trader, _ = _testnet(tmp_path, limits, {ENV_ALLOW_TESTNET: "1"}, perms=perms)
    with pytest.raises(ExecutionBlocked) as e:
        trader.verify_key()
    assert e.value.code == "key_can_withdraw" and trader.key_checked is False


def test_live_default_denies_then_human_approves(tmp_path, limits):
    env = {ENV_LIVE: LIVE_ACK}
    trader, client = _testnet(tmp_path, limits, env, mode=Mode.LIVE)
    trader.verify_key()
    out = trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    assert out.status == "blocked" and out.reasons == ["awaiting_approval"]
    assert _orders(client) == []

    trader2, client2 = _testnet(tmp_path, limits, env, mode=Mode.LIVE, approver=lambda i, a: True)
    trader2.verify_key()
    assert trader2.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000")).status == "sent"
    assert "testnet" not in str(client2.urls["api"]) and len(_orders(client2)) == 1


def test_journal_tamper_detected(tmp_path, limits):
    trader, journal, _ = _paper(tmp_path, limits)
    trader.submit(TradeProposal("BTCUSDT", "buy", "0.001", stop_loss="49000"))
    lines = journal.path.read_text().splitlines()
    lines[1] = lines[1].replace('"approved": true', '"approved": false')
    journal.path.write_text("\n".join(lines) + "\n")
    assert verify(journal.path)  # the next line's prev hash no longer matches
    # a reopened journal continues the chain from the tail
    j2 = Journal(tmp_path / "fresh.jsonl")
    j2.append("a", {})
    Journal(tmp_path / "fresh.jsonl").append("b", {})
    assert verify(tmp_path / "fresh.jsonl") == []


def test_economic_event_four_clocks():
    ev = EconomicEvent(
        "e1",
        "fred",
        "cpi",
        {"v": 3.1},
        "2026-09-30T00:00:00+00:00",
        "2026-10-10T12:30:00+00:00",
        "2026-10-10T12:31:00+00:00",
        "2026-10-10T12:31:00+00:00",
    )
    assert not ev.usable_at("2026-10-10T12:30:30+00:00") and ev.usable_at("2026-10-10T13:00:00+00:00")
    with pytest.raises(ValueError, match="look-ahead"):
        EconomicEvent(
            "e2",
            "fred",
            "cpi",
            {},
            "2026-09-30T00:00:00+00:00",
            "2026-10-10T12:30:00+00:00",
            "2026-10-10T12:31:00+00:00",
            "2026-10-10T12:00:00+00:00",
        )
