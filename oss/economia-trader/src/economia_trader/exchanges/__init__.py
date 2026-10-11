"""Exchange adapters, on mature libraries: **ccxt** (crypto) and **alpaca-py** (stocks).

``make_exchange`` wires the right network for each mode:

    paper    real market data, no orders leave the process (Bybit/MEXC public data needs no key;
             Alpaca data needs the free paper keys)
    testnet  Bybit testnet (ccxt sandbox) | MEXC ``/order/test`` (validation only, no testnet)
             | Alpaca paper account (broker-side simulation)
    live     Bybit / MEXC / Alpaca real orders, only reachable through ``safety.authorize``

Extras: ``pip install 'economia-trader[crypto]'`` (ccxt) / ``[stocks]`` (alpaca-py).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..safety import Mode
from .alpaca_py import AlpacaPy
from .base import Credentials, Exchange, ExchangeError, KeyCheck, Kline, Ticker
from .ccxt_spot import CcxtSpot

__all__ = [
    "AlpacaPy",
    "CcxtSpot",
    "Credentials",
    "Exchange",
    "ExchangeError",
    "KeyCheck",
    "Kline",
    "Ticker",
    "make_exchange",
]

EXCHANGES = ("bybit", "mexc", "alpaca")


def make_exchange(
    name: str,
    mode: Mode,
    *,
    env: Mapping[str, str] | None = None,
    client: Any = None,
) -> Exchange:
    """``client`` injects a ccxt-like client (crypto) or a ``(trading, data)`` pair (alpaca)."""
    if name not in EXCHANGES:
        raise ValueError(f"exchange must be one of {EXCHANGES}, got {name!r}")
    if name == "alpaca":
        creds = Credentials.from_env("ALPACA", env, var_names=("ALPACA_API_KEY", "ALPACA_SECRET_KEY"))
        trading, data = client if client else (None, None)
        network = "live" if mode is Mode.LIVE else "paper"
        return AlpacaPy(network, credentials=creds, trading=trading, data=data, allow_live_orders=mode is Mode.LIVE)
    creds = None if mode is Mode.PAPER else Credentials.from_env(name.upper(), env)
    network = "testnet" if mode is Mode.TESTNET else "mainnet"
    return CcxtSpot(name, network, credentials=creds, client=client, allow_mainnet_orders=mode is Mode.LIVE)
