# AUDIT-ORCHESTRATION.md — Auditoria técnica profunda: Multi-Agent Orchestration / Runtime / Planning

**Estado deste documento:** reescrita completa, padrão ouro. A versão anterior repetia, sem verificar, uma classificação errada herdada de `CORE-MAPPING.md` — "`Orchestrator.ts` é MOCK". **Isto é falso**, confirmado por leitura completa do ficheiro (480 linhas) e dos ficheiros à sua volta. É o achado mais importante desta ronda de auditorias, e obriga a corrigir também `FASE1-AGENTES.md`, `AUDIT-AGENTS.md` e várias entradas de `STATUS.md` que repetiram a mesma classificação.

## 0. Errata — como o erro aconteceu e onde se propagou

| Quando | O quê |
|---|---|
| 2026-08-18 | Último commit real a `Orchestrator.ts` — o ficheiro fica no estado que existe hoje |
| 2026-09-17 07:32 | `CORE-MAPPING.md` classifica `orchestrator/Orchestrator.ts` como **MOCK**, sem justificação (célula "—", ao contrário de `Planner.ts` que recebe uma frase explicando o REAL) |
| 2026-09-18 11:14 | `GOV-FASE1.md` cita essa classificação e acrescenta, incorretamente, que `SecurityManager.ts` tem `verifyPassword()` sempre `true` — **mas o fix real (`bcrypt.compareSync`) já tinha sido commitado às 2026-09-17 21:18**, antes deste documento ser escrito |
| Fases 1-6 da auditoria de Agentes (2026-09-18/19, sessão anterior) | Repetem "`Orchestrator.ts` é MOCK" como achado central — na síntese final, na secção 4, e em várias entradas de `STATUS.md` |
| Esta auditoria (2026-09-19) | Leitura completa de `Orchestrator.ts`, `AgentFactory.ts`, `apps/api/src/index.ts`, `DeliberationOrchestrator.ts`, `SecurityManager.ts`, `ComplianceManager.ts` — **nenhum destes é mock**; a classificação estava errada desde o início (`Orchestrator.ts`) ou ficou desatualizada por um dia sem ser revista (`SecurityManager.ts`) |

**Lição estrutural:** este repo tem, pelo menos duas vezes, o mesmo tipo de erro que a disciplina "código > README" existe para prevenir — só que desta vez a fonte não confiável não foi um README externo, foi **um documento de mapeamento interno do próprio repo, nunca re-verificado antes de ser citado em cadeia** por quatro documentos subsequentes. Isto reforça, com um exemplo concreto e caro, a regra que já vinha sendo seguida: nem a documentação do próprio repo é imune a precisar de verificação directa antes de ser citada como facto.

## 1. O que `Orchestrator.ts` realmente faz (lido por completo)

`packages/core/src/orchestrator/Orchestrator.ts` instancia ~30 subsistemas no construtor (segurança, economia de tokens, confiança, conselhos de arquitectura, auto-percepção, memória imunológica, etc.) e implementa `processRequest()` como um pipeline real de 14 passos, com lógica condicional genuína, não delegação vazia:

1. `security.detectPromptInjection(input)` — **real**: 10 regex patterns (`ignore previous instructions`, `you are now`, `jailbreak`, etc.), bloqueia e regista evento se detectar
2. `tokenEconomy.searchBeforeBuild(...)` — pesquisa antes de construir (não verificado em profundidade nesta passagem)
3. `router.route(input)` — **real** (`Router.ts`, classificado REAL por `CORE-MAPPING.md`, corroborado agora)
4. `deliberationOrchestrator.deliberate(...)` — **real**: chama `securityManager.detectPromptInjection` de novo + `deliberationEngine.assessLevel(...)` (scoring ponderado real, já confirmado REAL por `GOV-FASE1.md`) — se `!deliberation.approved`, **a função retorna cedo, bloqueando o pedido de facto**
5. `tokenEconomy.allocateBudget(executionId, 10000)` — aloca orçamento
6. `completenessValidator.getEmptyCapabilities()` — verifica capacidades vazias, regista eventos
7. **`agentFactory.getAgentsByDomain(domain)` → `planner.plan(input, domainAgents, ...)` → `executor.execute(plan, executionId)`** — **a chamada real de Router→Planner→Executor**, o próprio coração da alegação "está desligado" que esta auditoria refuta
8. `tokenEconomy.estimateCost(...)` + `recordUsage(...)`
9. `reflectionEngine.reflect(executionId, result)`
10. `accumulationCycle` — regista ciclo de aprendizagem se sucesso
11. `immunologicalMemory.registerEvent(...)` se falha
12. `selfAwareness.updateState()`
13. `metricsDashboard.updateMetrics()`
14. `complianceManager.logAudit(...)` — regista auditoria real (objecto `AuditLog` construído, não descartado)

**`AgentFactory.ts` (39 linhas, lido por completo):** `Map<string, Agent>` real, `registerAgent()`/`getAgentsByDomain()`/`getAgentsByLayer()` todos funcionais — nada de mock aqui.

## 2. Há um ponto de entrada real que instancia tudo isto

`apps/api/src/index.ts` (134 linhas, lido por completo) é um servidor Express **genuíno e completo**:
- Cria `Pool` de Postgres real (`pg`), `ToolRegistry` do MCP com as tools reais (`createDatabaseTools`, `createFilesystemTools`, `createWebTools`, `createBrazilianLawTools`, `createPortugueseLawTools` — **incluindo as tools que a auditoria `AUDIT-TOOLS-MCP.md` já identificou como vulneráveis**, confirmando que estão de facto ligadas ao servidor real, não só definidas isoladamente)
- `LLMService` com `OpenAIProvider` real
- `AGENT_CONFIGS.forEach((config) => agentFactory.registerAgent(config))` — os 24 agentes do `config/agents.config.ts` são registados um a um no arranque
- Instancia `Router`, `Planner`, `Executor`, depois `Orchestrator` com todos os 6 argumentos correctos
- Configura WebSocket, graceful shutdown, scans iniciais de oportunidade/auto-percepção/dashboard

**Isto não é scaffolding morto — é um servidor que, com as variáveis de ambiente certas (`DATABASE_URL`, `OPENAI_API_KEY`), arrancaria e serviria pedidos reais.**

## 3. Mas nunca foi corrido de verdade — e há um teste de integração com um bug real

`docs/STATUS.md` (histórico, 18/08/2026) já documentava isto com precisão: *"Scaffolding PCU... Implementado, `tsc --noEmit` limpo. **Nunca rodou contra um Postgres real.**"* Esta auditoria confirma que a situação não mudou: `node_modules/` não existe neste sandbox (não foi possível correr `pnpm install`/testes aqui), e não há evidência em nenhum log de CI de que `apps/api` tenha sido efectivamente arrancado contra infraestrutura real.

**Achado novo, por leitura de `tests/integration/ExecutionFlow.test.ts` (45 linhas):** o teste chama `new Orchestrator(mockAgentFactory, router, planner, executor, memory as any)` — **5 argumentos**, mas o construtor real de `Orchestrator` exige **6** (`agentFactory, router, planner, executor, memory, hitlManager`). O 6º argumento (`hitlManager`) fica `undefined`. Isto não impediria o teste de compilar sob `vitest`/esbuild (que normalmente não aplica checagem de tipo estrita como o `tsc`), mas **`this.hitlManager` fica `undefined` dentro do Orchestrator**, e é passado directamente a `new DeliberationOrchestrator(..., this.hitlManager)` e `new AttentionEconomy(this.hitlManager)` no construtor — se qualquer caminho de `processRequest()` chamar um método real de `hitlManager`, o teste falharia em runtime com `TypeError: Cannot read properties of undefined`. **Não foi possível confirmar nesta sessão se o teste passa ou falha de facto** (sem `node_modules`, não corre) — fica como **NOT VERIFIED, mas com uma hipótese concreta e testável**: é provável que o teste só passe hoje porque nenhum passo do `input: 'Test request'` usado chega a accionar um caminho que invoque `hitlManager` (ex. se `deliberation.approved` for sempre `true` no cenário de teste e nenhum HITL for pedido).

> **RESOLVIDO em 2026-09-19 — 2 bugs corrigidos no `ExecutionFlow.test.ts`: (a) `mockHitl` adicionado como 6º argumento (o construtor de `Orchestrator` exige 6, o teste passava 5); (b) `vi` adicionado ao import de `vitest` (era usado em 6 sítios sem estar importado, com `globals: false` no `vitest.config.ts`). Verificação pendente de `prisma generate` — ver B10/D8. Ver `EXECUTION-PROMPTS.md` B2.**

## 4. O que isto muda na leitura de toda a auditoria anterior

A afirmação repetida em `FASE1-AGENTES.md`, `AUDIT-AGENTS.md` (secção 1a e 4) e em várias entradas de `STATUS.md` — *"`Router.ts`/`Planner.ts`/`Executor.ts` são REAL, mas `Orchestrator.ts` que os liga é MOCK — peças reais, desligadas"* — **está corrigida aqui**: `Orchestrator.ts` não é mock, liga as três peças de facto, com lógica de segurança/deliberação/orçamento real à volta. **O que continua verdade, e é a formulação correcta:** o conjunto nunca foi executado de ponta a ponta contra infraestrutura real (Postgres, Redis, OpenAI de produção) neste sandbox nem, tanto quanto verificável, em nenhum outro ambiente até agora — é código real, testado só parcialmente (um teste de integração com um bug de assinatura de construtor por confirmar), nunca corrido em produção. É uma lacuna de **validação operacional**, não de **implementação**.

Isto muda também a leitura da dualidade TS/Python já registada: não são "um lado real (Python) e um lado desligado (TS)" — são **dois lados reais, com maturidades operacionais diferentes**: o lado Python (`runner/plan_runner/`) tem 167 testes que correm de facto (`pytest` confirmado, `87% cobertura`); o lado TypeScript tem código igualmente real mas **nunca validado a correr** contra infraestrutura de verdade, com pelo menos um teste de integração de correcção duvidosa.

## 5. As recomendações de `patterns-from-orchestrators/` foram exageradas?

Mantém-se a resposta já dada: não nos padrões extraídos (O01-O18); a única desactualização já identificada (checkpoint como "fase 3 futura" quando já está implementado no motor `langgraph`) continua válida e não muda com este achado.

## 6. Classificação consolidada (revista)

| Item | Classificação anterior (errada/imprecisa) | Classificação corrigida |
|---|---|---|
| `Orchestrator.ts` | MOCK | **REAL** — pipeline de 14 passos genuíno, liga Router→Planner→Executor de facto |
| Ligar `Orchestrator.ts` a Router/Planner/Executor | BUILD (prioridade 0) | **Já feito** — o trabalho que faltava não é ligar, é **validar em execução real** |
| `apps/api/src/index.ts` | Não auditado antes | **REAL** — entry point completo e coerente |
| `SecurityManager.verifyPassword()` | MOCK (sempre `true`) | **REAL desde 2026-09-17 21:18** (`bcrypt.compareSync`, fix CodeQL #5) |
| `ExecutionFlow.test.ts` | Não auditado antes | **NOT VERIFIED** — bug de assinatura de construtor (5 args vs. 6), pode ou não estar a mascarar uma falha real |
| Validar `apps/api` contra Postgres/OpenAI reais | Não identificado como prioridade | **BUILD, nova prioridade real** — é o único passo que falta para confirmar que o pipeline TS funciona de ponta a ponta, não só que compila |
| 14 frameworks externos avaliados (Fase 1 da auditoria de Agentes) | EXTRACT/REFERENCE | Sem mudança — a decisão de não adoptar continua correcta, independentemente desta correcção |

## 7. O que fazer a seguir (revisto)

1. **Corrigir `ExecutionFlow.test.ts`** — adicionar o 6º argumento (`mockHitl`, já definido no próprio teste mas nunca passado ao construtor) e confirmar que o teste passa depois da correcção.
2. **Correr `apps/api` uma vez contra infraestrutura real** (Postgres local ou de staging, chave OpenAI de teste) — é o único passo em falta para transformar "código real, nunca corrido" em "código validado". Isto é trabalho de validação, não de implementação nova.
3. **Não repetir o erro desta auditoria**: qualquer classificação REAL/INCOMPLETO/MOCK citada de `CORE-MAPPING.md` ou de qualquer documento de mapeamento anterior deve ser reconfirmada por leitura directa antes de ser usada como base para uma decisão — não só citada em cadeia.

## 8. O que NÃO fazer

- Não assumir que qualquer outra classificação de `CORE-MAPPING.md` está automaticamente certa só porque uma parte (`Planner.ts`, `Executor.ts`, `Router.ts`) foi confirmada correcta nesta e noutras auditorias — pelo menos duas classificações (`Orchestrator.ts`, e a citação desactualizada de `SecurityManager.ts` em `GOV-FASE1.md`) já se mostraram erradas.
- Não adoptar nenhum framework externo para "resolver" a orquestração — não há nada para resolver, o código já existe e já liga as peças certas; falta validação de execução, não arquitectura nova.
- Não presumir que o teste de integração actual prova que o pipeline funciona — tem um bug de assinatura não resolvido, o que o torna uma evidência fraca até ser corrigido e corrido.
