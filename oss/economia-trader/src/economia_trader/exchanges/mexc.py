"""MEXC Spot V3 REST adapter. Public market data needs no key; orders are HMAC-signed.

MEXC has **no public testnet**. The closest thing is ``POST /api/v3/order/test``, which
validates signature and parameters without sending an order to the book. This adapter uses it
whenever ``dry_run=True`` (the default), so the "testnet" rung of the ladder on MEXC is a
validation-only rung: it proves the key and the payload, not the fill.

Endpoints: GET /api/v3/ticker/24hr, GET /api/v3/klines, GET /api/v3/account,
POST /api/v3/order/test, POST /api/v3/order. Signature: HMAC_SHA256(secret, query string),
sent as ``signature`` with the key in the ``X-MEXC-APIKEY`` header.

MEXC futures are out of scope: its futures order API has been restricted for retail keys;
only spot is supported here.
"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from typing import Any

from ..contracts import OrderIntent, dec
from .base import Credentials, ExchangeError, KeyCheck, Kline, Ticker, Transport, check_interval, urllib_transport

BASE_URL = "https://api.mexc.com"
_INTERVALS = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "4h", "1d": "1d"}
RECV_WINDOW = 5000


def _now_ms() -> int:
    return int(time.time() * 1000)


def sign(secret: str, query: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


class Mexc:
    name = "mexc"
    supports_testnet = False

    def __init__(
        self,
        *,
        credentials: Credentials | None = None,
        transport: Transport | None = None,
        dry_run: bool = True,
        clock_ms: Any = None,
    ) -> None:
        self.base = BASE_URL
        self.credentials = credentials
        self._send = transport or urllib_transport()
        self.dry_run = dry_run
        self._clock_ms = clock_ms or _now_ms

    def _check(self, status: int, data: Any, what: str) -> Any:
        # Errors come back as {"code": <int>, "msg": "..."} with a non-200 status.
        if status != 200 or (isinstance(data, dict) and "code" in data and data.get("code") not in (0, 200)):
            d = data if isinstance(data, dict) else {"msg": data}
            raise ExchangeError(f"mexc {what}: http {status}, code {d.get('code')}, {d.get('msg')}")
        return data

    def _public(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        status, data = self._send("GET", url, {"Accept": "application/json"}, None)
        return self._check(status, data, path)

    def _signed(self, method: str, path: str, params: dict[str, Any]) -> Any:
        if self.credentials is None:
            raise ExchangeError("mexc: this call needs credentials (MEXC_API_KEY / MEXC_API_SECRET)")
        q = urllib.parse.urlencode({**params, "recvWindow": RECV_WINDOW, "timestamp": self._clock_ms()})
        url = f"{self.base}{path}?{q}&signature={sign(self.credentials.api_secret, q)}"
        headers = {"X-MEXC-APIKEY": self.credentials.api_key, "Content-Type": "application/json"}
        status, data = self._send(method, url, headers, None)
        return self._check(status, data, path)

    # ---- market data (no key) ----

    def ticker(self, symbol: str) -> Ticker:
        r = self._public("/api/v3/ticker/24hr", {"symbol": symbol.upper()})
        if isinstance(r, list):
            r = r[0] if r else {}
        if not r.get("lastPrice"):
            raise ExchangeError(f"mexc: unknown spot symbol {symbol}")
        return Ticker(
            symbol=r["symbol"],
            last=dec(r["lastPrice"]),
            bid=dec(r["bidPrice"]) if r.get("bidPrice") else None,
            ask=dec(r["askPrice"]) if r.get("askPrice") else None,
        )

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]:
        check_interval(interval)
        rows = self._public(
            "/api/v3/klines", {"symbol": symbol.upper(), "interval": _INTERVALS[interval], "limit": limit}
        )
        # [openTime, open, high, low, close, volume, closeTime, quoteVolume], oldest first
        return [Kline(int(r[0]), dec(r[1]), dec(r[2]), dec(r[3]), dec(r[4]), dec(r[5])) for r in rows or []]

    # ---- account ----

    def check_key(self) -> KeyCheck:
        """Read ``/api/v3/account``. ``canWithdraw`` true makes the key unsafe for this tool."""
        res = self._signed("GET", "/api/v3/account", {})
        can_trade = bool(res.get("canTrade"))
        return KeyCheck(
            can_trade=can_trade,
            can_withdraw=bool(res.get("canWithdraw")),
            read_only=not can_trade,
            detail={k: res.get(k) for k in ("canTrade", "canWithdraw", "canDeposit", "permissions", "accountType")},
        )

    # ---- orders ----

    def place_order(self, intent: OrderIntent) -> dict[str, Any]:
        params: dict[str, Any] = {
            "symbol": intent.symbol.upper(),
            "side": intent.side.upper(),
            "type": intent.order_type.upper(),
            "quantity": format(intent.qty.normalize(), "f"),
            "newClientOrderId": intent.client_order_id,
        }
        if intent.order_type == "limit":
            params["price"] = format(intent.price.normalize(), "f")  # type: ignore[union-attr]
        path = "/api/v3/order/test" if self.dry_run else "/api/v3/order"
        res = self._signed("POST", path, params)
        return {"exchange": "mexc", "dry_run": self.dry_run, "order_id": (res or {}).get("orderId"), **params}
