"""The whale screen: deterministic filters over institutional options flow.

Defaults reproduce the r/Trading method the maestro brought (mid-caps $1B-$10B, >= $30K per
order, IV rank >= 80, >= 70% bullish premium, Vol/OI < 0.5, 15-60 DTE). Every knob is config,
and every config has a ``version`` (hash of its values) that is stamped on each proposal, so
results can be compared per version while the screen is tuned.

Two deliberate differences from the post, both configurable:
- ``block_earnings_days`` (default 7): the post only *flags* earnings; we exclude them, because
  an earnings gap jumps over a stop and breaks the risk engine's loss-at-stop.
- ``vol_oi_max`` / ``vol_oi_min``: the post uses Vol/OI < 0.5, while "unusual activity" screens
  usually want Vol/OI > 1 (new positions). Test both; do not assume.

``screen`` also returns *why* each ticker was dropped, which is what tuning needs.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from .contracts import dec
from .flow import FlowPrint

_DEC_FIELDS = (
    "min_market_cap",
    "max_market_cap",
    "min_premium",
    "min_iv_rank",
    "min_bullish_pct",
    "vol_oi_max",
    "vol_oi_min",
)


@dataclass(frozen=True)
class ScreenConfig:
    min_market_cap: Decimal = Decimal("1000000000")
    max_market_cap: Decimal = Decimal("10000000000")
    min_premium: Decimal = Decimal("30000")
    min_iv_rank: Decimal = Decimal("80")
    min_bullish_pct: Decimal = Decimal("0.70")
    vol_oi_max: Decimal | None = Decimal("0.5")
    vol_oi_min: Decimal | None = None
    min_dte: int = 15
    max_dte: int = 60
    block_earnings_days: int | None = 7  # None = only flag, like the original post
    max_candidates: int = 3
    note: str = ""

    @property
    def version(self) -> str:
        payload = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in asdict(self).items() if k != "note"}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:10]

    @classmethod
    def from_mapping(cls, d: dict[str, Any]) -> ScreenConfig:
        unknown = set(d) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown screen config keys: {sorted(unknown)}")
        kw: dict[str, Any] = {}
        for k, v in d.items():
            kw[k] = (dec(v) if v is not None else None) if k in _DEC_FIELDS else v
        return cls(**kw)


@dataclass
class Candidate:
    ticker: str
    bullish_premium: Decimal
    bearish_premium: Decimal
    bullish_pct: Decimal
    iv_rank: Decimal
    vol_oi: Decimal
    largest_order: Decimal
    market_cap: Decimal
    earnings_date: str | None
    earnings_soon: bool
    print_ids: tuple[str, ...]


@dataclass
class ScreenResult:
    as_of: str
    config_version: str
    candidates: list[Candidate] = field(default_factory=list)
    dropped: dict[str, list[str]] = field(default_factory=dict)
    prints_seen: int = 0
    prints_kept: int = 0


def _days_until(as_of: str, day: str | None) -> int | None:
    if not day:
        return None
    return (date.fromisoformat(day[:10]) - date.fromisoformat(as_of[:10])).days


def screen(prints: list[FlowPrint], config: ScreenConfig, as_of: str) -> ScreenResult:
    res = ScreenResult(as_of=as_of, config_version=config.version, prints_seen=len(prints))
    kept: dict[str, list[FlowPrint]] = defaultdict(list)
    for p in prints:
        if p.available_at > as_of:
            continue  # never look ahead
        if not (config.min_market_cap <= p.market_cap <= config.max_market_cap):
            _drop(res, p.ticker, "market cap out of range")
            continue
        if p.premium < config.min_premium or not (config.min_dte <= p.dte <= config.max_dte):
            continue  # order-level noise: not a reason to drop the ticker
        kept[p.ticker].append(p)
    res.prints_kept = sum(len(v) for v in kept.values())

    for ticker, ps in kept.items():
        reasons: list[str] = []
        bull = sum((p.premium for p in ps if p.sentiment == "bullish"), Decimal(0))
        bear = sum((p.premium for p in ps if p.sentiment == "bearish"), Decimal(0))
        pct = bull / (bull + bear) if bull + bear > 0 else Decimal(0)
        oi = sum(p.open_interest for p in ps)
        vol_oi = Decimal(sum(p.volume for p in ps)) / oi if oi else Decimal("Infinity")
        latest = max(ps, key=lambda p: p.observed_at)
        days = _days_until(as_of, latest.earnings_date)
        earnings_soon = days is not None and 0 <= days <= (config.block_earnings_days or 7)

        if latest.iv_rank < config.min_iv_rank:
            reasons.append(f"iv_rank {latest.iv_rank} < {config.min_iv_rank}")
        if pct < config.min_bullish_pct:
            reasons.append(f"bullish {pct:.0%} < {config.min_bullish_pct:.0%}")
        if config.vol_oi_max is not None and vol_oi >= config.vol_oi_max:
            reasons.append(f"vol/oi {vol_oi:.2f} >= {config.vol_oi_max}")
        if config.vol_oi_min is not None and vol_oi <= config.vol_oi_min:
            reasons.append(f"vol/oi {vol_oi:.2f} <= {config.vol_oi_min}")
        if earnings_soon and config.block_earnings_days is not None:
            reasons.append(f"earnings in {days}d (blocked)")
        if reasons:
            for r in reasons:
                _drop(res, ticker, r)
            continue
        res.candidates.append(
            Candidate(
                ticker=ticker,
                bullish_premium=bull,
                bearish_premium=bear,
                bullish_pct=pct.quantize(Decimal("0.001")),
                iv_rank=latest.iv_rank,
                vol_oi=vol_oi.quantize(Decimal("0.001")),
                largest_order=max(p.premium for p in ps),
                market_cap=latest.market_cap,
                earnings_date=latest.earnings_date,
                earnings_soon=earnings_soon,
                print_ids=tuple(sorted(p.id for p in ps)),
            )
        )
    res.candidates.sort(key=lambda c: (c.bullish_pct, c.bullish_premium), reverse=True)
    for c in res.candidates[config.max_candidates :]:
        _drop(res, c.ticker, f"ranked below the top {config.max_candidates}")
    res.candidates = res.candidates[: config.max_candidates]
    return res


def _drop(res: ScreenResult, ticker: str, reason: str) -> None:
    reasons = res.dropped.setdefault(ticker, [])
    if reason not in reasons:
        reasons.append(reason)
