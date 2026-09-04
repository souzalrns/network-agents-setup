# Agno — revisão detalhada (padrões a roubar)

**O que é:** plataforma open-source (SDK + **AgentOS** runtime + Control Plane) para *build / run / manage* de agents, teams e workflows. Model-agnostic; forte em servir produção (FastAPI, sessões, MCP, HITL, RBAC).

**Regra:** estudar e extrair padrões. **Não** substituir `agent-network-mcp` por AgentOS sem decisão explícita. Setup continua contratos (Plan-Execute) + lab opcional.

---

## 1. Três camadas do produto

| Camada | Função |
|--------|--------|
| **SDK** | Definir Agent / Team / Workflow + memory, knowledge, guardrails, tools |
| **AgentOS** | Runtime: FastAPI, sessões DB, background runs, HITL, traces, schedules, auth |
| **Control Plane** | UI de monitorização (liga ao *vosso* runtime; dados no vosso ambiente) |

**Roubar:** separar *definição cognitiva* (quem é o agente) de *runtime* (como corre, persiste, aprova) de *control plane* (observar/aprovar). Vocês já tendem a isso (MCP + dashboard + agents); Agno nomeia a separação com clareza.

---

## 2. Três primitivos: Agent · Team · Workflow

| Primitivo | Quando | Execução |
|-----------|--------|----------|
| **Agent** | Um domínio, poucas tools | Loop modelo + tools + estado |
| **Team** | Especialistas + coordenação em runtime | Líder delega; modes (coordinate, tasks+deps, …) |
| **Workflow** | Processo conhecido, auditável | Steps fixos: seq, parallel, condition, loop, router |

FAQ oficial: Workflow = *assembly line*; Team = *task force* open-ended.

**Roubar (já parcialmente nosso):**

```text
action isolada     → Agent
supervisor dinâmico → Team
plan.yaml pipeline → Workflow
```

**Anti-padrão Agno também combate:** não meter Team onde um Workflow basta (custo + não-determinismo).

---

## 3. Workflow: controlo de fluxo rico

Primitivas típicas: **Step**, **Steps**, **Condition**, **Loop**, **Router**, parallel branches, nested workflows, function executors.

**Roubar para o plan schema (fase 2+):**

| Agno | Extensão conceptual do plan |
|------|-----------------------------|
| Condition | `if` sobre artefacto/estado |
| Loop + end condition | `max_replans` + critic até pass |
| Router | escolher ramo (ex. SEO vs só copy) |
| Parallel | steps com mesmo depends_on |
| Nested workflow | sub-plan / profile |

---

## 4. HITL — o ponto mais forte a roubar

Agno distingue níveis (workflows):

| Nível | O que pausa | Exemplos |
|-------|-------------|----------|
| **Step-level** | O passo inteiro | confirm before/after, user input, **output review**, router selection, loop iteration review |
| **Executor-level** | Uma **tool** dentro do agent | `@tool(requires_confirmation=True)`, `requires_user_input`, campos a preencher |
| **Nested** | Step gate **e** tool gate em sequência | |
| **External execution** | Tool “defer” a sistema externo | humano ou outro sistema executa |

Estados de run: `is_paused` → requirements → `confirm()` / `reject()` / input → `continue_run`.

**Três tipos de HITL recorrentes nos demos:**

1. **Confirmation** — aprovar tool/step sensível  
2. **User input** — pedir campos em falta (`destination`, `budget`)  
3. **External execution** — não correr a tool no agente; marcar para fora  

**Roubar para o nosso `human_gate`:**

```yaml
human_gate:
  level: step | executor   # passo inteiro vs tool
  kind: confirmation | user_input | output_review | external
  allow: [confirm, reject, edit]
  fields: []               # se user_input
  timeout: optional
```

Isto é **mais rico** que boolean e alinha LangGraph approve/edit + Timbal suspend.

AgentOS MCP: `continue_run` / `cancel_run` no lifecycle quando componentes estão expostos — HITL sobre MCP sem inventar protocolo à parte.

---

## 5. MCP nos dois sentidos

| Direcção | Mecânica |
|----------|----------|
| **Consumer** | `MCPTools` — agent usa tools de servidores MCP externos |
| **Provider** | AgentOS como MCP server — `run_agent` / `run_team` / `run_workflow` + `continue_run` / `cancel_run` / sessions |
| **as_tool** | Agent/Team/Workflow exposto com **nome e description para o modelo caller** (prompt do caller ≠ description humana) |

**Roubar:**

- Description de tool MCP = prompt para quem *chama*, não marketing interno.  
- Lifecycle tools (`continue_run`) viajam com componentes HITL.  
- **Cuidado:** expor pipeline inteiro como uma tool = blast radius; scopes + allowlist (já na policy pipeline).

Vocês já são **MCP-first** na produção; Agno valida “OS de agentes fala MCP” como padrão de mercado.

---

## 6. Memória, knowledge, learning, culture

| Capacidade | Ideia |
|------------|--------|
| **Sessions** | Multi-turn + history + metrics no DB configurável |
| **Memory** | Factos/preferências de utilizador cross-session |
| **Knowledge** | RAG (muitos vector stores, hybrid, filters, agentic filters) |
| **Learning** | Melhorar com feedback/outcomes (API learnings) |
| **Culture** | Memória partilhada *entre* agents |
| **Compression** | Manter sessões longas dentro da context window |
| **Context providers** | Injectar dados vivos (Drive, Slack, MCP, workspace) |

**Roubar:** alinhar a camadas Hermes — session ≠ user memory ≠ knowledge docs ≠ procedural skills.  
**Culture** = cuidado no multi-tenant; no setup genérico preferir knowledge versionado em git.

---

## 7. Guardrails, hooks, evals, tracing

- **Guardrails:** validar input/output (PII, injection nos demos).  
- **Pre/post hooks:** lifecycle do run (evals em background no AgentOS).  
- **Evals + tracing (OTel):** operações, não só “o modelo respondeu”.  

**Roubar:** policy pipeline (pre) + critic/verify (post) + event log; evals como jobs, não no hot path sempre.

---

## 8. Team modes e tasks com dependencies

- Leader cria tasks com **depends_on** entre members (pipeline dinâmico *dentro* do team).  
- Async members concurrent quando o mode permite.  
- `show_members_responses` para transparência.

**Roubar:** supervisor que emite sub-tasks com deps ≈ plan gerado em runtime; ainda assim preferir **persistir** esse sub-plan (event sourcing) em vez de só conversa.

---

## 9. Skills

LocalSkills / SKILL.md carregáveis em agents e teams (demo Operator).

**Roubar:** compatível com o que já têm; lifecycle candidate→active (Hermes) mantém-se.

---

## 10. AgentOS runtime — capacidades de plataforma

| Need | AgentOS |
|------|---------|
| API produto | REST amplo (runs, sessions, memory, knowledge, traces, schedules, approvals) |
| Interfaces | REST, SSE, WS, MCP, A2A, Slack, Telegram, … |
| Estado | DB que *vocês* configuram |
| Long-running | Background execution, reconectar stream, cancel, HITL |
| Access | JWT, RBAC, service accounts |
| Adapters | Também LangGraph, Claude Agent SDK, etc. |

**Roubar conceptualmente:**  
*approvals* como entidade de primeira classe (tabela/API), não só mensagem de chat.  
*cancel_run* explícito.  
RBAC por user_id/session ownership em multi-user.

**Não roubar cegamente:** dezenas de interfaces de messaging no core do framework de agentes empresariais método.

---

## 11. Mapa Agno → nosso setup

| Agno | Nosso |
|------|--------|
| Agent | action + skill |
| Team | supervisor + workers |
| Workflow | plan.yaml |
| Step HITL | human_gate level=step |
| Executor HITL | human_gate level=executor + tools_allowed |
| continue_run | resolver human_gate_resolved |
| MCP provider tools | futuro: expor *um* pipeline método com scope |
| MCPTools consumer | MCP prod / tools existentes |
| Sessions DB | pilots + events + (Supabase se usarem) |
| Knowledge | docs/knowledge + pgvector opcional |
| Guardrails | policy pipeline + constitution |
| Control plane | dashboard vosso |
| Structured output | JSON Schema outputs |
| max_iterations | budget.max_steps |

---

## 12. O que Agno faz *melhor* que o resumo O01

A shortlist só dizia “plataforma completa”. O detalhe útil é:

1. **Taxonomia Agent/Team/Workflow** com critério de escolha claro  
2. **HITL multi-nível** (step vs tool vs external vs output review)  
3. **MCP dual** (client + server + as_tool + continue_run)  
4. **Approvals/sessions como dados de plataforma**  
5. **Workflow primitives** (router/loop/condition) além do pipeline linear  
6. **Separação SDK / OS / Control Plane**  

LangGraph ganha em time-travel/reducers/Send de baixo nível; Agno ganha em **produto runtime + HITL de negócio + MCP serve**.

---

## 13. Recomendação para vocês

| Fase | Acção |
|------|--------|
| Agora | Adoptar vocabulário Agent/Team/Workflow + HITL kinds no plan schema draft |
| Lab | Opcional: um AgentOS mínimo *só* no setup, **sem** apontar a prod MCP |
| Prod | Manter agent-network-mcp; se um dia houver bridge, é adaptador, não replace |
| Nunca automático | `as_tool` de pipelines com write em produção sem scopes |

---

## Checklist de padrões Agno

- [x] O01 Agent vs Team vs Workflow  
- [ ] HITL: confirmation / user_input / output_review / external  
- [ ] level step vs executor  
- [ ] continue_run / cancel_run na API mental do orchestrator  
- [ ] tool description para *caller* model  
- [ ] approvals como registo persistente  
- [ ] Workflow: condition, loop, router (schema plan v2)  
- [ ] Knowledge ≠ Memory ≠ Session (camadas)  
- [ ] Guardrail pre + eval post  
- [ ] Lab AgentOS isolado (opcional)  
