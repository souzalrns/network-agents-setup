"""Paper broker: simulated spot fills against a mark price, with fees and slippage.

Conservative by construction: buys fill above the mark, sells below it, both pay the fee.
A strategy that only wins on paper because fills were free is caught here, not in production.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .contracts import Fill, OrderIntent, dec
from .risk import PortfolioState, Position


class PaperRejected(RuntimeError):
    pass


class PaperBroker:
    def __init__(
        self,
        cash: Decimal | str | int,
        *,
        fee_rate: Decimal | str = "0.001",
        slippage_bps: Decimal | str = "5",
    ) -> None:
        self.cash = dec(cash)
        self.fee_rate = dec(fee_rate)
        self.slippage = dec(slippage_bps) / Decimal(10_000)
        self.state = PortfolioState()

    def execute(self, intent: OrderIntent, mark: Decimal) -> Fill:
        mark = dec(mark)
        if intent.order_type == "limit":
            # A limit only fills if the mark is already through it (no queue modelling in v1).
            crossed = mark <= intent.price if intent.side == "buy" else mark >= intent.price  # type: ignore[operator]
            if not crossed:
                raise PaperRejected(f"limit {intent.price} not reached (mark {mark})")
            price = intent.price  # type: ignore[assignment]
        else:
            price = mark * (1 + self.slippage) if intent.side == "buy" else mark * (1 - self.slippage)
        notional = intent.qty * price
        fee = notional * self.fee_rate
        symbol = intent.symbol.upper()
        held = self.state.positions.get(symbol)
        realized = Decimal(0)

        if intent.side == "buy":
            if notional + fee > self.cash:
                raise PaperRejected(f"insufficient cash: need {notional + fee:.2f}, have {self.cash:.2f}")
            self.cash -= notional + fee
            if held:
                total = held.qty + intent.qty
                held.avg_price = (held.avg_price * held.qty + price * intent.qty) / total
                held.qty = total
            else:
                self.state.positions[symbol] = Position(intent.qty, price)
            realized = -fee
        else:
            if not held or held.qty < intent.qty:
                raise PaperRejected(f"cannot sell {intent.qty} {symbol}: holding {held.qty if held else 0}")
            self.cash += notional - fee
            realized = (price - held.avg_price) * intent.qty - fee
            held.qty -= intent.qty
            if held.qty == 0:
                del self.state.positions[symbol]

        self.state.realized_today += realized
        return Fill(intent.client_order_id, symbol, intent.side, intent.qty, price, fee, realized)

    def equity(self, marks: dict[str, Decimal]) -> Decimal:
        return self.cash + self.state.exposure(marks)

    def new_day(self) -> None:
        """Reset the daily realized P&L (the daily loss cap is per day)."""
        self.state.realized_today = Decimal(0)

    def to_dict(self) -> dict[str, Any]:
        """Serialisable state, so a scheduled run (cron, systemd timer) survives restarts."""
        return {
            "cash": str(self.cash),
            "fee_rate": str(self.fee_rate),
            "slippage": str(self.slippage),
            "realized_today": str(self.state.realized_today),
            "positions": {
                s: {"qty": str(p.qty), "avg_price": str(p.avg_price)} for s, p in self.state.positions.items()
            },
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PaperBroker:
        broker = cls(d["cash"], fee_rate=d["fee_rate"], slippage_bps=dec(d["slippage"]) * 10_000)
        broker.state.realized_today = dec(d.get("realized_today", "0"))
        for s, p in (d.get("positions") or {}).items():
            broker.state.positions[s] = Position(dec(p["qty"]), dec(p["avg_price"]))
        return broker
