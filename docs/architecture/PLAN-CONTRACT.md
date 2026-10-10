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
| `complexity` | **not in the YAML** | a **signal** read from the export JSON by the runner's selection logic (`model_tiers`/`router`); never the sole decider, never policy |

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

## Next (beyond this contract)

The runner's executor selection consuming `complexity`/`autonomy` from the export
(the "integrate" row of the matrix) — the signals travel today, but nothing reads
them yet to pick an `action`/`model_tier` automatically.
