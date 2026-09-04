# Padrões portáveis — shortlist de orquestradores (2026)

**Regra:** não substituir `agent-network-mcp` nem o setup por um framework. Extrair padrões; runtime canónico continua contratos (Plan-Execute) + MCP produção.

Shortlist: LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AutoGen/AG2, Haystack.
Infra: Temporal / Hatchet / Inngest / Trigger.dev.

---

## LangGraph (prioridade)

A tabela resumida era insuficiente. **Detalhe:** [`langgraph-deep.md`](./langgraph-deep.md)

Padrões-chave: **reducers**, checkpoint por nó, thread_id, interrupt com approve/edit/reject, **time-travel (replay/fork)**, **Send** map-reduce, **Command**, subgraphs + namespace isolation, durability, streaming.

---

## Mapa rápido: o que roubar de cada um

| Projecto | Melhor padrão a roubar | NÃO adoptar como core |
|----------|------------------------|------------------------|
| **LangGraph** | Ver langgraph-deep.md | Stack LangChain inteiro |
| **Agno** | Agent vs Team vs Workflow; MCP expose | Substituir MCP prod |
| **Timbal** | suspend / requires_approval + resume | Única base jovem |
| **CrewAI** | Roles + process | SO de agentes |
| **PydanticAI** | Output tipado | Runtime se não for Python |
| **Mastra** | Workflows TS | Forçar TS |
| **AG2** | Debate patterns | Base nova (maintenance lineage) |
| **Haystack** | RAG pipeline | Orquestração global |

---

## Padrões unificados (IDs)

| ID | Padrão | Origem | Fase |
|----|--------|--------|------|
| O01 | Agent vs Team vs Workflow | Agno | 1 |
| O02 | Grafo / edges | LangGraph | 1 |
| O03 | Checkpoint + resume | LangGraph | 2–3 |
| O04 | interrupt / suspend HITL | LangGraph, Timbal | 1–3 |
| O05 | Approve / reject / **edit** | LangGraph | 2 |
| O06 | Role-based crew | CrewAI | 1 |
| O07 | Structured output | PydanticAI | 1 |
| O08 | Handoff via orchestrator | SDKs | 2 |
| O09 | Component as MCP tool | Agno | 2–3 |
| O10 | Guardrails / budget | Vários | 1 |
| O11 | RAG pipeline nodes | Haystack | vertical |
| O12 | Observability run/token | Agno / LG-style | 2 |
| O13 | Infra durável separada | Temporal et al. | 3 |
| **O14** | **State reducers (append vs overwrite)** | **LangGraph** | **1–2** |
| **O15** | **Send / foreach map-reduce** | **LangGraph** | **2** |
| **O16** | **Time-travel fork (não apagar timeline)** | **LangGraph** | **2** |
| **O17** | **Subgraph namespace isolation** | **LangGraph** | **2–3** |
| **O18** | **Command = state_patch + next** | **LangGraph** | **2** |

Ver também: [`unified-patterns.md`](./unified-patterns.md) · [`when-to-use-what.md`](./when-to-use-what.md) · [`langgraph-deep.md`](./langgraph-deep.md)
