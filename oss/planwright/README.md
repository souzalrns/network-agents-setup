# planwright

**A maker of plans.** Keep your plan as a plain Markdown table; planwright tells
you the three things a project manager actually needs to know:

- **what is ready to start now,**
- **what can run in parallel,**
- **what the critical path is** (the floor on how long the remaining work can take).

The plan is **data** — a Markdown file in git. The engine is **deterministic**
and has **zero runtime dependencies**. And a **Claude Code hook** keeps the plan
honest: it refuses to let the plan drift into a cycle or a dangling dependency.

Use it as a Python CLI, as a library, or as a Claude Code plugin (slash
commands + a planning skill + the hook). It is built to plug into any project or
agent and get out of the way.

---

## Why it exists

Most "project-manager" agents are a prompt persona: they write a nice plan and
then forget everything — no source of truth, no enforcement, so the work drifts
back into a pile. planwright inverts that. The plan lives in a file you own, the
schedule is computed from facts (not guessed by a model), and the discipline is
enforced by a hook rather than good intentions. See [POSITIONING.md](POSITIONING.md).

## Install

```bash
pip install planwright          # the CLI + library
```

Or use it straight from a checkout with no install:

```bash
PYTHONPATH=src python3 -m planwright.cli graph PLAN.md
```

## The plan file

A plain GitHub-flavoured Markdown table. `ID` and `Title` are the only required
columns; the rest are optional. Headers are case-insensitive and accept aliases
(including Portuguese), so planwright reads a plan written in your own words.

```markdown
| ID | Title                      | Status | Owner | Est  | Depends | Track |
|----|----------------------------|--------|-------|------|---------|-------|
| A1 | Design the data model      | done   | ana   | 1d   | -       | core  |
| A2 | Build the parser           | doing  | ana   | 2d   | A1      | core  |
| A3 | Build the dependency graph | todo   | luis  | 2d   | A1      | core  |
| A4 | Wire the CLI               | todo   | ana   | 1d   | A2, A3  | core  |
| B1 | Write the README           | todo   | bea   | 0.5d | -       | docs  |
```

- **Status**: `todo · doing · blocked · done` (aliases: `open`/`aberto`, `wip`/`em curso`, `bloqueado`, `fechado`, …).
- **Est**: a size `S/M/L/XL`, or a duration `2h` / `3d` / `1w`; `-` = not sized yet.
- **Depends**: ids this item waits on (comma/space separated); `-` = none.
- **Track**: any label to group items (a feature, a workstream, a phase).

The table can live inside a larger document — planwright reads the first table
that has `ID` and `Title` and ignores everything else.

## Commands

```bash
planwright graph    PLAN.md          # ready now · parallel layers · blocked · critical path
planwright action   PLAN.md          # a manager's action plan: ranked ready, who-unblocks-what, critical
planwright mermaid  PLAN.md          # Mermaid diagrams (deps + Kanban board) — render in GitHub/Markdown
planwright next     PLAN.md          # just the ids ready to start now (one per line)
planwright validate PLAN.md [--strict]  # check the plan is sound (and disciplined)
planwright status   PLAN.md          # one-line status counts
```

`graph`/`next`/`status` take `--json`; `mermaid` takes `--view deps|board|all`.
The path defaults to `PLAN.md` (override with `$PLANWRIGHT_PLAN`).

### See it, don't read it

`planwright mermaid` emits ```mermaid``` blocks that render natively on GitHub,
so a manager sees the dependency graph (coloured by status) and a Kanban board
without reading the CLI. `planwright action` ranks what to start now by leverage:
human decisions that unblock others first, then the critical path, then the rest.

### Optional columns (for routing)

Two optional columns feed autonomy/complexity-aware routing; absent, they are
ignored:

- **Autonomy** — `auto` (an agent can close it) · `assisted` · `human` (needs a person).
- **Complexity** — `C1`..`C4` (cognitive risk, for cheap→expensive model routing),
  **independent** of `Est` (effort). A task can be `Est=S` and `C4`.

Example:

```text
$ planwright graph PLAN.md
plan: 5 items  (todo 3, doing 1, blocked 0, done 1)

READY NOW (3): start these today
  A2  Build the parser  (2d @ana)
  A3  Build the dependency graph  (2d @luis)
  B1  Write the README  (4h @bea)

PARALLEL LAYERS (2): each layer can run at once
  L0: A2, A3, B1
  L1: A4

CRITICAL PATH: 4d — A1 -> A2 -> A4
  (the floor on remaining time; shortening the plan means shortening this)
```

## As a Claude Code plugin

planwright is also a plugin. Load it straight from a checkout:

```bash
claude --plugin-dir oss/planwright          # from the monorepo root
# or, once published as its own repo / marketplace:
# /plugin install planwright --marketplace <owner>/<repo>
```

You then get:

- **`/planwright:plan-status`** — the schedule, summarised.
- **`/planwright:plan-new`** — start a plan or add an item through the method.
- **`/planwright:plan-triage`** — sort a crowded backlog into real vs. resolvable vs. stale.
- the **`governed-planning` skill** — the five-gate method (idea → research →
  spec → WBS → execute) and the one rule (nothing starts without an estimate and
  explicit dependencies).
- a **`PostToolUse` hook** — after any edit to a plan file (`PLAN.md` or
  `*.plan.md`), it validates and **blocks on an unsound schedule** so the plan
  never silently rots. Set `PLANWRIGHT_STRICT=1` to also block on governance
  warnings.

## Validation rules

**Errors** (not a sound schedule — fix before trusting the graph): a parse
failure, a duplicate id, a dependency naming no item, a self-dependency, a
cycle.

**Warnings** (schedulable but undisciplined; `--strict` turns these into
failures): an item marked `doing`/`done` with no estimate; a `done` item that
still depends on unfinished work.

## Library

```python
from planwright.parse import parse_plan
from planwright.graph import Graph

plan = parse_plan("PLAN.md")
g = Graph(plan)
print([i.id for i in g.ready()])      # ready now
print(g.parallel_layers())            # [[...], [...]]
print(g.critical_path().hours)        # float (hours)
```

## License

MIT. No third-party runtime dependencies. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
