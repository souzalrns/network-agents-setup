import hashlib
import hmac
from decimal import Decimal as D

import pytest
from conftest import FakeTransport, bybit_ok

from economia_trader import Mode, OrderIntent
from economia_trader.exchanges import Bybit, Credentials, ExchangeError, Mexc, make_exchange

CREDS = Credentials("KEY123456", "SECRET")
CLOCK = lambda: 1700000000000  # noqa: E731


# ---- Bybit ----


def test_bybit_ticker_public_no_key():
    t = FakeTransport(
        {
            "/v5/market/tickers": bybit_ok(
                {"list": [{"symbol": "BTCUSDT", "lastPrice": "50000.5", "bid1Price": "50000", "ask1Price": "50001"}]}
            )
        }
    )
    tick = Bybit(transport=t).ticker("btcusdt")
    assert tick.last == D("50000.5") and tick.bid == D("50000")
    call = t.calls[0]
    assert call["url"].startswith("https://api.bybit.com/v5/market/tickers")
    assert call["query"] == {"category": "spot", "symbol": "BTCUSDT"}
    assert "X-BAPI-API-KEY" not in call["headers"]


def test_bybit_klines_sorted_and_interval_mapped():
    rows = [["2000", "2", "3", "1", "2.5", "10", "0"], ["1000", "1", "2", "0.5", "1.5", "5", "0"]]
    t = FakeTransport({"/v5/market/kline": bybit_ok({"list": rows})})
    ks = Bybit(transport=t).klines("BTCUSDT", "1h", 2)
    assert [k.open_time_ms for k in ks] == [1000, 2000]
    assert t.calls[0]["query"]["interval"] == "60"
    with pytest.raises(ValueError):
        Bybit(transport=t).klines("BTCUSDT", "2h")


def test_bybit_error_raises():
    t = FakeTransport({"/v5/market/tickers": (200, {"retCode": 10001, "retMsg": "params error"})})
    with pytest.raises(ExchangeError, match="params error"):
        Bybit(transport=t).ticker("BTCUSDT")


def test_bybit_mainnet_orders_refused_by_default():
    t = FakeTransport({})
    with pytest.raises(ExchangeError, match="mainnet orders are disabled"):
        Bybit(credentials=CREDS, transport=t).place_order(OrderIntent("BTCUSDT", "buy", D("0.001")))
    assert t.calls == []


def test_bybit_testnet_signed_market_order():
    t = FakeTransport({"/v5/order/create": bybit_ok({"orderId": "o-1", "orderLinkId": "x"})})
    ex = Bybit("testnet", credentials=CREDS, transport=t, clock_ms=CLOCK)
    out = ex.place_order(OrderIntent("BTCUSDT", "buy", D("0.00100"), client_order_id="etabc"))
    call = t.calls[0]
    assert call["url"] == "https://api-testnet.bybit.com/v5/order/create"
    assert call["body"] == {
        "category": "spot",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "orderType": "Market",
        "qty": "0.001",
        "orderLinkId": "etabc",
        "marketUnit": "baseCoin",
    }
    h = call["headers"]
    expected = hmac.new(
        b"SECRET", b"1700000000000" + b"KEY123456" + b"5000" + call["raw_body"], hashlib.sha256
    ).hexdigest()
    assert h["X-BAPI-SIGN"] == expected and h["X-BAPI-TIMESTAMP"] == "1700000000000"
    assert out["order_id"] == "o-1" and out["network"] == "testnet"


def test_bybit_limit_order_body():
    t = FakeTransport({"/v5/order/create": bybit_ok({"orderId": "o-2"})})
    Bybit("testnet", credentials=CREDS, transport=t).place_order(
        OrderIntent("BTCUSDT", "sell", D("0.001"), "limit", D("51000.00"))
    )
    body = t.calls[0]["body"]
    assert body["orderType"] == "Limit" and body["price"] == "51000" and body["timeInForce"] == "GTC"
    assert "marketUnit" not in body


def test_bybit_check_key_detects_withdraw():
    perms = {"Spot": ["SpotTrade"], "Wallet": ["AccountTransfer", "Withdraw"]}
    t = FakeTransport({"/v5/user/query-api": bybit_ok({"readOnly": 0, "permissions": perms})})
    kc = Bybit("testnet", credentials=CREDS, transport=t, clock_ms=CLOCK).check_key()
    assert kc.can_trade and kc.can_withdraw and not kc.safe_for_trading
    assert t.calls[0]["method"] == "GET" and "X-BAPI-SIGN" in t.calls[0]["headers"]


def test_bybit_check_key_safe():
    t = FakeTransport({"/v5/user/query-api": bybit_ok({"readOnly": 0, "permissions": {"Spot": ["SpotTrade"]}})})
    assert Bybit("testnet", credentials=CREDS, transport=t).check_key().safe_for_trading


def test_signed_call_needs_credentials():
    with pytest.raises(ExchangeError, match="needs credentials"):
        Bybit("testnet", transport=FakeTransport({})).check_key()


# ---- MEXC ----


def test_mexc_ticker_and_klines():
    t = FakeTransport(
        {
            "/api/v3/ticker/24hr": (
                200,
                {"symbol": "BTCUSDT", "lastPrice": "50000", "bidPrice": "49999", "askPrice": "50001"},
            ),
            "/api/v3/klines": (200, [[1000, "1", "2", "0.5", "1.5", "5", 1999, "7"]]),
        }
    )
    m = Mexc(transport=t)
    assert m.ticker("BTCUSDT").ask == D("50001")
    ks = m.klines("BTCUSDT", "1h", 1)
    assert ks[0].close == D("1.5") and t.calls[1]["query"]["interval"] == "60m"


def test_mexc_dry_run_uses_order_test_and_signs_query():
    t = FakeTransport({"/api/v3/order/test": (200, {})})
    m = Mexc(credentials=CREDS, transport=t, clock_ms=CLOCK)
    out = m.place_order(OrderIntent("BTCUSDT", "buy", D("0.001"), client_order_id="etxyz"))
    call = t.calls[0]
    assert call["path"] == "/api/v3/order/test" and out["dry_run"] is True
    q = call["url"].split("?", 1)[1]
    unsigned, sig = q.rsplit("&signature=", 1)
    assert sig == hmac.new(b"SECRET", unsigned.encode(), hashlib.sha256).hexdigest()
    assert call["query"]["side"] == "BUY" and call["query"]["type"] == "MARKET"
    assert call["query"]["timestamp"] == "1700000000000"
    assert call["headers"]["X-MEXC-APIKEY"] == "KEY123456"


def test_mexc_live_uses_real_endpoint():
    t = FakeTransport({"/api/v3/order": (200, {"orderId": "m-1"})})
    out = Mexc(credentials=CREDS, transport=t, dry_run=False).place_order(OrderIntent("BTCUSDT", "buy", D("0.001")))
    assert t.calls[0]["path"] == "/api/v3/order" and out["order_id"] == "m-1"


def test_mexc_error_and_key_check():
    t = FakeTransport({"/api/v3/account": (200, {"canTrade": True, "canWithdraw": True, "canDeposit": True})})
    assert not Mexc(credentials=CREDS, transport=t).check_key().safe_for_trading
    bad = FakeTransport({"/api/v3/ticker/24hr": (400, {"code": -1121, "msg": "Invalid symbol."})})
    with pytest.raises(ExchangeError, match="Invalid symbol"):
        Mexc(transport=bad).ticker("NOPE")


# ---- factory + credentials ----


def test_make_exchange_modes():
    paper = make_exchange("bybit", Mode.PAPER, env={})
    assert paper.network == "mainnet" and paper.credentials is None and not paper.allow_mainnet_orders
    env = {"BYBIT_API_KEY": "k", "BYBIT_API_SECRET": "s", "MEXC_API_KEY": "k", "MEXC_API_SECRET": "s"}
    assert make_exchange("bybit", Mode.TESTNET, env=env).network == "testnet"
    assert make_exchange("bybit", Mode.LIVE, env=env).allow_mainnet_orders
    assert make_exchange("mexc", Mode.TESTNET, env=env).dry_run is True
    assert make_exchange("mexc", Mode.LIVE, env=env).dry_run is False
    with pytest.raises(ExchangeError, match="BYBIT_API_KEY"):
        make_exchange("bybit", Mode.TESTNET, env={})
    with pytest.raises(ValueError):
        make_exchange("binance", Mode.PAPER)


def test_credentials_never_printed():
    r = repr(Credentials("ABCDEFGH", "TOPSECRET"))
    assert "TOPSECRET" not in r and "EFGH" not in r
