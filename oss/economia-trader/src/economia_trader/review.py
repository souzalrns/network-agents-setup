"""Post-trade review from the journal: the process is graded apart from the outcome.

Method adapted from the HyperGrok Trade Reviewer (galleonlabs/hypergrok-trading-desk, MIT,
``skills/desk-post-trade-review``):

- review from the exchange record (the ``fill`` lines), never from chat or intentions;
- grade the process first (clean / minor break / major break, naming the stage), then state the
  outcome in R and money, without adjectives;
- measure the costs: entry and exit slippage against the ticket price, fees;
- one repeatable finding per trade, not a list.

A trade is flat -> position -> flat on one symbol, so a grid run with several lots is one trade and
its 1R is the sum of the entries' ``loss_at_stop``. Read-only: nothing here touches an exchange.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .journal import Journal

EPS = Decimal("1e-8")
PROTECTION_GAP_S = 60  # an exchange stop should rest within a minute of the entry fill
SLIPPAGE_LEAK_BPS = Decimal(20)  # above this, slippage is the finding of a clean trade
FEES_LEAK_SHARE = Decimal("0.5")  # fees above half of a winning trade's gross are a leak
_EVENTS = {"stop_placed", "stop_cancelled", "stop_dropped", "stop_client_side", "reconcile_mismatch"}
_EVENTS_WITH_ID = {"error", "order_unfilled"}


def _d(value: Any) -> Decimal:
    return Decimal(str(value)) if value not in (None, "") else Decimal(0)


def _symbol(value: Any) -> str:
    """``BTCUSDT`` whatever the line carries (exchange payloads can hold ccxt's ``BTC/USDT``)."""
    return str(value or "").split(":")[0].replace("/", "").upper()


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _q(value: Decimal | None, places: str) -> str | None:
    return None if value is None else str(value.quantize(Decimal(places)))


def _weighted(rows: list[tuple[Decimal, Decimal]]) -> Decimal | None:
    qty = sum((q for q, _ in rows), Decimal(0))
    return sum((q * p for q, p in rows), Decimal(0)) / qty if qty > 0 else None


class _Ledger:
    """What the journal says about each proposal and order, to resolve every fill to its ticket."""

    def __init__(self) -> None:
        self.proposals: dict[str, dict[str, Any]] = {}
        self.assessments: dict[str, dict[str, Any]] = {}
        self.intents: dict[str, dict[str, Any]] = {}  # client_order_id -> intent
        self.orders: dict[str, str] = {}  # exchange order_id -> client_order_id

    def see(self, kind: str, p: dict[str, Any]) -> None:
        if kind == "proposal":
            self.proposals[p["id"]] = p
        elif kind == "assessment":
            self.assessments[p["proposal_id"]] = p
        elif kind == "intent":
            self.intents[p["client_order_id"]] = p
        elif kind == "order" and p.get("order_id"):
            self.orders[str(p["order_id"])] = p.get("client_order_id", "")

    def proposal_for(self, fill: dict[str, Any]) -> str | None:
        coid = fill.get("client_order_id") or self.orders.get(str(fill.get("order_id", "")), "")
        return (self.intents.get(coid) or {}).get("proposal_id") or None

    def mode_for(self, proposal_id: str | None) -> str | None:
        for intent in self.intents.values():
            if intent.get("proposal_id") == proposal_id:
                return intent.get("mode")
        return None


def _review_trade(t: dict[str, Any], led: _Ledger) -> dict[str, Any]:
    buys = [f for f in t["fills"] if f["side"] == "buy"]
    sells = [f for f in t["fills"] if f["side"] == "sell"]
    entry_ids = list(dict.fromkeys(f["proposal_id"] for f in buys if f["proposal_id"]))
    entry_props = [led.proposals.get(i, {}) for i in entry_ids]
    stop = next((_d(p["stop_loss"]) for p in reversed(entry_props) if p.get("stop_loss")), None)
    mode = led.mode_for(entry_ids[0] if entry_ids else None) or "unknown"

    def ticket(f: dict[str, Any]) -> Decimal | None:
        if f["stop_order"]:
            return stop
        prop = led.proposals.get(f["proposal_id"] or "", {})
        if prop.get("entry_price"):
            return _d(prop["entry_price"])
        price = (led.assessments.get(f["proposal_id"] or "") or {}).get("price")
        return _d(price) if price else None

    def slippage(fills: list[dict[str, Any]], sign: int) -> Decimal | None:
        rows = [(f["qty"], f["price"], ticket(f)) for f in fills]
        rows = [r for r in rows if r[2]]
        if not rows:
            return None
        avg, ref = _weighted([(q, p) for q, p, _ in rows]), _weighted([(q, r) for q, _, r in rows])
        return sign * (avg - ref) / ref * 10_000  # type: ignore[operator]  # positive = worse for us

    bought = sum((f["qty"] * f["price"] for f in buys), Decimal(0))
    sold = sum((f["qty"] * f["price"] for f in sells), Decimal(0))
    fees = sum((f["fee"] for f in t["fills"]), Decimal(0))
    gross, net = sold - bought, sold - bought - fees
    risk = sum((_d((led.assessments.get(i) or {}).get("loss_at_stop")) for i in entry_ids), Decimal(0))
    if risk <= 0 and stop is not None:
        qty_in = sum((f["qty"] for f in buys), Decimal(0))
        risk = qty_in * (bought / qty_in - stop) if qty_in > 0 else Decimal(0)
    r_multiple = net / risk if risk > 0 else None

    exit_by = sorted(
        {
            "stop on exchange"
            if f["stop_order"]
            else (led.proposals.get(f["proposal_id"] or "", {}).get("proposer") or "unknown")
            for f in sells
        }
    )

    # ---- process ----
    breaks: list[dict[str, str]] = []

    def brk(severity: str, stage: str, detail: str) -> None:
        breaks.append({"severity": severity, "stage": stage, "detail": detail})

    for pid, prop in zip(entry_ids, entry_props, strict=True):
        if not prop.get("stop_loss"):
            brk("major", "proposal", f"entry {pid} had no stop_loss")
        if not (led.assessments.get(pid) or {}).get("approved"):
            brk("major", "risk", f"entry {pid} filled without an approved risk assessment")
    events = t["events"]
    kinds = [e["kind"] for e in events]
    first_fill = _ts(buys[0]["ts"])
    protection: dict[str, Any]
    if mode == "paper":
        protection = {"where": "client-side (paper)", "gap_s": None, "drops": 0}
    else:
        placed = [e for e in events if e["kind"] == "stop_placed"]
        gap = (_ts(placed[0]["ts"]) - first_fill).total_seconds() if placed else None
        protection = {
            "where": "exchange" if placed else "client-side" if "stop_client_side" in kinds else "none",
            "gap_s": None if gap is None else round(gap, 1),
            "drops": kinds.count("stop_dropped"),
        }
        if not placed and "stop_client_side" not in kinds:
            brk("major", "protection", "the position never had a stop (neither on the exchange nor client-side)")
        elif not placed:
            brk("minor", "protection", "the stop stayed client-side (the venue has no exchange stop for spot)")
        elif gap is not None and gap > PROTECTION_GAP_S:
            brk("minor", "protection", f"the exchange stop rested {gap:.0f}s after the entry fill")
        if protection["drops"]:
            brk("minor", "protection", f"the venue dropped the stop {protection['drops']}x (re-placed)")
    for e in events:
        if e["kind"] == "reconcile_mismatch":
            brk("major", "reconcile", f"book {e['payload'].get('book')} vs exchange {e['payload'].get('exchange')}")
        elif e["kind"] == "error":
            brk("minor", "execution", str(e["payload"].get("error", ""))[:120])
        elif e["kind"] == "order_unfilled":
            brk("minor", "execution", f"order {e['payload'].get('order_id')} ended unfilled")

    grade = "major break" if any(b["severity"] == "major" for b in breaks) else "minor break" if breaks else "clean"
    entry_slip, exit_slip = slippage(buys, 1), slippage(sells, -1)
    if breaks:
        first = next(b for b in breaks if b["severity"] == "major") if grade == "major break" else breaks[0]
        finding = {"type": "break", "stage": first["stage"], "detail": first["detail"]}
    elif max((s for s in (entry_slip, exit_slip) if s is not None), default=Decimal(0)) > SLIPPAGE_LEAK_BPS:
        worst = "entry" if (entry_slip or 0) >= (exit_slip or 0) else "exit"
        bps = entry_slip if worst == "entry" else exit_slip
        finding = {"type": "leak", "stage": worst, "detail": f"{worst} slippage {bps:.1f} bps against the ticket"}
    elif gross > 0 and fees > gross * FEES_LEAK_SHARE:
        finding = {"type": "leak", "stage": "fees", "detail": f"fees took {fees / gross:.0%} of the gross gain"}
    elif "stop on exchange" in exit_by:
        detail = f"the exchange stop closed the trade ({_q(exit_slip, '0.1')} bps from the stop)"
        finding = {"type": "control worked", "stage": "protection", "detail": detail}
    else:
        finding = {"type": "clean", "stage": "-", "detail": "nothing to change"}

    return {
        "symbol": t["symbol"],
        "mode": mode,
        "opened_at": buys[0]["ts"],
        "closed_at": t["fills"][-1]["ts"],
        "holding_s": round((_ts(t["fills"][-1]["ts"]) - first_fill).total_seconds(), 1),
        "entries": entry_ids,
        "proposers": sorted({p.get("proposer", "unknown") for p in entry_props}),
        "exit_by": exit_by,
        "process": {"grade": grade, "breaks": breaks, "protection": protection},
        "outcome": {
            "net": _q(net, "0.0001"),
            "gross": _q(gross, "0.0001"),
            "r": _q(r_multiple, "0.01"),
            "risk_1r": _q(risk, "0.0001"),
        },
        "costs": {
            "fees": _q(fees, "0.0001"),
            "fees_bps": _q(fees / bought * 10_000 if bought > 0 else None, "0.1"),
            "entry_slippage_bps": _q(entry_slip, "0.1"),
            "exit_slippage_bps": _q(exit_slip, "0.1"),
        },
        "finding": finding,
    }


def _week(trades: list[dict[str, Any]]) -> dict[str, Any]:
    rs = [Decimal(t["outcome"]["r"]) for t in trades if t["outcome"]["r"] is not None]
    nets = [Decimal(t["outcome"]["net"]) for t in trades]
    gross = sum((Decimal(t["outcome"]["gross"]) for t in trades), Decimal(0))
    fees = sum((Decimal(t["costs"]["fees"]) for t in trades), Decimal(0))
    wins, losses = [r for r in rs if r > 0], [r for r in rs if r <= 0]
    breaks = Counter(f"{b['severity']}:{b['stage']}" for t in trades for b in t["process"]["breaks"])

    def mean(xs: list[Decimal]) -> str | None:
        return _q(sum(xs, Decimal(0)) / len(xs), "0.01") if xs else None

    return {
        "closed": len(trades),
        "hit_rate": round(len([n for n in nets if n > 0]) / len(nets), 3) if nets else None,
        "avg_win_r": mean(wins),
        "avg_loss_r": mean(losses),
        "expectancy_r": mean(rs),
        "net": _q(sum(nets, Decimal(0)), "0.0001"),
        "largest_loss": _q(min(nets, default=Decimal(0)), "0.0001"),
        "fees": _q(fees, "0.0001"),
        "fees_share_of_gross": _q(fees / gross, "0.01") if gross > 0 else None,
        "process": dict(Counter(t["process"]["grade"] for t in trades)),
        "breaks": dict(breaks.most_common()),
        "pattern": breaks.most_common(1)[0][0] if breaks else None,
    }


def review(journal_path: str | Path, *, since: str | None = None) -> dict[str, Any]:
    """Every closed trade in the journal, reviewed, plus a summary per ISO week of the close."""
    led = _Ledger()
    open_: dict[str, dict[str, Any]] = {}
    closed: list[dict[str, Any]] = []
    orphan_sells = 0

    for e in Journal(journal_path).entries():
        kind, p = e["kind"], e["payload"]
        led.see(kind, p)
        sym = _symbol(p.get("symbol"))
        if kind == "fill":
            fill = {
                "side": p["side"],
                "qty": _d(p["qty"]),
                "price": _d(p["price"]),
                "fee": _d(p.get("fee")),
                "ts": e["ts"],
                "stop_order": bool(p.get("stop_order")),
                "proposal_id": None if p.get("stop_order") else led.proposal_for(p),
            }
            trade = open_.get(sym)
            if fill["side"] == "buy":
                trade = trade or open_.setdefault(sym, {"symbol": sym, "fills": [], "events": [], "qty": Decimal(0)})
                trade["qty"] += fill["qty"]
            elif trade is None:
                orphan_sells += 1
                continue
            else:
                trade["qty"] -= fill["qty"]
            trade["fills"].append(fill)
            if trade["qty"] <= EPS:
                closed.append(_review_trade(open_.pop(sym), led))
        elif sym in open_ and (kind in _EVENTS or kind in _EVENTS_WITH_ID):
            open_[sym]["events"].append(e)

    if since:
        closed = [t for t in closed if t["closed_at"] >= since]
    weeks: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in closed:
        year, week, _ = _ts(t["closed_at"]).isocalendar()
        weeks[f"{year}-W{week:02d}"].append(t)
    return {
        "trades": closed,
        "weeks": {w: _week(ts) for w, ts in sorted(weeks.items())},
        "open": sorted(open_),
        "orphan_sells": orphan_sells,
        "method": "process graded apart from outcome; adapted from HyperGrok's Trade Reviewer (MIT)",
    }
