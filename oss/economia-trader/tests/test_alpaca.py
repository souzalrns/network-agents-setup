from datetime import datetime, timezone
from decimal import Decimal as D

import pytest
from conftest import FakeTransport

from economia_trader import Journal, KillSwitch, Mode, TradeProposal, Trader
from economia_trader.exchanges import Alpaca, Credentials, ExchangeError, make_exchange
from economia_trader.safety import ENV_ALLOW_TESTNET

CREDS = Credentials("PKTEST", "SECRETX")
FIXED = lambda: datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc)  # noqa: E731

DATA = {
    "/v2/stocks/AAPL/quotes/latest": (200, {"quote": {"bp": 229.9, "ap": 230.1}}),
    "/v2/stocks/AAPL/trades/latest": (200, {"trade": {"p": 230.0}}),
}


def test_ticker_uses_data_api_with_key_headers():
    t = FakeTransport(DATA)
    tick = Alpaca(credentials=CREDS, transport=t).ticker("aapl")
    assert tick.last == D("230.0") and tick.ask == D("230.1")
    call = t.calls[0]
    assert call["url"].startswith("https://data.alpaca.markets/v2/stocks/AAPL/quotes/latest")
    assert call["query"]["feed"] == "iex"
    assert call["headers"]["APCA-API-KEY-ID"] == "PKTEST" and call["headers"]["APCA-API-SECRET-KEY"] == "SECRETX"


def test_bars_sorted_and_timeframe():
    bars = {
        "bars": [
            {"t": "2026-10-09T15:00:00Z", "o": 2, "h": 3, "l": 1, "c": 2.5, "v": 9},
            {"t": "2026-10-09T14:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 5},
        ]
    }
    t = FakeTransport({"/v2/stocks/AAPL/bars": (200, bars)})
    ks = Alpaca(credentials=CREDS, transport=t, clock=FIXED).klines("AAPL", "1h", 2)
    assert [k.close for k in ks] == [D("1.5"), D("2.5")]
    q = t.calls[0]["query"]
    assert q["timeframe"] == "1Hour" and q["limit"] == "2" and q["start"] == "2026-10-09T10:00:00Z"


def test_needs_keys_even_for_data():
    with pytest.raises(ExchangeError, match="ALPACA_API_KEY"):
        Alpaca(transport=FakeTransport(DATA)).ticker("AAPL")
    with pytest.raises(ExchangeError, match="ALPACA_SECRET_KEY"):
        make_exchange("alpaca", Mode.PAPER, env={})


def test_paper_account_order_and_live_refused_by_default():
    t = FakeTransport({"/v2/orders": (200, {"id": "a-1"})})
    from economia_trader import OrderIntent

    out = Alpaca("paper", credentials=CREDS, transport=t).place_order(
        OrderIntent("AAPL", "buy", D("0.25000"), client_order_id="etq")
    )
    call = t.calls[0]
    assert call["url"] == "https://paper-api.alpaca.markets/v2/orders"
    assert call["body"] == {
        "symbol": "AAPL",
        "qty": "0.25",
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "client_order_id": "etq",
    }
    assert out["order_id"] == "a-1"
    with pytest.raises(ExchangeError, match="live orders are disabled"):
        Alpaca("live", credentials=CREDS, transport=t).place_order(OrderIntent("AAPL", "buy", D("1")))


def test_check_key_and_errors():
    acc = {"status": "ACTIVE", "trading_blocked": False, "account_blocked": False, "pattern_day_trader": False}
    t = FakeTransport({"/v2/account": (200, acc)})
    kc = Alpaca(credentials=CREDS, transport=t).check_key()
    assert kc.safe_for_trading and kc.detail["network"] == "paper"
    blocked = FakeTransport({"/v2/account": (200, {**acc, "trading_blocked": True})})
    assert not Alpaca(credentials=CREDS, transport=blocked).check_key().can_trade
    bad = FakeTransport({"/v2/account": (403, {"message": "forbidden."})})
    with pytest.raises(ExchangeError, match="forbidden"):
        Alpaca(credentials=CREDS, transport=bad).check_key()


def test_factory_networks():
    env = {"ALPACA_API_KEY": "k", "ALPACA_SECRET_KEY": "s"}
    assert make_exchange("alpaca", Mode.PAPER, env=env).network == "paper"
    assert make_exchange("alpaca", Mode.TESTNET, env=env).network == "paper"
    live = make_exchange("alpaca", Mode.LIVE, env=env)
    assert live.network == "live" and live.allow_live_orders


def test_trader_on_alpaca_paper_account(tmp_path):
    from economia_trader import RiskLimits

    limits = RiskLimits.from_mapping(
        {"max_order_notional": "100", "max_loss_per_trade": "2", "max_daily_loss": "5", "allowed_symbols": ["AAPL"]}
    )
    acc = {"status": "ACTIVE", "trading_blocked": False, "account_blocked": False}
    t = FakeTransport({**DATA, "/v2/account": (200, acc), "/v2/orders": (200, {"id": "a-9"})})
    trader = Trader(
        Alpaca("paper", credentials=CREDS, transport=t),
        mode=Mode.TESTNET,
        limits=limits,
        journal=Journal(tmp_path / "j.jsonl"),
        kill_switch=KillSwitch(tmp_path / "K", env={}),
        env={ENV_ALLOW_TESTNET: "1"},
    )
    trader.verify_key()
    out = trader.submit(TradeProposal("AAPL", "buy", "0.2", stop_loss="225", proposer="t"))
    assert out.status == "sent" and out.order["order_id"] == "a-9"
    assert t.calls[-1]["url"] == "https://paper-api.alpaca.markets/v2/orders"
