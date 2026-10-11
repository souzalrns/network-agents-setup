"""Adapters on mature libraries: real ccxt (offline markets) and real alpaca-py request objects."""

from datetime import datetime, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import ccxt
import pytest
from conftest import offline_ccxt

from economia_trader import Mode, OrderIntent
from economia_trader.exchanges import AlpacaPy, CcxtSpot, Credentials, ExchangeError, make_exchange

# ---- ccxt: Bybit / MEXC ----


def test_ticker_and_klines_accept_compact_and_unified_symbols():
    client = offline_ccxt("bybit")
    ex = CcxtSpot("bybit", client=client)
    assert ex.ticker("btcusdt").last == D("50000") and ex.ticker("BTC/USDT").symbol == "BTCUSDT"
    ks = ex.klines("BTCUSDT", "1h", 2)
    assert [k.close for k in ks] == [D("1.5"), D("2.5")]
    assert client.calls[-1][2] == {"timeframe": "1h", "limit": 2}
    with pytest.raises(ExchangeError, match="unknown spot symbol"):
        ex.ticker("NOPEUSDT")


def test_real_ccxt_precision_and_minimum():
    client = offline_ccxt("bybit")
    ex = CcxtSpot("bybit", "testnet", client=client)
    out = ex.place_order(OrderIntent("BTCUSDT", "buy", D("0.0012345678")))
    assert out["qty"] == "0.001234"  # ccxt rounded to the market's step, down
    with pytest.raises(ExchangeError, match="below the minimum"):
        ex.place_order(OrderIntent("BTCUSDT", "buy", D("0.00001")))
    limit = ex.place_order(OrderIntent("BTCUSDT", "sell", D("0.001"), "limit", D("50000.129")))
    assert limit["price"] == "50000.13"  # ccxt rounds the price to the nearest tick


def test_mainnet_orders_refused_unless_live():
    client = offline_ccxt("bybit")
    with pytest.raises(ExchangeError, match="mainnet orders are disabled"):
        CcxtSpot("bybit", client=client).place_order(OrderIntent("BTCUSDT", "buy", D("0.001")))
    assert [c for c in client.calls if c[0] == "create_order"] == []


def test_sandbox_switches_real_urls():
    client = offline_ccxt("bybit")
    CcxtSpot("bybit", "testnet", client=client)
    assert "api-testnet" in str(client.urls["api"])


def test_mexc_testnet_rung_is_test_orders():
    client = offline_ccxt("mexc")
    ex = CcxtSpot("mexc", "testnet", client=client)
    assert ex.test_orders and ex.supports_testnet
    out = ex.place_order(OrderIntent("BTCUSDT", "buy", D("0.001"), client_order_id="etx"))
    params = [c for c in client.calls if c[0] == "create_order"][-1][1][5]
    assert params == {"clientOrderId": "etx", "test": True} and out["test_order"] is True


def test_key_checks():
    bad = CcxtSpot("bybit", client=offline_ccxt("bybit", perms={"Wallet": ["Withdraw"], "Spot": ["SpotTrade"]}))
    assert not bad.check_key().safe_for_trading
    assert CcxtSpot("bybit", client=offline_ccxt("bybit")).check_key().safe_for_trading
    m = CcxtSpot("mexc", client=offline_ccxt("mexc", account={"canTrade": True, "canWithdraw": True}))
    assert m.check_key().can_withdraw
    other = CcxtSpot("binance", client=offline_ccxt("bybit"))  # no checker for this venue
    with pytest.raises(ExchangeError, match="refusing"):
        other.check_key()


def test_ccxt_errors_become_exchange_errors():
    ex = CcxtSpot("bybit", client=offline_ccxt("bybit", fail=ccxt.NetworkError("boom")))
    with pytest.raises(ExchangeError, match="NetworkError"):
        ex.ticker("BTCUSDT")


def test_factory_builds_real_ccxt_clients_without_network():
    paper = make_exchange("bybit", Mode.PAPER, env={})
    assert isinstance(paper.client, ccxt.bybit) and paper.network == "mainnet" and not paper.allow_mainnet_orders
    env = {"BYBIT_API_KEY": "k", "BYBIT_API_SECRET": "s", "MEXC_API_KEY": "k", "MEXC_API_SECRET": "s"}
    t = make_exchange("bybit", Mode.TESTNET, env=env)
    assert "api-testnet" in str(t.client.urls["api"]) and t.client.apiKey == "k"
    assert make_exchange("bybit", Mode.LIVE, env=env).allow_mainnet_orders
    assert make_exchange("mexc", Mode.TESTNET, env=env).test_orders is True
    assert make_exchange("mexc", Mode.LIVE, env=env).test_orders is False
    with pytest.raises(ExchangeError, match="BYBIT_API_KEY"):
        make_exchange("bybit", Mode.TESTNET, env={})


def test_credentials_never_printed():
    r = repr(Credentials("ABCDEFGH", "TOPSECRET"))
    assert "TOPSECRET" not in r and "EFGH" not in r


# ---- alpaca-py ----


class FakeData:
    def __init__(self):
        self.requests = []

    def get_stock_latest_trade(self, req):
        self.requests.append(req)
        return {"AAPL": SimpleNamespace(price=230.0)}

    def get_stock_latest_quote(self, req):
        self.requests.append(req)
        return {"AAPL": SimpleNamespace(bid_price=229.9, ask_price=230.1)}

    def get_stock_bars(self, req):
        self.requests.append(req)
        ts = [datetime(2026, 10, 9, h, tzinfo=timezone.utc) for h in (15, 14)]
        bars = [
            SimpleNamespace(timestamp=t, open=1, high=2, low=0.5, close=c, volume=5)
            for t, c in zip(ts, (2.5, 1.5), strict=True)
        ]
        return SimpleNamespace(data={"AAPL": bars})


class FakeTrading:
    def __init__(self, **acc):
        self.orders = []
        self.acc = {
            "status": "ACTIVE",
            "trading_blocked": False,
            "account_blocked": False,
            "pattern_day_trader": False,
            **acc,
        }

    def get_account(self):
        return SimpleNamespace(**self.acc)

    def submit_order(self, req):
        self.orders.append(req)
        return SimpleNamespace(id="a-1")


def test_alpaca_data_with_real_request_objects():
    from alpaca.data.requests import StockBarsRequest, StockLatestTradeRequest

    data = FakeData()
    ex = AlpacaPy(trading=FakeTrading(), data=data, clock=lambda: datetime(2026, 10, 9, 20, tzinfo=timezone.utc))
    t = ex.ticker("aapl")
    assert t.last == D("230.0") and t.ask == D("230.1")
    assert isinstance(data.requests[0], StockLatestTradeRequest) and data.requests[0].feed.value == "iex"
    ks = ex.klines("AAPL", "1h", 2)
    assert [k.close for k in ks] == [D("1.5"), D("2.5")]
    assert isinstance(data.requests[-1], StockBarsRequest) and data.requests[-1].limit == 2


def test_alpaca_orders_and_live_lock():
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

    tr = FakeTrading()
    ex = AlpacaPy("paper", trading=tr, data=FakeData())
    out = ex.place_order(OrderIntent("AAPL", "buy", D("0.25"), client_order_id="etq"))
    req = tr.orders[-1]
    assert isinstance(req, MarketOrderRequest) and req.qty == 0.25 and req.client_order_id == "etq"
    assert req.time_in_force.value == "day" and out["order_id"] == "a-1"
    ex.place_order(OrderIntent("AAPL", "sell", D("0.25"), "limit", D("231")))
    assert isinstance(tr.orders[-1], LimitOrderRequest) and tr.orders[-1].limit_price == 231
    with pytest.raises(ExchangeError, match="live orders are disabled"):
        AlpacaPy("live", trading=tr, data=FakeData()).place_order(OrderIntent("AAPL", "buy", D("1")))


def test_alpaca_key_check_and_factory():
    assert AlpacaPy(trading=FakeTrading(), data=FakeData()).check_key().safe_for_trading
    assert not AlpacaPy(trading=FakeTrading(trading_blocked=True), data=FakeData()).check_key().can_trade
    env = {"ALPACA_API_KEY": "k", "ALPACA_SECRET_KEY": "s"}
    pair = (FakeTrading(), FakeData())
    assert make_exchange("alpaca", Mode.TESTNET, env=env, client=pair).network == "paper"
    live = make_exchange("alpaca", Mode.LIVE, env=env, client=pair)
    assert live.network == "live" and live.allow_live_orders
    with pytest.raises(ExchangeError, match="ALPACA_SECRET_KEY"):
        make_exchange("alpaca", Mode.PAPER, env={})
    # the real SDK clients build offline too (no request is made at construction)
    real = make_exchange("alpaca", Mode.TESTNET, env=env)
    assert type(real.trading).__name__ == "TradingClient"
