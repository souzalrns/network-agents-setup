"""Data contracts (schema v1). Every hop of the cycle is a typed, serialisable record:

    EconomicEvent -> TradeProposal -> RiskAssessment -> OrderIntent -> Fill -> SimulationRun

Money is ``Decimal`` end to end (never float); ``to_dict`` turns it into strings so the
journal round-trips exactly. Timestamps are ISO-8601 UTC strings.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from functools import partial
from typing import Any, Literal

SCHEMA_VERSION = "1"

Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


def new_id(prefix: str, n: int) -> str:
    return f"{prefix}{uuid.uuid4().hex[:n]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def dec(value: Any) -> Decimal:
    """Parse a money/quantity value exactly. Floats go through ``str`` to avoid binary noise."""
    if isinstance(value, Decimal):
        return value
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"not a number: {value!r}") from exc
    if not out.is_finite():
        raise ValueError(f"not a finite number: {value!r}")
    return out


def to_dict(record: Any) -> dict[str, Any]:
    """Dataclass -> JSON-safe dict (Decimal -> str, tuple -> list)."""

    def conv(v: Any) -> Any:
        if isinstance(v, Decimal):
            return str(v)
        if isinstance(v, (list, tuple)):
            return [conv(x) for x in v]
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return v

    return {"schema": SCHEMA_VERSION, "type": type(record).__name__, **conv(asdict(record))}


@dataclass(frozen=True)
class EconomicEvent:
    """A piece of evidence with the four clocks that prevent look-ahead bias.

    ``event_at``: when it happened in the world. ``published_at``: when the source published
    it. ``observed_at``: when we fetched it. ``available_at``: the earliest time a decision may
    use it (>= published_at and observed_at). A backtest must only see events whose
    ``available_at`` <= the simulated clock (``usable_at``).
    """

    id: str
    source: str
    kind: str
    payload: dict[str, Any]
    event_at: str
    published_at: str
    observed_at: str
    available_at: str

    def __post_init__(self) -> None:
        if self.available_at < max(self.published_at, self.observed_at):
            raise ValueError(f"{self.id}: available_at precedes published_at/observed_at (look-ahead)")

    def usable_at(self, clock_iso: str) -> bool:
        return self.available_at <= clock_iso


@dataclass(frozen=True)
class TradeProposal:
    """What an analyst (human, rule or LLM) wants to do, with the evidence behind it.

    Spot, long-only in v1: ``buy`` opens/increases a position and must carry a ``stop_loss``
    below the entry; ``sell`` only reduces a position that exists.
    """

    symbol: str
    side: Side
    qty: Decimal
    stop_loss: Decimal | None = None
    entry_price: Decimal | None = None  # None = market
    take_profit: Decimal | None = None
    rationale: str = ""
    evidence_ids: tuple[str, ...] = ()
    proposer: str = "unknown"
    id: str = field(default_factory=partial(new_id, "prop_", 12))
    created_at: str = field(default_factory=now_iso)

    def __post_init__(self) -> None:
        for name in ("qty", "stop_loss", "entry_price", "take_profit"):
            v = getattr(self, name)
            if v is not None and not isinstance(v, Decimal):
                object.__setattr__(self, name, dec(v))
        if self.side not in ("buy", "sell"):
            raise ValueError(f"side must be buy|sell, got {self.side!r}")


@dataclass(frozen=True)
class RiskAssessment:
    proposal_id: str
    approved: bool
    reasons: tuple[str, ...]
    price: Decimal
    notional: Decimal
    loss_at_stop: Decimal
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class OrderIntent:
    """A risk-approved order, exchange-agnostic. ``client_order_id`` is the idempotency key."""

    symbol: str
    side: Side
    qty: Decimal
    order_type: OrderType = "market"
    price: Decimal | None = None
    proposal_id: str = ""
    client_order_id: str = field(default_factory=partial(new_id, "et", 20))

    def __post_init__(self) -> None:
        if self.order_type == "limit" and self.price is None:
            raise ValueError("limit order needs a price")


@dataclass(frozen=True)
class Fill:
    client_order_id: str
    symbol: str
    side: Side
    qty: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal = Decimal(0)
    ts: str = field(default_factory=now_iso)


@dataclass
class SimulationRun:
    """The evaluation record of a paper run or a backtest."""

    exchange: str
    symbol: str
    strategy: str
    starting_cash: Decimal
    id: str = field(default_factory=partial(new_id, "sim_", 12))
    fills: list[Fill] = field(default_factory=list)
    equity_curve: list[Decimal] = field(default_factory=list)
    rejected: int = 0
    blocked: int = 0

    def summary(self) -> dict[str, Any]:
        closes = [f for f in self.fills if f.side == "sell"]
        wins = [f for f in closes if f.realized_pnl > 0]
        peak, max_dd = Decimal(0), Decimal(0)
        for eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                max_dd = max(max_dd, (peak - eq) / peak)
        final = self.equity_curve[-1] if self.equity_curve else self.starting_cash
        return {
            "id": self.id,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "strategy": self.strategy,
            "starting_cash": str(self.starting_cash),
            "final_equity": str(final.quantize(Decimal("0.01"))),
            "return_pct": str(((final / self.starting_cash - 1) * 100).quantize(Decimal("0.01"))),
            "realized_pnl": str(sum((f.realized_pnl for f in self.fills), Decimal(0)).quantize(Decimal("0.01"))),
            "fees": str(sum((f.fee for f in self.fills), Decimal(0)).quantize(Decimal("0.01"))),
            "trades_closed": len(closes),
            "win_rate": round(len(wins) / len(closes), 3) if closes else None,
            "max_drawdown_pct": str((max_dd * 100).quantize(Decimal("0.01"))),
            "rejected_by_risk": self.rejected,
            "blocked_by_gate": self.blocked,
        }
