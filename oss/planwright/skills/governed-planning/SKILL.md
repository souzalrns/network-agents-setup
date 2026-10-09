---
name: governed-planning
description: Use when turning an idea, feature, or messy backlog into a tracked plan — breaking work into items with estimates and explicit dependencies so you can see what is ready, what runs in parallel, and the critical path. Use before starting non-trivial work, and whenever a plan has drifted into an untracked pile.
---

# Governed planning

A method that takes an idea to a plan you can actually manage. It exists because
agents (and people) skip from "idea" straight to "doing", and the work becomes a
pile with no order, no estimates, and no visible dependencies — so nobody can
see what blocks what or what could run in parallel. This method closes that gap
with five gates and one rule.

## The five gates

Work does not advance to the next gate until the current one is done.

1. **Idea** — one sentence: what and why. Nothing is built from a vague idea.
2. **Research** — a short findings note that ends in **A/B/C options with an
   explicit recommendation and a one-line reason**. If there is no
   recommendation, the decision is not ready.
3. **Spec** — what the result is and its **done-when** condition (how you will
   know it is finished). No spec, no build.
4. **Plan (WBS)** — break the spec into work items. Each item gets:
   an **id**, a **title**, a **status**, an **owner**, an **estimate**, and its
   **dependencies as explicit ids**. This is the gate that makes a schedule
   possible.
5. **Execute** — do the work; move items `todo → doing → done`. An item is only
   `done` when its done-when holds (for code: merged, not just written).

## The one rule

**Nothing is marked `doing` or `done` without an estimate, and no dependency is
implicit.** This is the whole discipline. An estimate forces you to size the
work; an explicit `Depends` id is what lets the engine compute the schedule.
The planwright hook enforces the sound-schedule half of this automatically
(it blocks a plan with a cycle, a dangling dependency, or a duplicate id), and
`planwright validate --strict` enforces the rest.

## The plan file

The plan is a plain Markdown table — the single source of truth, living in git.
Keep work state nowhere else. Minimum columns (aliases and Portuguese headers
are accepted; `ID` and `Title` are the only required ones):

```markdown
| ID | Title                        | Status  | Owner | Est | Depends | Track |
|----|------------------------------|---------|-------|-----|---------|-------|
| A1 | Design the data model        | done    | ana   | 1d  | -       | core  |
| A2 | Build the parser             | doing   | ana   | 2d  | A1      | core  |
| A3 | Build the dependency graph   | todo    | luis  | 2d  | A1      | core  |
| A4 | Wire the CLI                 | todo    | ana   | 1d  | A2, A3  | core  |
| B1 | Write the README             | todo    | bea   | 0.5d| -       | docs  |
```

- **Status**: `todo | doing | blocked | done` (aliases: open/aberto, wip/em curso, bloqueado, fechado…).
- **Est**: a size `S/M/L/XL`, or a duration `2h` / `3d` / `1w`; `-` means "not sized yet".
- **Depends**: ids this item waits on, comma- or space-separated; `-` for none.
- **Track**: a free label to group items (a feature, a workstream, a phase).

## Reading the schedule

Run the engine (installed `planwright …`, or `PYTHONPATH=<plugin>/src python3 -m planwright.cli …`):

- `planwright graph PLAN.md` — the full picture: **ready now**, **parallel
  layers**, **blocked** (and on what), and the **critical path** with its
  duration.
- `planwright next PLAN.md` — just the ids ready to start now (assign these).
- `planwright validate PLAN.md` — check the plan is sound; `--strict` also fails
  on the governance warnings.
- `planwright status PLAN.md` — one-line counts.

**How to use the output as a manager:**
- *Ready now* is today's assignment list.
- *Parallel layers* tell you what you can hand to different people at once.
- The *critical path* is the floor on how long the remaining work can take —
  adding people elsewhere will not shorten it; only shortening the path does.

## Do not

- Do not invent items, estimates, or dependencies. If you do not know, ask.
- Do not keep a second copy of work state outside the plan file.
- Do not cut an item silently; propose it (gate 2, A/B/C) and let the owner decide.
