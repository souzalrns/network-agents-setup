"""Exchange adapters. ``make_exchange`` wires the right network for each mode:

paper    public mainnet market data, no key, no orders leave the process
testnet  Bybit testnet (test funds) | MEXC ``/order/test`` (validation only, no testnet exists)
live     Bybit mainnet | MEXC ``/order`` — only reachable through ``safety.authorize``
"""

from __future__ import annotations

from collections.abc import Mapping

from ..safety import Mode
from .alpaca import Alpaca
from .base import Credentials, Exchange, ExchangeError, KeyCheck, Kline, Ticker, Transport
from .bybit import Bybit
from .mexc import Mexc

__all__ = [
    "Alpaca",
    "Bybit",
    "Credentials",
    "Exchange",
    "ExchangeError",
    "KeyCheck",
    "Kline",
    "Mexc",
    "Ticker",
    "make_exchange",
]

EXCHANGES = ("bybit", "mexc", "alpaca")


def make_exchange(
    name: str,
    mode: Mode,
    *,
    transport: Transport | None = None,
    env: Mapping[str, str] | None = None,
) -> Exchange:
    if name not in EXCHANGES:
        raise ValueError(f"exchange must be one of {EXCHANGES}, got {name!r}")
    if name == "alpaca":
        creds = Credentials.from_env("ALPACA", env, var_names=("ALPACA_API_KEY", "ALPACA_SECRET_KEY"))
        network = "live" if mode is Mode.LIVE else "paper"
        return Alpaca(network, credentials=creds, transport=transport, allow_live_orders=mode is Mode.LIVE)
    creds = None if mode is Mode.PAPER else Credentials.from_env(name.upper(), env)
    if name == "bybit":
        network = "testnet" if mode is Mode.TESTNET else "mainnet"
        return Bybit(network, credentials=creds, transport=transport, allow_mainnet_orders=mode is Mode.LIVE)
    return Mexc(credentials=creds, transport=transport, dry_run=mode is not Mode.LIVE)
