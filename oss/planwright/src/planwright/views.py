"""Derived text views over a plan — same data, another lens. Zero dependencies.

- **load**: effort grouped by owner (a pure group-by of `Est`).
- **cost**: an *indicative* token/USD estimate from `Complexity` (C1..C4).

Neither is a measurement. `load` is effort, not a calendar. `cost` is a planning
estimate from a small, overridable table — **never** the billing ledger: real
tokens and USD are recorded by the execution runtime (plan_runner / token_usage)
after a run. The commands say so in their own output.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .model import Plan
from .report import _fmt_hours

# Indicative token/USD per complexity band. Deliberately round numbers — this is a
# planning signal, not a price sheet. Override with a JSON file (same schema) via
# $PLANWRIGHT_COST_MODEL; absent or unset, these defaults are used.
DEFAULT_COST_MODEL: dict[str, tuple[int, float]] = {
    "C1": (5_000, 0.10),
    "C2": (15_000, 0.50),
    "C3": (40_000, 2.00),
    "C4": (100_000, 5.00),
}

COST_MODEL_ENV = "PLANWRIGHT_COST_MODEL"


class CostModelError(ValueError):
    """The override cost model (``$PLANWRIGHT_COST_MODEL``) is malformed."""


def load_cost_model(path: str | None = None) -> dict[str, tuple[int, float]]:
    """The cost model: the override file if given or set, else the built-in defaults.

    Fails loud on a malformed override — a silently-ignored wrong table would give
    false numbers, which is worse than no estimate.
    """
    src = path or os.environ.get(COST_MODEL_ENV)
    if not src:
        return dict(DEFAULT_COST_MODEL)
    try:
        raw = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CostModelError(f"cannot read {COST_MODEL_ENV}={src}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CostModelError(f'{src}: cost model must be a JSON object {{"C1": [tokens, usd], ...}}')
    model: dict[str, tuple[int, float]] = {}
    for band, val in raw.items():
        if band not in DEFAULT_COST_MODEL:
            raise CostModelError(f"{src}: unknown complexity band {band!r} (expected C1..C4)")
        if (
            not isinstance(val, (list, tuple))
            or len(val) != 2
            or not all(isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0 for x in val)
        ):
            raise CostModelError(f"{src}: {band} must be [tokens, usd], both numbers >= 0")
        model[band] = (int(val[0]), float(val[1]))
    # Missing bands fall back to the defaults, so a partial override is allowed.
    return {**DEFAULT_COST_MODEL, **model}


def _fmt_tokens(n: int) -> str:
    if n >= 1000 and n % 1000 == 0:
        return f"{n // 1000}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


# --------------------------------------------------------------------------
# load
# --------------------------------------------------------------------------


def render_load(plan: Plan) -> str:
    """Effort grouped by owner. Unsized items count as 0 and are flagged."""
    if len(plan) == 0:
        return "## Esforço por owner\n\n(plano vazio)"
    by_owner: dict[str, list] = {}
    for it in plan:
        by_owner.setdefault(it.owner or "(sem owner)", []).append(it)

    lines = ["## Esforço por owner (estimativa de esforço, não calendário)", ""]
    for owner in sorted(by_owner):
        items = sorted(by_owner[owner], key=lambda it: (-(it.estimate_hours or 0.0), it.id))
        total = sum(it.estimate_hours or 0.0 for it in items)
        unsized = [it.id for it in items if not it.has_estimate]
        head = f"### {owner} — {_fmt_hours(total)}"
        if unsized:
            head += f"  (sem estimativa: {', '.join(unsized)})"
        lines.append(head)
        for it in items:
            est = _fmt_hours(it.estimate_hours) if it.has_estimate else "?"
            extra = " ".join(x for x in (it.complexity or "", it.autonomy or "") if x)
            tail = f"  [{extra}]" if extra else ""
            lines.append(f"  {it.id}  {est}{tail}")
        lines.append("")
    return "\n".join(lines).rstrip()


# --------------------------------------------------------------------------
# cost
# --------------------------------------------------------------------------


def render_cost(plan: Plan, model: dict[str, tuple[int, float]] | None = None) -> str:
    """Indicative token/USD from Complexity. `autonomy=human` costs the agent 0."""
    cm = model or load_cost_model()
    if len(plan) == 0:
        return "## Custo estimado (indicativo — não é o ledger)\n\n(plano vazio)"

    lines = ["## Custo estimado (indicativo — não é o ledger)", ""]
    total_tok = 0
    total_usd = 0.0
    for it in plan:
        human = it.autonomy == "human"
        band = it.complexity
        if human or band is None or band not in cm:
            tok, usd = 0, 0.0
        else:
            tok, usd = cm[band]
        total_tok += tok
        total_usd += usd
        c = band or "—"
        a = it.autonomy or "auto?"
        shown = "—        $0.00" if (human or band is None or band not in cm) else f"~{_fmt_tokens(tok):<6} ~${usd:.2f}"
        lines.append(f"  {it.id:<10} {c:<3} {a:<9} {shown}")
    lines.append("  " + "─" * 34)
    lines.append(f"  {'Total estimado':<24} ~{_fmt_tokens(total_tok)}  ~${total_usd:.2f}")
    lines.append("")
    lines.append("Nota: estimativa a partir de Complexity (C1..C4); `autonomy=human` conta 0 do")
    lines.append("lado do agente. Tokens/USD reais → plan_runner / token_usage, após o run.")
    return "\n".join(lines)
