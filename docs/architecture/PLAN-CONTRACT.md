# Plan contract — planwright (plan) ↔ plan_runner (execution)

The one-page interface that lets the two compose **without coupling**. It is the
piece the Fase-A capability matrix named as the only blocker to a *proven*
composition (`docs/initiatives/CAPABILITY-MATRIX-PLANWRIGHT.md`, criterion 10).

- **planwright describes and prioritizes** a plan. It never executes, authorizes,
  budgets, or calls tools.
- **plan_runner executes and governs.** It imports a plan and owns authz, HITL,
  budget, tools, events, retries.
- The boundary is this contract. Neither imports the other's internals; planwright
  has zero runtime dependencies and no `import plan_runner`.

## The export (`planwright export PLAN.md`)

Stable, versioned JSON — `schema: "planwright-plan/v1"`:

```json
{
  "schema": "planwright-plan/v1",
  "items": [
    {
      "id": "A2", "title": "feature", "status": "todo", "owner": "ana",
      "estimate_hours": 16.0, "depends": ["A1"], "track": "eng",
      "autonomy": "human", "complexity": "C4"
    }
  ]
}
```

Field meanings: `status` ∈ todo/doing/blocked/done; `estimate_hours` is effort
(null if unsized); `depends` are item ids; `autonomy` ∈ auto/assisted/human or
null; `complexity` ∈ C1..C4 or null.

## The import (`python -m plan_runner.plan_import plan.json --id <id>`)

Maps each item to a runner **step** and produces a plan valid against
`runner/plan_runner/plan.schema.json`. It is a **skeleton**, not an executable
plan — planwright does not know the runner's actions.

| planwright item | runner step | Notes |
|-----------------|-------------|-------|
| `id` | `id` | — |
| `title` | `task` | — |
| `depends` | `depends_on` | — |
| `track` | `action` | placeholder; `"unassigned"` when no track — the router/human sets the real action before a run |
| `autonomy` = human/assisted | `human_gate: true` | planning *intent* → a gate; the runner's HITL remains the runtime authority |
| `autonomy` = auto | (no gate) | — |
| `complexity` | **not a step field** | a **signal**: `plan_import --signals` carries it into `router.signals` (top-level metadata), which the runner's selection (`model_tiers`) reads to pick a model when the step has no `model_tier`; never the sole decider, never policy |

## What the contract does NOT guarantee / carry

- It does not choose the runner **action** (placeholder only) — that is the
  router/human's job.
- It does not set **model_tier** (planner/executor/verifier is a runner *role*,
  not a complexity level). Complexity only *informs* that choice, downstream.
- It carries **no** authz, budget, tools, events, or retries — those are the
  runner's and never travel through planwright.
- A schema-valid import is **not** an executable plan; it is a sound scaffold to
  be completed by the runner/human.

## Acceptance (what the tests prove)

- `planwright export` emits valid `planwright-plan/v1` JSON (`test_export.py`).
- `import_contract(...)` → a plan with `plan_errors(...) == []` against
  `plan.schema.json` (`runner/tests/test_plan_import.py`).
- autonomy → human_gate; empty/foreign contract rejected.
- zero `import plan_runner` inside the published planwright package.

## Proven end-to-end

The canonical scenario (`CANONICAL-SCENARIO.md`) takes this contract the whole
way: a planwright plan → export → import → a completed executable plan that the
runner runs with a human gate, a budget cap and `done_when` by evidence — all in
one run, proven by `runner/tests/test_canonical_composition.py` and
`oss/planwright/tests/test_export.py`. The composition is no longer an assertion;
it is a test.

## Signals consumed (the "integrate" row, done)

The runner's selection now **reads** the signals, not just carries them:
`plan_import --signals` writes `complexity`/`autonomy` into `router.signals`, and
`model_tiers.resolve_model` picks a model from `complexity` (config
`model-tiers.yaml`, section `complexity`, cheap→expensive) **when the step has no
`model_tier`** — an explicit tier (role) always wins, and with the shipped all-null
config nothing changes. Proven by `runner/tests/test_model_tier.py` and the signal
leg of `test_canonical_composition.py`. `autonomy` was already consumed (→
`human_gate`). `complexity` never becomes the role tier; it only picks the model,
downstream.

## Next (beyond this contract)

Automatic `action` selection from the plan (the `track` placeholder → a real
runner action) is still the router/human's job; nothing infers it yet.
