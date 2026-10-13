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

from .contracts import Fill, OrderIntent, TradeProposal, dec, new_id, to_dict
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
        # testnet/live: orders the exchange has not settled yet, and the stop orders resting on it
        self.pending: dict[str, dict[str, Any]] = {}
        self.exchange_stops: dict[str, dict[str, Any]] = {}
        self._client_side_noted: set[str] = set()

    @property
    def reconciles(self) -> bool:
        """Testnet/live with an adapter that reports fills (both adapters do)."""
        return self.mode is not Mode.PAPER and hasattr(self.exchange, "order_status")

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

        if intent.side == "sell":
            self._cancel_exchange_stop(intent.symbol, why="exit by the trader")  # never sell twice
        try:
            order = self.exchange.place_order(intent)
        except ExchangeError as exc:
            self.journal.append("error", {"proposal_id": proposal.id, "error": str(exc)})
            return Outcome("error", proposal.id, [str(exc)])
        self.journal.append("order", order)
        self._track_stop(proposal)
        if not self.reconciles or order.get("test_order") or not order.get("order_id"):
            # validation-only orders (MEXC /order/test) never fill: book locally, as v0.1 did
            self._book_locally(intent, assessment.price)
            return Outcome("sent", proposal.id, order=order)
        self.pending[str(order["order_id"])] = {
            "symbol": intent.symbol,
            "side": intent.side,
            "qty": str(intent.qty),
            "booked": "0",
            "price": str(assessment.price),
            "proposal_id": proposal.id,
        }
        self.reconcile()  # market orders usually settle at once; anything else on the next tick
        return Outcome("sent", proposal.id, order=order)

    def equity(self, marks: Mapping[str, Decimal]) -> Decimal | None:
        """Paper: the broker's equity. Testnet/live: the exchange's own (use a dedicated account or
        sub-account: deposits and withdrawals move it too). None when the exchange cannot tell us."""
        if self.broker is not None:
            return self.broker.equity(dict(marks))
        if not hasattr(self.exchange, "account_equity"):
            return None
        try:
            return self.exchange.account_equity(dict(marks))  # type: ignore[attr-defined]
        except ExchangeError as exc:
            self.journal.append("error", {"error": f"account equity: {exc}"})
            return None

    # ---- reconciliation with the exchange (testnet/live) ----

    def reconcile(self) -> list[dict[str, Any]]:
        """Book what the exchange actually filled, follow the resting stops, keep them in sync."""
        if not self.reconciles:
            return []
        fills: list[dict[str, Any]] = []
        for oid, p in list(self.pending.items()):
            fill = self._settle(p["symbol"], oid, p["side"], p, fallback=dec(p["price"]))
            if fill is not None:
                fills.append(fill)
        for sym, st in list(self.exchange_stops.items()):
            fill = self._settle(sym, st["order_id"], "sell", st, fallback=dec(st["stop"]), stop=True)
            if fill is not None:
                fills.append(fill)
        for sym in list(self.state.positions):
            self._sync_exchange_stop(sym)
        return fills

    def _settle(
        self, symbol: str, oid: str, side: str, rec: dict[str, Any], *, fallback: Decimal, stop: bool = False
    ) -> dict[str, Any] | None:
        try:
            st = self.exchange.order_status(symbol, oid)  # type: ignore[attr-defined]
        except ExchangeError as exc:
            self.journal.append("error", {"order_id": oid, "symbol": symbol, "error": f"order status: {exc}"})
            return None
        new = st.filled_qty - dec(rec.get("booked", "0"))
        fill = None
        if new > 0:
            price = st.avg_price or fallback
            self._book_fill(symbol, side, new, price)
            rec["booked"] = str(st.filled_qty)
            fill = {
                "source": "exchange",
                "order_id": oid,
                "symbol": symbol,
                "side": side,
                "qty": str(new),
                "price": str(price),
                "fee": str(st.fee),
                "status": st.status,
                "stop_order": stop,
            }
            self.journal.append("fill", fill)
        if st.final:
            if stop:
                self.exchange_stops.pop(symbol, None)
                if st.filled_qty <= 0:  # expired/cancelled by the venue (e.g. a DAY stop): re-placed below
                    self.journal.append("stop_dropped", {"symbol": symbol, "order_id": oid, "status": st.status})
            else:
                self.pending.pop(oid, None)
                if st.filled_qty <= 0:
                    self.journal.append("order_unfilled", {"order_id": oid, "symbol": symbol, "status": st.status})
        return fill

    def _sync_exchange_stop(self, symbol: str) -> None:
        """One stop order on the exchange for the whole position, at the trader's stop price."""
        held = self.state.positions.get(symbol)
        stop = self.stops.get(symbol)
        current = self.exchange_stops.get(symbol)
        if not held or held.qty <= 0 or stop is None:
            self._cancel_exchange_stop(symbol, why="no position")
            return
        if current and dec(current["qty"]) == held.qty and dec(current["stop"]) == stop:
            return
        if symbol in self._client_side_noted:
            return
        self._cancel_exchange_stop(symbol, why="position changed")
        coid = new_id("stop-", 16)  # short and unique (Bybit orderLinkId <= 36 chars)
        try:
            res = self.exchange.place_stop(symbol, held.qty, stop, coid)  # type: ignore[attr-defined]
        except (ExchangeError, AttributeError) as exc:
            self._client_side_noted.add(symbol)
            self.journal.append("stop_client_side", {"symbol": symbol, "stop": str(stop), "why": str(exc)})
            return
        self.exchange_stops[symbol] = {
            "order_id": str(res.get("order_id")),
            "qty": str(held.qty),
            "stop": str(stop),
            "booked": "0",
        }
        self.journal.append("stop_placed", {"symbol": symbol, **res})

    def _cancel_exchange_stop(self, symbol: str, *, why: str) -> None:
        current = self.exchange_stops.pop(symbol, None)
        if not current:
            return
        try:
            self.exchange.cancel_order(symbol, current["order_id"])  # type: ignore[attr-defined]
            self.journal.append("stop_cancelled", {"symbol": symbol, "order_id": current["order_id"], "why": why})
        except ExchangeError as exc:  # already filled or gone: the next reconcile books whatever happened
            self.journal.append("error", {"symbol": symbol, "error": f"cancel stop: {exc}"})
            self.exchange_stops[symbol] = current

    def sync_positions(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        """Compare the book with the exchange. Only ever adjusts DOWN: if the exchange holds less than we
        think (a fill we missed, a manual sell), the book follows it. If it holds more, it may be the
        owner's own coins, so nothing is adopted; both cases are journaled (``reconcile_mismatch``)."""
        if not self.reconciles or not hasattr(self.exchange, "position_qty"):
            return []
        out = []
        for sym in sorted(set(symbols or []) | set(self.state.positions)):
            try:
                real = self.exchange.position_qty(sym)  # type: ignore[attr-defined]
            except ExchangeError as exc:
                self.journal.append("error", {"symbol": sym, "error": f"position: {exc}"})
                continue
            held = self.state.positions.get(sym)
            book = held.qty if held else Decimal(0)
            if real + Decimal("1e-8") < book:
                held.qty = real  # type: ignore[union-attr]
                if held and held.qty <= 0:
                    del self._state.positions[sym]
                rec = {"symbol": sym, "book": str(book), "exchange": str(real), "action": "book adjusted down"}
            elif real > book + Decimal("1e-8"):
                rec = {"symbol": sym, "book": str(book), "exchange": str(real), "action": "none (not ours?)"}
            else:
                continue
            self.journal.append("reconcile_mismatch", rec)
            out.append(rec)
        return out

    def check_stops(self, marks: Mapping[str, Decimal]) -> list[Outcome]:
        """Exit any position whose mark is at or below its stop. A stop resting on the exchange is the
        exchange's job (``reconcile`` books it); this client-side check covers paper and venues without."""
        out = []
        for symbol, stop in list(self.stops.items()):
            if symbol in self.exchange_stops:
                continue
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
        # Only for orders that never fill on the exchange (validation-only, e.g. MEXC /order/test) or
        # adapters without fills: booked at the assessed price. Real orders go through ``reconcile``.
        self._book_fill(intent.symbol, intent.side, intent.qty, price)

    def _book_fill(self, symbol: str, side: str, qty: Decimal, price: Decimal) -> None:
        book = self._state.positions
        held = book.get(symbol)
        if side == "buy":
            if held:
                total = held.qty + qty
                held.avg_price = (held.avg_price * held.qty + price * qty) / total
                held.qty = total
            else:
                book[symbol] = Position(qty, price)
        elif held:
            qty = min(qty, held.qty)
            self._state.realized_today += (price - held.avg_price) * qty
            held.qty -= qty
            if held.qty <= 0:
                del book[symbol]
                self.stops.pop(symbol, None)
