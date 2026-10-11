"""tokenwright: a token-cost ledger and a budget cap that refuses BEFORE you spend.

Most cost tools tell you what a run cost *after* it ran. tokenwright does two things
the observability tools don't:

1. **Fail closed on an unknown price.** If a model has no confirmed price, cost is not
   silently treated as zero — ``CostUnknown`` is raised. You never under-count spend
   because a price was missing.
2. **A projective cap.** Before the next call, estimate its cost and refuse it when
   ``spent + next > cap`` (``BudgetExceeded``). The overrun is *prevented*, not
   reported afterwards.

    from tokenwright import prices_from_mapping, ledger_cost_usd, guard_next_call

    prices = prices_from_mapping({
        "gemini-2.5-flash": {"usd_per_1m_input": 0.30, "usd_per_1m_output": 2.50},
    })
    spent = ledger_cost_usd("runs/42/token_usage.jsonl", prices)   # USD so far
    guard_next_call(spent, projected_in=1200, projected_out=800,
                    model="gemini-2.5-flash", prices=prices, cap_usd=0.05)
    # -> raises BudgetExceeded if this call would cross the cap,
    #    or CostUnknown if the model has no confirmed price.

A ledger row is ``{"model", "tokens_in", "tokens_out"?, "tokens_total"?}``. When
``tokens_total`` is present, output = ``tokens_total - tokens_in`` (so reasoning
tokens, billed as output, are counted). Rows with no tokens cost 0. Zero runtime
dependencies: prices are a plain mapping (load them from JSON, YAML, a DB — your call).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

__all__ = [
    "BudgetExceeded",
    "CostUnknown",
    "Prices",
    "__version__",
    "estimate_cost_usd",
    "guard_next_call",
    "ledger_cost_usd",
    "prices_from_mapping",
    "row_cost_usd",
    "would_exceed",
]

# {model: {"in": USD per 1M input tokens, "out": USD per 1M output tokens}}
Prices = dict[str, dict[str, float]]


class CostUnknown(Exception):
    """A model that is used (or about to be used) has no confirmed price."""


class BudgetExceeded(Exception):
    """The next call would cross the cost cap. Carries spent/projected/cap (USD)."""

    def __init__(self, spent: float, projected: float, cap: float) -> None:
        super().__init__(f"budget exceeded: spent {spent:.6f} + next {projected:.6f} > cap {cap:.6f} USD")
        self.spent = spent
        self.projected = projected
        self.cap = cap


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def _int(v: Any) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def prices_from_mapping(data: dict[str, Any]) -> Prices:
    """Normalize ``{model: {usd_per_1m_input, usd_per_1m_output}}`` to a ``Prices`` table.

    Only models with **both** prices confirmed (numbers >= 0) are kept; a model with a
    ``null``/missing price is left out, so it fails closed later (``CostUnknown``).
    """
    prices: Prices = {}
    for name, p in (data or {}).items():
        p = p or {}
        i, o = p.get("usd_per_1m_input"), p.get("usd_per_1m_output")
        if _num(i) and _num(o):
            prices[str(name)] = {"in": float(i), "out": float(o)}
    return prices


def estimate_cost_usd(tokens_in: int, tokens_out: int, model: str, prices: Prices) -> float:
    """USD for a call of ``tokens_in``/``tokens_out`` on ``model``. Fail-closed."""
    if tokens_in <= 0 and tokens_out <= 0:
        return 0.0
    if model not in prices:
        raise CostUnknown(model)
    p = prices[model]
    return (max(tokens_in, 0) * p["in"] + max(tokens_out, 0) * p["out"]) / 1_000_000


def row_cost_usd(row: dict[str, Any], prices: Prices) -> float:
    """USD for one ledger row. Output = ``tokens_total - tokens_in`` when total is
    present (counts reasoning tokens); else ``tokens_out``. Fail-closed on price."""
    tokens_in = _int(row.get("tokens_in")) or 0
    total = _int(row.get("tokens_total"))
    tokens_out = (total - tokens_in) if total is not None else (_int(row.get("tokens_out")) or 0)
    return estimate_cost_usd(tokens_in, tokens_out, str(row.get("model")), prices)


def ledger_cost_usd(ledger: str | Path | Iterable[dict[str, Any]], prices: Prices) -> float:
    """Total USD across a ledger: a JSONL file path, or an iterable of row dicts.

    A malformed JSONL line is skipped (one bad line never invalidates the ledger).
    """
    rows: Iterable[dict[str, Any]]
    if isinstance(ledger, (str, Path)):
        path = Path(ledger)
        if not path.is_file():
            return 0.0
        rows = _iter_jsonl(path)
    else:
        rows = ledger
    return sum(row_cost_usd(r, prices) for r in rows if isinstance(r, dict))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            yield row


def would_exceed(spent_usd: float, next_usd: float, cap_usd: float) -> bool:
    """True iff spending ``next_usd`` more would cross ``cap_usd``."""
    return (spent_usd + next_usd) > cap_usd


def guard_next_call(
    spent_usd: float,
    *,
    projected_in: int,
    projected_out: int,
    model: str,
    prices: Prices,
    cap_usd: float,
) -> float:
    """Refuse the next call if it would cross the cap; return its projected USD otherwise.

    Raises ``CostUnknown`` if ``model`` has no confirmed price (fail-closed), or
    ``BudgetExceeded`` if ``spent + projected > cap``. This is the projective guard:
    call it *before* the request, not after.
    """
    projected = estimate_cost_usd(projected_in, projected_out, model, prices)
    if would_exceed(spent_usd, projected, cap_usd):
        raise BudgetExceeded(spent_usd, projected, cap_usd)
    return projected
