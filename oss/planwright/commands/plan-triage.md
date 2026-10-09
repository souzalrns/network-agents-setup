---
description: Triage a backlog or a pile of blocked items into real vs. resolvable vs. tidy-up.
argument-hint: "[path to PLAN.md]"
allowed-tools: ["Bash", "Read"]
---

Help the user make sense of a crowded or stuck plan.

1. Run `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m planwright.cli graph <plan-file> --json` and read the `blocked` map and `critical_path`.
2. For each blocked item, classify the blocker using the plan's own `Depends` and the item's text:
   - **real** — waits on another item in this plan (name it);
   - **external** — waits on something outside the plan (a person, infra, a decision): propose capturing it as its own item so the dependency becomes explicit;
   - **stale** — no longer makes sense: propose marking it done or removing it (never silently; put the proposal to the user).
3. Surface the **top items on the critical path** — these are where effort shortens the whole plan.
4. End with a short A/B/C of what to do next, each option with a one-line reason and a recommendation.

Classify from evidence in the plan; do not guess blockers that are not written down.
