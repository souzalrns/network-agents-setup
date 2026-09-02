<!-- COPIA de agent-network-mcp/.claude/skills/ponytail/SKILL.md — 2026-09-02 — setup only -->
---
name: ponytail
description: Lightweight task runner patterns and sequential work queues for agent sessions. Use when organizing multi-step local work without a heavy orchestrator.
---

# Ponytail

Keep work queues short, explicit, and sequential.

## Principles

- One active critical path
- Clear done criteria per step
- Prefer small commits over large unfinished branches
- Surface blockers early

## Workflow

1. List steps as a short ordered checklist
2. Execute the first incomplete step fully
3. Mark done with evidence (command output, link, test)
4. Only then advance

## Anti-patterns

- Parallel half-finished threads without a merge plan
- Claiming done without verification
- Expanding scope mid-step without updating the checklist
