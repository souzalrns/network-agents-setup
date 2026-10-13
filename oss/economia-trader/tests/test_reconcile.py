"""Testnet/live gaps closed: real fills, stops resting on the exchange, drawdown on the real equity."""

import json
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import offline_ccxt

from economia_trader import RiskLimits, TradeProposal, Trader
from economia_trader.exchanges.alpaca_py import AlpacaPy
from economia_trader.exchanges.base import ExchangeError, KeyCheck, OrderStatus, Ticker
from economia_trader.exchanges.ccxt_spot import CcxtSpot
from economia_trader.grid import GridBot, GridConfig
from economia_trader.journal import Journal
from economia_trader.safety import ENV_ALLOW_TESTNET, KillSwitch, Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.example.json").read_text()))
ENV = {ENV_ALLOW_TESTNET: "1"}


class Venue:
    """A protocol-level fake exchange: we script what it says about each order."""

    name = "venue"
    supports_testnet = True

    def __init__(self, price="50000", stops=True):
        self.price, self.stops_ok = D(price), stops
        self.status: dict[str, list[OrderStatus]] = {}
        self.placed, self.stops, self.cancelled = [], [], []
        self.balance = D(0)
        self.equity_value = D("1000")

    def ticker(self, s):
        return Ticker(s, self.price, None, None)

    def check_key(self):
        return KeyCheck(True, False, False, {})

    def place_order(self, intent):
        oid = f"o{len(self.placed) + 1}"
        self.placed.append((oid, intent.side, intent.qty))
        return {"order_id": oid, "symbol": intent.symbol, "side": intent.side, "qty": str(intent.qty)}

    def order_status(self, symbol, oid):
        seq = self.status.get(oid) or [OrderStatus(oid, "open", D(0), None)]
        return seq.pop(0) if len(seq) > 1 else seq[0]

    def place_stop(self, symbol, qty, stop, coid):
        if not self.stops_ok:
            raise ExchangeError("venue: no exchange-side stop on spot; the stop stays client-side")
        sid = f"s{len(self.stops) + 1}"
        self.stops.append((sid, qty, stop))
        return {"order_id": sid, "qty": str(qty), "stop": str(stop)}

    def cancel_order(self, symbol, oid):
        self.cancelled.append(oid)

    def position_qty(self, symbol):
        return self.balance

    def account_equity(self, marks):
        return self.equity_value


def trader(tmp, venue, mode=Mode.TESTNET):
    t = Trader(
        venue,
        mode=mode,
        limits=LIMITS,
        journal=Journal(tmp / "j.jsonl"),
        kill_switch=KillSwitch(tmp / "KILL", env={}),
        env=ENV,
    )
    t.verify_key()
    return t


def kinds(tmp):
    return [json.loads(x)["kind"] for x in (tmp / "j.jsonl").read_text().splitlines()]


BUY = TradeProposal("BTCUSDT", "buy", "0.0008", stop_loss="49000")


# ---- fills ----


def test_books_the_exchange_fills_partial_then_full(tmp_path):
    v = Venue()
    v.status["o1"] = [
        OrderStatus("o1", "partially_filled", D("0.0003"), D("50010")),
        OrderStatus("o1", "filled", D("0.0008"), D("50020"), D("0.04")),
    ]
    t = trader(tmp_path, v)
    assert t.submit(BUY).status == "sent"
    pos = t.state.positions["BTCUSDT"]
    assert pos.qty == D("0.0003") and pos.avg_price == D("50010") and "o1" in t.pending
    t.reconcile()
    assert t.state.positions["BTCUSDT"].qty == D("0.0008") and t.pending == {}
    fills = [
        json.loads(x)["payload"]
        for x in (tmp_path / "j.jsonl").read_text().splitlines()
        if json.loads(x)["kind"] == "fill"
    ]
    assert [(f["qty"], f["price"], f["source"]) for f in fills] == [
        ("0.0003", "50010", "exchange"),
        ("0.0005", "50020", "exchange"),
    ]


def test_unfilled_order_books_nothing(tmp_path):
    v = Venue()
    v.status["o1"] = [OrderStatus("o1", "canceled", D(0), None)]
    t = trader(tmp_path, v)
    t.submit(BUY)
    assert t.state.positions == {} and t.pending == {} and "order_unfilled" in kinds(tmp_path)
    assert v.stops == []  # no position, no stop on the exchange


# ---- stops on the exchange ----


def test_stop_rests_on_the_exchange_and_its_fill_closes_the_position(tmp_path):
    v = Venue()
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.0008"), D("50000"))]
    t = trader(tmp_path, v)
    t.submit(BUY)
    assert v.stops == [("s1", D("0.0008"), D("49000"))] and t.exchange_stops["BTCUSDT"]["order_id"] == "s1"
    assert t.check_stops({"BTCUSDT": D("48000")}) == []  # the exchange's job now: no second sell
    v.status["s1"] = [OrderStatus("s1", "filled", D("0.0008"), D("48990"))]
    t.reconcile()
    assert t.state.positions == {} and t.exchange_stops == {} and "BTCUSDT" not in t.stops
    assert t.state.realized_today == (D("48990") - D("50000")) * D("0.0008")


def test_trader_exit_cancels_the_resting_stop_first(tmp_path):
    v = Venue()
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.0008"), D("50000"))]
    v.status["o2"] = [OrderStatus("o2", "filled", D("0.0008"), D("51000"))]
    t = trader(tmp_path, v)
    t.submit(BUY)
    t.submit(TradeProposal("BTCUSDT", "sell", "0.0008", rationale="take-profit"))
    assert v.cancelled == ["s1"] and t.state.positions == {} and len(v.stops) == 1


def test_venue_without_exchange_stops_keeps_the_client_side_stop(tmp_path):
    v = Venue(stops=False)
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.0008"), D("50000"))]
    v.status["o2"] = [OrderStatus("o2", "filled", D("0.0008"), D("48900"))]
    t = trader(tmp_path, v)
    t.submit(BUY)
    t.reconcile()
    assert kinds(tmp_path).count("stop_client_side") == 1  # said once, not every tick
    out = t.check_stops({"BTCUSDT": D("48900")})
    assert [o.status for o in out] == ["sent"] and t.state.positions == {}


def test_a_dropped_day_stop_is_placed_again(tmp_path):
    v = Venue()
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.0008"), D("50000"))]
    t = trader(tmp_path, v)
    t.submit(BUY)
    v.status["s1"] = [OrderStatus("s1", "canceled", D(0), None)]  # e.g. an Alpaca DAY stop at the close
    t.reconcile()
    assert "stop_dropped" in kinds(tmp_path) and [s[0] for s in v.stops] == ["s1", "s2"]
    assert t.exchange_stops["BTCUSDT"]["order_id"] == "s2"


# ---- position check ----


def test_sync_positions_only_adjusts_down(tmp_path):
    v = Venue()
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.0008"), D("50000"))]
    t = trader(tmp_path, v)
    t.submit(BUY)
    v.balance = D("0.0003")  # someone sold on the exchange
    rec = t.sync_positions()
    assert t.state.positions["BTCUSDT"].qty == D("0.0003") and rec[0]["action"] == "book adjusted down"
    v.balance = D("2")  # the owner's own coins: never adopted
    rec = t.sync_positions()
    assert t.state.positions["BTCUSDT"].qty == D("0.0003") and rec[0]["action"].startswith("none")


# ---- the grid loop on testnet: persistence and real-equity drawdown ----


def test_grid_testnet_persists_orders_and_kills_on_real_drawdown(tmp_path):
    v = Venue(price="100000")
    v.status["o1"] = [OrderStatus("o1", "filled", D("0.00008"), D("100000"))]
    cfg = GridConfig.from_mapping(
        {"symbol": "BTCUSDT", "lower": "94000", "upper": "106000", "levels": 6, "order_notional": "8", "max_lots": 4}
    )
    bot = GridBot(v, mode=Mode.TESTNET, limits=LIMITS, config=cfg, state_dir=tmp_path, env=ENV)
    bot.trader.verify_key()
    out = bot.run_once()
    assert out["action"]["status"] == "sent" and bot.trader.state.positions["BTCUSDT"].qty == D("0.00008")
    saved = json.loads((tmp_path / "state.json").read_text())
    assert saved["exchange_stops"]["BTCUSDT"]["order_id"] == "s1"
    bot2 = GridBot(v, mode=Mode.TESTNET, limits=LIMITS, config=cfg, state_dir=tmp_path, env=ENV)
    assert bot2.trader.exchange_stops == bot.trader.exchange_stops
    v.equity_value = D("800")  # the exchange's own equity fell 20 % from the 1000 peak
    bot2.trader.verify_key()
    bot2.peak = D("1000")
    bot2.run_once()
    assert bot2.kill_switch.engaged() and "auto_kill" in kinds_from(tmp_path / "journal.jsonl")


def kinds_from(path):
    return [json.loads(x)["kind"] for x in path.read_text().splitlines()]


# ---- the real adapters (no network) ----


def test_ccxt_bybit_status_stop_balance_and_equity():
    client = offline_ccxt("bybit")
    ex = CcxtSpot("bybit", "testnet", client=client)
    client.book["x1"] = {"id": "x1", "status": "open", "filled": 0.0004, "average": 50001, "fee": {"cost": 0.02}}
    st = ex.order_status("BTCUSDT", "x1")
    assert (st.status, st.filled_qty, st.avg_price, st.fee) == ("partially_filled", D("0.0004"), D("50001"), D("0.02"))
    client.book["x2"] = {"id": "x2", "status": "canceled", "filled": 0.0004, "average": 50001}
    assert ex.order_status("BTCUSDT", "x2").status == "filled"  # cancelled after a partial: final
    res = ex.place_stop("BTCUSDT", D("0.001"), D("49000.123"), "stop-abc")
    (_, args, _kw) = [c for c in client.calls if c[0] == "create_order"][-1]
    assert args[:4] == ("BTC/USDT", "market", "sell", 0.001) and args[5]["triggerPrice"] == 49000.12  # Bybit tick 0.01
    assert res["order_id"].startswith("s-")
    client.balance.update({"USDT": 900, "BTC": 0.002})
    assert ex.position_qty("BTCUSDT") == D("0.002")
    assert ex.account_equity({"BTCUSDT": D("50000")}) == D("1000")
    ex.cancel_order("BTCUSDT", res["order_id"])
    assert client.book[res["order_id"]]["status"] == "canceled"


def test_ccxt_mexc_has_no_exchange_stop_and_mainnet_stays_locked():
    with pytest.raises(ExchangeError, match="client-side"):
        CcxtSpot("mexc", "testnet", client=offline_ccxt("mexc")).place_stop("BTCUSDT", D("1"), D("1"), "s")
    with pytest.raises(ExchangeError, match="mainnet orders are disabled"):
        CcxtSpot("bybit", "mainnet", client=offline_ccxt("bybit")).place_stop("BTCUSDT", D("1"), D("1"), "s")


class AlpacaTrading:
    def __init__(self):
        self.orders, self.cancelled = [], []

    def get_order_by_id(self, oid):
        return SimpleNamespace(
            id=oid, status=SimpleNamespace(value="partially_filled"), filled_qty="3", filled_avg_price="187.5"
        )

    def submit_order(self, req):
        self.orders.append(req)
        return SimpleNamespace(id="st-1")

    def cancel_order_by_id(self, oid):
        self.cancelled.append(oid)

    def get_open_position(self, sym):
        from alpaca.common.exceptions import APIError

        if sym == "NONE":
            raise APIError('{"code":40410000,"message":"position does not exist"}')
        return SimpleNamespace(qty="3")

    def get_account(self):
        return SimpleNamespace(equity="1234.5")


def test_alpaca_status_stops_positions_equity():
    tr = AlpacaTrading()
    ex = AlpacaPy("paper", trading=tr, data=object())
    st = ex.order_status("SPY", "a-1")
    assert (st.status, st.filled_qty, st.avg_price) == ("partially_filled", D("3"), D("187.5"))
    ex.place_stop("SPY", D("3"), D("180"), "stop-1")
    ex.place_stop("SPY", D("0.5"), D("180"), "stop-2")
    tif = [str(getattr(o.time_in_force, "value", o.time_in_force)).lower() for o in tr.orders]
    assert tif == ["gtc", "day"] and tr.orders[0].stop_price == 180.0  # fractional stops must be DAY
    assert ex.position_qty("SPY") == D("3") and ex.position_qty("NONE") == D(0)
    assert ex.account_equity({}) == D("1234.5")
    ex.cancel_order("SPY", "st-1")
    assert tr.cancelled == ["st-1"]
