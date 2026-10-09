---
description: Show the plan's schedule — ready now, parallel layers, blocked, critical path.
argument-hint: "[path to PLAN.md]"
allowed-tools: ["Bash"]
---

Run the planwright engine against the plan and summarise it for the user.

1. Resolve the plan file: use `$1` if given, else `$PLANWRIGHT_PLAN`, else `PLAN.md` in the project root.
2. Run: `python3 "${CLAUDE_PLUGIN_ROOT}/src/../" ` is not needed — call the CLI module directly:
   `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m planwright.cli graph <plan-file>`
   (if the `planwright` package is installed on PATH, `planwright graph <plan-file>` also works).
3. Present, in this order: what is **ready now** (assign these today), the **parallel layers**, what is **blocked** and on what, and the **critical path** with its duration.
4. If the engine reports NOT SCHEDULABLE, lead with the cycle or dangling dependency — nothing else matters until it is fixed.

Do not invent items or estimates. Report only what the plan file contains.
