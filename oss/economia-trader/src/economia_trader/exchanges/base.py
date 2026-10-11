"""What every exchange adapter provides. The adapters themselves sit on mature libraries
(ccxt for crypto, alpaca-py for stocks); this module only holds the shared types.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from ..contracts import OrderIntent

INTERVALS = ("1m", "5m", "15m", "1h", "4h", "1d")


class ExchangeError(RuntimeError):
    """The exchange answered with an error (or not at all)."""


@dataclass(frozen=True)
class Credentials:
    """API key + secret, read from the environment only. Never printed, never serialised."""

    key_id: str  # the exchange's "API key" (public half, sent in a header)
    signing_key: str  # the exchange's "API secret" (HMAC key / auth header, never logged)

    def __repr__(self) -> str:
        return f"Credentials(key_id={self.key_id[:4]}…, signing_key=***)"

    @classmethod
    def from_env(
        cls, prefix: str, env: Mapping[str, str] | None = None, *, var_names: tuple[str, str] | None = None
    ) -> Credentials:
        """Read ``<PREFIX>_API_KEY``/``<PREFIX>_API_SECRET`` (or the two ``var_names`` given)."""
        env = os.environ if env is None else env
        key_var, secret_var = var_names or (f"{prefix}_API_KEY", f"{prefix}_API_SECRET")
        key, secret = env.get(key_var, ""), env.get(secret_var, "")
        if not key or not secret:
            raise ExchangeError(f"{key_var} and {secret_var} must be set in the environment")
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
