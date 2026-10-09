---
description: Show the plan as a visual board + action plan (Mermaid graph, Kanban, ranked next moves).
argument-hint: "[path to PLAN.md]"
allowed-tools: ["Bash"]
---

Give the user a manager's view of the plan — visual, not CLI text.

1. Resolve the plan file: `$1` if given, else `$PLANWRIGHT_PLAN`, else `PLAN.md`.
2. Run both:
   - `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m planwright.cli mermaid <plan-file>`
   - `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m planwright.cli action <plan-file>`
   (or the installed `planwright mermaid`/`planwright action`).
3. Present the **Mermaid** blocks verbatim (so they render as the dependency graph
   and the Kanban board), then the **action plan** (what to start now, by leverage).
4. Lead with the single highest-leverage move and the critical chain.

Report only what the plan contains; do not invent items, estimates, or metadata.
