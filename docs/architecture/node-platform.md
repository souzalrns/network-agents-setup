# Node platform — apps/api + packages/core

Documenta a **plataforma Node** do monorepo: a API Express (`apps/api/`) e o pacote core (`packages/core/`). Distinta do motor Python (`runner/plan_runner/`) e do MCP governado (`mcp/plan_runner/`).

**Nota de maturidade:** o README do repo avisa que "alguns módulos podem conter stubs; tratar antes de produção". Este documento descreve o que existe hoje, não o que está pronto para produção.

---

## Layout

### `apps/api/`

| Pasta | Conteúdo |
|-------|----------|
| `src/controllers/` | `AgentController`, `ChatController`, `ExecutionController`, `HitlController`, `MetricsController` |
| `src/middleware/` | `auth.ts`, `errorHandler.ts`, `logging.ts` |
| `src/routes/` | `agents`, `chat`, `executions`, `health`, `hitl`, `metrics` |
| `src/services/` | `ExecutionService.ts` |
| `src/` | `index.ts` (bootstrap), `server.ts` (Express app), `websocket.ts` (canal de eventos) |

### `packages/core/` (parcial — os módulos que importam para esta doc)

| Pasta | Módulos |
|-------|---------|
| `orchestrator/` | `Orchestrator`, `Router`, `Planner`, `Executor`, `ReflectionEngine`, `DeliberationOrch.` |
| `governance/` | `TrustManager`, `TrustOrchestrator`, `Councils`, `DeliberationEngine`, `ArchitectureCouncil`, `CompletenessValidator`, `DocumentationGovernance`, `IngestionOrchestrator` |
| `hitl/` | `HitlManager` |
| `llm/` | `LLMService` |
| `observability/` | `MetricsDashboard`, `SelfAwareness` |
| `security/` | `SecurityManager` |
| `agents/` | `AgentFactory`, `HorizontalAgents` |

Outros módulos (`economy/`, `evolution/`, `immunity/`, `simulation/`, `opportunity/`, `products/`, `domains/`, `search/`, `ux/`, `compliance/`, `data/`, `knowledge/`, `operations/`, `infrastructure/`, `development/`) existem mas não são o foco desta doc.

---

## Boot sequence (`apps/api/src/index.ts`)

O `main()` corre 14 passos ordenados. A ordem importa — comentários do próprio ficheiro explicam porquê.

| # | Passo | Nota |
|---|-------|------|
| 0 | `assertAuthConfig()` | **Fail-closed**: em `NODE_ENV=production` sem `API_KEY`, lança erro e a API não arranca |
| 1 | `new Pool({ connectionString: DATABASE_URL })` | Postgres |
| 2 | `new ToolRegistry([...])` | Carrega MCP tools: `database`, `filesystem`, `web`, `BrazilianLaw`, `PortugueseLaw` |
| 3 | `new OpenAIProvider(...)` + `new LLMService(...)` | `OPENAI_API_KEY`, `DEFAULT_MODEL` (default `gpt-4-turbo`) |
| 4 | `new AgentFactory({ publicMode })` + `registerAgent` por `AGENT_CONFIGS` | Vem de `config/agents.config.ts` |
| 5 | `new MemoryManager({ redisUrl, cacheTTL: 3600 })` | `REDIS_URL` |
| 6 | `new HitlManager({ autoExpireMinutes })` | **Criado antes de Executor/Orchestrator**, que dependem dele |
| 7 | `new Router()`, `new Planner(...)`, `new Executor(...)` | Executor recebe `agentFactory, memory, llm, hitlManager` |
| 8 | `new Orchestrator(agentFactory, router, planner, executor, memory, hitlManager)` | Instancia internamente governança, economia, segurança, observabilidade, produtos, conformidade |
| 9 | `new ExecutionService(memory)` | |
| 10 | `createServer(...)` + `app.listen(PORT)` | `PORT` (default `3000`) |
| 11 | `setupWebSocket(server, ...)` | Canal de eventos em tempo real |
| 12 | `opportunityRadar.scanAll()` + `selfAwareness.updateState()` | Scans iniciais |
| 13 | `metricsDashboard.updateMetrics()` | Dashboard inicial |
| 14 | Registo de `SIGTERM`/`SIGINT` para graceful shutdown | Para radar, worker supervisor, dashboard, memory, db, server |

---

## HITL — lado Node

### `HitlManager` (`packages/core/src/hitl/HitlManager.ts`)

Extende `EventEmitter`. Estado **em memória**, por instância:

- `pendingRequests: Map<string, HitlRequest>`
- `approvedRequests: Map<string, HitlRequest>`
- `rejectedRequests: Map<string, HitlRequest>`
- `checkpoints: Map<string, any>` — chave = `hitlRequestId`

**Eventos emitidos:** `request-created`, `request-approved`, `request-rejected`, `request-expired`.

**Métodos públicos:**

| Método | O que faz |
|--------|-----------|
| `requestApproval(params)` | Cria `HitlRequest` com `id: hitl_<uuid>`, `status: PENDING`, `expiresAt` (default 60 min). Agenda expiração com `setTimeout`. |
| `approveRequest(id, responderId, comment?)` | Move de pending → approved. Erro se não existir ou não estiver PENDING. |
| `rejectRequest(id, responderId, comment?)` | Move de pending → rejected. Mesmas guardas. |
| `getPendingRequests(domain?)` | Lista, filtrável por `domain`. |
| `getRequest(id)` | Procura nos 3 maps. |
| `isPending(id)` | Bool. |
| `saveCheckpoint({ hitlRequestId, planId, currentStepIndex, executionState, memorySnapshot })` | Guarda checkpoint por `hitlRequestId`. |
| `getCheckpoint(hitlRequestId)` | Devolve ou `undefined`. |
| `clearCheckpoint(hitlRequestId)` | Devolve `true` se existia. |

**Expiração:** `scheduleExpiration` usa `setTimeout` com o delta até `expiresAt`. Quando dispara, `status = EXPIRED`, move para fora de pending, emite `request-expired`.

### HTTP surface (`apps/api/src/routes/hitl.ts`)

Montado pelo `createServer()`; todas as rotas passam por `HitlController`.

| Método | Path | Controller | Notas |
|--------|------|------------|-------|
| `GET` | `/hitl/pending` | `listPending` | Aceita `?domain=` |
| `GET` | `/hitl/:id` | `getRequest` | 404 se não existir |
| `GET` | `/hitl/:id/checkpoint` | `getCheckpoint` | 404 se não existir |
| `POST` | `/hitl/:id/approve` | `approveRequest` | Body: `{ responderId, comment? }`. **`responderId` obrigatório** (400 sem ele) |
| `POST` | `/hitl/:id/reject` | `rejectRequest` | Body: `{ responderId, comment? }`. **`responderId` obrigatório** |
| `GET` | `/hitl/stats` | `getStats` | Agrega por `priority` (critical/high/medium/low) e `category` (financial/legal/medical/strategic/approval) |

### Categorias e prioridades

Do `HitlController.getStats()`:

- **Prioridades:** `critical`, `high`, `medium`, `low`
- **Categorias:** `financial`, `legal`, `medical`, `strategic`, `approval`

---

## Auth (fail-closed)

`apps/api/src/middleware/auth.ts` — commit `1a3e613`.

**Regra:** sem `API_KEY` configurada, a API **NÃO** serve pedidos. A versão anterior fazia `if (!process.env.API_KEY) return next()`, o que deixava todos os endpoints abertos — incluindo `POST /hitl/:id/approve` e `/reject`, ou seja, qualquer pessoa podia aprovar um gate humano.

**Comportamento:**

- `assertAuthConfig()` corre no passo 0 do boot.
  - `API_KEY` definida → `{ ok: true }`.
  - `NODE_ENV=production` sem `API_KEY` → **lança** (`API_KEY em falta: a API recusa arrancar em produção sem autenticação configurada.`).
  - `ALLOW_UNAUTHENTICATED=true` e `NODE_ENV !== production` → `{ ok: true, warning }`.
  - Caso contrário → `{ ok: false, warning }` (a API arranca mas todos os pedidos recebem 503).

- `authMiddleware` (por request):
  - Sem `API_KEY` e sem `ALLOW_UNAUTHENTICATED=true` → **503** (`Service unavailable: authentication is not configured`).
  - Sem `API_KEY` mas com `ALLOW_UNAUTHENTICATED=true` (e `NODE_ENV !== production`) → passa.
  - `API_KEY` definida: compara `x-api-key` com **`safeEqual`** (comparação em tempo constante, para não vazar tamanho/prefixo via timing). Falha → **401**.

**Variáveis de ambiente:** `API_KEY`, `ALLOW_UNAUTHENTICATED`, `NODE_ENV`.

---

## Relação com o `plan_runner` (Python)

Dois motores, dois papéis:

| | Node (`apps/api` + `packages/core`) | Python (`runner/plan_runner`) |
|---|---|---|
| **Papel** | Plataforma de agentes (marketing, negócio) — orquestra agentes, expõe HTTP/WebSocket, gere HITL em memória | Motor de planos YAML com HITL, crash recovery, external workers |
| **HITL** | `HitlManager` (Node, em memória, expiração por `setTimeout`) | Contrato v1 (ver `docs/architecture/hitl/`) — lado Python é S6 no STATUS.md (`runner/plan_runner/hitl.py`) |
| **Transporte** | HTTP + WebSocket | CLI + (via MCP) stdio |
| **Contrato** | `HitlRequest` / `HitlStatus` / `HitlPriority` / `HitlCategory` (em `@network-agents/shared`) | Pendente — o contrato v1 define o formato de ficheiro/eventos que ambos os lados partilham |

**Estado actual:** o `HitlManager` Node existe e está montado na API. O lado Python (`hitl.py`) ainda não existe (é **S6** no `docs/initiatives/STATUS.md`). O contrato v1 está definido em `docs/architecture/hitl/`.

---

## Env vars (referência rápida)

| Var | Onde | Efeito |
|-----|------|--------|
| `NODE_ENV` | auth, boot | `production` ativa fail-closed; sem ele, modo dev |
| `API_KEY` | auth | Chave esperada em `x-api-key`; sem ela → 503 (ou erro de boot em prod) |
| `ALLOW_UNAUTHENTICATED` | auth | `true` permite dev local sem chave; ignorado em `production` |
| `DATABASE_URL` | boot | Postgres pool |
| `REDIS_URL` | boot | MemoryManager |
| `OPENAI_API_KEY` | boot | OpenAIProvider |
| `DEFAULT_MODEL` | boot | Default `gpt-4-turbo` |
| `PORT` | boot | Default `3000` |
| `PUBLIC_MODE` | boot | `AgentFactory({ publicMode })` |
| `HITL_EXPIRE_MINUTES` | boot | Default `60` (passado a `HitlManager`) |
| `FILESYSTEM_BASE` | boot | Base das filesystem tools MCP (default `./data`) |

---

## Ver também

- `docs/architecture/hitl/` — contrato HITL v1
- `docs/architecture/plan-execute/` — schema do plano
- `docs/architecture/patterns-from-mcp/` — MCP server governado (Python)
- `docs/initiatives/STATUS.md` — S6 (HitlManager Python)