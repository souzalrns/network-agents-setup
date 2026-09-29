# DECISÃO 1 — Dois runtimes ou um?

> **Base:** commit `3dc3b25` + auditoria Fase 1 (`AUDIT-*.md`, branch `claude/audit-completo`). **Data:** 2026-09-29.
> **Natureza:** análise para decisão. Nada foi implementado nem corrigido.
> **Evidência nova desta secção** (além da Fase 1):
> - leitura read-only de `agent-network-mcp` `origin/main` (`024e0ee`): `lib/agentRuntime.js`, `app/api/mcp/route.js`;
> - `SELECT` read-only na tabela `code_tasks` (Supabase `agent-network-memory`);
> - contagem de testes TS por ficheiro;
> - LOC das peças TS com valor.

## Resumo

O **Python** é o runtime mais maduro para a visão. Tem memória, RAG, HITL durável, 195 testes com e2e e já usa Gemini. Falta-lhe um planeador dinâmico, um cliente LLM e tools.

O **TypeScript** tem as peças que faltam ao Python: Planner/Router por LLM, tool-calling, `SsrfGuard`/`ToolPolicy` e API HTTP. Mas estão em ~2,3k LOC dentro de ~19,5k, e o caminho está bloqueado (Q1–Q4). Nenhum consumidor usa a API hoje.

Há **um terceiro runtime** que a Fase 1 só tocou: o `agent-network-mcp`, em JavaScript, que tem o **único router LLM em produção** e um padrão de worker por fila (`code_tasks`).

**Recomendação provisória: VIA A (consolidar em Python), trazendo ~1,2k LOC do TS.** Depende de 4 perguntas ao humano (secção 1.3), sobretudo *quem chama o sistema* e *onde corre*.

---

## 1.1 Estado real de cada runtime `[PEDIDO]`

### Python — `runner/plan_runner` (+ `mcp/plan_runner`, `scripts/ingest_*`)

| Aspecto | Facto | Evidência |
|---|---|---|
| **O que faz de facto** | Executa planos YAML (ordem por `depends_on`), gates humanos, auditoria `events.jsonl`, retoma; 2 engines (`native`, `langgraph` com `SqliteSaver`) | Corrido na Fase 2 (AUDIT-2 §2.3): `stub` → `paused_human_gate`; `resume --decision approve` → `done` |
| HITL | **Durável** (ficheiros `hitl-requests.jsonl`/`hitl-decisions.jsonl`) e retomável | `hitl.py`; run real escreveu `hitl-requests.jsonl` |
| RAG | Ingestão real em CI (Gemini 768d → `knowledge_chunks_t6`, 110 chunks); retrieve via MCP (tabela errada, AU-19) | `embedder.py:26,77`; `supabase_writer.py:3-12`; `ingest-knowledge.yml`; SELECT ao vivo |
| Memória | L2 (eventos por run); FTS por run (`session_search`); memória de cliente (`working_memory`, só leitura) | AUDIT-4 §4.3 |
| Superfície externa | MCP **stdio** com política (`authorize`, `sanitize_repo_path`, `rate_limit`, `audit`) | `mcp/plan_runner/mcp_plan_runner/policy.py:42,109,129,145`; smoke OK |
| Qualidade | **195/195** testes (incluindo 34 lentos, e2e); ruff; Codecov; gate de release | `pytest -m ""` (Fase 1); `runner-tests.yml`; `release.yml` |
| **O que falta** | (1) **Nenhum cliente LLM de geração** (só embeddings); (2) nenhum planeador dinâmico (o plano é escrito à mão); (3) **nenhum worker**: o modo `external` pára em `waiting_external`; (4) tools não aplicadas (`tools_allowed` é só informativo) | grep `openai\|anthropic\|generativelanguage` → só `embedder.py`; `executor.py:117-119`; `executor.py:37,79` |
| **Código morto/incompleto** | `max_replans`, `done_when`, `on_fail` e `knowledge_refs` ignorados; `max_steps` sem efeito no engine `langgraph` | AUDIT-2 Y7–Y9 |
| **O que tem de bom** | O desenho "governança primeiro" (`runner/README.md:13-17`), testes reais, custo zero já nos embeddings | — |

### TypeScript — `apps/api` + `packages/*`

| Aspecto | Facto | Evidência |
|---|---|---|
| **O que faz de facto** | Arranca Express com auth fail-closed, rate-limit, helmet e WebSocket; instancia 31 módulos. **Todo o pedido `/chat` pára na deliberação** | AUDIT-2 Q1 (sonda: 0 chamadas LLM) |
| Planner/Router | Router por palavras-chave (6 domínios); Planner que pede o plano ao LLM (JSON) com fallback | `Router.ts:2-18`; `Planner.ts:9-77` |
| Tool-calling | `ToolRegistry`/`ToolExecutor` com 5 conjuntos (db, filesystem, web, 2 jurídicos); `ToolPolicy`; `SsrfGuard`; `ActionReceipt` (hash encadeado); `McpAuth` | `apps/api/src/index.ts:44-51`; `packages/mcp/src/tools/*` |
| LLM | **Só `OpenAIProvider`** (omissão `gpt-4-turbo`), com function-calling corrigido (S33) | `LLMService.ts:98`; `index.ts:54-57` |
| Qualidade | 196 testes: **~125 sobre peças com valor** (tools, policy, SSRF, auth, Router, Planner, Executor, MCP) e **~71 sobre módulos órfãos/MOCK** (HitlManager 14, SecurityManager 9, Immunological 6, …); integração falso-verde | Contagem `it(` por ficheiro; AU-17 |
| **O que está quebrado** | Q1 deliberação; Q2 `update` sem `create`; Q3 `finalOutput` vazio; Q4 tokens não somados; **build de produção** (TS6059); HITL em RAM sem retoma | AUDIT-2; AUDIT-1 §1.4 |
| **Código morto** | 18 módulos órfãos (6 039 LOC); `packages/langgraph`; `apps/web` | AUDIT-4 §4.4; AUDIT-1 |
| **O que tem de bom** | Peças de segurança de tools testadas (`SsrfGuard` 10 testes, `ToolPolicy` 12, `web` 12); Planner LLM; API HTTP pronta a expor | Contagem de testes |
| Peças com valor (LOC) | ~2 319 LOC: `Executor` 366, `LLMService` 221, `DeliberationEngine` 182, `ToolPolicy` 161, jurídicos 282, `web` 131, `ActionReceipt` 116, `McpAuth` 102, `Planner` 102, `auth` 95, `SsrfGuard` 93, `filesystem` 90, `ToolExecutor` 82, … | `wc -l` |

### `[ACRESCENTADO PELO AUDITOR]` Terceiro runtime — `agent-network-mcp` (JavaScript, produção Vercel)

| Aspecto | Facto | Evidência |
|---|---|---|
| Router | **LLM real em produção**: Gemini (`gemini-flash-lite-latest` por omissão) classifica o pedido para 1 de 33 agentes; devolve `{agent\|null, reason}`; ~200 tokens de saída | `lib/agentRuntime.js:10,62-84` |
| Execução de agente | Estado por projecto (`project_state`) + RAG (`knowledge_chunks`, top-12, limiar 0.22) + directivas de concisão e grounding; grava `last_interaction` | `lib/agentRuntime.js:94-177` |
| Worker | Fila `code_tasks` + `bridge-worker.js` que corre `claude -p` numa máquina | `app/api/mcp/route.js` (`dispatch_code_task`/`check_code_task`) |
| Estado do worker | **28 `done` (US$ 7,01), 20 `error`, 2 presos em `running` desde 2026-09-05; última actividade a 2026-09-09.** Não é custo zero (Claude Code pago) e está parado | SELECT `code_tasks` |
| Nota de segurança | O `callGemini` põe a chave na query string (`?key=`) | `lib/agentRuntime.js:39` (o setup corrigiu o mesmo problema no `embedder.py`, A7) |

### Sobreposição (o que existe em duplicado)

| Capacidade | Python | TypeScript | JS (MCP) | Nota |
|---|---|---|---|---|
| Orquestração | `plan_runner` (plano estático) | `Orchestrator` (plano por LLM) | router + `runAgent` (1 agente) | 3 metades |
| Ingestão RAG | `scripts/ingest_*` (Gemini, CI) | `packages/scripts/src/ingest/*` (`openai`, manual) | `ingest_knowledge` (tool) | 3 caminhos, 2 tabelas |
| Retrieve RAG | `mcp_knowledge.py` → MCP | — | `retrieveKnowledgeHits` | Lê `knowledge_chunks`, não o t6 |
| Política de tools | `policy.py` (MCP stdio) | `ToolPolicy.ts` | Zod `.strict()` + `withAuth` | 3 implementações do mesmo padrão |
| Superfície MCP | `mcp/plan_runner` (stdio, **real**) | `MCPServer.ts` (**não montado**) | `route.js` (HTTP, **produção**) | — |
| HITL | ficheiros (durável) | `HitlManager` (RAM) | — | Ponte M2 sem chamadores |
| LangGraph | `langgraph_engine.py` (**real**) | `packages/langgraph` (**morto**) | — | — |
| "Dois `plan_runner`" | `runner/plan_runner` + `mcp/plan_runner` | — | — | **Não é duplicação**: o segundo é o wrapper MCP do primeiro (`tools_impl.py:15-16,69`) |

---

## 1.2 As vias possíveis `[PEDIDO]`

Os custos vêm em **LOC e testes** (medidos). Os esforços em dias são **estimativas do auditor, NÃO VERIFICADAS**, e servem só para comparar as vias entre si.

### VIA A — Consolidar em Python

| | Conteúdo |
|---|---|
| **Mantém** | `runner/plan_runner` inteiro, `mcp/plan_runner`, `scripts/ingest_*`, skills/agents `.md`, 195 testes, CI Python |
| **Migra do TS** (≈1,2k LOC + ~66 testes a reescrever) | Cliente LLM com tools (`LLMService` 221, **trocando OpenAI por Gemini**); lógica do `Planner` (102) e do `Router` (34); `web` + `SsrfGuard` (224); `ToolPolicy`/`ToolExecutor`/`ToolRegistry` (286, **parcialmente já coberto** por `policy.py`); `ActionReceipt` (116); opcional: `DeliberationEngine` (182, função pura) |
| **Constrói de novo** | Worker do modo `external` (AU-23); planeador dinâmico que gera `plan.yaml` (ou steps) a partir de um pedido |
| **Apaga/arquiva do TS** | `apps/api`, `apps/web`, `packages/*` (≈17k LOC), CI TS, `Dockerfile`/`k8s` |
| **Esforço (estimativa)** | Médio: ~1,2k LOC portados + worker + planeador |
| **Riscos** | (1) **Perde-se a API HTTP** — mas hoje não tem consumidor nem build (AU-01/AU-03); (2) perde-se o tool-calling OpenAI testado, que tem de ser refeito para Gemini; (3) perdem-se 71 testes, mas são de módulos órfãos; (4) o runner é **baseado em ficheiros** (`pilots/…`) e não em serverless, por isso precisa de uma máquina (VM) para correr como serviço — **NÃO VERIFICADO** se a VM Oracle o suporta (S27: limites reduzidos) |
| **Ganha** | Um só runtime, uma só pipeline de ingestão, HITL durável já pronto, L4 onde a síntese de memória já disse que devia viver (`FASE4-SINTESE.md:143`), custo zero alinhado com o Gemini já usado |

### VIA B — Consolidar em TypeScript

| | Conteúdo |
|---|---|
| **Mantém** | `apps/api`, `packages/core` (orchestrator + governance reais), `packages/mcp`, ~125 testes com valor |
| **Migra do Python** (≈4,3k LOC + 195 testes a reescrever) | `runner/plan_runner` (3 157), `mcp/plan_runner` (511), `scripts/ingest_*` (594); engine LangGraph → LangGraph.js (o `packages/langgraph` TS actual está morto e não serve de base) |
| **Constrói/corrige** | Q1–Q4; HITL durável (M4) e retoma (AU-18); `GeminiProvider` (M6); build de produção (AU-01) |
| **Apaga do Python** | Runner, MCP stdio, scripts de ingest, CI Python |
| **Esforço (estimativa)** | Alto: ~3,5× o volume da VIA A, mais a correcção das quebras |
| **Riscos** | (1) **Perdem-se 195 testes que passam**, incluindo o e2e do motor; (2) perde-se o checkpoint LangGraph Python (crash recovery com 3 cenários testados, `runner/README.md:52-54`); (3) reescrever ingestão e embeddings que já correm em CI; (4) a L4 desenhada para Python tem de ser redesenhada |
| **Ganha** | Uma linguagem igual à da produção (`agent-network-mcp` é JS), o que permite partilhar código com o router real; API HTTP e tool-calling já existentes |

### VIA C — Manter os dois

| | Conteúdo |
|---|---|
| **O que implica** | Definir quem chama quem. Hoje só se tocam por ficheiros HITL (M2, sem chamadores). Opções: TS como maestro (Planner) que despacha planos para o `plan_runner` (via MCP/fila); ou Python como motor e TS só como API/tools |
| **Custo de sincronia** | 2 árvores de dependências (npm + pip, e o Python sem lockfile, A9); 2 CIs; 2 clientes LLM; 2 políticas de tools (já existem 3); 2 schemas de HITL (M2 já teve de traduzir `approved↔approve`, `STATUS.md:74`); correcção de Q1–Q4 **e** worker **e** ponte |
| **Esforço (estimativa)** | O mais alto no total: tudo o que A e B fazem nas partes que mantêm, mais a ponte |
| **Riscos** | A duplicação já medida (tabela de sobreposição) agrava-se; é o estado actual, e foi ele que produziu as "peças reais desligadas" registadas em 5 auditorias (`STATUS.md:426`) |
| **Quando faz sentido** | Só se houver um consumidor real da API TS **e** necessidade do motor Python; hoje nenhum dos dois está provado |

### `[ACRESCENTADO PELO AUDITOR]` VIA D — O maestro na produção (JS), o motor em Python

| | Conteúdo |
|---|---|
| **Ideia** | O router Gemini do `agent-network-mcp` (já em produção) é o maestro; para tarefas multi-passo, despacha um plano para o `plan_runner` (fila como a `code_tasks`, mas com worker Gemini); o TS deste repo é descontinuado |
| **A favor** | Reaproveita o único router real; o padrão de fila já existe (28 tarefas feitas) |
| **Contra** | Contradiz a divisão registada (`ECOSYSTEM.md:9-10`: "setup = núcleo, MCP = plug-in"); acopla 2 repos; o worker actual custa dinheiro (US$ 7,01/28 tarefas) e está parado |
| **Estado** | Opção a avaliar, não recomendada sem decisão sobre o papel dos repos |

---

## 1.3 Recomendação fundamentada `[PEDIDO]`

### Pontuação por critério da visão (evidência, não opinião)

| Critério | Python | TypeScript | Evidência |
|---|---|---|---|
| **Custo zero** | ✅ já usa Gemini (embeddings, CI) | ❌ só OpenAI `gpt-4-turbo` | `embedder.py:26`; `index.ts:54-57` |
| **Memória persistente** | ✅ L2, FTS, memória de cliente; L4 desenhada para `runner/` | ⚠️ Prisma (repos órfãos); HITL em RAM | `FASE4-SINTESE.md:143`; AUDIT-4 |
| **Ingestão robusta** | ✅ pipeline em CI a escrever hoje | ⚠️ pipeline paralela manual (`openai`) | Runs ingest #127–#129 ✅ |
| **Redução de tokens** | ⚠️ não mede, mas `events.jsonl` por passo é o sítio natural para um ledger | ❌ não mede (Q4); `TokenEconomy` MOCK | AU-16; `layers.md:15-32` |
| **Maestro + delegação** | ❌ sem planeador dinâmico | ⚠️ Planner LLM real mas bloqueado; Router por palavras-chave | AUDIT-3 §3.4 |
| **HITL (pré-requisito do trader)** | ✅ durável e retomável | ❌ RAM, sem retoma | AUDIT-2 |
| **Tools seguras** | ⚠️ `policy.py`, sem tool web | ✅ `web`/`SsrfGuard`/`ToolPolicy` testados | Contagem de testes |
| **API HTTP** | ❌ só MCP stdio | ✅ mas sem consumidor nem build | AU-01, AU-03 |
| **Maturidade de testes** | ✅ 195 com e2e, gate de release | ⚠️ 196, dos quais ~71 em órfãos; integração falso-verde | AU-17 |

**Leitura:** o Python ganha em 6 critérios e o TS em 3: tools, API e, marginalmente, maestro (o Planner LLM existe, mas está bloqueado; o Python não tem planeador). As vantagens do TS são **portáveis** (~600 LOC de tools/política + ~140 de Planner/Router). As do Python não o são sem reescrever ~4,3k LOC e 195 testes.

**Recomendação provisória: VIA A**, com migração selectiva das ~1,2k LOC do TS listadas na VIA A e arquivo do resto do TS (não apagar sem ADR).

### Perguntas que o humano tem de responder antes de fechar

| # | Pergunta | Porque muda a decisão |
|---|---|---|
| Q1 | **Quem vai chamar o sistema?** (tu no IDE via MCP stdio? o `agent-network-mcp` em produção? uma app/frontend? clientes externos por HTTP?) | Se houver um consumidor HTTP real, a VIA A precisa de uma camada HTTP (ou a VIA C/D ganha peso). Hoje não há nenhum (AU-03) |
| Q2 | **Onde corre o motor em regime de serviço?** (VM Oracle? PC local? serverless?) | O `plan_runner` escreve em disco (`pilots/`); serverless (Vercel) não serve. A VM tem limites novos (S27, **NÃO VERIFICÁVEL daqui**) |
| Q3 | **O `agent-network-mcp` continua a ser a porta de entrada de produção?** | Se sim, a VIA D (maestro lá) evita duplicar o router; se não, o maestro nasce aqui |
| Q4 | **O código de governança TS (18 módulos órfãos) tem valor de roadmap para ti?** | Na VIA A é arquivado; se é roadmap activo, pesa a favor da C |

---

## 1.4 Impacto nas prioridades da Fase 1 `[PEDIDO]`

| Prioridade (Fase 1) | VIA A (Python) | VIA B (TS) | VIA C (os dois) | VIA D (maestro MCP) |
|---|---|---|---|---|
| **#1 Maestro** | Construir o planeador/router em Python (portar `Planner` 102 + `Router` 34 + registo de áreas) | Corrigir Q1–Q4 e dar áreas ao Router | Decidir quem manda **e** construir a ponte TS↔Py | Reusar o router Gemini de produção; só falta o despacho para o `plan_runner` |
| **#2 RAG** (AU-19) | **Simplifica**: o Python já tem `DATABASE_URL`/psycopg (`supabase_writer.py:46`); o retrieve pode ler o t6 directamente, sem passar pelo MCP | Retrieve novo em TS + escolher a pipeline de ingestão (a TS usa `openai`) | Corrigir nos dois lados | Nova RPC no Supabase que leia o t6 (ou unificar tabelas), consumida pelo MCP |
| **#6 Worker externo** (AU-23) | **Sobe para #2**: é o que faz o motor executar | **Desaparece**: o Executor TS chama o LLM directamente | Necessário para a metade Python | Existe o padrão (`code_tasks`), mas é pago e está parado; precisa de versão Gemini |
| #4 Medir tokens | Ledger no `events.jsonl`/Supabase a partir do worker | Corrigir Q4 + ledger | Duas implementações | Ledger no `runAgent` do MCP (hoje também não mede: ignora `usageMetadata`, `agentRuntime.js:56-59`) |
| #5 Provider custo zero | Cliente Gemini novo no worker | `GeminiProvider` (M6) | Os dois | Já é Gemini |
| #8 Corrigir o `/chat` TS | **Deixa de ser necessário** (arquivado) | Obrigatório e prioritário | Obrigatório | Deixa de ser necessário |

---

## Limites desta secção

- Os esforços são estimativas do auditor; **só os LOC e as contagens de testes foram medidos**.
- A capacidade da VM Oracle para correr o motor como serviço é **NÃO VERIFICÁVEL daqui** (requer consola/SSH).
- A VIA D assume que o `agent-network-mcp` pode chamar um serviço fora do Vercel. **NÃO VERIFICADO** (não relida a config de rede nem as funções do Vercel).
