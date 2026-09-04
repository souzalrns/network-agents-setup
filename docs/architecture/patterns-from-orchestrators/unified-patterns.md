# Padrões unificados (detalhe)

## O01 — Agent vs Team vs Workflow (Agno)

| Abstração | Quando | Mapa nosso |
|-----------|--------|------------|
| **Agent** | Um domínio, poucas tools | Um `action` / skill |
| **Team** | Especialistas + líder dinâmico | Supervisor + workers |
| **Workflow** | Sequência fixa, auditável | `plan.yaml` pipeline |

Regra: não usar Team onde um Workflow basta (custo e não-determinismo).

## O02 — Grafo explícito (LangGraph)

- Nós = passos/agents; arestas = transições e condições.  
- Nosso equivalente: `depends_on` + `on_fail` + ordem do plan.  
- Vantagem mental: “sem aresta = não corre”.

## O03 — Checkpoint + resume

- Persistir estado do run após cada passo (ou superstep).  
- Crash ou HITL → retomar **do checkpoint**, não do zero.  
- Lab futuro: `events.jsonl` + snapshot de plan status (event sourcing).

## O04 / O05 — HITL durável

Timbal: `requires_approval` em tool/step; `suspend()`; resume com mapa de decisões.  
LangGraph: `interrupt` + checkpointer; decisões approve / reject / edit / respond.

Mapa nosso:

```text
human_gate: true no step
  → emitir evento human_gate_requested
  → não executar side-effect até human_gate_resolved
```

## O06 — Crew por papéis (CrewAI)

- Role + goal + backstory + tools limitados.  
- Process sequential vs hierarchical.  
- Nosso: roles no registry; process = pipeline ou supervisor no plan.

## O07 — Structured output (PydanticAI)

- Resultado do agente **valida schema** ou falha.  
- Já: SeoBrief, CopyAnswerFirst, CriticReport, Plan.schema.json.

## O08 — Handoff

- Agente A transfere autoridade/contexto a B sem peer mesh livre.  
- Preferir handoff **via orquestrador** (evento + novo step) para audit.

## O09 — Expor componente como MCP tool (Agno)

- Útil: `seo_pipeline.as_tool()` para um cliente MCP.  
- Risco: tool genérica demais = privilege sprawl.  
- Só com allowlist e description escrita para o *caller* model.

## O10 — Guardrails

- max steps, max tool calls, timeout, denylist tools.  
- Já no plan: `budget.max_steps`, `max_replans`.

## O11 — Haystack

- Usar padrões de **pipeline de documentos** (retrieve → rank → generate), não como orquestrador global da rede.

## O12 — Observabilidade

- Correr com `run_id`, tokens, tool latency, status.  
- Ligar a event log / dashboard existente — não obrigar LangSmith.

## O13 — Infra durável ≠ orquestrador cognitivo

| Camada cognitiva | Camada infra |
|------------------|--------------|
| Quem pensa, tools, HITL de decisão | Filas, retries, cron, exactly-once de jobs |
| Plan-Execute, LangGraph-style graph | Temporal, Hatchet, Inngest, Trigger.dev |

HITL de **negócio** pode usar interrupt no grafo; **retry de webhook** pertence à infra.
