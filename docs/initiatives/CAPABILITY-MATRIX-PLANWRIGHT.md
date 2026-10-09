# Capability matrix — planwright × plan_runner (Fase A)

> Self-audit per `docs/initiatives/REPO-EVAL-PLAYBOOK.md`, before adding
> competitors or publishing. Evaluated at **`main` `71f0b8e`**. Evidence is
> **code and tests only** — a README is documentation, not proof.
>
> Guiding question: *if someone found planwright alone, with what evidence could
> we recommend it for planning, what are its limits, and what optional
> integration lets a platform use it without making it dependent?*

Status legend: **proven** (code + passing test) · **partial** (exists, limited or
untested end-to-end) · **absent** · **N/V** (not verified).

## The 10 criteria

| # | Criterion | Lives in | Status | Evidence (code · test) | Gap |
|---|-----------|----------|--------|------------------------|-----|
| 1 | Research & discovery | plan_runner | **partial** | `scripts/web_fetch.py` (F2 fetch, allowlist/SSRF) · `runner/tests/test_web_fetch.py`, `test_web_allowlist.py`; RAG retrieve `plan_runner/mcp_knowledge.py` · `test_mcp_knowledge.py` | no agent that takes a goal → finds unknowns → reports alternatives/uncertainty end-to-end; `discover` (vs `fetch`) missing |
| 2 | Structural planning | — (human/doc) | **absent (auto)** | ADRs + `plan_runner/areas.py`/`plan_schema.py` describe structure, but goal→architecture is authored by a human/agent, not produced by the system | no automated structural planner; this is a meta-agent/concierge job, not built |
| 3 | Executive planning (WBS, deps, effort, autonomy, blocks) | **planwright** | **proven** (repr+analysis) / partial (auto-decompose) | `oss/planwright/src/planwright/{model,parse,graph}.py`, Autonomy/Complexity cols · `oss/planwright/tests/` (48); runner plan form `plan_runner/plan_schema.py` · `test_plan_schema.py` | decomposing a goal *into* the table is still manual/agent, not automatic |
| 4 | Visualization | **planwright** | **proven** (static) / partial (interactive) | `oss/planwright/src/planwright/{mermaid,report}.py` (graph+Kanban+action) · `test_visual.py` | static Mermaid only; no interactive board / live exec state |
| 5 | Executor selection (model/agent/tool) | plan_runner | **partial** | `plan_runner/model_tiers.py` (planner/executor/verifier → `config/model-tiers.yaml`) · `test_model_tier.py`; `plan_runner/router.py` (area routing) · `test_router.py` | selection does **not** read planwright `Complexity`/`Autonomy`; not budget/availability-aware |
| 6 | Governed execution (authz, HITL, retries, budget, cancel, recovery) | **plan_runner** | **proven** | `hitl.py` · `test_hitl_contract.py`; `tool_executor.py` (flag-gated authz) · `test_tool_executor.py`; `cost.py` (budget ceiling→paused_budget) · `test_budget.py`; `events.py` · `test_events.py`; `external_worker.py` · `test_external_worker.py`; recovery · `test_crash_recovery.py` | the runner's core strength — do **not** duplicate it in planwright |
| 7 | Validation & completion (evidence, not self-declared) | **plan_runner** | **proven** (mechanisms) / partial (arbitrary criteria) | `done_when.py` (file exists/contains, no free-text trust) · `test_done_when.py`; `l5_eval.py` (regression gate, provenance_ok) · `test_l5_eval.py`; `test_f5_evidence.py`, `test_engenharia_ship_gate.py` | `done_when` supports limited forms; richer acceptance checks are future |
| 8 | Operational learning (estimated vs actual, cost, quality) | plan_runner | **partial** | `cost.py` (actual cost from token ledger) · `test_budget.py`; `capabilities.py` capability-maturity · `test_capabilities.py`; `token_projection.py` **N/V** (its own docstring says not verified) | no loop feeding estimated-vs-actual back into future plans |
| 9 | Integrity & security (audit, access, isolation, limits, policy) | plan_runner + oss | **proven** (several) / partial (access/isolation) | `events.py` (audit log); `web_allowlist.py` (SSRF/allowlist) · `test_web_allowlist.py`; `skill_scan.py`/`oss/skill-scout` (skill safety); `provenance.py` · `test_provenance.py`; `test_privacy_separation.py`; governance `test_governance_mapping.py` + ISO docs; `oss/auditron` (CI security) | DB access-control/data-isolation (RLS) tracked elsewhere (S-005); not fully proven here |
| 10 | Portability & maintenance (contracts, tests, versions, license) | **planwright** (pkg) / contract gap | **proven** (packaging) / **partial** (contract) | planwright: zero-dep, MIT, `pyproject` v0.2.0, `CHANGELOG`, 48 tests, own CI; runner: ~70 test files | **no formal plan export/import contract** between planwright (Markdown) and plan_runner (YAML `plan_schema`); only `graph --json` |

## Autonomy test (the boundary holds today)

- **Delete plan_runner** → `planwright validate|graph|action|mermaid` still works (zero-dep, own tests). ✅
- **Delete planwright** → the runner still executes its own YAML plans (`plan_schema.py`). ✅
- **No `from plan_runner import …` inside the published planwright package** (it has zero deps). ✅

The boundary is clean **because** the two are not yet wired together. That is the
honest state: composition is *viable*, not yet *demonstrated end-to-end*.

## What to develop / integrate / leave

- **Develop (small, highest-leverage): the contract.** A stable planwright **plan
  export (JSON)** + a documented **importer/mapping in plan_runner** (planwright
  item → runner step; `Autonomy`→intent, `Complexity`→`model_tier` signal). This
  is the single missing piece that turns "two good tools" into the composition.
- **Integrate (no new code in planwright): executor selection reads the plan's
  metadata.** `model_tiers.py`/`router.py` consume `Complexity`/`Autonomy` from
  the imported plan. Routing/budget stay in the runner.
- **Leave as-is:** governed execution, HITL, budget, tools, events, validation —
  all proven in plan_runner. **Never duplicate** them in planwright.
- **Defer:** autonomous research/discovery loop (crit 1), automated structural
  planning (crit 2 — the meta-agent/concierge job), learning loop (crit 8),
  interactive visualization (crit 4) — real gaps, but not the next move.

## Verdict

- planwright **earns** the planning/analysis/visualization/packaging cells
  (3, 4, 10-pkg) with code+tests.
- plan_runner **earns** execution/governance/validation (6, 7) and partially
  5, 8, 9.
- The recommendation is a **composition**, and the one thing blocking it from
  being *proven* (not just viable) is the **export/import contract** (crit 10).
  Build that next; then run the canonical scenario (Step 4 of the playbook) to
  prove the cycle end-to-end. Only after that do competitor comparisons earn
  their cost — and only in the cells still marked partial/absent.
