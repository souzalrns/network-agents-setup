# Plug-in Agents

> How `plan_runner` fits into a multi-tenant, multi-horizontal agent platform.

**Status:** vision document
**Scope:** architectural context, not implementation
**Last updated:** 2026-09-10

---

## Context

Most AI agent frameworks optimise for autonomy: give the agent a goal, let it decide what to do. That works for demos and prototypes. It breaks in two places when the work becomes real:

1. **Governance.** Who approved this? What exactly did the agent do? Can we audit it six months from now? Most frameworks don't answer this.
2. **Reuse.** Every new client or project reinvents the same capabilities (SEO, copy, review, extraction). Nothing accumulates.

`plan_runner` exists to address both. It executes declarative plans (YAML) with human gates and full auditability, and it treats capabilities as reusable assets rather than one-off scripts.

This document describes where `plan_runner` sits in the bigger picture, and how the parts around it are meant to compose.

---

## The three layers

A plug-in agent platform has three distinct layers. Each has a different owner, a different lifecycle, and a different relationship to the code.

```
+------------------------------------------+
|  1. ORCHESTRATION                        |
|     plan_runner                          |
|     - runs plans                         |
|     - enforces gates                     |
|     - writes audit trail                 |
|     - this repo (public)                 |
+------------------------------------------+
                    |
                    v
+------------------------------------------+
|  2. AGENTS  (per client / per project)   |
|     - plug-in per client                 |
|     - own context, rules, memory         |
|     - e.g. ViannaLegal, MesaFlow         |
|     - each one lives in its own repo     |
+------------------------------------------+
                    |
                    v
+------------------------------------------+
|  3. HORIZONTALS  (shared capabilities)   |
|     - marketing, SEO, social, legal,     |
|       code review, data quality, ...     |
|     - one implementation, used by many   |
|     - lives here (public)                |
+------------------------------------------+
```

### Layer 1 - Orchestration

`plan_runner` is the execution engine. It knows nothing about clients or domains. It reads a plan, respects dependencies, pauses at human gates, writes events, and can resume from a crash.

It is deliberately domain-agnostic. Any plan, from any layer, can be executed by it.

### Layer 2 - Agents (plug-in)

A plug-in agent is the opposite: it is **domain-specific and client-specific**. It knows the client's brand, tone, constraints, and history.

A plug-in agent is not a separate program. It is a **combination of three things**:

- a set of plans (YAML)
- a set of memory namespaces (LightRAG + Cognee, optional)
- a set of allowed horizontals

Because it is only a combination - not a fork of the engine - a new client can be onboarded by creating a directory of plans and a memory namespace. No new code.

### Layer 3 - Horizontals

Horizontals are capabilities that any client can use: SEO briefs, social copy, code review, extraction, review rounds, etc.

They live **once** in this repo. When a plug-in agent calls `seo_brief`, it is not invoking a copy that belongs to the client. It is invoking the shared implementation, with the client's context passed as input.

This is what makes reuse real: one improvement to `seo_brief` benefits every client that uses it.

---

## How a plug-in agent works

Concrete example: **ViannaLegal wants a new SEO article on Portuguese citizenship for grandchildren.**

1. A human writes a plan, or reuses a template from `docs/orchestration/marketing/templates/`. The plan is stored **inside the ViannaLegal plug-in** (its own repo, not this one).

2. The ViannaLegal plug-in invokes:

```
plan_runner run viannalegal/plans/seo-article.plan.yaml \
    --engine langgraph --out runs/2026-09-10
```

3. The plan refers to **horizontals**, not to copies:

- `seo_brief` resolves to `skills/marketing/seo_brief/` (in this repo)
- `copy_answer_first` resolves to `skills/marketing/copy/`
- `critic_item13` resolves to `skills/marketing/critic_item13/`

4. Every step that has a `human_gate` pauses the run and waits for approval:

```
state: paused_human_gate
paused_at_step: hitl_publish_decision
```

5. A human reviews the artifacts, approves, and the run completes:

```
state: done
completed: [research, seo_brief, copy, critic, hitl_publish_decision]
```

6. The whole execution is auditable: `status.json`, `events.jsonl`, and `checkpoints.db` are written to disk. If the process dies mid-run, `resume` picks up from the last checkpoint.

7. Optionally, before and after each step, the runner consults the client's memory (see next section) and writes back what was learned.

The ViannaLegal plug-in contains **only** what is specific to ViannaLegal: plans, prompts, rules, knowledge references. The engine and the horizontals are not forked.

---

## Memory as a plug-in

Memory is **optional**. A `plan_runner` run with no memory enabled works exactly as it does today. This is deliberate: memory is a capability, not a requirement.

When memory is enabled, there are two distinct kinds. They answer different questions, and neither replaces the other.

### LightRAG - "what we know"

**LightRAG** builds a graph-based knowledge index from documents. It answers questions like:

- What do we already know about Portuguese citizenship for grandchildren?
- Which prior briefs touched this topic?
- What are the common pitfalls around this vertical?

It is loaded with the **corpus** - the accumulated documents of the plug-in agent. Each plug-in agent has its own LightRAG namespace. Two clients never share one.

### Cognee - "what we did"

**Cognee** stores episodic memory: past decisions, outcomes, what worked and what failed. It answers questions like:

- Did this brief approach succeed last time?
- What feedback did the human give on the last three reviews?
- Which patterns keep appearing in failures?

It is written to at the end of each step, so the plug-in agent gets smarter over time.

### How they are wired in

Both are opt-in, both are per-client, and both are invoked through the same small surface:

- `--client-id` isolates the memory namespace. Two clients cannot see each other's data.
- `--memory` selects which backends to enable. If omitted, no memory is used.

Under the hood, the runner calls small adapters that delegate to the respective Python libraries. If a library is missing or fails, the run continues without memory. Memory is never a hard dependency.

**Implementation status:** not yet integrated. See [`memory-integration.md`](./memory-integration.md) for the technical contract, and `docs/initiatives/backlog.md` for tracking (`INIT-010`, `INIT-011`, `INIT-012`).

---

## Public vs private

One of the reasons to keep orchestration and agents separate is licensing and confidentiality. Here is the split, by design:

| Component | Where it lives | Public? |
|---|---|---|
| `plan_runner` (engine) | this repo | Yes |
| Horizontals (skills, templates) | this repo | Yes |
| Generic plans (ship-parallel, seo-article, etc.) | this repo | Yes |
| Documentation, examples | this repo | Yes |
| Plug-in agents (per client) | client's own repo | No |
| Client-specific knowledge | client's own repo + their own LightRAG namespace | No |
| Client-specific memory | client's own Cognee namespace | No |
| Client names, brands, plans | client's own repo | No |

The rule of thumb:

- **If it is useful to more than one client** -> belongs here (horizontal).
- **If it names a specific client** -> belongs in that client's repo (plug-in).

If in doubt, it belongs in the client's repo. Moving something from private to public is easy; removing it after it has leaked is not.

---

## Current status

**Done (in this repo):**

- `plan_runner` engine (native + langgraph)
- Human-in-the-loop (approve / reject / edit)
- Crash recovery (3 scenarios tested)
- External workers (`--mode external`)
- 6 real plans validated end-to-end
- 72 tests, ~83% coverage
- CI: lint (ruff) + tests + coverage (Codecov)
- Release workflow (tag -> GitHub Release)
- This vision document

**Planned (see `docs/initiatives/backlog.md` for tracking):**

- `--client-id` and `--memory` flags on the CLI (`INIT-012`)
- LightRAG integration (`INIT-010`)
- Cognee integration (`INIT-011`)
- Log with 5 metrics per demand (`INIT-004`)
- Fast-path vs full-cycle decision rule (`INIT-003`)
- Capability catalog with 8 fields (`INIT-005`)

**Explicitly parked:**

- The "PCU Constitution" and related formalisms (`INIT-100`)
- META Compiler / MCL DSL (`INIT-101`)
- AR-000 through AR-015 (`INIT-102`)

---

## What this document is not

This is not a specification. It is a **context document** to explain why the pieces are arranged the way they are, and where the next pieces belong.

For the engine internals, see `docs/architecture/langgraph-lab/README.md`.
For the plan format and templates, see `docs/orchestration/marketing/templates/`.
For the backlog and what is being built next, see `docs/initiatives/backlog.md`.

---

## Em português

**Plug-in agents** descrevem como o `plan_runner` encaixa numa plataforma com três camadas:

1. **Orquestração** — o motor (este repo), corre planos, aplica gates, grava auditoria.
2. **Agentes plug-in** — específicos por cliente, vivem no repo do cliente, contêm apenas planos + memória + regras.
3. **Horizontais** — capacidades partilhadas (marketing, SEO, revisão), vivem uma vez, beneficiam todos.

**Memória é opcional.** LightRAG responde a "o que sabemos"; Cognee responde a "o que fizemos". Ambos isolados por `--client-id`. Nenhum é dependência obrigatória — o motor funciona sem memória.

**Público vs privado**: motor e horizontais são públicos; agentes plug-in e dados de cliente são privados por desenho.