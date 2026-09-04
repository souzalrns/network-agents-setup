# Restantes — extracção detalhada (Timbal, CrewAI, PydanticAI, Mastra, AG2, Haystack)

Complementa `langgraph-deep.md` e `agno-deep.md`. Só padrões portáveis.

---

## Timbal

**Perfil:** core pequeno (<10k LOC), Agent + Workflow + Tool **mesma interface** e event stream; async/await + Pydantic; sem magia escondida.

### Padrões a roubar

| Padrão | Detalhe |
|--------|--------|
| **Uma interface** | Agent, Workflow e Tool chamam-se da mesma forma e emitem o mesmo tipo de eventos |
| **`requires_approval`** | Em Tool (e steps): predicado + `approval_prompt`; emite `ApprovalEvent` |
| **`resume={approval_id: bool}`** | Retoma o mesmo run com mapa de decisões |
| **`suspend()`** | Pausar a meio para perguntar ao humano (além de approval de tool) |
| **Durable cross-process** | Estado de pausa sobrevive restart |
| **Parallel gates** | Várias approvals em paralelo; `pending_approvals()` |
| **get_run_context / step_span** | Workflow step lê output de step anterior por nome |
| **FallbackModel** | Cadeia de providers se um falhar |
| **Skills on demand** | Pacotes knowledge+tools carregados quando o loop já faz sentido |
| **Evals YAML** | Suite declarativa de validação |
| **Tracing OTLP** | Spans exportáveis |

### Mapa nosso

- `requires_approval(lambda)` → policy + human_gate em tools com threshold  
- `resume` map → `human_gate_resolved` com decisões por id  
- Uma interface → registry de actions com contrato único de invocação  
- step_span output → `inputs` / artefact paths entre steps  

**Não:** adoptar Timbal como único runtime só porque é “simples”; é candidato a **lab** se quiserem HITL enxuto.

---

## CrewAI

**Perfil:** papéis + tasks fáceis; produção séria usa **Flow + Crew**, não só Crew.

### Padrões a roubar

| Padrão | Detalhe |
|--------|--------|
| **Role / goal / backstory / tools** | Especialização clara por agente |
| **Process.sequential** | Pipeline previsível de tasks |
| **Process.hierarchical** | Manager delega e revê |
| **Crew = músculo** | Trabalho LLM colaborativo num “job” |
| **Flow = espinha** | `@start` / `@listen` / `@router` — ordem, branch, estado tipado |
| **Flow embute Crew** | Step determinístico chama Crew só onde precisa de autonomia |
| **Estado Pydantic no Flow** | Persistível entre steps |
| **@human_feedback** (Flows) | HITL ao nível de orquestração |

### Mapa nosso

```text
Flow     ≈ plan.yaml / Workflow Agno
Crew     ≈ Team / supervisor+workers num step
Role     ≈ entry no registry + skill
sequential ≈ depends_on linear
hierarchical ≈ Team mode
```

**Não:** CrewAI como SO de dezenas de áreas + auditoria dura; é excelente **modelo mental de roles** e protótipo.

---

## PydanticAI

**Perfil:** type-safety ponta a ponta; structured output; durable execution **como capability** (Temporal, DBOS, Prefect, …) — não reinventar filas dentro do agent framework.

### Padrões a roubar

| Padrão | Detalhe |
|--------|--------|
| **Output = modelo Pydantic/schema** | Falha de validação → retry (`ModelRetry`) em vez de prosa |
| **Typed tools + deps injection** | Tools e dependências tipadas |
| **output_validator** com RunContext | Validação com estado (ex. relaxar após N retries) |
| **Durable = motor externo** | Model/tool calls viram Activities; workflow sobrevive crash |
| **Separação O13 reforçada** | Cérebro tipado ≠ engine de retries/filas |
| **MCP first-class** | Tools via MCP com tipos |
| **Observability (Logfire/OTel)** | Runs observáveis |

### Mapa nosso

- JSON Schema nos outputs do plan **já é o padrão PydanticAI** sem Python  
- Critic/verify = output_validator  
- Temporal/Hatchet = camada infra se jobs longos; não meter isso no MCP “de chat”  

---

## Mastra (TypeScript)

**Perfil:** TS-native (AI SDK); Agents + Workflows separados; memory, RAG, MCP, evals, tool approval, supervisor agents.

### Padrões a roubar

| Padrão | Detalhe |
|--------|--------|
| **Agent ≠ Workflow** | Loop modelo vs grafo de steps determinístico |
| **Workflow suspend/resume** | HITL no grafo |
| **Tool approval** | Aprovar/rejeitar tool call antes de executar |
| **Zod typed step I/O** | Contratos entre steps |
| **Memory: lastMessages + semantic recall** | Janela recente + recuperação semântica |
| **Observational memory** | Resumo denso em background (contexto estável) |
| **threadId + resourceId** | Isolar conversa vs utilizador/recurso |
| **Supervisor agents** | Coordenar especialistas |
| **Evals / scorers / guardrails** | Qualidade em produção |
| **Workspaces + skills** | Filesystem/sandbox + skill files |

### Mapa nosso

- Só prioritário se o **lab/runtime** for TypeScript (ex. Next na Vercel)  
- threadId ≈ plan_id; resourceId ≈ user/project  
- Observational memory ≈ compressão Hermes MEMORY, com gate  

---

## AutoGen / AG2

**Perfil:** pioneiro multi-agent conversacional; AutoGen MS em maintenance; **AG2** fork community. Não base nova para vosso core.

### Padrões a roubar (só conceitos)

| Padrão | Detalhe |
|--------|--------|
| **Group chat / debate** | Vários agentes falam; útil em pesquisa/crítica |
| **Speaker selection** | Quem fala a seguir (regra ou modelo) |
| **Actor-style concurrency** | AG2 forte em concorrência conversacional |
| **Human proxy** | Humano como “agente” no loop |

### Mapa nosso

- Critic + writer ≈ debate **estruturado** (schemas), não chat livre sem log  
- Preferir orquestrador central a swarm peer-to-peer  

**Não:** AG2 como orquestrador de produção do network.

---

## Haystack

**Perfil:** pipelines de NLP/RAG; agents como nós de pipeline, não SO multi-domínio.

### Padrões a roubar

| Padrão | Detalhe |
|--------|--------|
| **Pipeline explícito** | retrieve → rank → prompt → generate |
| **Component I/O tipado** | Cada nó declara inputs/outputs |
| **Agent como componente** | Raciocínio só onde o pipeline precisa |
| **Eval de retrieval** | Métricas de RAG separadas de “agent success” |

### Mapa nosso

- Vertical **knowledge / Item 13 / SEO research** pode inspirar-se em pipeline RAG  
- Não usar Haystack para orquestrar marketing+legal+obras  

---

## Infra (lembrete final)

Temporal · Hatchet · Inngest · Trigger.dev = **O13**: retries, cron, wait days, exactly-once de *jobs*.  
HITL de negócio pode pausar no grafo cognitivo; **durabilidade de processo** é desta camada (PydanticAI deixa isso explícito).
