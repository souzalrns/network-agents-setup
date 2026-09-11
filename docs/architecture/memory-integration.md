# Memory Integration

> How LightRAG and Cognee will plug into `plan_runner`.
>
> **Status:** design note. Not implemented.
> This document defines the contract, not the code.
>
> **Last updated:** 2026-09-11

---

## Why two memories

A plug-in agent needs to answer two very different questions about its own past:

1. **"What do we know about this?"** — the accumulated corpus of a client: documents, briefs, prior work, domain knowledge. This is **semantic memory**.
2. **"What have we done about this?"** — the history of decisions, outcomes, what worked, what failed. This is **episodic memory**.

These are not the same thing, and one does not replace the other. A single vector store can answer neither well. This document describes how `plan_runner` will support both, as **optional, per-client capabilities**.

Neither is required for `plan_runner` to work. The engine runs today with zero memory. Memory is a layer that a plug-in agent opts into when the value justifies the cost.

---

## LightRAG — "what we know"

**LightRAG** builds a graph-based knowledge index from a corpus of documents.

It extracts entities and relationships, and answers queries by traversing the graph. This is different from a plain vector store: it can answer questions that no single document contains, because it reasons over connections between documents.

### What it gives a plug-in agent

- "What do we already know about Portuguese citizenship for grandchildren?"
- "Which prior briefs touched this topic?"
- "What are the common pitfalls around this vertical?"

### How it is scoped

Each plug-in agent gets its **own LightRAG namespace**. Two clients never share one. This is a hard rule: knowledge from one client must never leak into another's answers.

### How it is queried

The recommended integration is through LightRAG's HTTP API:

    POST /query/data

This endpoint returns entities, relationships and source chunks **without** calling an LLM for generation. The caller (a step in the plan) decides what to do with the result.

A small `knowledge_search(query)` tool wraps this call. The tool is registered on the agent, and the agent calls it when a step needs context.

### What it is not

- Not a chatbot.
- Not a replacement for reading the source documents.
- Not shared between clients.

---

## Cognee — "what we did"

**Cognee** stores episodic memory: past decisions, outcomes, what worked and what failed.

It is the memory of *action*, not of *knowledge*. Where LightRAG answers "what do we know", Cognee answers "what have we done and what did we learn".

### What it gives a plug-in agent

- "Did this brief approach succeed last time?"
- "What feedback did the human give on the last three reviews?"
- "Which patterns keep appearing in failures?"

### How it is scoped

Each plug-in agent gets its **own Cognee namespace**. The isolation is enforced by the integration layer.

### How it is queried

Cognee has an official LangGraph integration package:

    pip install cognee-integration-langgraph

The integration exposes two tools:

    from cognee_integration_langgraph import get_sessionized_cognee_tools

    add_tool, search_tool = get_sessionized_cognee_tools("viannalegal")

- `add_tool` — writes a new episode to the session
- `search_tool` — queries past episodes

The `session_id` argument is the client id. This is what makes the isolation work: two clients never see each other's data.

### What it is not

- Not a knowledge base.
- Not a log of raw events (that is `events.jsonl`).
- Not shared between clients.

---

## The contract

`plan_runner` will expose two new flags on the CLI:

    plan_runner run <plan.yaml> --client-id <id> --memory <backends>

### `--client-id`

- **Required** when `--memory` is set.
- Identifies the plug-in agent (e.g. `viannalegal`).
- Used to scope both LightRAG and Cognee namespaces.
- Two runs with the same `--client-id` share memory. Two runs with different ids never do.

### `--memory`

- **Optional.** Default: no memory.
- Comma-separated list: `lightrag`, `cognee`, or `lightrag,cognee`.
- If a backend is requested but not available (missing library, no LLM key, network error), the run **continues without it** — memory is never a hard dependency.

### Example

    # No memory (today's behaviour)
    plan_runner run viannalegal/plans/seo-article.plan.yaml --out runs/2026-09-11

    # With both memory backends
    plan_runner run viannalegal/plans/seo-article.plan.yaml \
        --client-id viannalegal \
        --memory lightrag,cognee \
        --out runs/2026-09-11

The plan itself does not change. Memory is a property of the *run*, not of the plan.

---

## How it wires into the engine

Design (not yet implemented):

1. **New module:** `runner/plan_runner/memory.py`
   - Defines a `MemoryBackend` protocol with two methods: `get_context(query)` and `save_outcome(data)`.
   - Provides three implementations: `NullMemory` (no-op), `LightRAGMemory`, `CogneeMemory`.
   - Selection is driven by the `--memory` flag.

2. **New CLI flags:** `--client-id` and `--memory`
   - Parsed in `cli.py`.
   - Passed to the engine.

3. **Engine hook:** before and after each step
   - Before: if memory is enabled, call `get_context(step)` and inject the result into the step's inputs.
   - After: if memory is enabled and the step produced an outcome, call `save_outcome(outcome)`.

4. **No changes to the plan format.**
   - The plan stays as it is today.
   - No new fields, no new syntax, no YAML changes.

5. **No changes to the engine's core.**
   - The engine stays domain-agnostic.
   - Memory is a layer that wraps step execution.

This is the same design philosophy as `--mode external`: the plan does not know how a step gets executed. It just declares the step. The engine handles the rest.

---

## Prerequisites

Before any of this can be implemented:

- **An LLM provider.** Both LightRAG and Cognee need an LLM to:
  - extract entities and relationships (LightRAG indexing),
  - summarise and retrieve episodes (Cognee).

  The project currently uses **DeepSeek**, but top-ups on their platform are blocked. Alternatives: OpenRouter, Ollama Cloud, or Anthropic/OpenAI API keys.

- **A storage backend for LightRAG.** Options: filesystem (for testing), PostgreSQL + pgvector (recommended for production), or Neo4j for graph-native use.

- **A storage backend for Cognee.** Its defaults are local files + SQLite. For production, a proper vector store and relational database are recommended.

None of these are blockers for the *design* — they are blockers for the *implementation*.

---

## What changes in code, and what does not

| Component | Changes? |
|---|---|
| `plan_runner/cli.py` | +2 flags |
| `plan_runner/memory.py` (new) | full module |
| `plan_runner/engine.py` | 2 hook calls |
| `plan_runner/langgraph_engine.py` | 2 hook calls |
| Plan format (YAML) | no change |
| Existing plans | no change |
| Existing tests | no change |
| CI | no change (memory tests are mocked) |

The engine stays the same. The plans stay the same. Memory is additive.

---

## Status

**Not implemented.** Tracked in `docs/initiatives/backlog.md`:

- `INIT-010` — LightRAG integration (research)
- `INIT-011` — Cognee integration (research)
- `INIT-012` — `--client-id` and `--memory` flags (candidate)

This document defines the contract so that, when the prerequisites are met, the implementation can start without a design phase.

---

## What this document is not

It is not a specification. It is a **design note** — enough to guide implementation, not enough to be one.

For the bigger picture (three layers, public vs private), see `docs/architecture/plug-in-agents.md`.
For the engine internals, see `docs/architecture/langgraph-lab/README.md`.
For the plan format, see `docs/orchestration/marketing/templates/`.

---

## Em português

**Documento de desenho.** Descreve como o `plan_runner` vai suportar duas memórias opcionais:

- **LightRAG** — "o que sabemos". Índice de conhecimento em grafo, por cliente. Responde a perguntas sobre o corpus acumulado.
- **Cognee** — "o que fizemos". Memória episódica, por cliente. Responde a perguntas sobre decisões passadas e resultados.

**Contrato:** `--client-id` (identifica o plug-in agent) + `--memory` (escolhe backends). Memória é sempre opcional — o motor funciona sem ela.

**Estado:** não implementado. Requer um provider LLM (DeepSeek está bloqueado, alternativas: OpenRouter, Ollama Cloud). Registado no backlog como `INIT-010`, `INIT-011`, `INIT-012`.

**Não muda:** formato dos planos, código do motor, testes existentes. **Muda:** 1 módulo novo (`memory.py`), 2 flags no CLI, 2 chamadas de hook no engine.