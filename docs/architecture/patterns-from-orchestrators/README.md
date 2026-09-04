# Padrões portáveis — shortlist de orquestradores (2026)

**Regra:** não substituir `agent-network-mcp` nem o setup por um framework. Extrair padrões; runtime canónico continua contratos (Plan-Execute) + MCP produção.

Shortlist analisada: LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AutoGen/AG2, Haystack.
Camada **infra** (outra caixa): Temporal / Hatchet / Inngest / Trigger.dev.

---

## Mapa rápido: o que roubar de cada um

| Projecto | Melhor padrão a roubar | NÃO adoptar como core |
|----------|------------------------|------------------------|
| **LangGraph** | Grafo explícito, checkpoint, interrupt/HITL durável, branching | Todo o stack LangChain se não precisarem |
| **Agno** | Agent vs Team vs Workflow; AgentOS (serve + MCP); control plane | Substituir MCP prod por AgentOS cedo |
| **Timbal** | Uma interface Agent+Workflow+Tool; `requires_approval` / `suspend()` + resume | Framework ainda jovem como única base |
| **CrewAI** | Papéis + tasks + crew process; Flows determinísticos | Núcleo de “SO de agentes” |
| **PydanticAI** | Output tipado; durable execution adapters | Só se Python tipado for o runtime lab |
| **Mastra** | TS-native workflows/agents se stack for TS | Forçar TS se prod for outro |
| **AG2/AutoGen** | Debate / group chat patterns (pesquisa) | Novos projectos em maintenance lineage |
| **Haystack** | Pipelines RAG + agent nodes | Orquestração geral multi-domínio |

---

## Padrões unificados (IDs)

| ID | Padrão | Origem principal | Fase setup |
|----|--------|------------------|------------|
| O01 | **Agent vs Team vs Workflow** | Agno | 1 — já (worker vs pipeline vs supervisor) |
| O02 | **Grafo / edges explícitos** | LangGraph | 1 — plan steps + depends_on |
| O03 | **Checkpoint + resume** | LangGraph, Timbal, Pydantic durable | 2–3 runtime |
| O04 | **interrupt / suspend HITL** | LangGraph, Timbal, Agno | 1 conceptual; 3 runtime |
| O05 | **Approve / reject / edit** | LangGraph HITL | 2 |
| O06 | **Role-based crew** | CrewAI | 1 — roles em registry |
| O07 | **Structured output (schema)** | PydanticAI, nós | 1 — JSON Schema |
| O08 | **Handoff** | OpenAI SDK / Mastra | 2 |
| O09 | **Component as MCP tool** | Agno | 2–3 (cuidado com blast radius) |
| O10 | **Guardrails / max iterations** | Vários | 1 — budget no plan |
| O11 | **RAG pipeline nodes** | Haystack | Só vertical conhecimento |
| O12 | **Observability run/token** | Agno, LangSmith-style | 2 |
| O13 | **Infra durável separada** | Temporal et al. | 3 — não misturar com LLM loop |

Detalhe: [`unified-patterns.md`](./unified-patterns.md) · decisão: [`when-to-use-what.md`](./when-to-use-what.md)

---

## Relação com o que já temos

```text
Constitution + Plan-Execute + registry + policy + Hermes memory layers + dsh plugin/log
        │
        ├── O01/O02/O06/O07/O10  já cobertos ou quase
        ├── O03/O04/O05          próximo estágio runtime lab
        └── O13                  jobs/filas — fora do “cérebro” LLM
```

**Não** fazer: “migrar tudo para Agno/LangGraph” enquanto o valor está nos contratos e no MCP operacional.
