from __future__ import annotations

from decimal import Decimal

import pytest

from economia_trader import RiskLimits

MARKETS = {
    "bybit": [
        {
            "id": "BTCUSDT",
            "symbol": "BTC/USDT",
            "base": "BTC",
            "quote": "USDT",
            "spot": True,
            "type": "spot",
            "active": True,
            "precision": {"amount": 0.000001, "price": 0.01},
            "limits": {"amount": {"min": 0.000048}, "cost": {"min": 1}},
        },
        {
            "id": "ETHUSDT",
            "symbol": "ETH/USDT",
            "base": "ETH",
            "quote": "USDT",
            "spot": True,
            "type": "spot",
            "active": True,
            "precision": {"amount": 0.00001, "price": 0.01},
            "limits": {"amount": {"min": 0.0001}, "cost": {"min": 1}},
        },
    ],
}
MARKETS["mexc"] = MARKETS["bybit"]


def offline_ccxt(name, prices=None, *, perms=None, account=None, fail=None):
    """A REAL ccxt client (real symbols, precision, sandbox URLs) with markets loaded offline and
    every network call replaced by a recorder. Nothing here can reach an exchange."""
    import ccxt

    client = getattr(ccxt, name)({"options": {"defaultType": "spot"}})
    client.set_markets(MARKETS[name])
    client.calls = []
    prices = {"BTC/USDT": 50000, "ETH/USDT": 3000, **(prices or {})}

    def rec(method, result):
        def f(*args, **kwargs):
            client.calls.append((method, args, kwargs))
            if fail:
                raise fail
            return result(*args) if callable(result) else result

        return f

    client.fetch_ticker = rec("fetch_ticker", lambda s: {"last": prices[s], "bid": None, "ask": None})
    client.fetch_ohlcv = rec("fetch_ohlcv", [[1000, 1, 2, 0.5, 1.5, 5], [2000, 1.5, 3, 1, 2.5, 9]])
    client.create_order = rec("create_order", {"id": "o-9"})
    client.privateGetV5UserQueryApi = rec(
        "query_api", {"retCode": 0, "result": {"readOnly": 0, "permissions": perms or {"Spot": ["SpotTrade"]}}}
    )
    client.spotPrivateGetAccount = rec(
        "account", account or {"canTrade": True, "canWithdraw": False, "canDeposit": True}
    )
    return client


@pytest.fixture
def limits():
    return RiskLimits.from_mapping(
        {
            "max_order_notional": "100",
            "max_loss_per_trade": "5",
            "max_daily_loss": "10",
            "allowed_symbols": ["BTCUSDT", "ETHUSDT"],
            "max_open_positions": 1,
        }
    )


D = Decimal
