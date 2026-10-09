# Positioning — would I choose planwright?

The maestro's test for every autonomous project: *faced with the alternatives,
would I pick this one?* Here is the honest answer, not the marketing one.

## The problem it solves

Teams and agents jump from "idea" to "doing" and the work becomes a pile: no
estimates, no visible dependencies, so nobody can see what blocks what or what
could run in parallel. The usual "project-manager" agent makes this worse, not
better, because it is a **stateless prompt persona**: it produces a plan and
forgets it. There is no source of truth and no enforcement, so the pile returns.

## What planwright is

Three layers, each in the form that fits it — the opposite of a single persona:

| Layer | Form | Why this form |
|---|---|---|
| Source of truth | a Markdown file in git | durable, diffable, owned by the team, zero LLM cost |
| The schedule | a deterministic engine | ready / parallel / critical path are **facts**, checkable, not a model's guess |
| The method | a skill (five gates + one rule) | the agent follows it consistently, loaded on demand |
| Enforcement | a hook | the plan *cannot* silently rot into a cycle — the discipline no persona has |
| Entry points | slash commands | `/plan-status`, `/plan-new`, `/plan-triage` |

## Honest comparison

| | Stateless PM subagent (VoltAgent, contains-studio) | conductor | **planwright** |
|---|---|---|---|
| Source of truth | none (ephemeral) | files (`conductor/`) | files (one Markdown table) |
| Computes critical path / parallelism | no | no | **yes, deterministically** |
| Enforces discipline | no | no | **yes (hook blocks an unsound plan)** |
| Runtime dependencies | n/a | n/a | **zero** |
| Couples you to a workflow | — | opinionated (its own dir + TDD flow) | **minimal — one file you already own** |
| Reusable by any agent / CI / human | prompt only | Claude Code only | **CLI + library + plugin** |

## Would I choose it? — yes, with honest limits

**I would choose it** for one reason the others cannot match: it turns a plan
into **checkable facts and enforced discipline**, with **zero dependencies** and
**no lock-in** — a single Markdown file you keep anyway. For a solo maintainer or
a small team that is drowning in untracked work, that is exactly the leverage
point, and it is the lightest thing that delivers it.

**Where I would not oversell it (Phase 1 scope):**

- It is **single-file, single-plan** per invocation. Cross-plan portfolios and
  roll-ups are Phase 2.
- Estimates are **effort**, not a calendar. It computes the critical path in
  work-hours; it does not place items on dates or model people's availability,
  holidays, or part-time allocation. That is deliberate — a dated Gantt is a
  heavier tool and a different promise.
- It does not assign owners or balance load; it tells you what is *assignable*,
  a human decides who.
- The hook enforces a **sound schedule** (no cycles/dangling); the fuller
  discipline (every started item estimated) is opt-in via `--strict`, so it
  never blocks a team that is not ready for it.

**When another tool is the right call:** if you need dated timelines, resource
leveling, or stakeholder/budget tracking across many projects, reach for a real
PM suite — planwright is a sharp instrument, not a suite, and it is honest about
that. If you only ever have a five-item list, you do not need it at all.

## Honest status & boundary (what this is / isn't)

To keep the claims accurate (and after an external audit of v0.2):

| Capability | State |
|---|---|
| Deterministic planning (ready / parallel / critical path / cycles) | **done** |
| Static visualization (Mermaid graph + Kanban) + initial prioritization (`action`) | **done (v0.2)** |
| Transitive-impact ranking in `action` | **done (v0.2)** |
| Interactive dashboard (drag, live recompute) | **not** — out of scope |
| Governed autonomous execution (approvals, tools, permissions) | **not here — belongs to an execution runner** |
| Dynamic model/cost routing | **not** — metadata is prepared (`Complexity`/`Autonomy`), the router is not built |

**The boundary.** planwright **describes and prioritizes** a plan; it does not
execute it. `Autonomy` (`auto`/`assisted`/`human`) and `Complexity` (`C1..C4`)
are **planning intent and routing signals**, not runtime policy. The actual
authority — who may run what, human approval gates, tool permissions, token
budgets, real cost — lives in whatever **execution runner** drives the work, and
that stays the source of truth at runtime. A visual board must never imply an
agent is authorized to do something the runner would refuse. planwright exports
the metadata; it does not enforce it.

## The bar for Phase 2 (`PLANWRIGHT-2`) — integrate, don't rebuild

Phase 2 adds dated, resource-aware scheduling. The rule: **integrate mature
engines behind optional extras; never pull them into the core.** `pip install
planwright` stays zero-dependency (plan-as-data + critical path on effort);
`pip install planwright[schedule]` unlocks the heavy parts. This is the same DNA
as auditron, which orchestrates existing engines instead of reimplementing them.

The layer breaks into four pieces with different build-vs-integrate answers:

| Piece | What it adds | Decision |
|---|---|---|
| Dates from effort + working calendar | real start/end dates skipping weekends/holidays | **integrate** a calendar lib (e.g. `workalendar`) + a thin layer |
| Resource-constrained scheduling / leveling (RCPSP) | "only N people — who does what, when, no overload" | **integrate** a solver — Google OR-Tools CP-SAT (Apache-2.0) via PyJobShop; never rebuild |
| Gantt / timeline rendering | a visual schedule | **integrate** Mermaid `gantt` (zero-dep, renders in Markdown/GitHub) |
| Portfolio roll-up across plans | merge N plans, namespace ids | **build** — thin connective code, and the governance differentiator |

The integration work that remains is small but real, and is the whole of Phase 2:
extend the plan schema to carry per-resource availability and calendars, map the
plan to and from the engine, and keep every engine an **optional extra** so the
core stays light and portable. An alternative adapter is to shell out to
TaskJuggler (GPLv2) at arm's length — the way auditron invokes its engines —
for a full dated+levelled schedule from a text plan; kept as an *additional*
adapter, not the only one, so the GPL stays contained and no runtime is forced.

Also in Phase 2: an MCP wrapper so any agent (not just Claude Code) can call
`graph`/`next` as tools, and extraction to its own repo + PyPI/marketplace
publish. None of it is needed for the Phase-1 promise above to stand today.
