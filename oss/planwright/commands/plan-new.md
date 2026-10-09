---
description: Start a new plan, or add a work item to an existing one, through the five-gate method.
argument-hint: "[idea or item title]"
allowed-tools: ["Bash", "Read", "Edit", "Write"]
---

Use the **governed-planning** skill to turn `$ARGUMENTS` into a well-formed plan item.

1. If no plan file exists yet, create `PLAN.md` from the template in the skill (the header row with ID, Title, Status, Owner, Est, Depends, Track).
2. Walk the five gates with the user for this idea: Idea → Research (A/B/C + a recommendation) → Spec (done-when) → break into items → add rows with **estimate** and **explicit `Depends` ids**.
3. Never add an item in status `doing`/`done` without an estimate, and never invent a dependency — ask if unsure.
4. After editing, run `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m planwright.cli validate <plan-file>` and fix anything it flags before finishing.

The plan file is the single source of truth. Keep it the only place work state lives.
