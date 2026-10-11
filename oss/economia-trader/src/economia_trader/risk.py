"""The risk engine: a deterministic, fail-closed gate between an idea and an order.

No LLM sits here. A proposal passes only if *every* rule passes; the assessment carries the
list of reasons so the journal shows exactly why something was refused.

Limits have **no money defaults**: ``RiskLimits.from_mapping`` refuses a config that does not
state the order cap, the per-trade loss cap and the daily loss cap explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .contracts import RiskAssessment, TradeProposal, dec

_REQUIRED = ("max_order_notional", "max_loss_per_trade", "max_daily_loss", "allowed_symbols")


@dataclass(frozen=True)
class RiskLimits:
    """Caps in the quote currency (e.g. USDT). Spot, long-only, no leverage in v1."""

    max_order_notional: Decimal
    max_loss_per_trade: Decimal
    max_daily_loss: Decimal
    allowed_symbols: frozenset[str]  # ["*"] = any symbol (explicit opt-in, e.g. a screened universe)
    max_open_positions: int = 1
    max_total_exposure: Decimal | None = None  # default: max_order_notional * max_open_positions
    fee_rate: Decimal = Decimal("0.001")  # per side, used to price the loss at stop
    max_price_deviation: Decimal = Decimal("0.02")  # a limit price may sit at most 2% from mark

    def __post_init__(self) -> None:
        for name in ("max_order_notional", "max_loss_per_trade", "max_daily_loss"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be > 0")
        if self.max_loss_per_trade > self.max_daily_loss:
            raise ValueError("max_loss_per_trade cannot exceed max_daily_loss")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be >= 1")

    @property
    def exposure_cap(self) -> Decimal:
        return self.max_total_exposure or self.max_order_notional * self.max_open_positions

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> RiskLimits:
        missing = [k for k in _REQUIRED if k not in data]
        if missing:
            raise ValueError(f"risk limits must be explicit; missing: {', '.join(missing)}")
        symbols = data["allowed_symbols"]
        if not isinstance(symbols, list) or not symbols:
            raise ValueError("allowed_symbols must be a non-empty list")
        kwargs: dict[str, Any] = {
            "max_order_notional": dec(data["max_order_notional"]),
            "max_loss_per_trade": dec(data["max_loss_per_trade"]),
            "max_daily_loss": dec(data["max_daily_loss"]),
            "allowed_symbols": frozenset(s.upper() for s in symbols),
        }
        if "max_open_positions" in data:
            kwargs["max_open_positions"] = int(data["max_open_positions"])
        for key in ("max_total_exposure", "fee_rate", "max_price_deviation"):
            if key in data:
                kwargs[key] = dec(data[key])
        return cls(**kwargs)


@dataclass
class Position:
    qty: Decimal
    avg_price: Decimal


@dataclass
class PortfolioState:
    """What the risk engine needs to know about the book. ``realized_today`` is signed."""

    positions: dict[str, Position] = field(default_factory=dict)
    realized_today: Decimal = Decimal(0)

    def exposure(self, marks: dict[str, Decimal]) -> Decimal:
        return sum((p.qty * marks.get(s, p.avg_price) for s, p in self.positions.items()), Decimal(0))


def assess(
    proposal: TradeProposal,
    *,
    mark_price: Decimal,
    limits: RiskLimits,
    state: PortfolioState,
    marks: dict[str, Decimal] | None = None,
) -> RiskAssessment:
    """Apply every rule; approve only if none fails."""
    reasons: list[str] = []
    symbol = proposal.symbol.upper()
    mark = dec(mark_price)
    price = proposal.entry_price if proposal.entry_price is not None else mark
    qty = proposal.qty
    notional = qty * price
    loss_at_stop = Decimal(0)

    if mark <= 0:
        reasons.append("no valid mark price")
    if qty <= 0:
        reasons.append("qty must be > 0")
    if symbol not in limits.allowed_symbols and "*" not in limits.allowed_symbols:
        reasons.append(f"{symbol} is not in allowed_symbols")
    if proposal.entry_price is not None and mark > 0:
        deviation = abs(proposal.entry_price - mark) / mark
        if deviation > limits.max_price_deviation:
            reasons.append(f"limit price {deviation:.2%} away from mark (max {limits.max_price_deviation:.2%})")

    if state.realized_today <= -limits.max_daily_loss and proposal.side == "buy":
        reasons.append(f"daily loss cap hit ({state.realized_today} <= -{limits.max_daily_loss}); only exits allowed")

    if proposal.side == "buy":
        if proposal.stop_loss is None:
            reasons.append("buy without stop_loss")
        elif proposal.stop_loss >= price:
            reasons.append("stop_loss must be below the entry price")
        else:
            loss_at_stop = qty * (price - proposal.stop_loss) + notional * limits.fee_rate * 2
            if loss_at_stop > limits.max_loss_per_trade:
                reasons.append(f"loss at stop {loss_at_stop:.2f} > max_loss_per_trade {limits.max_loss_per_trade}")
            headroom = limits.max_daily_loss + min(state.realized_today, Decimal(0))
            if loss_at_stop > headroom:
                reasons.append(f"loss at stop {loss_at_stop:.2f} > remaining daily loss budget {headroom:.2f}")
        if notional > limits.max_order_notional:
            reasons.append(f"notional {notional:.2f} > max_order_notional {limits.max_order_notional}")
        if symbol not in state.positions and len(state.positions) >= limits.max_open_positions:
            reasons.append(f"max_open_positions ({limits.max_open_positions}) reached")
        exposure = state.exposure(marks or {symbol: mark}) + notional
        if exposure > limits.exposure_cap:
            reasons.append(f"total exposure {exposure:.2f} > cap {limits.exposure_cap}")
    else:
        held = state.positions.get(symbol)
        if held is None or held.qty <= 0:
            reasons.append(f"sell without an open {symbol} position (spot, no shorting)")
        elif qty > held.qty:
            reasons.append(f"sell qty {qty} > held {held.qty}")

    return RiskAssessment(
        proposal_id=proposal.id,
        approved=not reasons,
        reasons=tuple(reasons),
        price=price,
        notional=notional,
        loss_at_stop=loss_at_stop,
    )
