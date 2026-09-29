# AUDIT-2 — Cadeia de execução e estado real de funcionamento

> **Base:** commit `3dc3b25`. **Data:** 2026-09-29.
> **Método:** leitura da cadeia a partir de `apps/api/src/index.ts`, mais **execução real**:
> (a) sondas `vitest` fora do repo (scratchpad) sobre `Orchestrator`→`Planner`→`Executor`, com LLM e HITL mockados;
> (b) o `plan_runner` corrido de facto nos modos `stub` (native + langgraph), `external` e `resume`, a partir de uma cópia do repo;
> (c) `SELECT`s read-only no Supabase `agent-network-memory` (projecto `mpsuurqilnhsvbnjmrpm`) para o RAG.
> Nada foi escrito no repo fora de `docs/audit/`.

## Resumo

- **O caminho TS (`POST /chat` e WebSocket) não chega ao LLM.** Todo o pedido é classificado como `tactical` pela deliberação, gera um pedido HITL e é devolvido como `"Deliberation rejected: Aguardando aprovação humana"`. Não existe caminho de retoma depois da aprovação. Verificado por execução.
- **Atrás desse bloqueio há mais três quebras:** `executions.update` sem `create` prévio, `finalOutput` nunca preenchido e tokens nunca contados.
- **`toolsAllowed` confirmado:** nunca é gerado no lado TS.
- **O motor Python funciona** (verificado), mas **não executa trabalho nenhum sozinho**: pausa à espera de um worker externo que não existe no repo.
- **O RAG está partido na junção:** ingere para `knowledge_chunks_t6` (110 chunks) e o retrieve lê `knowledge_chunks` (210 chunks de outro projecto). Verificado no Supabase ao vivo.

Legenda de estado: **LIGADO** (corre e produz efeito), **DESLIGADO** (existe mas nada o chama, ou nunca é alcançado), **SÓ-NO-PAPEL** (descrito ou configurado, mas sem efeito real), **MOCK** (finge fazer).

---

## 2.1 Cadeia TypeScript — `POST /chat` `[PEDIDO]`

### Arranque (`apps/api/src/index.ts`)

| # | Peça | Evidência | Estado | Nota |
|---|---|---|---|---|
| B1 | Auth fail-closed | `index.ts:35`, `middleware/auth.ts:31-82` | **LIGADO** | `API_KEY` única, comparação em tempo constante (`auth.ts:88-95`); 503 se não configurada. **Não é `return true`**: esse caso é o `SecurityManager.verifyPassword` (Fase 4), que não está no caminho HTTP |
| B2 | Pool Postgres | `index.ts:40-42` | LIGADO | Usado pelas tools `database` |
| B3 | `ToolRegistry` (5 conjuntos) | `index.ts:44-51` | LIGADO (construído) | Chega ao `Executor` (`:77`, S33), mas ver 2.2 |
| B4 | Provider LLM | `index.ts:54-58` | LIGADO — **só OpenAI** | `OpenAIProvider` é o único provider (`LLMService.ts:98`); omissão `gpt-4-turbo`. Não há Gemini (contra "custo zero", M6) |
| B5 | Agentes | `index.ts:60-62` | LIGADO | `AGENT_CONFIGS` → `AgentFactory` em `Map` (Fase 3) |
| B6 | Memória | `index.ts:64-67` | LIGADO | Prisma + Redis opcional |
| B7 | HITL | `index.ts:69-71` | LIGADO — **volátil** | `HitlManager` em `Map`s (Fase 4) |
| B8 | Orchestrator | `index.ts:81-88`; `Orchestrator.ts:86-190` | LIGADO | Instancia **31 módulos** no construtor |
| B9 | Timers de arranque | `index.ts:109-118` | LIGADO | `opportunityRadar.scanAll`, `selfAwareness`, `metricsDashboard` (conteúdo MOCK/INCOMPLETO, Fase 4) |

### Pedido (`server.ts` → `ChatController` → `Orchestrator.processRequest`)

| # | Passo | Evidência | Estado | Nota |
|---|---|---|---|---|
| P1 | Middleware | `server.ts:35-50` | LIGADO | `cors()` aberto (`:36`, S13 bloqueado por decisão); rate-limit 60/min por IP |
| P2 | Rota | `routes/chat.ts:11-12` | LIGADO | `/chat/stream` usa o **mesmo** handler; só faz stream com `body.stream=true`. `getChatStatus` (`ChatController.ts:45`) existe mas **não tem rota** → DESLIGADO |
| P3 | Anti prompt-injection | `Orchestrator.ts:208`; `SecurityManager.ts:277-296` | LIGADO (ingénuo) | Lista de regex. `/act as/i`, `/override/i` e `/system prompt/i` bloqueiam pedidos legítimos ("act as a reviewer", "override the default") |
| P4 | "Search before build" | `Orchestrator.ts:232-239`; `TokenEconomy.ts:256-257,332` | **MOCK** | "Simula busca"; o resultado só é logado |
| P5 | Routing de domínio | `Orchestrator.ts:242`; `Router.ts:2-18` | LIGADO | Palavras-chave, **primeiro match ganha**, omissão `business`. O `domain` do body tem prioridade |
| **P6** | **Deliberação** | `Orchestrator.ts:246-270`; `DeliberationOrchestrator.ts:96-125`; `DeliberationEngine.ts:84-109` | **LIGADO e BLOQUEIA TUDO** | Ver **Q1** |
| P7 | Orçamento de tokens | `Orchestrator.ts:273` | **SÓ-NO-PAPEL** | `allocateBudget(…,10000)` é guardado num `Map` e nunca aplicado. Nenhum código compara uso com orçamento |
| P8 | Completude | `Orchestrator.ts:277-294` | DESLIGADO (nunca alcançado) | — |
| P9 | Agentes do domínio | `Orchestrator.ts:297-300` | DESLIGADO (nunca alcançado) | Lança erro se o domínio não tiver agentes |
| P10 | Planner | `Planner.ts:9-77` | DESLIGADO (nunca alcançado) | Se alcançado: chamada LLM real + fallback. Ver 2.2 |
| P11 | Executor | `Executor.ts:29-149` | DESLIGADO (nunca alcançado) | Se alcançado: ver Q2–Q4 |
| P12 | Pós-execução | `Orchestrator.ts:306-355` | DESLIGADO | Reflexão, acumulação, auditoria: INCOMPLETO/MOCK (Fase 4) |
| P13 | Streaming SSE/WS | `Orchestrator.ts:385-406`; `ChatController.ts:54-86`; `websocket.ts:22,42,98` | **SÓ-NO-PAPEL** | `processRequestWithProgress` só chama `onComplete`/`onError`; `onStepStart`/`onStepComplete` nunca são invocados. O WS usa o mesmo `processRequest` → mesmo bloqueio |
| P14 | Aprovar HITL | `HitlController.ts:20-42`; `websocket.ts:134-155` | LIGADO — **sem efeito na execução** | Muda o estado no `HitlManager`, mas nada retoma o pedido original. `approveTactical` (`DeliberationOrchestrator.ts:187`) **não tem nenhum chamador** (grep) |

### Quebras encontradas no caminho TS

| ID | Quebra | Evidência | Verificação |
|---|---|---|---|
| **Q1** | **Todo o pedido é bloqueado na deliberação.** O `Orchestrator` passa critérios em escala 0–1 (`uncertainty 0.5, risk 0.3, reversibility 0.7, cost 0.4`, `Orchestrator.ts:253-258`), mas o `DeliberationEngine` espera 0–10: calcula `10 − reversibility` = 9.3, "quase irreversível" (`DeliberationEngine.ts:94`). Score = `3·impact + 11.3` → **20.3 / 26.3 / 32.3** para os 3 valores possíveis de `estimateImpact` (`Orchestrator.ts:408-413`). Com o limiar operacional em 20 (`DeliberationEngine.ts:37`), o nível `operational` fica **inalcançável** e tudo cai em `tactical` → HITL → `approved=false` → `return` | Leitura + fórmula | **Execução**: sonda devolve `agentId=deliberation`, `content="Deliberation rejected: Aguardando aprovação humana (HITL h1)"`, `level=tactical`, **0 chamadas LLM**, 0 escritas na memória |
| Q1-origem | A normalização `weighted * 10` que expôs o desajuste de escala entrou no commit `1a3e613` (2026-09-11, "deliberacao normalizada"). Antes, tudo caía em `operational` (comentário `DeliberationEngine.ts:102-107`) | `git log -S "weighted * 10"` | Histórico git |
| **Q2** | **`executions.update` sem `create`.** O Executor faz `memory.executions.update(executionId, …)` antes do 1.º passo, fora do `try` (`Executor.ts:54-57`). **Nenhum código chama `executions.create`** (grep em `packages`/`apps`/`tests`: só a definição em `ExecutionRepository.ts:5`). O Prisma `update` num id inexistente lança `P2025` | Leitura + semântica documentada do Prisma | **NÃO VERIFICADO contra Postgres real** (sem BD no sandbox). Se Q1 for corrigido, esta é a quebra seguinte |
| **Q3** | **`finalOutput` nunca preenchido.** Única atribuição: o inicializador `''` (`Executor.ts:44`). O `Orchestrator` devolve-o como `content` (`Orchestrator.ts:359`) → o `/chat` responderia `result: ""`. `finalConsolidator` é lido pelo Planner (`Planner.ts:68`) mas nunca usado | grep exaustivo `finalOutput`/`finalConsolidator` | Estático (conclusivo: só 4 ocorrências) |
| **Q4** | **Tokens nunca somados.** `results.metadata.totalTokens` nunca é atribuído (grep: nenhuma atribuição no Executor/Orchestrator). O custo registado (`Orchestrator.ts:306-311`) e o `totalTokens` persistido (`Executor.ts:135`) são sempre 0. Só existe um contador em memória por passo (`Executor.ts:100`) | grep | Estático |
| **Q5** | **Teste de integração falso-verde.** `tests/integration/ExecutionFlow.test.ts:47-48` só verifica `toBeDefined()`; passa com a resposta "Deliberation rejected", por isso Q1–Q4 nunca foram apanhados | Leitura + sonda | Execução (a sonda reproduz o mesmo cenário) |
| Q6 | HITL no Executor bloqueia o pedido HTTP até 5 min com polling de 1 s sobre um `Map` em RAM (`Executor.ts:335-365`); num restart perde-se o pedido | Leitura | Estático |

**Consequência:** não há evidência de o caminho TS alguma vez ter devolvido uma resposta de LLM a um pedido real. Pela leitura, mesmo antes de `1a3e613` a Q2 aplicava-se. **NÃO VERIFICADO contra BD real.**

---

## 2.2 O caso `toolsAllowed` — **CONFIRMADO** `[PEDIDO]`

| Pergunta | Resposta | Evidência |
|---|---|---|
| Onde é lido? | Condição `step.toolsAllowed?.length && this.toolExecutor && this.toolRegistry` | `Executor.ts:180` |
| Quem o gera no caminho real? | **Ninguém.** O schema JSON pedido ao LLM não tem o campo (`Planner.ts:36-50`); o Planner copia `planData.steps` tal como vêm (`:67`); o `fallbackPlan` não o define (`:86-101`) | grep `toolsAllowed`: só `execution.ts:24`, `Executor.ts` e `tests/unit/Executor.test.ts` |
| Há outra fonte possível? | `AgentConfig.tools` existe (`packages/shared/src/types/agent.ts:10,22`) e o `AgentFactory` guarda-o (`AgentFactory.ts:19`), mas **o Executor nunca lê `agent.tools`** (grep `agent.tools`: nenhuma leitura no core/api) | grep |
| A condição chega a ser verdadeira? | **Nunca em produção.** Só nos 3 testes que constroem o plano à mão com `toolsAllowed: ['read_file']` (`Executor.test.ts:170,192,218`). E, por Q1, o Executor nem é alcançado | grep + Q1 |
| No motor Python? | `tools_allowed` **tem fonte declarativa** (quem escreve o `plan.yaml` define-o por step, `models.py:33,63`), mas é **só informativo**: passa para o `request.json`/stub (`executor.py:37,79`) e nada o aplica. O worker externo decide | Leitura + execução (`request.json` do step `research` mostra `tools=['read_repo_file','web_search']`) |

**O que falta:** decidir **a fonte** de `toolsAllowed`. Há três opções: (a) derivar de `agent.tools` no Executor, (b) adicionar o campo ao schema do `Planner.plan()` e validá-lo contra o `ToolRegistry`, ou (c) herdar de um plano declarativo como no Python. Qualquer uma exige também resolver Q1.

---

## 2.3 Cadeia Python — `plan_runner` `[PEDIDO]`

| # | Peça | Evidência | Estado | Verificação |
|---|---|---|---|---|
| Y1 | CLI (`run`/`resume`/`compile-graph`/`search`) | `cli.py:15-38` | LIGADO | Execução |
| Y2 | Guard do `--out` (tem de ficar em `<repo>/pilots/`) | erro real: "--out must be inside …/pilots" | LIGADO | Execução. Consequência: correr o runner **escreve sempre dentro do repo** |
| Y3 | Engine `native` | `engine.py` | LIGADO | `stub` → `paused_human_gate` com 4 artefactos placeholder |
| Y4 | Engine `langgraph` | `langgraph_engine.py` | LIGADO | Mesmo resultado, com `waves`/`thread_id` |
| Y5 | HITL (ficheiros + `resume`) | `hitl.py`; `cli.py` | LIGADO | `resume --decision approve` → `state=done` |
| Y6 | Modo `external` | `executor.py:61-134` | LIGADO — **à espera de um worker que não existe** | `state=waiting_external`; `request.json` com `skill_path`/`agent_path` resolvidos. **Nenhum código do repo escreve `result.json`** (grep): o worker é humano ou um agente IDE |
| Y7 | Budget `max_steps` | `engine.py:138,285` | LIGADO **só no `native`** | grep: `langgraph_engine.py` não tem `budget`/`max_steps` → o engine "recomendado" (`runner/README.md:29`) não aplica o limite |
| Y8 | `max_replans`, `done_when`, `on_fail` | `models.py:49-50,67,77-79` | **SÓ-NO-PAPEL** | Lidos, nunca usados (grep: só `models.py`). `on_fail: retry` do plano de exemplo não tem efeito |
| Y9 | `knowledge_refs` (topo do plano) | `seo-article-demo.plan.yaml` | **SÓ-NO-PAPEL** | Nem é lido por `models.py` |
| Y10 | Bloco `knowledge:` por step → RAG | `knowledge_wiring.py:1-40`; `engine.py:155,296`; `langgraph_engine.py:76,305,445` | LIGADO (opt-in) — **lê a tabela errada** | Ver 2.4 |
| Y11 | Memória do cliente (`client_id` → `MEMORY.md`) | `engine.py` `_load_client_memory`; `executor.py:97-115` | LIGADO (opt-in, só leitura) | Documentado em S30; não re-executado aqui |
| Y12 | Chamadas de rede | `embedder.py:26,77` (Gemini); `mcp_knowledge.py:133` (MCP); `supabase_writer.py:46` (Postgres) | LIGADO | **Nenhuma chamada a um LLM de geração** no runner (grep `openai\|anthropic\|generativelanguage`: só o embedder) |

**Leitura:** o motor Python é **governação de execução** (ordem, gates, auditoria, retoma) e não execução de agentes. Os "agentes" são ficheiros `.md` entregues a quem fizer de worker. Isto é coerente com o `runner/README.md:13-17` ("optimises for governance"), mas significa que **no repo não há nenhum agente a correr autonomamente em nenhum dos dois runtimes**.

---

## 2.4 Cadeia RAG — ingestão → retrieve `[ACRESCENTADO PELO AUDITOR]`

| Elo | Onde | Tabela | Evidência |
|---|---|---|---|
| Ingestão (CI, em cada push a `docs/**/*.md`) | `scripts/ingest_apply.py` → `supabase_writer.py` | **`knowledge_chunks_t6`** | `supabase_writer.py:3-12`; `.github/workflows/ingest-knowledge.yml` |
| Retrieve (runner) | `mcp_knowledge.py` → MCP `retrieve_knowledge` (`agent-network-mcp`) | — | `mcp_knowledge.py:4-5,32-33,53-54` |
| Retrieve (servidor MCP) | `agent-network-mcp/lib/knowledge.js:54` → RPC `match_knowledge` | **`knowledge_chunks`** | Leitura read-only do repo irmão |
| RPC no Supabase | 2 overloads de `public.match_knowledge` | ambos `FROM knowledge_chunks` | `pg_get_functiondef` (SELECT ao vivo) |

**Dados ao vivo (SELECT, 2026-09-29):**

| Tabela | Chunks | Fontes | Última escrita |
|---|---|---|---|
| `knowledge_chunks` (lida pelo retrieve) | 210 | 88 | 2026-09-16 |
| `knowledge_chunks_t6` (escrita pelo setup) | 110 | 33 | **2026-09-29** (activa) |
| Fontes do setup que também existem em `knowledge_chunks` | — | **1 de 33** | — |

**Quebra Q7:** o C8 foi fechado como "pipeline completo markdown → chunk → embed → Supabase → retrieve" (`docs/initiatives/STATUS.md:17,237`), mas **o retrieve nunca lê o que o setup ingere**. A ingestão continua activa (escritas até hoje) sem consumidor. Achado menor: `agent_id` em `knowledge_chunks_t6` inclui o valor composto `marketing+produto-tech-transversal`, que nenhum `kb` pedido vai igualar.

---

## 2.5 Superfície MCP do motor — `mcp/plan_runner` `[ACRESCENTADO PELO AUDITOR]`

| Peça | Estado | Evidência |
|---|---|---|
| `list_templates`, `run_plan` (dry-run) | **LIGADO** | `python -m mcp_plan_runner.smoke`: ok; `list_templates()` devolve 12 templates (= `find docs/orchestration -name "*.plan.yaml"`) |
| Autorização em `moderate` (omissão) | LIGADO — **aberto sem chave** | Aviso real: `[SECURITY] moderate_lab_open: run_plan autorizado sem chave`. Aceitável só em stdio local (`README` de `mcp/plan_runner`) |

---

## 2.6 Condições que nunca se tornam verdadeiras `[PEDIDO]`

| Condição | Onde | Porquê nunca é verdadeira |
|---|---|---|
| `step.toolsAllowed?.length` | `Executor.ts:180` | Nenhuma fonte (2.2) |
| `assessment.level === OPERATIONAL` (via `/chat`) | `DeliberationOrchestrator.ts:97` | Score mínimo 20.3 > limiar 20 (Q1) |
| `deliberation.approved` (via `/chat`) | `Orchestrator.ts:263` | Q1; e o caminho `STRATEGIC` também não é alcançado com os critérios fixos |
| `searchResult.recommendation === 'reuse'` | `Orchestrator.ts:237` | Busca simulada (`TokenEconomy.ts:332`); e o resultado só é logado |
| Retoma depois do `approve` HITL | `HitlController.ts:28`; `websocket.ts:136` | Nada liga o `approve` ao pedido original; `approveTactical` sem chamadores |
| `result.json` do worker | `executor.py:117-119` | Nenhum worker no repo |
| Retrieve devolver chunks do setup | `mcp_knowledge.py` → `match_knowledge` | Lê outra tabela (Q7) |

---

## Limites desta fase

- **Q2 não executada contra Postgres** (sem BD no sandbox); conclusão por leitura + semântica documentada do `prisma.update` (lança `P2025` quando o registo não existe).
- As sondas mockam o LLM e o HITL, e usam `MemoryManager` real (sem BD) ou um stub. Não chamam OpenAI.
- O RAG foi verificado por `SELECT` read-only no projecto `agent-network-memory`. Assumi que é o mesmo projecto que o `DATABASE_URL` do CI do setup usa: a tabela `knowledge_chunks_t6` só existe lá e tem escritas de hoje, o que é consistente com isso.
