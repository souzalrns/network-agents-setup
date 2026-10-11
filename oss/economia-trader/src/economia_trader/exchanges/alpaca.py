"""Alpaca adapter (US stocks/ETFs, Trading API v2 + Market Data v2). Key + secret headers, no
request signing.

Alpaca's **paper account is a real broker-side simulation** (free, same API, separate keys),
so it is this adapter's "testnet" rung: orders go to ``paper-api.alpaca.markets`` and fill
against the live book in simulation. Market data needs a key even for the free IEX feed, so
the paper rung (simulated fills here) also reads ``ALPACA_API_KEY``/``ALPACA_SECRET_KEY``;
use the *paper* account's keys for it.

Endpoints: GET data /v2/stocks/{s}/quotes/latest, /trades/latest, /bars; GET /v2/account;
POST /v2/orders. The Trading API has no withdrawal endpoint, so ``check_key`` cannot see
one: ``can_withdraw`` is reported False *by API design*, and money movement stays in
Alpaca's dashboard.
"""

from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from ..contracts import OrderIntent, dec
from .base import Credentials, ExchangeError, KeyCheck, Kline, Ticker, Transport, check_interval, urllib_transport

TRADING_URLS = {"paper": "https://paper-api.alpaca.markets", "live": "https://api.alpaca.markets"}
DATA_URL = "https://data.alpaca.markets"
_TIMEFRAMES = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "1h": "1Hour", "4h": "4Hour", "1d": "1Day"}
_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ms(ts: str) -> int:
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)


class Alpaca:
    name = "alpaca"
    supports_testnet = True  # the paper account

    def __init__(
        self,
        network: Literal["paper", "live"] = "paper",
        *,
        credentials: Credentials | None = None,
        transport: Transport | None = None,
        allow_live_orders: bool = False,
        feed: str = "iex",
        clock: Any = None,
    ) -> None:
        if network not in TRADING_URLS:
            raise ValueError(f"network must be paper|live, got {network!r}")
        self.network = network
        self.base = TRADING_URLS[network]
        self.credentials = credentials
        self._send = transport or urllib_transport()
        self.allow_live_orders = allow_live_orders
        self.feed = feed
        self._clock = clock or _now

    def _call(self, method: str, url: str, body: dict[str, Any] | None = None) -> Any:
        if self.credentials is None:
            raise ExchangeError("alpaca: needs ALPACA_API_KEY / ALPACA_SECRET_KEY (paper keys are free)")
        headers = {
            "APCA-API-KEY-ID": self.credentials.key_id,
            "APCA-API-SECRET-KEY": self.credentials.signing_key,
            "Accept": "application/json",
        }
        raw = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            raw = json.dumps(body, separators=(",", ":")).encode()
        status, data = self._send(method, url, headers, raw)
        if status not in (200, 201):
            msg = data.get("message") if isinstance(data, dict) else data
            raise ExchangeError(f"alpaca {method} {url.split('?')[0]}: http {status}, {msg}")
        return data

    # ---- market data ----

    def ticker(self, symbol: str) -> Ticker:
        s = urllib.parse.quote(symbol.upper())
        q = (self._call("GET", f"{DATA_URL}/v2/stocks/{s}/quotes/latest?feed={self.feed}") or {}).get("quote") or {}
        t = (self._call("GET", f"{DATA_URL}/v2/stocks/{s}/trades/latest?feed={self.feed}") or {}).get("trade") or {}
        if not t.get("p"):
            raise ExchangeError(f"alpaca: no trades for {symbol}")
        return Ticker(
            symbol=symbol.upper(),
            last=dec(t["p"]),
            bid=dec(q["bp"]) if q.get("bp") else None,
            ask=dec(q["ap"]) if q.get("ap") else None,
        )

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]:
        check_interval(interval)
        # Bars only exist in market hours: look back ~5x the span so `limit` bars are there.
        start = self._clock() - timedelta(minutes=_MINUTES[interval] * limit * 5)
        params = {
            "timeframe": _TIMEFRAMES[interval],
            "limit": limit,
            "feed": self.feed,
            "sort": "desc",
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        s = urllib.parse.quote(symbol.upper())
        rows = (self._call("GET", f"{DATA_URL}/v2/stocks/{s}/bars?{urllib.parse.urlencode(params)}") or {}).get("bars")
        out = [Kline(_ms(b["t"]), dec(b["o"]), dec(b["h"]), dec(b["l"]), dec(b["c"]), dec(b["v"])) for b in rows or []]
        return sorted(out, key=lambda k: k.open_time_ms)

    # ---- account ----

    def check_key(self) -> KeyCheck:
        acc = self._call("GET", f"{self.base}/v2/account")
        can_trade = acc.get("status") == "ACTIVE" and not acc.get("trading_blocked") and not acc.get("account_blocked")
        return KeyCheck(
            can_trade=bool(can_trade),
            can_withdraw=False,  # the Trading API exposes no withdrawal endpoint
            read_only=not can_trade,
            detail={k: acc.get(k) for k in ("status", "trading_blocked", "account_blocked", "pattern_day_trader")}
            | {"network": self.network, "withdraw_via_api": "not exposed by the Trading API"},
        )

    # ---- orders ----

    def place_order(self, intent: OrderIntent) -> dict[str, Any]:
        if self.network == "live" and not self.allow_live_orders:
            raise ExchangeError("alpaca: live orders are disabled in this adapter instance")
        body: dict[str, Any] = {
            "symbol": intent.symbol.upper(),
            "qty": format(intent.qty.normalize(), "f"),
            "side": intent.side,
            "type": intent.order_type,
            "time_in_force": "day",  # fractional orders must be DAY
            "client_order_id": intent.client_order_id,
        }
        if intent.order_type == "limit":
            body["limit_price"] = format(intent.price.normalize(), "f")  # type: ignore[union-attr]
        res = self._call("POST", f"{self.base}/v2/orders", body)
        return {"exchange": "alpaca", "network": self.network, "order_id": (res or {}).get("id"), **body}
