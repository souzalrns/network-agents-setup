# AUDIT-4 — Módulos MOCK / INCOMPLETO / órfãos

> **Base:** commit `3dc3b25`. **Data:** 2026-09-29.
> **Método:** varrimento automático dos 39 ficheiros de `packages/core/src` (LOC, `Map`s, marcadores de simulação, `Math.random`, importadores), seguido de leitura directa dos casos citados. Classificação de alcançabilidade cruzada com a Fase 2 (quem é de facto chamado por pedido, timer ou rota). Histórico git (386 commits obtidos por fetch limitado) para datar as contradições com `CORE-MAPPING.md`.

## Resumo

O `CORE-MAPPING.md` (commit `6ff59f8`) acerta no retrato geral (5/19/14/1), mas tem **duas classificações erradas** e **uma desactualizada**:

- **`Orchestrator.ts` não é MOCK.** É o pipeline real e não mudou desde o mapeamento.
- **`SecurityManager`:** o `verifyPassword` "sempre `true`" e o hash sem salt foram corrigidos **depois** do mapeamento (`d00cad5`), e o doc nunca foi actualizado.
- **`Executor`:** está "REAL" mas tem 3 bugs (Q2–Q4).

O **HitlManager em `Map`** está confirmado. A ponte para ficheiros (`importFromFile`/`exportToFile`) existe mas tem **0 chamadores**.

Em alcançabilidade: dos 31 módulos que o `Orchestrator` instancia, **só 6 correm num pedido real** (até à deliberação), **4 correm em timers** e **18 são órfãos funcionais**, porque só são alcançáveis por métodos sem chamador.

---

## 4.1 Contradições internas — `CORE-MAPPING.md` vs código `[PEDIDO]`

| Módulo | `CORE-MAPPING.md` diz | Código diz | Evidência | Achado |
|---|---|---|---|---|
| `orchestrator/Orchestrator.ts` | **MOCK** (`CORE-MAPPING.md:49`, nota "—") | **REAL**: pipeline de 14 passos que chama deliberação, Planner e Executor. Os MOCKs são módulos que ele *usa* | `Orchestrator.ts:194-374`; `git log 6ff59f8..origin/main -- Orchestrator.ts` = **0 commits**; `git show 6ff59f8:…Orchestrator.ts` já tinha `deliberate`/`planner.plan`/`executor.execute` (`:262,302,303`) | **Classificação errada desde o início** (DOC-ERRADO). Confirmado por leitura directa, como o brief pedia |
| `security/SecurityManager.ts` | "`verifyPassword()` devolve sempre `true`"; "hash sem salt SHA-256" (`CORE-MAPPING.md:88-89`) | `bcrypt.hashSync(password, 10)`; `bcrypt.compareSync`, fail-closed sem hash guardado | `SecurityManager.ts:491-506`; fix `d00cad5` (2026-09-17), **posterior** a `6ff59f8` na ordem do `git log` (posição 46 vs 154) | **Doc desactualizado** (DOC-ERRADO). **Continua verdade:** `verifyMFA` aceita `'123456'` (`SecurityManager.ts:239`) |
| `security/SecurityManager.ts` (uso) | Implica risco de auth | O login, o registo e o MFA **não têm chamadores** fora do próprio ficheiro (grep `.login(`/`.register(`/`.verifyMFA(`). A auth HTTP real é `apps/api/src/middleware/auth.ts` (API key, fail-closed) | grep | O "auth é `return true`" do brief **não se aplica ao caminho real**. O MFA fixo é código morto |
| `orchestrator/Executor.ts` | **REAL** (`CORE-MAPPING.md:48`) | Real na intenção, mas com Q2 (`update` sem `create`), Q3 (`finalOutput` vazio) e Q4 (tokens nunca somados) | `Executor.ts:44,54-57,135` | REAL com bugs: precisa correcção, não só persistência |
| `orchestrator/Planner.ts` | **REAL** | Real, mas não gera `toolsAllowed` e o `finalConsolidator` nunca é usado | `Planner.ts:36-51,68` | REAL-incompleto |
| `ExecutionService.getHitlStats` (fora do core) | — | Devolve zeros fixos: "Será implementado" | `apps/api/src/services/ExecutionService.ts:96-99` | MOCK não mapeado (acrescentado) |

---

## 4.2 MOCK — o que falta para serem reais `[PEDIDO]`

Os 14 do `CORE-MAPPING.md`, **menos o `Orchestrator`** (4.1), mais os MOCK encontrados fora do core. A evidência vem de leitura directa.

| Módulo | Evidência de simulação | O que falta para ser real |
|---|---|---|
| `economy/TokenEconomy.ts` | "Simula busca em capacidades existentes / Em produção… Catálogo Universal" (`:256-257,332`); cache e compressão só emitem eventos (`:293-296`); orçamento alocado e nunca aplicado (`Orchestrator.ts:273`) | Fonte real do catálogo de capacidades; **contagem real de tokens por chamada** (depende de Q4); aplicar o orçamento (abortar ou degradar quando `used > allocated`); cache de respostas real. **É o módulo do objectivo central da visão** |
| `governance/CompletenessValidator.ts` | "Processa a ingestão (simulação)" (`:90`) | Ligar a ingestão real (Python `scripts/ingest_*`) e à tabela `knowledge_sources` |
| `governance/IngestionOrchestrator.ts` | "Simula ingestão… Em produção buscaria conteúdo de fontes" (`:149-150`) | Idem; hoje duplica em TS a ingestão que o Python já faz |
| `opportunity/OpportunityRadar.ts` | "Simula escaneamento… Em produção integração real" (`:152-153,178`); corre num `setInterval` (`:54`) | Fontes reais (API GitHub, releases); ou desligar o timer. **Corre sempre em background** |
| `operations/WorkerSupervisor.ts` | "Simula reinicialização" (`:181`); `setInterval` (`:48`) | Workers reais para supervisionar (não existem, Fase 2 Y6) |
| `agents/HorizontalAgents.ts` | "Em produção armazenaria em Redis" (`:123`); `confidence = 70 + Math.random()*20` (`:152`) | Substituir o `Math.random` por métrica real; persistência |
| `development/RepositoryManager.ts` | "Simula análise"; `alignment = 60 + Math.random()*30` (`:158-159`) | Análise real de repositório (ou remover) |
| `domains/SpecialtyManager.ts` | Catálogo de especialidades com ferramentas fictícias (`:92`) | Ligar a `AgentFactory`/config reais |
| `search/AIVisibilityEngine.ts` | "Indexa ativo (simulação)" (`:309`); 7 `Math.random` | Integração real de medição de visibilidade (Item 13) |
| `simulation/OrganizationalSimulator.ts` | 70 ocorrências de marcadores de simulação, 8 `Math.random` | É um simulador por natureza. Decidir se tem lugar no produto |
| `compliance/ComplianceManager.ts` | Respostas fixas + `complianceScore: 80` (`CORE-MAPPING.md:22`); construtor recebe dependências que não usa | Implementar direitos RGPD reais sobre dados reais; ligar `SecurityManager`/`DataGovernance` |
| `data/DataGovernance.ts` | "Simula observação de dados" (`CORE-MAPPING.md:23`) | Fonte real de dados observados |
| `security/SecurityManager.ts` | Após `d00cad5`: só o MFA é fixo (`:239`); utilizadores e sessões em `Map` | TOTP real **ou** remover o subsistema de utilizadores (não é usado, 4.1) |
| `packages/mcp/src/tools/legal/brazilian-law.ts`, `portuguese-law.ts` | Query real ao Prisma com **fallback** `SIMULATED_*_LAWS`, marcado `source:'simulated'`, quando a base está vazia (`brazilian-law.ts:20-25,57`; `portuguese-law.ts:14,37`) | Ingerir documentos (`packages/scripts/src/ingest/*`). **Aceitável como está**: fallback honesto e documentado |
| `apps/api/.../ExecutionService.getHitlStats` | Zeros fixos (`:96-99`) | Ler do `HitlManager` (ou de uma tabela HITL depois do M4) |

---

## 4.3 INCOMPLETO — lógica real, estado volátil `[PEDIDO]`

| Módulo | Estado em RAM | Confirmação |
|---|---|---|
| **`hitl/HitlManager.ts`** | **5 `Map`s**: `pendingRequests`, `approvedRequests`, `rejectedRequests`, `expiredRequests`, `checkpoints` (`:90-94`) | **Confirmado.** Existe ponte para ficheiros (`importFromFile` `:228`, `exportToFile` `:247`, M2), mas **0 chamadores** fora do próprio ficheiro e dos testes (grep). Num restart perde-se todo o HITL pendente. O `Executor` faz polling deste `Map` até 5 min (`Executor.ts:335-365`). O `Checkpoint` vai para o Prisma (`Executor.ts:320`), o pedido HITL não: a persistência fica **meia feita** |
| `agents/AgentFactory.ts` | 1 `Map` | Aceitável: é reconstruído a partir da config em cada arranque |
| `evolution/AccumulationCycle.ts`, `evolution/VersionManager.ts` | 1–2 `Map`s | Leitura de sinais (tabela da secção de varrimento) |
| `governance/ArchitectureCouncil.ts`, `Councils.ts`, `DocumentationGovernance.ts`, `TrustManager.ts`, `TrustOrchestrator.ts` | 1–2 `Map`s cada | Idem |
| `immunity/ImmunologicalMemory.ts` | 3 `Map`s | Idem |
| `infrastructure/InfrastructureManager.ts` | 2 `Map`s; `implementTokenEconomy()` usa `Math.random` (`CORE-MAPPING.md:91`) | Idem: fabrica o resultado, é mais MOCK do que INCOMPLETO |
| `knowledge/CognitiveRepository.ts` | 1 `Map` | Idem |
| `observability/MetricsDashboard.ts`, `SelfAwareness.ts` | `Map`/array | Idem |
| `orchestrator/DeliberationOrchestrator.ts`, `ReflectionEngine.ts` | 1 `Map` cada | Idem |
| `products/ProductManager.ts`, `ux/AdaptiveInterface.ts`, `ux/AttentionEconomy.ts` | 1–2 `Map`s | Idem |
| **Fora do core:** `packages/observability/src/Metrics.ts` | 3 `Map`s (`:9-11`) | Métricas do Executor só em memória; o `Tracer` exporta por OTLP só se `OTLP_ENDPOINT` estiver definido (`Tracer.ts:86-111`) |
| **Fora do core:** `runner/plan_runner/working_memory.py` | Só leitura: nenhuma função escreve (`def`s: `_resolve_repo_root`, `resolve_memory_path`, `read_memory`, `memory_status`) | O `MEMORY.md` por cliente é mantido à mão |
| **Fora do core:** `runner/plan_runner/session_search.py` | Índice FTS5 por run | Não há índice global entre sessões (`STATUS.md:60`, S31) |

**Sem implementação nenhuma:** memória L4 (`remember`/`recall`/`forget`). O grep em `runner/` e `packages/` não devolve nada (S29, `STATUS.md:58`).

---

## 4.4 Órfãos reais — sem consumidor em produção `[PEDIDO]`

Definição usada: **órfão funcional** = nenhum método do módulo é chamado a partir do caminho de pedido (`processRequest`), de timers de arranque ou de rotas/WS. Instanciar no construtor do `Orchestrator` não conta como consumo.

### Alcançabilidade dos 31 módulos instanciados pelo `Orchestrator`

| Categoria | Módulos | Evidência |
|---|---|---|
| **Correm num pedido real** (até à deliberação, por Q1) | `SecurityManager.detectPromptInjection`, `TokenEconomy.searchBeforeBuild`, `Router`, `DeliberationOrchestrator` (+ `DeliberationEngine`), `HitlManager.requestApproval`, `ImmunologicalMemory.registerEvent` (só quando há injecção) | `Orchestrator.ts:208-270`; sonda da Fase 2 |
| **Correm em timers** | `OpportunityRadar.scanAll` (intervalo), `SelfAwareness.updateState`, `MetricsDashboard.updateMetrics` (→ `SelfAwareness.getState`), `WorkerSupervisor.checkWorkers` | `index.ts:109-118`; `OpportunityRadar.ts:54`; `MetricsDashboard.ts:87,96`; `SelfAwareness.ts:73`; `WorkerSupervisor.ts:48` |
| **Inalcançáveis** (depois da deliberação, bloqueados por Q1) | `AgentFactory.getAgentsByDomain`, `CompletenessValidator`, `Planner`, `Executor`, `ReflectionEngine`, `AccumulationCycle`, `ComplianceManager.logAudit` | `Orchestrator.ts:277-355` |
| **Órfãos funcionais** (só via métodos sem chamador) | `TrustManager`, `TrustOrchestrator`, `CouncilsOrchestrator`, `IngestionOrchestrator`, `AttentionEconomy`, `VersionManager`, `CognitiveRepository`, `HorizontalAgents`, `DataGovernance`, `AdaptiveInterface`, `InfrastructureManager`, `RepositoryManager`, `SpecialtyManager`, `ProductManager`, `DocumentationGovernance`, `AIVisibilityEngine`, `OrganizationalSimulator`, `ArchitectureCouncil` (só pelo ramo `STRATEGIC`, inalcançável) — **18** | grep `orchestrator\.` em `apps/`+`packages/scripts`: só `processRequest`(6), `processRequestWithProgress`(2), timers e `stop`. `getSystemStatus`, `createSpecialty`, `createProduct`, `submitAmendment`, `registerDigitalAsset`, `getComplianceReport`, `getInfrastructureRecommendation`, `get*Report` (`Orchestrator.ts:417-479`) **sem chamadores** |

**Custo destes órfãos:** **6 039 LOC** dos 12 689 do core (≈48%; soma dos LOC da tabela 4.5 para os 18) e 3 timers em background, só para manter estado que nenhuma resposta usa.

### Órfãos fora do core

| Unidade | Evidência | Estado |
|---|---|---|
| `packages/langgraph/**` | Fase 1 | MORTO |
| `apps/web/**` | Fase 1 | MORTO (não compila) |
| `packages/mcp/src/server/MCPServer.ts`, `McpAuth.ts`, `client/MCPClient.ts` | grep `new MCPServer\|new MCPClient\|createHttpHandler` fora do pacote = 0 | Construídos e testados (S11), **nenhuma superfície montada** |
| `packages/memory`: `UserRepository`, `ConversationRepository`, `MetricsRepository`, `getOrCreateUser`, `getOrCreateConversation`, `saveExecutionState`, `getExecutionState`, `getConversationHistory` | 0 usos fora do pacote (grep) | Órfãos. Só `executions.*`, `checkpoints.*` e `addMessage` são usados |
| `packages/memory` `RedisCache` | Só se `REDIS_URL` estiver definido; e só via `saveExecutionState`/`getExecutionState` (órfãos) | Órfão de facto, mesmo com Redis ligado |
| `packages/core` `resolveAgentPrompt` | Só testes (Fase 3 A3) | Órfão (F1 não ligado) |
| `packages/core` `Router.routeWithConfidence` | `Router.ts:19-33`; sem chamadores | Órfão |
| `packages/core` `DeliberationOrchestrator.approveTactical` | Sem chamadores (Fase 2) | Órfão |
| `packages/core` `HitlManager.importFromFile`/`exportToFile` | 0 chamadores | Órfão (M2 "Done", mas não ligado) |
| `apps/api` `ChatController.getChatStatus` | Sem rota (`routes/chat.ts:11-12`) | Órfão |
| `packages/scripts/src/bootstrap.ts`, `legal-agents.ts` | Sem script em `package.json` nem workflow (só citados em docs) | Órfãos (manuais) |
| `packages/scripts/src/ingest/*` (TS) | Scripts `ingest:*` existem (`packages/scripts/package.json`), nenhum workflow os corre | Manual; paralelo ao ingest Python (Fase 1) |
| `runner/plan_runner/knowledge.py` `MockKnowledge` | Só testes; o backend por omissão é `NullKnowledge` (`knowledge.py:16`); `knowledge_wiring.py:81` usa `McpKnowledge` | OK (dublê de teste) |

---

## 4.5 Varrimento completo de `packages/core/src` `[ACRESCENTADO PELO AUDITOR]`

Sinais automáticos (não substituem a leitura, mas permitem priorizar). SIMUL = linhas com `simula|em produção|placeholder|mock|fake|hardcod|TODO` (case-insensitive).

| Ficheiro | LOC | Maps | SIMUL | `Math.random` | Classif. corrigida |
|---|---|---|---|---|---|
| agents/AgentFactory | 57 | 1 | 1 | 0 | INCOMPLETO (OK) |
| agents/HorizontalAgents | 320 | 0 | 1 | 1 | MOCK · órfão |
| compliance/ComplianceManager | 362 | 2 | 4 | 3 | MOCK · inalcançável |
| data/DataGovernance | 350 | 2 | 5 | 6 | MOCK · órfão |
| development/RepositoryManager | 330 | 2 | 3 | 3 | MOCK · órfão |
| domains/SpecialtyManager | 430 | 1 | 1 | 1 | MOCK · órfão |
| economy/TokenEconomy | 457 | 2 | 6 | 0 | MOCK · **no caminho** |
| evolution/AccumulationCycle | 272 | 1 | 1 | 2 | INCOMPLETO · inalcançável |
| evolution/VersionManager | 253 | 2 | 1 | 0 | INCOMPLETO · órfão |
| governance/ArchitectureCouncil | 249 | 2 | 0 | 1 | INCOMPLETO · órfão |
| governance/CompletenessValidator | 264 | 2 | 3 | 2 | MOCK · inalcançável |
| governance/Councils | 336 | 1 | 0 | 4 | INCOMPLETO · órfão |
| governance/DeliberationEngine | 182 | 0 | 0 | 0 | REAL · **no caminho** (mas ver Q1) |
| governance/DocumentationGovernance | 410 | 2 | 2 | 2 | INCOMPLETO · órfão |
| governance/IngestionOrchestrator | 193 | 0 | 2 | 0 | MOCK · órfão |
| governance/TrustManager | 409 | 2 | 0 | 1 | INCOMPLETO · órfão |
| governance/TrustOrchestrator | 238 | 1 | 0 | 0 | INCOMPLETO · órfão |
| hitl/HitlManager | 310 | 6 | 1 | 0 | INCOMPLETO · **no caminho** |
| immunity/ImmunologicalMemory | 575 | 3 | 0 | 3 | INCOMPLETO · no caminho (injecção) |
| index | 83 | 0 | 3 | 0 | BARREL |
| infrastructure/InfrastructureManager | 362 | 2 | 2 | 2 | INCOMPLETO/MOCK · órfão |
| knowledge/CognitiveRepository | 255 | 1 | 3 | 1 | INCOMPLETO · órfão |
| llm/LLMService | 221 | 0 | 1 | 0 | REAL (só OpenAI) · inalcançável |
| observability/MetricsDashboard | 393 | 2 | 1 | 0 | INCOMPLETO · timer |
| observability/SelfAwareness | 463 | 0 | 6 | 0 | INCOMPLETO · timer |
| operations/WorkerSupervisor | 295 | 2 | 3 | 0 | MOCK · timer |
| opportunity/OpportunityRadar | 520 | 2 | 6 | 1 | MOCK · timer |
| orchestrator/DeliberationOrchestrator | 258 | 1 | 0 | 0 | INCOMPLETO · **no caminho** |
| orchestrator/Executor | 366 | 0 | 1 | 0 | REAL c/ bugs · inalcançável |
| orchestrator/Orchestrator | 480 | 0 | 7 | 0 | **REAL** (era "MOCK") · no caminho |
| orchestrator/Planner | 102 | 0 | 0 | 0 | REAL · inalcançável |
| orchestrator/ReflectionEngine | 403 | 1 | 0 | 1 | INCOMPLETO · inalcançável |
| orchestrator/Router | 34 | 0 | 0 | 0 | REAL · no caminho |
| products/ProductManager | 333 | 1 | 1 | 1 | INCOMPLETO · órfão |
| search/AIVisibilityEngine | 438 | 2 | 3 | 7 | MOCK · órfão |
| security/SecurityManager | 553 | 3 | 3 | 3 | INCOMPLETO (auth real, MFA fixo, sem uso) · no caminho (só regex) |
| simulation/OrganizationalSimulator | 566 | 2 | 70 | 8 | MOCK · órfão |
| ux/AdaptiveInterface | 332 | 2 | 0 | 0 | INCOMPLETO · órfão |
| ux/AttentionEconomy | 235 | 2 | 0 | 1 | INCOMPLETO · órfão |

*(Muitos `Math.random` servem só para gerar ids, por exemplo `` `x_${Date.now()}_${Math.random()...}` ``. Só contam como simulação quando fabricam valores, como em `HorizontalAgents.ts:152` e `RepositoryManager.ts:159`.)*

---

## Limites desta fase

- As classificações INCOMPLETO sem linha citada herdam a leitura do `CORE-MAPPING.md`, confirmada aqui só pelo sinal automático (presença de `Map`s). Não reli linha a linha os 19 módulos. As afirmações que o brief pediu explicitamente (HitlManager, Orchestrator) foram lidas por inteiro.
- "Órfão funcional" é por alcançabilidade estática (grep de chamadores). Não houve execução em runtime com Postgres e Redis.
