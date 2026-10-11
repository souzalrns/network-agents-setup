"""Bybit V5 REST adapter (spot). Public market data needs no key; orders are HMAC-signed.

Endpoints: GET /v5/market/tickers, GET /v5/market/kline, GET /v5/user/query-api,
POST /v5/order/create. Signature (V5): HMAC_SHA256(signing_key, ts + key_id + recv_window + payload)
where payload is the query string (GET) or the raw JSON body (POST).

Mainnet orders are refused by the adapter itself unless it was built with
``allow_mainnet_orders=True`` — which only ``Trader`` does, after ``safety.authorize`` passed
in LIVE mode. Defence in depth: the gate *and* the adapter must agree.
"""

from __future__ import annotations

import json
import time
import urllib.parse
from decimal import Decimal
from typing import Any, Literal

from ..contracts import OrderIntent, dec
from .base import (
    Credentials,
    ExchangeError,
    KeyCheck,
    Kline,
    Ticker,
    Transport,
    check_interval,
    hmac_sha256_hex,
    urllib_transport,
)

BASE_URLS = {"mainnet": "https://api.bybit.com", "testnet": "https://api-testnet.bybit.com"}
_INTERVALS = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
RECV_WINDOW = "5000"


def _now_ms() -> int:
    return int(time.time() * 1000)


def sign(signing_key: str, timestamp: str, key_id: str, recv_window: str, payload: str) -> str:
    return hmac_sha256_hex(signing_key, timestamp + key_id + recv_window + payload)


def _num(d: Decimal) -> str:
    return format(d.normalize(), "f")


class Bybit:
    name = "bybit"
    supports_testnet = True

    def __init__(
        self,
        network: Literal["mainnet", "testnet"] = "mainnet",
        *,
        credentials: Credentials | None = None,
        transport: Transport | None = None,
        allow_mainnet_orders: bool = False,
        clock_ms: Any = None,
    ) -> None:
        if network not in BASE_URLS:
            raise ValueError(f"network must be mainnet|testnet, got {network!r}")
        self.network = network
        self.base = BASE_URLS[network]
        self.credentials = credentials
        self._send = transport or urllib_transport()
        self.allow_mainnet_orders = allow_mainnet_orders
        self._clock_ms = clock_ms or _now_ms

    # ---- plumbing ----

    def _result(self, status: int, data: Any, what: str) -> Any:
        if status != 200 or not isinstance(data, dict) or data.get("retCode") != 0:
            d = data if isinstance(data, dict) else {"retMsg": data}
            raise ExchangeError(f"bybit {what}: http {status}, retCode {d.get('retCode')}, {d.get('retMsg')}")
        return data.get("result") or {}

    def _public(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        status, data = self._send("GET", url, {"Accept": "application/json"}, None)
        return self._result(status, data, path)

    def _signed(self, method: str, path: str, params: dict[str, Any]) -> Any:
        if self.credentials is None:
            raise ExchangeError("bybit: this call needs credentials (BYBIT_API_KEY / BYBIT_API_SECRET)")
        ts = str(self._clock_ms())
        if method == "GET":
            payload = urllib.parse.urlencode(params)
            url, body = f"{self.base}{path}" + (f"?{payload}" if payload else ""), None
        else:
            payload = json.dumps(params, separators=(",", ":"))
            url, body = f"{self.base}{path}", payload.encode()
        headers = {
            "X-BAPI-API-KEY": self.credentials.key_id,
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-RECV-WINDOW": RECV_WINDOW,
            "X-BAPI-SIGN": sign(self.credentials.signing_key, ts, self.credentials.key_id, RECV_WINDOW, payload),
            "Content-Type": "application/json",
        }
        status, data = self._send(method, url, headers, body)
        return self._result(status, data, path)

    # ---- market data (no key) ----

    def ticker(self, symbol: str) -> Ticker:
        rows = self._public("/v5/market/tickers", {"category": "spot", "symbol": symbol.upper()}).get("list") or []
        if not rows:
            raise ExchangeError(f"bybit: unknown spot symbol {symbol}")
        r = rows[0]
        return Ticker(
            symbol=r["symbol"],
            last=dec(r["lastPrice"]),
            bid=dec(r["bid1Price"]) if r.get("bid1Price") else None,
            ask=dec(r["ask1Price"]) if r.get("ask1Price") else None,
        )

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]:
        check_interval(interval)
        params = {"category": "spot", "symbol": symbol.upper(), "interval": _INTERVALS[interval], "limit": limit}
        rows = self._public("/v5/market/kline", params).get("list") or []
        # Bybit returns newest first: [start, open, high, low, close, volume, turnover]
        out = [Kline(int(r[0]), dec(r[1]), dec(r[2]), dec(r[3]), dec(r[4]), dec(r[5])) for r in rows]
        return sorted(out, key=lambda k: k.open_time_ms)

    # ---- account ----

    def check_key(self) -> KeyCheck:
        """Inspect the key. Any ``Withdraw`` permission makes it unsafe for this tool."""
        res = self._signed("GET", "/v5/user/query-api", {})
        perms: dict[str, list[str]] = res.get("permissions") or {}
        flat = {p for group in perms.values() for p in (group or [])}
        read_only = bool(int(res.get("readOnly", 1)))
        return KeyCheck(
            can_trade=not read_only and bool(flat & {"SpotTrade", "Order"}),
            can_withdraw=any("withdraw" in p.lower() for p in flat),
            read_only=read_only,
            detail={"permissions": perms, "readOnly": res.get("readOnly"), "ips": res.get("ips")},
        )

    # ---- orders ----

    def place_order(self, intent: OrderIntent) -> dict[str, Any]:
        if self.network == "mainnet" and not self.allow_mainnet_orders:
            raise ExchangeError("bybit: mainnet orders are disabled in this adapter instance")
        body: dict[str, Any] = {
            "category": "spot",
            "symbol": intent.symbol.upper(),
            "side": "Buy" if intent.side == "buy" else "Sell",
            "orderType": "Market" if intent.order_type == "market" else "Limit",
            "qty": _num(intent.qty),
            "orderLinkId": intent.client_order_id,
        }
        if intent.order_type == "market":
            body["marketUnit"] = "baseCoin"  # spot market buys default to quote units otherwise
        else:
            body["price"] = _num(intent.price)  # type: ignore[arg-type]
            body["timeInForce"] = "GTC"
        res = self._signed("POST", "/v5/order/create", body)
        return {"exchange": "bybit", "network": self.network, "order_id": res.get("orderId"), **body}
