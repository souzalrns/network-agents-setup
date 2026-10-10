"""Import a planwright plan contract into a runner-plan skeleton.

The other half of the plan↔execution contract (docs/architecture/PLAN-CONTRACT.md).
planwright exports a stable JSON (`planwright-plan/v1`); this maps each item to a
runner step and produces a plan that validates against `plan.schema.json`.

Deliberately a **skeleton**, not an executable plan: planwright does not know the
runner's actions, so `action` is a documented placeholder (`"unassigned"`) that
the router or a human sets before a run. What maps cleanly:

- item.id        -> step.id
- item.title     -> step.task
- item.depends   -> step.depends_on
- item.autonomy  -> step.human_gate (human/assisted → gate; auto → none)

`complexity` and `autonomy` also stay in the export JSON as **signals** the
runner's own selection logic (model_tiers/router) may read — they are not runtime
policy and are never decided here. authz, budget, tools, events stay in the
runner, never in planwright.

    python -m plan_runner.plan_import plan.json --id my-plan [--validate]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .plan_schema import plan_errors

CONTRACT_SCHEMA = "planwright-plan/v1"
PLACEHOLDER_ACTION = "unassigned"  # the router/human assigns the real action pre-run


class ContractError(ValueError):
    """Raised when the contract is missing or malformed."""


def _step_from_item(item: dict[str, Any]) -> dict[str, Any]:
    step: dict[str, Any] = {
        "id": str(item["id"]),
        "action": (item.get("track") or PLACEHOLDER_ACTION) or PLACEHOLDER_ACTION,
    }
    if item.get("title"):
        step["task"] = str(item["title"])
    depends = [str(d) for d in (item.get("depends") or [])]
    if depends:
        step["depends_on"] = depends
    # Autonomy is planning intent → a human gate when the item needs a person.
    if item.get("autonomy") in ("human", "assisted"):
        step["human_gate"] = True
    return step


def _signals_from_items(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Os sinais de planeamento (complexity/autonomy) por passo, para o runner LER.

    Vao no bloco de topo `router.signals` (metadados, livre no schema), nunca em
    campos do passo: `complexity` continua a NAO ser um campo do YAML, so um sinal.
    A seleccao do runner (model_tiers) le daqui a complexidade quando o passo nao
    declara `model_tier`. Ver docs/architecture/CANONICAL-SCENARIO.md.
    """
    signals: dict[str, dict[str, Any]] = {}
    for it in items:
        sig = {k: it[k] for k in ("complexity", "autonomy") if it.get(k) is not None}
        if sig:
            signals[str(it["id"])] = sig
    return signals


def import_contract(contract: dict[str, Any], *, plan_id: str, with_signals: bool = False) -> dict[str, Any]:
    """Map a planwright contract into a runner plan dict (schema-valid skeleton).

    `with_signals` (opt-in) carries the planning signals into `router.signals`, so
    the runner's selection can read them; the default stays the thin skeleton.
    """
    if not isinstance(contract, dict) or contract.get("schema") != CONTRACT_SCHEMA:
        raise ContractError(f"not a {CONTRACT_SCHEMA} contract")
    items = contract.get("items")
    if not isinstance(items, list) or not items:
        raise ContractError("contract has no items (a runner plan needs at least one step)")
    plan: dict[str, Any] = {"id": plan_id, "steps": [_step_from_item(it) for it in items]}
    if with_signals:
        signals = _signals_from_items(items)
        if signals:
            plan["router"] = {"signals": signals}
    return plan


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m plan_runner.plan_import", description=__doc__.splitlines()[0])
    ap.add_argument("contract", help="planwright export JSON (planwright-plan/v1)")
    ap.add_argument("--id", default="planwright-import", help="runner plan id (default: planwright-import)")
    ap.add_argument("--validate", action="store_true", help="validate against plan.schema.json and exit non-zero on error")
    ap.add_argument("--signals", action="store_true", help="carry complexity/autonomy into router.signals (for the runner's selection)")
    args = ap.parse_args(argv)

    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        plan = import_contract(contract, plan_id=args.id, with_signals=args.signals)
    except (OSError, ValueError) as exc:
        print(f"plan_import: {exc}", file=sys.stderr)
        return 2

    errors = plan_errors(plan)
    if args.validate and errors:
        print("plan_import: produced plan is INVALID:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
