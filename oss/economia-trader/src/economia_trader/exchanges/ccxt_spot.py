"""Crypto spot through **ccxt** (MIT, 100+ exchanges): Bybit and MEXC today.

We do not hand-roll exchange HTTP: ccxt already knows each venue's signing, symbols, testnet
URLs, precision/lot size and quirks (e.g. Bybit spot market buys are quote-denominated unless
``marketUnit=baseCoin``: ccxt handles it). What stays ours is the policy around it:

- mainnet orders are refused unless the instance was built for LIVE (the gate decides that);
- MEXC has no testnet, so its "testnet" rung sends ``params={"test": True}`` (``/order/test``);
- the key check reads each venue's own permission endpoint and refuses withdraw rights.

``pip install economia-trader[crypto]``. ``client=`` injects any object with the ccxt API
(tests pass a real ccxt instance with offline markets, or a fake).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from ..contracts import OrderIntent, dec
from .base import Credentials, ExchangeError, KeyCheck, Kline, OrderStatus, Ticker, check_interval

TESTNET_VIA_TEST_ORDERS = {"mexc"}  # venues with no sandbox: validate-only orders instead
EXCHANGE_STOPS = {"bybit"}  # spot stop orders on the exchange (MEXC spot has none: client-side stop)
_STATUS = {
    "open": "open",
    "closed": "filled",
    "canceled": "canceled",
    "cancelled": "canceled",
    "expired": "canceled",
    "rejected": "rejected",
}


def _ccxt_errors() -> tuple[type[BaseException], ...]:
    try:
        import ccxt
    except ImportError:  # pragma: no cover - only without the extra
        return ()
    return (ccxt.BaseError,)


class CcxtSpot:
    def __init__(
        self,
        name: str,
        network: Literal["mainnet", "testnet"] = "mainnet",
        *,
        credentials: Credentials | None = None,
        client: Any = None,
        allow_mainnet_orders: bool = False,
    ) -> None:
        self.name = name
        self.network = network
        self.credentials = credentials
        self.allow_mainnet_orders = allow_mainnet_orders
        if client is None:
            try:
                import ccxt
            except ImportError as exc:
                raise ExchangeError("ccxt is not installed: pip install 'economia-trader[crypto]'") from exc
            config: dict[str, Any] = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
            if credentials:
                config |= {"apiKey": credentials.key_id, "secret": credentials.signing_key}
            client = getattr(ccxt, name)(config)
        self.client = client
        self.test_orders = network == "testnet" and name in TESTNET_VIA_TEST_ORDERS
        if network == "testnet" and not self.test_orders:
            if not (getattr(client, "has", {}) or {}).get("sandbox"):
                raise ExchangeError(f"{name}: no testnet/sandbox in ccxt")
            client.set_sandbox_mode(True)
        self.supports_testnet = bool((getattr(client, "has", {}) or {}).get("sandbox")) or self.test_orders
        self._errors = _ccxt_errors()

    # ---- plumbing ----

    def _call(self, what: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except ExchangeError:
            raise
        except self._errors as exc:
            raise ExchangeError(f"{self.name} {what}: {type(exc).__name__}: {exc}") from exc

    def _market(self, symbol: str) -> dict[str, Any]:
        """Accept our compact ids (``BTCUSDT``) or ccxt unified symbols (``BTC/USDT``)."""
        markets = self._call("load_markets", self.client.load_markets)
        sym = symbol.upper()
        if sym in markets and markets[sym].get("spot"):
            return markets[sym]
        for m in markets.values():
            if m.get("spot") and m.get("id", "").upper() == sym:
                return m
        raise ExchangeError(f"{self.name}: unknown spot symbol {symbol}")

    # ---- market data ----

    def ticker(self, symbol: str) -> Ticker:
        m = self._market(symbol)
        t = self._call("fetch_ticker", self.client.fetch_ticker, m["symbol"])
        if t.get("last") is None:
            raise ExchangeError(f"{self.name}: no last price for {symbol}")
        return Ticker(
            symbol=m["id"],
            last=dec(t["last"]),
            bid=dec(t["bid"]) if t.get("bid") is not None else None,
            ask=dec(t["ask"]) if t.get("ask") is not None else None,
        )

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]:
        check_interval(interval)  # our intervals are ccxt's timeframes
        m = self._market(symbol)
        rows = self._call("fetch_ohlcv", self.client.fetch_ohlcv, m["symbol"], timeframe=interval, limit=limit)
        return [Kline(int(r[0]), dec(r[1]), dec(r[2]), dec(r[3]), dec(r[4]), dec(r[5])) for r in rows or []]

    # ---- account ----

    def check_key(self) -> KeyCheck:
        """Each venue's own permission endpoint (ccxt implicit API). Unknown venue = refuse."""
        if self.name == "bybit":
            res = (self._call("query-api", self.client.privateGetV5UserQueryApi) or {}).get("result") or {}
            perms: dict[str, list[str]] = res.get("permissions") or {}
            flat = {p for group in perms.values() for p in (group or [])}
            read_only = bool(int(res.get("readOnly", 1)))
            return KeyCheck(
                can_trade=not read_only and bool(flat & {"SpotTrade", "Order"}),
                can_withdraw=any("withdraw" in p.lower() for p in flat),
                read_only=read_only,
                detail={"permissions": perms, "readOnly": res.get("readOnly"), "ips": res.get("ips")},
            )
        if self.name == "mexc":
            res = self._call("account", self.client.spotPrivateGetAccount) or {}
            can_trade = bool(res.get("canTrade"))
            return KeyCheck(
                can_trade=can_trade,
                can_withdraw=bool(res.get("canWithdraw")),
                read_only=not can_trade,
                detail={k: res.get(k) for k in ("canTrade", "canWithdraw", "canDeposit", "permissions", "accountType")},
            )
        raise ExchangeError(f"{self.name}: no key-permission check implemented; refusing to trade with it")

    # ---- orders ----

    def place_order(self, intent: OrderIntent) -> dict[str, Any]:
        if self.network == "mainnet" and not self.allow_mainnet_orders:
            raise ExchangeError(f"{self.name}: mainnet orders are disabled in this adapter instance")
        m = self._market(intent.symbol)
        amount = Decimal(self._call("precision", self.client.amount_to_precision, m["symbol"], float(intent.qty)))
        if amount <= 0:
            raise ExchangeError(f"{self.name}: qty {intent.qty} rounds to 0 at {m['symbol']} precision")
        min_amount = ((m.get("limits") or {}).get("amount") or {}).get("min")
        if min_amount is not None and amount < dec(min_amount):
            raise ExchangeError(f"{self.name}: qty {amount} below the minimum {min_amount} for {m['symbol']}")
        price = None
        if intent.order_type == "limit":
            price = Decimal(self._call("precision", self.client.price_to_precision, m["symbol"], float(intent.price)))
        params: dict[str, Any] = {"clientOrderId": intent.client_order_id}
        if self.test_orders:
            params["test"] = True
        order = self._call(
            "create_order",
            self.client.create_order,
            m["symbol"],
            intent.order_type,
            intent.side,
            float(amount),
            float(price) if price is not None else None,
            params,
        )
        return {
            "exchange": self.name,
            "network": self.network,
            "test_order": self.test_orders,
            "order_id": (order or {}).get("id"),
            "symbol": m["symbol"],
            "side": intent.side,
            "type": intent.order_type,
            "qty": str(amount),
            "price": str(price) if price is not None else None,
            "client_order_id": intent.client_order_id,
        }

    # ---- reconciliation (testnet/live) ----

    def order_status(self, symbol: str, order_id: str) -> OrderStatus:
        m = self._market(symbol)
        o = self._call("fetch_order", self.client.fetch_order, order_id, m["symbol"]) or {}
        filled = dec(o.get("filled") or 0)
        status = _STATUS.get(str(o.get("status")), "open")
        if status == "open" and filled > 0:
            status = "partially_filled"
        if status == "canceled" and filled > 0:
            status = "filled"  # cancelled after a partial fill: what filled is final
        fee = dec(((o.get("fee") or {}).get("cost")) or 0)
        avg = o.get("average") or o.get("price")
        return OrderStatus(str(o.get("id") or order_id), status, filled, dec(avg) if avg else None, fee)

    def place_stop(self, symbol: str, qty: Decimal, stop_price: Decimal, client_order_id: str) -> dict[str, Any]:
        if self.name not in EXCHANGE_STOPS:
            raise ExchangeError(f"{self.name}: no exchange-side stop on spot; the stop stays client-side")
        if self.network == "mainnet" and not self.allow_mainnet_orders:
            raise ExchangeError(f"{self.name}: mainnet orders are disabled in this adapter instance")
        m = self._market(symbol)
        amount = float(self._call("precision", self.client.amount_to_precision, m["symbol"], float(qty)))
        trigger = float(self._call("precision", self.client.price_to_precision, m["symbol"], float(stop_price)))
        o = self._call(
            "create_order",
            self.client.create_order,
            m["symbol"],
            "market",
            "sell",
            amount,
            None,
            {"triggerPrice": trigger, "clientOrderId": client_order_id},
        )
        return {
            "order_id": (o or {}).get("id"),
            "symbol": m["symbol"],
            "qty": str(amount),
            "stop": str(trigger),
            "client_order_id": client_order_id,
        }

    def cancel_order(self, symbol: str, order_id: str) -> None:
        m = self._market(symbol)
        self._call("cancel_order", self.client.cancel_order, order_id, m["symbol"])

    def position_qty(self, symbol: str) -> Decimal:
        m = self._market(symbol)
        bal = self._call("fetch_balance", self.client.fetch_balance) or {}
        return dec(((bal.get("total") or {}).get(m["base"])) or 0)

    def account_equity(self, marks: dict[str, Decimal]) -> Decimal:
        """Quote balance plus every marked symbol's base balance at its mark (spot, no leverage)."""
        bal = (self._call("fetch_balance", self.client.fetch_balance) or {}).get("total") or {}
        quotes = {self._market(s)["quote"] for s in marks} or {"USDT"}
        equity = sum((dec(bal.get(q) or 0) for q in quotes), Decimal(0))
        for sym, mark in marks.items():
            equity += dec(bal.get(self._market(sym)["base"]) or 0) * mark
        return equity
