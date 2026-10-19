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
MARKETS["bybiteu"] = MARKETS["bybit"]


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
    # orders the fake exchange "holds": market orders fill at once at the ticker price, stops rest open
    client.book = {}
    client.balance = {"USDT": 1000, "BTC": 0, "ETH": 0}

    def create(symbol, otype, side, amount, price=None, params=None):
        is_stop = bool((params or {}).get("triggerPrice"))
        n = len(client.book)
        oid = f"s-{n + 1}" if is_stop else ("o-9" if "o-9" not in client.book else f"o-{n + 9}")
        last = prices[symbol]
        client.book[oid] = {
            "id": oid,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "status": "open" if is_stop else "closed",
            "filled": 0 if is_stop else amount,
            "average": None if is_stop else last,
            "fee": {"cost": 0},
        }
        if not is_stop:
            base = symbol.split("/")[0]
            client.balance[base] = client.balance.get(base, 0) + (amount if side == "buy" else -amount)
        return {"id": oid}

    client.create_order = rec("create_order", create)
    client.fetch_order = rec("fetch_order", lambda oid, symbol=None: dict(client.book[oid]))
    client.cancel_order = rec("cancel_order", lambda oid, symbol=None: client.book[oid].update(status="canceled") or {})
    client.fetch_balance = rec("fetch_balance", lambda: {"total": dict(client.balance)})
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
