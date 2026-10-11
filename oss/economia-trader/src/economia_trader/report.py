"""Results per strategy version, straight from the journal (the source of truth).

Each round trip (buy -> sell) is credited to the version that *opened* it, whatever closed it
(stop, take-profit, time exit, signal). This is what tuning needs: did version B beat A?
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from .journal import Journal


def report(journal_path: str | Path) -> dict[str, Any]:
    entries = Journal(journal_path).entries()
    proposer: dict[str, str] = {}
    intent_prop: dict[str, str] = {}
    blocked: Counter[str] = Counter()
    rejected: Counter[str] = Counter()
    opened_by: dict[str, str] = {}
    buy_fees: dict[str, Decimal] = defaultdict(Decimal)
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"entries": 0, "closed": 0, "pnl": [], "proposals": 0})

    for e in entries:
        kind, p = e["kind"], e["payload"]
        if kind == "proposal":
            proposer[p["id"]] = p.get("proposer", "unknown")
            if p.get("side") == "buy":
                stats[proposer[p["id"]]]["proposals"] += 1
        elif kind == "assessment" and not p.get("approved"):
            for r in p.get("reasons", []):
                rejected[r.split(" (")[0][:60]] += 1
        elif kind == "blocked":
            blocked[p.get("code", "?")] += 1
        elif kind == "intent":
            intent_prop[p["client_order_id"]] = p.get("proposal_id", "")
        elif kind == "fill":
            version = proposer.get(intent_prop.get(p["client_order_id"], ""), "unknown")
            sym = p["symbol"]
            if p["side"] == "buy":
                opened_by[sym] = version
                buy_fees[sym] += Decimal(p["fee"])
                stats[version]["entries"] += 1
            else:
                owner = opened_by.pop(sym, version)
                pnl = Decimal(p["realized_pnl"]) - buy_fees.pop(sym, Decimal(0))
                stats[owner]["closed"] += 1
                stats[owner]["pnl"].append(pnl)

    by_version = {}
    for version, s in stats.items():
        pnls: list[Decimal] = s["pnl"]
        wins = [x for x in pnls if x > 0]
        losses = [x for x in pnls if x <= 0]
        by_version[version] = {
            "proposals": s["proposals"],
            "entries": s["entries"],
            "closed": s["closed"],
            "win_rate": round(len(wins) / len(pnls), 3) if pnls else None,
            "pnl": str(sum(pnls, Decimal(0)).quantize(Decimal("0.01"))),
            "avg_win": str((sum(wins, Decimal(0)) / len(wins)).quantize(Decimal("0.01"))) if wins else None,
            "avg_loss": str((sum(losses, Decimal(0)) / len(losses)).quantize(Decimal("0.01"))) if losses else None,
            "expectancy": str((sum(pnls, Decimal(0)) / len(pnls)).quantize(Decimal("0.01"))) if pnls else None,
        }
    return {
        "by_version": by_version,
        "open_positions": sorted(opened_by),
        "rejected_by_risk": dict(rejected.most_common(10)),
        "blocked_by_gate": dict(blocked),
        "auto_kills": [e["payload"]["reason"] for e in entries if e["kind"] == "auto_kill"],
    }
