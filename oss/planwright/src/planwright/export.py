"""Export a plan as a stable JSON contract — the hand-off to an execution runner.

planwright's job ends at *describing* the plan. This is the frozen interface a
runner imports: a versioned list of items with exactly the fields a scheduler
needs. planwright knows nothing about "steps", authorization, budgets or tools —
those belong to the runner. Autonomy and complexity travel as **signals** for the
runner's own selection logic, not as runtime policy.

Stdlib only; no runner import. See docs/architecture/PLAN-CONTRACT.md.
"""

from __future__ import annotations

from .model import Plan

CONTRACT_SCHEMA = "planwright-plan/v1"


def plan_to_contract(plan: Plan) -> dict:
    """The stable export object. Shape is frozen under CONTRACT_SCHEMA."""
    return {
        "schema": CONTRACT_SCHEMA,
        "items": [
            {
                "id": it.id,
                "title": it.title,
                "status": it.status.value,
                "owner": it.owner or None,
                "estimate_hours": it.estimate_hours,
                "depends": list(it.depends),
                "track": it.track or None,
                "autonomy": it.autonomy,  # signal for the runner; None if unset
                "complexity": it.complexity,  # signal for the runner; None if unset
            }
            for it in plan
        ],
    }
