<!-- COPIA de agent-network-mcp/.claude/skills/find-skills/SKILL.md — 2026-09-02 — setup only -->
---
name: find-skills
description: Discover and recommend relevant agent skills for the current task. Use when unsure which skill applies or when onboarding to a skill library.
---

# Find Skills

Help the user or agent locate the right skill for a task.

## Workflow

1. Clarify the goal (debug, implement, review, ship, document, design, test).
2. Match against available skills by name and description.
3. Recommend 1–3 skills with why each fits.
4. If none fit, say so and suggest writing a minimal skill or using a general workflow.

## Output

- Skill name + path
- When to use
- What it does not cover
