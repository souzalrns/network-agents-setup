# Extracção mestra — o que interessa (tudo visto)

Fontes: dsh/Cordis · Hermes · LangGraph · Agno · Timbal · CrewAI · PydanticAI · Mastra · AG2 · Haystack · event sourcing · Spec Kit.

**Princípio:** contratos e evidência no **setup**; MCP **produção** intacto; frameworks só como padrões ou lab isolado.

---

## A. Já temos / reforçar já (fase 1)

| # | Padrão | Origem | Onde no setup |
|---|--------|--------|----------------|
| 1 | Plan-Execute + depends_on + budget | LG / geral | plan-execute/ |
| 2 | Output schemas (SeoBrief, Copy, Critic, Plan) | PydanticAI | schemas/ |
| 3 | tools_allowed default-deny | dsh / Timbal policy | plan steps |
| 4 | human_gate | LG / Agno / Timbal | plan |
| 5 | Registry de actions | dsh / Agno | registry-actions |
| 6 | Skills SKILL.md | Hermes / Agno / Mastra | skills/ |
| 7 | setup ≠ produção | constitution | CONSTITUTION-DRAFT |
| 8 | Model-visible → evidência | dsh / event sourcing | pilots/ |
| 9 | Agent vs Team vs Workflow | Agno / Crew Flow+Crew | vocabulário |
| 10 | Memória em camadas | Hermes | memory-layers |
| 11 | Skill candidate + human promote | Hermes | skill-lifecycle |
| 12 | Role specialization | CrewAI | registry roles |

---

## B. Estender contratos (fase 1–2, só docs/schema)

| # | Padrão | Origem | Acção |
|---|--------|--------|--------|
| 13 | HITL kinds: confirm / user_input / output_review / external | Agno | human_gate expandido |
| 14 | HITL level: step vs executor | Agno | idem |
| 15 | approve / reject / **edit** | LangGraph | protocolo resume |
| 16 | requires_approval predicado + resume map | Timbal | policy tools |
| 17 | Reducers: append vs overwrite | LangGraph | artifacts[] / events[] |
| 18 | fork_of / time-travel meta | LangGraph | pilots |
| 19 | foreach / Send map-reduce | LangGraph | plan schema v2 |
| 20 | Workflow: condition, loop, router | Agno / Crew Flow / Mastra | plan schema v2 |
| 21 | Flow spine + Crew muscle | CrewAI | sub-plan num step |
| 22 | Tool description = prompt do *caller* | Agno MCP | se expuser MCP |
| 23 | thread_id / run_id / resource_id | LG / Mastra | naming runs |
| 24 | Prompt em camadas | dsh / Hermes | constitution + knowledge + step |

---

## C. Runtime lab (fase 3 — setup only)

| # | Padrão | Origem |
|---|--------|--------|
| 25 | Checkpoint por step + events.jsonl | LG + event sourcing |
| 26 | continue_run / cancel_run | Agno |
| 27 | Approvals como registo persistente | Agno |
| 28 | execute_verified_action (policy pipeline) | dsh + Timbal |
| 29 | Durability via Temporal/Hatchet se jobs longos | PydanticAI O13 |
| 30 | Streaming de step events para control plane | LG / Agno |
| 31 | Subgraph / namespace isolation | LangGraph |
| 32 | Optional: um de {LangGraph, Agno, Timbal} isolado | — |

---

## D. Explicitamente fora do core

| Item | Porquê |
|------|--------|
| Substituir agent-network-mcp por Agno/LangGraph/Hermes/dsh | Produção já operacional |
| Auto-merge de skills | Contaminação |
| Swarm AG2 peer-to-peer sem orquestrador | Sem audit trail |
| Gateway multi-canal como núcleo do framework | Ruído |
| Haystack como orquestrador global | É RAG/pipeline |
| Vendor Cordis kernel | Complexidade |

---

## E. Comparação rápida “cérebro”

| Necessidade | Melhor fonte de padrão |
|-------------|------------------------|
| Grafo + time-travel + reducers + Send | **LangGraph** |
| Agent/Team/Workflow + HITL negócio + MCP serve | **Agno** |
| HITL mínimo + core legível | **Timbal** |
| Roles + Flow/Crew híbrido | **CrewAI** |
| Schemas + durable *via* infra | **PydanticAI** |
| Stack TypeScript | **Mastra** |
| Learning loop skills | **Hermes** |
| Plugin/policy/log | **dsh/Cordis** |
| RAG pipeline | **Haystack** |
| Jobs/retries dias | **Temporal et al.** |

---

## F. Ordem de trabalho recomendada

1. Spec Kit constitution + specify (setup de agentes, não cliente)  
2. Incorporar B13–B16 no draft do plan schema (HITL rico)  
3. Reducers + fork_of na doc de pilots  
4. Runner lab mínimo (C25–C28) **sem** tocar MCP prod  
5. Só então experimentar **um** framework no lab  

---

## G. Índice de docs

| Doc | Conteúdo |
|-----|----------|
| `patterns-from-harness/` | dsh/Cordis |
| `patterns-from-hermes/` | memória, skills |
| `langgraph-deep.md` | LG profundo |
| `agno-deep.md` | Agno profundo |
| `remaining-deep.md` | Timbal…Haystack |
| `unified-patterns.md` | O01–O18 |
| `when-to-use-what.md` | decisão |
| **este ficheiro** | fecho da extracção |
