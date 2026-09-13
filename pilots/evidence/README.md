# Evidence — ITEM13-MARKETING-ROADMAP A4/A5/A6

Snapshots of local runs proving A4, A5 and A6. The full run directories
live under `pilots/run-*` and are gitignored; this folder is the
committed, minimal proof.

## A5-A6-seo-stub-2026-09-07

Proves:
- A5: dry-run on `seo-article.plan.yaml` (step order correct).
- A6: stub mode + HITL pause + `resume --decision approve`.

Files:
- `status.json` — final state `done`, `paused_at_step: hitl_publish_decision`.
- `HITL.md` — the HITL decision file produced during the pause.

Reproduce:
    python -m runner.plan_runner stub --plan pilots/run-seo-stub/plan.yaml --out pilots/run-seo-stub
    python -m runner.plan_runner resume --run pilots/run-seo-stub --decision approve

## A4-seo-external-2026-09-08

Proves A4: external mode with HITL resume.

Files:
- `status.json` — from `run-seo-demo` (plan `example-seo-article-demo`).
- `status-external.json` — from `run-seo-external` (plan `template-seo-article`).

Both show `state: done`, `mode: external`.