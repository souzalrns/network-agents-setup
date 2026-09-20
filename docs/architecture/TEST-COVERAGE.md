# Cobertura de Testes TypeScript — 2026-09-20

Primeira medição real de cobertura TS deste repo (antes só existia a heurística src-vs-test da auditoria de cobertura, 2g). Produzido no item **S24**.

**Ferramenta:** `@vitest/coverage-v8@1.6.1` (mesma major do `vitest@1.6.1` já instalado). Instalado como devDependency na raiz (`pnpm add -D -w`).

**Configuração:** `vitest.config.ts` (raiz) ganhou o bloco `coverage` (`provider: 'v8'`, reporters `text`+`json-summary`+`html`, `include: ['packages/*/src/**/*.ts', 'apps/*/src/**/*.ts']`). Novo script `pnpm run test:coverage` → `vitest run tests/unit tests/integration --coverage`.

**Achado que forçou um ajuste de escopo:** o `vitest.config.ts` original inclui `tests/**/*.test.ts`, o que apanha `tests/e2e/api.test.ts` — um teste e2e genuíno (`import request from 'supertest'`, espera um servidor real em `localhost:3000`). A dependência `supertest` **nunca foi instalada** (não está em nenhum `package.json` do repo) — este ficheiro nunca correu com sucesso, nem localmente nem em CI (`ci.yml` só corre `vitest run tests/unit`, nunca tocou em `tests/e2e/`). Para conseguir um `--coverage` que termina, o script `test:coverage` restringe-se a `tests/unit` + `tests/integration` (mesmo padrão que a CI já usa para a parte unitária, estendido com a integração). **`tests/e2e/api.test.ts` continua por resolver — ver secção de achados abaixo.**

---

## Resultado agregado

**178/178 testes passam** (31 ficheiros de teste, `tests/unit` + `tests/integration`), 0 falhas.

| Métrica | % |
|---|---|
| Statements | 48.86% |
| Branch | 66.83% |
| Functions | 43.19% |
| Lines | 48.86% |

---

## Cobertura por pasta (`% Stmts`)

| Pasta | % Stmts | Nota |
|---|---|---|
| `apps/api/src` | 47.49 | `controllers` 33.33, `middleware` 78.1, `routes` 84.84, `services` **0**, `utils` 100 |
| `apps/web/src/hooks` | 0 | único ficheiro (`useWebSocket.ts`), frontend — sem teste |
| `packages/core/src/agents` | 34.74 | |
| `packages/core/src/compliance` | 29.83 | |
| `packages/core/src/data` | 34.57 | |
| `packages/core/src/development` | 45.15 | |
| `packages/core/src/domains` | 66.04 | |
| `packages/core/src/economy` | 62.36 | |
| `packages/core/src/evolution` | 44.38 | |
| `packages/core/src/governance` | 48.88 | |
| `packages/core/src/hitl` | 97.1 | melhor pasta do repo — reflecte o trabalho B1/B4/M2 desta sessão |
| `packages/core/src/immunity` | 69.04 | |
| `packages/core/src/infrastructure` | 59.11 | |
| `packages/core/src/knowledge` | 69.41 | |
| `packages/core/src/llm` | 44.39 | inclui `LLMService.ts`, instrumentado com spans nesta sessão (D2) |
| `packages/core/src/observability` | 91.23 | (não confundir com `packages/observability`) |
| `packages/core/src/operations` | 32.54 | |
| `packages/core/src/opportunity` | 79.23 | |
| `packages/core/src/orchestrator` | 56.84 | `Orchestrator.ts` 67.08, `Executor.ts` 60.45, `ReflectionEngine.ts` **23.57** |
| `packages/core/src/products` | 75.37 | |
| `packages/core/src/search` | 32.42 | `AIVisibilityEngine.ts` (438 linhas, já conhecido MOCK/INCOMPLETO em `CORE-MAPPING.md`) |
| `packages/core/src/security` | 64.01 | `SecurityManager.ts` |
| `packages/core/src/simulation` | 87.98 | |
| `packages/core/src/ux` | 32.98 | |
| `packages/langgraph/src/*` (graphs + state) | **0** | pacote inteiro sem cobertura TS — ver achados |
| `packages/mcp/src/client` | 48.14 | `MCPClient.ts` |
| `packages/mcp/src/server` | **0** | `MCPServer.ts` — ver achados (crítico) |
| `packages/mcp/src/tools` | 91.79 | inclui `ActionReceipt.ts` (98.27, novo nesta sessão, C5) |
| `packages/mcp/src/tools/built-in` | 81.89 | inclui `SsrfGuard.ts` (74.19) |
| `packages/mcp/src/tools/legal` | 74.12 | |
| `packages/mcp/src/util` | 100 | `sanitizeError.ts` |
| `packages/memory/src` | 37.37 | `MemoryManager.ts` |
| `packages/memory/src/cache` | 34.28 | `RedisCache.ts` |
| `packages/memory/src/repositories` | 23.44 | 5 repositórios, todos <35% |
| `packages/observability/src` | 74.7 | `Tracer.ts` 79.83 (D1, memory leak corrigido nesta sessão), `Logger.ts` 93.54, `Metrics.ts` 50 |
| `packages/observability/src/middlewares` | 100 | |
| `packages/scripts/src` | 0 | scripts de bootstrap/CLI — ver achados |
| `packages/scripts/src/docs` | 32.58 | `generate-agents-doc.ts` 62.34 (reescrito nesta sessão, F6) |
| `packages/scripts/src/ingest` | 0 | scripts de ingestão RAG |
| `packages/scripts/src/monitor`, `/schedule`, `/validate` | 0 | inclui `check-consistency.ts` (445 linhas, usado por `ci.yml`) — ver achados |
| `packages/shared/src/types` | 100 | só tipos |
| `packages/websocket/src` | 18.49 | `WebSocketClient.ts` 16.79, `WebSocketServer.ts` 19.68 |
| `packages/websocket/src/rooms` | 17.75 | `RoomManager.ts` |
| `packages/websocket/src/types` | 100 | só tipos |

---

## Ficheiros com 0% de cobertura

| Ficheiro | Linhas | Nota |
|---|---|---|
| `apps/api/src/middleware/logging.ts` | 24 | |
| `apps/api/src/services/*Service.ts` | 126 | |
| `apps/web/src/hooks/useWebSocket.ts` | 54 | frontend, fora do padrão de testes deste repo (sem testes de componentes React) |
| `packages/langgraph/src/graphs/base/StateGraph.ts` | 69 | |
| `packages/langgraph/src/graphs/execution/ExecutionGraph.ts` | 123 | |
| `packages/langgraph/src/graphs/multi-agent/MultiAgentGraph.ts` | 114 | |
| `packages/langgraph/src/state/StateManager.ts` | 81 | |
| `packages/mcp/src/server/MCPServer.ts` | 46 | **crítico — ver achados** |
| `packages/mcp/src/tools/legal/db.ts` | 4 | trivial (stub de conexão) |
| `packages/scripts/src/bootstrap.ts` | 89 | |
| `packages/scripts/src/db.ts` | 7 | trivial |
| `packages/scripts/src/legal-agents.ts` | 67 | |
| `packages/scripts/src/smoke-test.ts` | 324 | maior ficheiro sem teste do repo; é ele próprio uma ferramenta de smoke-test (`ci.yml` chama-o directamente, não via vitest) |
| `packages/scripts/src/docs/generate-code-map.ts` | 148 | |
| `packages/scripts/src/ingest/brazilian-law.ts` | 375 | |
| `packages/scripts/src/ingest/doctrine.ts` | 166 | |
| `packages/scripts/src/ingest/embeddings.ts` | 109 | |
| `packages/scripts/src/ingest/jurisprudence.ts` | 206 | |
| `packages/scripts/src/ingest/portuguese-law.ts` | 298 | |
| `packages/scripts/src/monitor/quality-check.ts` | 93 | |
| `packages/scripts/src/schedule/ingestion-schedule.ts` | 51 | |
| `packages/scripts/src/validate/completeness.ts` | 104 | |
| `packages/scripts/src/validate/check-consistency.ts` | 445 | **usado por `ci.yml` (`validate:consistency`) — ver achados** |
| `packages/scripts/src/validate/test-agents.ts` | 91 | |

---

## Achados

1. **`packages/mcp/src/server/MCPServer.ts` (0%) é o ficheiro mais crítico desta lista.** É o ponto onde, segundo **S11** (já registado em `STATUS.md`), a identidade real (`caller`/`providedKey`) devia ser propagada ao `ToolExecutor` — hoje `caller='unknown'` por omissão. Zero cobertura de testes neste ficheiro significa que a lógica de autorização (ou a sua ausência) nunca foi exercitada por um teste automatizado.
2. **`packages/langgraph/src/*` (0% em todo o pacote TS)** — o motor de execução Python (`langgraph_engine.py`) tem cobertura real e testada (93% via pytest, ver auditoria 2g), mas o pacote TypeScript equivalente (`StateGraph.ts`, `ExecutionGraph.ts`, `MultiAgentGraph.ts`, `StateManager.ts`) nunca é exercitado por nenhum teste `tests/unit`/`tests/integration`. Requer confirmação: este pacote está mesmo em uso em produção (via `apps/api`) ou é código ainda não ligado?
3. **`packages/scripts/src/validate/check-consistency.ts` (445 linhas, 0%)** é invocado por `ci.yml` (`validate:consistency`) mas nunca por um teste `vitest` — a única validação da sua correcção é a CI a correr contra o estado real do repo, não um teste unitário isolado com casos conhecidos (positivos/negativos).
4. **`packages/scripts/src/ingest/*` (0%, 5 ficheiros, ~1150 linhas no total)** — todo o pipeline de ingestão RAG (que alimentou os 110 chunks do C8, um resultado já confirmado a funcionar) não tem nenhum teste automatizado; a única validação até agora foi a execução manual bem-sucedida documentada no C8.
5. **`tests/e2e/api.test.ts` está genuinamente quebrado** (dependência `supertest` nunca instalada) — não é um "0% de cobertura", é um ficheiro de teste que **nunca correu**, nem antes nem depois desta sessão. Não corrigido aqui (corrigir implicaria decidir se vale a pena manter um teste e2e que precisa de um servidor real a correr — fora do âmbito de "instalar tooling de cobertura").
6. **`packages/core/src/orchestrator/ReflectionEngine.ts` (23.57%)** é o pior ficheiro dentro de uma pasta já com boa cobertura de resto (`Router.ts`/`Planner.ts` 100%) — destoa o suficiente para merecer nota, mas não tão crítico como o MCPServer (não está ligado a nenhuma pendência de segurança conhecida).

## Item registado (S24)

Ver `STATUS.md`: **S24** regista como pendência de valor real (não bloqueante) fechar a cobertura de `MCPServer.ts` (achado 1) e decidir o destino de `tests/e2e/api.test.ts` (achado 5) — os 2 achados mais accionáveis desta lista.

---

*Gerado durante a auditoria de cobertura de 2026-09-20 (Tarefa 4). Relatório completo (HTML) disponível em `coverage/index.html` após correr `pnpm run test:coverage` — não commitado (ver `.gitignore`).*
