"""Exchange adapters. ``make_exchange`` wires the right network for each mode:

paper    public mainnet market data, no key, no orders leave the process
testnet  Bybit testnet (test funds) | MEXC ``/order/test`` (validation only, no testnet exists)
live     Bybit mainnet | MEXC ``/order`` — only reachable through ``safety.authorize``
"""

from __future__ import annotations

from collections.abc import Mapping

from ..safety import Mode
from .base import Credentials, Exchange, ExchangeError, KeyCheck, Kline, Ticker, Transport
from .bybit import Bybit
from .mexc import Mexc

__all__ = ["Bybit", "Credentials", "Exchange", "ExchangeError", "KeyCheck", "Kline", "Mexc", "Ticker", "make_exchange"]

EXCHANGES = ("bybit", "mexc")


def make_exchange(
    name: str,
    mode: Mode,
    *,
    transport: Transport | None = None,
    env: Mapping[str, str] | None = None,
) -> Exchange:
    if name not in EXCHANGES:
        raise ValueError(f"exchange must be one of {EXCHANGES}, got {name!r}")
    creds = None if mode is Mode.PAPER else Credentials.from_env(name.upper(), env)
    if name == "bybit":
        network = "testnet" if mode is Mode.TESTNET else "mainnet"
        return Bybit(network, credentials=creds, transport=transport, allow_mainnet_orders=mode is Mode.LIVE)
    return Mexc(credentials=creds, transport=transport, dry_run=mode is not Mode.LIVE)
