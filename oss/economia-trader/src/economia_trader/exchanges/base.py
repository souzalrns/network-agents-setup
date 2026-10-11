"""What every exchange adapter provides, and the HTTP seam it talks through.

The transport is a plain function, so tests (and CI) run the adapters against canned
responses with no network, and a deployment can swap in its own client (proxy, retries,
fetchtron-style egress allowlist) without touching an adapter.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from ..contracts import OrderIntent

# (method, url, headers, body) -> (http_status, parsed_json)
Transport = Callable[[str, str, Mapping[str, str], bytes | None], tuple[int, Any]]

INTERVALS = ("1m", "5m", "15m", "1h", "4h", "1d")


class ExchangeError(RuntimeError):
    """The exchange answered with an error (or not at all)."""


def urllib_transport(timeout_s: float = 10.0) -> Transport:
    """Default transport: stdlib only, HTTPS only, JSON in/out."""

    def _send(method: str, url: str, headers: Mapping[str, str], body: bytes | None) -> tuple[int, Any]:
        if not url.startswith("https://"):
            raise ExchangeError(f"refusing non-HTTPS URL: {url}")
        req = urllib.request.Request(url, data=body, method=method, headers=dict(headers))  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosemgrep  # noqa: S310 (https-only above)
                return resp.status, json.loads(resp.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                return exc.code, json.loads(raw)
            except json.JSONDecodeError:
                return exc.code, {"raw": raw[:500]}
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ExchangeError(f"{method} {url.split('?')[0]}: {exc}") from exc

    return _send


@dataclass(frozen=True)
class Credentials:
    """API key + secret, read from the environment only. Never printed, never serialised."""

    api_key: str
    api_secret: str

    def __repr__(self) -> str:
        return f"Credentials(api_key={self.api_key[:4]}…, api_secret=***)"

    @classmethod
    def from_env(cls, prefix: str, env: Mapping[str, str] | None = None) -> Credentials:
        env = os.environ if env is None else env
        key, secret = env.get(f"{prefix}_API_KEY", ""), env.get(f"{prefix}_API_SECRET", "")
        if not key or not secret:
            raise ExchangeError(f"{prefix}_API_KEY and {prefix}_API_SECRET must be set in the environment")
        return cls(key, secret)


@dataclass(frozen=True)
class Ticker:
    symbol: str
    last: Decimal
    bid: Decimal | None
    ask: Decimal | None


@dataclass(frozen=True)
class Kline:
    open_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class KeyCheck:
    """Result of inspecting an API key's permissions before any signed order."""

    can_trade: bool
    can_withdraw: bool
    read_only: bool
    detail: dict[str, Any]

    @property
    def safe_for_trading(self) -> bool:
        return self.can_trade and not self.can_withdraw


class Exchange(Protocol):
    name: str
    supports_testnet: bool

    def ticker(self, symbol: str) -> Ticker: ...

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]: ...

    def check_key(self) -> KeyCheck: ...

    def place_order(self, intent: OrderIntent) -> dict[str, Any]: ...


def check_interval(interval: str) -> None:
    if interval not in INTERVALS:
        raise ValueError(f"interval must be one of {INTERVALS}, got {interval!r}")
