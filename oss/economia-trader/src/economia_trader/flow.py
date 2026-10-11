"""Institutional options flow as evidence: one ``FlowPrint`` per large option order.

Provider-agnostic on purpose: any flow vendor (or an export from one) becomes a list of
``FlowPrint``. ``available_at`` is when *we* could have known it (e.g. the next morning for a
previous-session scan), so a screen run "as of" a time never sees the future.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Protocol

from .contracts import dec

Sentiment = Literal["bullish", "bearish"]


@dataclass(frozen=True)
class FlowPrint:
    id: str
    ticker: str
    sentiment: Sentiment  # vendor's call: e.g. calls bought at the ask = bullish
    premium: Decimal  # USD paid for the order
    volume: int  # contracts traded on the day (that strike/expiry)
    open_interest: int  # contracts open before the day
    dte: int  # days to expiry
    iv_rank: Decimal  # 0..100
    market_cap: Decimal  # USD
    observed_at: str
    available_at: str
    earnings_date: str | None = None  # YYYY-MM-DD of the next earnings, if known
    source: str = "unknown"

    @classmethod
    def from_mapping(cls, d: dict[str, Any]) -> FlowPrint:
        sentiment = str(d["sentiment"]).lower()
        if sentiment not in ("bullish", "bearish"):
            raise ValueError(f"{d.get('id')}: sentiment must be bullish|bearish")
        return cls(
            id=str(d["id"]),
            ticker=str(d["ticker"]).upper(),
            sentiment=sentiment,  # type: ignore[arg-type]
            premium=dec(d["premium"]),
            volume=int(d["volume"]),
            open_interest=int(d["open_interest"]),
            dte=int(d["dte"]),
            iv_rank=dec(d["iv_rank"]),
            market_cap=dec(d["market_cap"]),
            observed_at=str(d["observed_at"]),
            available_at=str(d.get("available_at") or d["observed_at"]),
            earnings_date=d.get("earnings_date"),
            source=str(d.get("source", "unknown")),
        )


class FlowSource(Protocol):
    def prints(self, as_of: str) -> list[FlowPrint]: ...


class JsonFileFlowSource:
    """A JSON list of prints (an export from any vendor). Only prints available ``as_of``."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def prints(self, as_of: str) -> list[FlowPrint]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [p for p in (FlowPrint.from_mapping(r) for r in raw) if p.available_at <= as_of]


class StaticFlowSource:
    """In-memory source (tests, notebooks)."""

    def __init__(self, prints: Iterable[FlowPrint]) -> None:
        self._prints = list(prints)

    def prints(self, as_of: str) -> list[FlowPrint]:
        return [p for p in self._prints if p.available_at <= as_of]
