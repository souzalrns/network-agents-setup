"""The cycle: proposal -> risk -> gate -> order (paper or exchange) -> journal.

``Trader`` is the only object that can turn a ``TradeProposal`` into an order, and it always
goes through ``risk.assess`` and ``safety.authorize`` first. Analysts (rules, humans, LLM
agents) only ever *propose*; they never hold a key.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from .contracts import Fill, OrderIntent, TradeProposal, to_dict
from .exchanges.base import Exchange, ExchangeError
from .journal import Journal
from .paper import PaperBroker, PaperRejected
from .risk import PortfolioState, Position, RiskLimits, assess
from .safety import Approver, ExecutionBlocked, KillSwitch, Mode, authorize, deny_all

Status = Literal["filled", "sent", "rejected", "blocked", "error"]


@dataclass
class Outcome:
    status: Status
    proposal_id: str
    reasons: list[str] = field(default_factory=list)
    fill: Fill | None = None
    order: dict[str, Any] | None = None


class Trader:
    def __init__(
        self,
        exchange: Exchange,
        *,
        mode: Mode,
        limits: RiskLimits,
        journal: Journal,
        kill_switch: KillSwitch | None = None,
        approver: Approver = deny_all,
        broker: PaperBroker | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if mode is Mode.PAPER and broker is None:
            raise ValueError("paper mode needs a PaperBroker")
        if mode is Mode.TESTNET and exchange.name == "mexc":
            journal.append("note", {"msg": "mexc has no testnet: orders go to /api/v3/order/test (validation only)"})
        self.exchange, self.mode, self.limits, self.journal = exchange, mode, limits, journal
        self.kill_switch = kill_switch or KillSwitch(env=env)
        self.approver, self.broker, self.env = approver, broker, env
        self._state = PortfolioState()  # local book for testnet/live (paper uses the broker's)
        self.stops: dict[str, Decimal] = {}
        self.key_checked = False

    @property
    def state(self) -> PortfolioState:
        return self.broker.state if self.broker else self._state

    def verify_key(self) -> dict[str, Any]:
        """Required once before testnet/live orders. A key that can withdraw is refused."""
        check = self.exchange.check_key()
        self.journal.append(
            "key_check",
            {
                "exchange": self.exchange.name,
                "safe": check.safe_for_trading,
                "can_withdraw": check.can_withdraw,
                "can_trade": check.can_trade,
            },
        )
        if check.can_withdraw:
            raise ExecutionBlocked("key_can_withdraw", "this API key can withdraw; create one with read+trade only")
        if not check.can_trade:
            raise ExecutionBlocked("key_cannot_trade", "this API key cannot trade (read-only)")
        self.key_checked = True
        return check.detail

    def submit(self, proposal: TradeProposal, mark: Decimal | None = None) -> Outcome:
        self.journal.append("proposal", to_dict(proposal))
        try:
            mark = mark if mark is not None else self.exchange.ticker(proposal.symbol).last
        except ExchangeError as exc:
            self.journal.append("error", {"proposal_id": proposal.id, "error": str(exc)})
            return Outcome("error", proposal.id, [str(exc)])

        assessment = assess(proposal, mark_price=mark, limits=self.limits, state=self.state)
        self.journal.append("assessment", to_dict(assessment))
        if not assessment.approved:
            return Outcome("rejected", proposal.id, list(assessment.reasons))

        intent = OrderIntent(
            symbol=proposal.symbol.upper(),
            side=proposal.side,
            qty=proposal.qty,
            order_type="limit" if proposal.entry_price is not None else "market",
            price=proposal.entry_price,
            proposal_id=proposal.id,
        )
        try:
            authorize(
                self.mode,
                intent,
                assessment,
                kill_switch=self.kill_switch,
                approver=self.approver,
                key_checked=self.key_checked,
                env=self.env,
            )
        except ExecutionBlocked as exc:
            self.journal.append("blocked", {"proposal_id": proposal.id, "code": exc.code, "msg": str(exc)})
            return Outcome("blocked", proposal.id, [exc.code])
        self.journal.append("intent", {"mode": self.mode.value, **to_dict(intent)})

        if self.mode is Mode.PAPER:
            try:
                fill = self.broker.execute(intent, mark)  # type: ignore[union-attr]
            except PaperRejected as exc:
                self.journal.append("rejected_by_broker", {"proposal_id": proposal.id, "msg": str(exc)})
                return Outcome("rejected", proposal.id, [str(exc)])
            self.journal.append("fill", to_dict(fill))
            self._track_stop(proposal)
            return Outcome("filled", proposal.id, fill=fill)

        try:
            order = self.exchange.place_order(intent)
        except ExchangeError as exc:
            self.journal.append("error", {"proposal_id": proposal.id, "error": str(exc)})
            return Outcome("error", proposal.id, [str(exc)])
        self.journal.append("order", order)
        self._book_locally(intent, assessment.price)
        self._track_stop(proposal)
        return Outcome("sent", proposal.id, order=order)

    def check_stops(self, marks: Mapping[str, Decimal]) -> list[Outcome]:
        """Exit any position whose mark is at or below its stop (client-side stop in v1)."""
        out = []
        for symbol, stop in list(self.stops.items()):
            held = self.state.positions.get(symbol)
            if held and symbol in marks and marks[symbol] <= stop:
                exit_ = TradeProposal(symbol, "sell", held.qty, rationale=f"stop {stop} hit", proposer="stop")
                out.append(self.submit(exit_, marks[symbol]))
        return out

    def _track_stop(self, proposal: TradeProposal) -> None:
        symbol = proposal.symbol.upper()
        if proposal.side == "buy" and proposal.stop_loss is not None:
            self.stops[symbol] = proposal.stop_loss
        elif symbol not in self.state.positions:
            self.stops.pop(symbol, None)

    def _book_locally(self, intent: OrderIntent, price: Decimal) -> None:
        # v1 books acknowledged orders as filled at the assessed price (conservative for the
        # exposure caps). Reconciling with the exchange's own fills is the next step.
        book = self._state.positions
        held = book.get(intent.symbol)
        if intent.side == "buy":
            if held:
                total = held.qty + intent.qty
                held.avg_price = (held.avg_price * held.qty + price * intent.qty) / total
                held.qty = total
            else:
                book[intent.symbol] = Position(intent.qty, price)
        elif held:
            self._state.realized_today += (price - held.avg_price) * intent.qty
            held.qty -= intent.qty
            if held.qty <= 0:
                del book[intent.symbol]
