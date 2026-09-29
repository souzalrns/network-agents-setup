# AUDIT-COMPLETO — `network-agents-setup`

> **Base auditada:** commit `3dc3b25` (`main`). **Branch da auditoria:** `claude/audit-completo`. **Data:** 2026-09-29.
> **Âmbito:** só leitura, verificação e prescrição. Nenhum ficheiro fora de `docs/audit/` foi alterado.
> **Ambiente de verificação:** clone Linux do GitHub (Node 22, pnpm 8.15.9, Python 3.11 em venv isolada); execuções de teste e sondas numa scratchpad fora do repo; `SELECT`s read-only no Supabase `agent-network-memory`; leitura read-only do repo irmão `agent-network-mcp`.

---

## Resumo executivo

**O que o projecto é hoje.** Um monorepo com **dois runtimes que não se falam**:

| Runtime | O que é | Estado |
|---|---|---|
| **Motor Python** (`runner/plan_runner`, ~3.2k LOC) | Executa planos YAML com gates humanos, auditoria e retoma | **Funciona e está testado** (195/195), mas não executa trabalho nenhum sozinho: entrega cada passo a um "worker externo" que não existe no repo |
| **Plataforma TypeScript** (`apps/api` + 8 pacotes, ~19.5k LOC, 12.7k só no `core`) | Router → Planner (LLM) → Executor | **Não chega ao LLM**: todos os pedidos são bloqueados na deliberação por um erro de escala. Atrás desse bloqueio há mais três quebras |

Além disso: **226 documentos de desenho e auditoria**, **67 skills** e **35 agentes em markdown**.

**O que está ligado de facto.**

- **Motor Python:** `stub`, `external`, HITL por ficheiros, retoma, LangGraph com checkpoints, memória de cliente (só leitura), pesquisa de eventos.
- **Superfície MCP do motor:** stdio.
- **Ingestão RAG:** escreve 110 chunks no Supabase em cada push.
- **Autenticação HTTP:** fail-closed.
- **CI:** TS e Python verdes, sem vulnerabilidades npm.

**O que está morto ou só no papel.**

- **Mortos:** `apps/web`, `packages/langgraph` e `tests/package.json`.
- **Build de produção TS inexistente:** `pnpm build`/`Dockerfile` falham; o `k8s/` descreve um deploy que nunca existiu.
- **Workflow `keep-alive`:** falhou em todos os 5 runs.
- **Core:** 18 dos 31 módulos que o orquestrador instancia são órfãos (6 039 LOC).
- **Ferramentas externas:** 45 referidas nos docs, **0** em código.

**Lacunas críticas.**

| # | Lacuna | Achado |
|---|---|---|
| 1 | Não há maestro: dois orquestradores sem ponte, e o único router real vive noutro repo | AU-07 |
| 2 | O RAG ingere para `knowledge_chunks_t6` e o retrieve lê `knowledge_chunks` | AU-19 |
| 3 | Os tokens nunca são contados, por isso o objectivo n.º 1 da visão não tem instrumento | AU-16/L8 |
| 4 | A memória L4 tem zero código | S29 |
| 5 | O HITL TS é volátil e não tem retoma | AU-18 |
| 6 | Nenhum agente corre sozinho | L9 |
| 7 | Financeiro, jogos e segurança não existem como áreas; "jogo" é encaminhado para um domínio com 0 agentes | AU-35/AU-30 |

**O que falta para ter "pernas".** Primeiro, **três decisões**:

1. qual é o maestro;
2. qual é a tabela canónica do RAG;
3. como se implementa a memória L4.

Depois, **quatro construções pequenas**:

1. um worker de custo zero para o modo `external`;
2. um ledger de tokens com orçamento aplicado;
3. um registo único de áreas;
4. um teste end-to-end no CI.

Com isto, os nichos (trader, jogos, segurança) passam a ser **conteúdo** (agentes, skills, tools por área) e deixam de ser infraestrutura por construir.

---

## As fases

| Fase | Documento | Em 1–2 linhas | Commit |
|---|---|---|---|
| 1 | [AUDIT-1-estrutura.md](./AUDIT-1-estrutura.md) | 2 runtimes sem ponte; 3 unidades mortas; build TS verificado como quebrado (`TS6059`); duplicações de ingestão, LangGraph e MCP; 13 retificações (R1–R13) | `fb1ba73` |
| 2 | [AUDIT-2-cadeia.md](./AUDIT-2-cadeia.md) | Cadeia `/chat` seguida e **executada por sonda**: bloqueada na deliberação (Q1); depois Q2–Q4; `toolsAllowed` confirmado sem fonte; motor Python corrido de facto; RAG partido confirmado no Supabase | `96aa9ec` |
| 3 | [AUDIT-3-agentes.md](./AUDIT-3-agentes.md) | 24 agentes na config (8 inalcançáveis, 22 sem prompt); 35 `.agent.md` (12 alcançáveis); 27 de marketing desenhados (não 23); 4 taxonomias de áreas; necessidades por nicho | `dcca4d0` |
| 4 | [AUDIT-4-modulos.md](./AUDIT-4-modulos.md) | `CORE-MAPPING` com 2 erros confirmados (Orchestrator não é MOCK; SecurityManager corrigido depois); HitlManager em `Map` confirmado; 18 órfãos funcionais | `ec3b637` |
| 5 | [AUDIT-5-itens.md](./AUDIT-5-itens.md) | ~175 itens, cada um com estado verificado; 4 "Done" só no papel (C8, keep-alive, S33, S15b); 50 achados novos (AU-01…AU-50) | `e3cc0ee` |
| 6 | [AUDIT-6-lacunas.md](./AUDIT-6-lacunas.md) | 10 lacunas estruturais; 12 retificações priorizadas; 12 inclusões; ligações por área (L/D/N); inventário de ~30 ferramentas pendentes | `b2ae5e9` |

---

## 7.1 Atribuição — critérios e justificação `[PEDIDO]`

A coluna "Quem" de cada item está nas tabelas da Fase 5. Estes são os critérios usados, aplicados de forma conservadora (na dúvida, DEV):

| Atribuição | Critério | Exemplos |
|---|---|---|
| **CLAUDE** | Correcção local, verificável por teste ou leitura, sem nova dependência de produção, sem decisão de produto, sem credenciais | AU-14/15/16/17 (bugs com correcção óbvia), AU-08 (`.env.example`), AU-09 (CI), AU-28, AU-31, AU-32, AU-37, AU-45/46 (docs) |
| **DEV** | Exige decisão de produto ou arquitectura, credenciais/acesso (secrets, SSH, consolas), dados reais, ou aprovação de dependência | AU-07 (maestro), AU-33 (áreas), AU-35 (escopo dos nichos), AU-47 (secrets GitHub), S20/S27 (VM), S29 (L4), M5 (lista de módulos), EX-C3/C4 |
| **AMBOS** | O DEV decide ou dá acesso, e a execução é mecânica para o Claude | AU-13 (política de HITL + correcção de escala), AU-19 (tabela canónica + RPC), AU-23 (escolha do LLM + worker), M6 (spec do provider), AU-01 (tsconfig, só se o TS ficar) |

**Casos que merecem justificação:**

- **AU-13 é AMBOS, não CLAUDE.** A correcção técnica é trivial (escala 0–10), mas *que pedidos devem exigir aprovação humana* é política de produto. Se o Claude corrigisse sozinho, podia tirar um gate que o DEV quer manter.
- **AU-14 é CLAUDE**, apesar de precisar de Postgres para ser verificado de ponta a ponta: o CI já tem Postgres com pgvector (`ci.yml`, serviço `postgres`).
- **AU-47 é DEV**, porque as secrets do GitHub só o dono do repo as define. A tabela `keepalive` pode ser criada pelo Claude com SQL versionado, mas só depois de o DEV confirmar o projecto Supabase.
- **Os grupos G–J ficam em DEV.** São decisões de escopo, e o próprio `OPEN-ITEMS.md:55` diz para não executar antes de A–F.

**Contagem (itens abertos):** achados AU = CLAUDE **25** · DEV **11** · AMBOS **14** (contagem exacta). Itens abertos do STATUS/EX sem G–J ≈ CLAUDE 11 · DEV 34 · AMBOS 12 (contagem manual). Grupos G–J (~45 linhas) = todos DEV. Os fechados não entram.

---

## 7.2 Índice-mestre `[PEDIDO]`

Colunas: ID | título | estado | tipo | severidade | quem | evidência. As linhas completas, com "o que falta" e o bloqueio, estão na **AUDIT-5**.

### Achados novos (AU)

| ID | Título | Estado | Tipo | Sev. | Quem | Evidência |
|---|---|---|---|---|---|---|
| AU-01 | Build TS de produção não funciona | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | AUDIT-1 §1.4 |
| AU-02 | Dockerfile quebrado; k8s só no papel | NÃO INICIADO | BUG | Média | DEV | `Dockerfile:5-6,22` |
| AU-03 | `apps/web` morto | MORTO | FALTA-DECIDIR | Baixa | AMBOS | `Dashboard.tsx:3,15` |
| AU-04 | `packages/langgraph` morto | MORTO | FALTA-DECIDIR | Baixa | AMBOS | AUDIT-1 §1.1 |
| AU-05 | `tests/package.json` órfão (gera PRs Dependabot) | MORTO | BUG | Baixa | CLAUDE | `pnpm-workspace.yaml:2-3` |
| AU-06 | Duas pipelines de ingestão | EM CURSO | FALTA-DECIDIR | Alta | DEV | AUDIT-1 §1.2 |
| AU-07 | Dois orquestradores sem ponte; maestro por escolher | NÃO INICIADO | FALTA-DECIDIR | **Crítica** | DEV | AUDIT-3 §3.4 |
| AU-08 | `.env.example` incompleto | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE | AUDIT-1 R12 |
| AU-09 | CI Python ignora os testes lentos | NÃO INICIADO | FALTA-TESTE | Média | CLAUDE | `pytest.ini:4` |
| AU-10 | `skills/claude` sem proveniência | NÃO INICIADO | DOC-ERRADO | Baixa | CLAUDE | AUDIT-1 |
| AU-11 | Schema RAG em dois sítios | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | `schema.prisma:138` |
| AU-12 | STATUS de 95 KB / docs pesados | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS | AUDIT-1 R10 |
| AU-13 | Deliberação bloqueia 100% dos pedidos | NÃO INICIADO | BUG | **Crítica** | AMBOS | AUDIT-2 Q1 |
| AU-14 | `update` sem `create` (P2025) | NÃO INICIADO | BUG | **Crítica** | CLAUDE | `Executor.ts:54` |
| AU-15 | `finalOutput` vazio | NÃO INICIADO | BUG | Alta | CLAUDE | `Executor.ts:44` |
| AU-16 | Tokens nunca somados | NÃO INICIADO | BUG | Alta | CLAUDE | AUDIT-2 Q4 |
| AU-17 | Teste de integração falso-verde | NÃO INICIADO | FALTA-TESTE | Alta | CLAUDE | `ExecutionFlow.test.ts:47` |
| AU-18 | Sem retoma pós-HITL; polling em RAM | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | AUDIT-2 P14 |
| AU-19 | RAG: ingere t6, lê knowledge_chunks | NÃO INICIADO | BUG | **Crítica** | AMBOS | AUDIT-2 §2.4 |
| AU-20 | `toolsAllowed` sem fonte | NÃO INICIADO | FALTA-DECIDIR | Alta | AMBOS | AUDIT-2 §2.2 |
| AU-21 | Streaming só no papel | NÃO INICIADO | FALTA-CONSTRUIR | Baixa | CLAUDE | `Orchestrator.ts:385` |
| AU-22 | Campos de plano mortos | NÃO INICIADO | BUG | Média | CLAUDE | AUDIT-2 Y7–Y9 |
| AU-23 | Sem worker para `external` | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | AUDIT-2 Y6 |
| AU-24 | Regex anti-injecção com falsos positivos | NÃO INICIADO | BUG | Baixa | CLAUDE | `SecurityManager.ts:277` |
| AU-25 | MCP `moderate` sem chave | EM CURSO | FALTA-DECIDIR | Baixa | DEV | smoke Fase 2 |
| AU-26 | 8 agentes sem domínio inalcançáveis | NÃO INICIADO | BUG | Alta | AMBOS | AUDIT-3 A1 |
| AU-27 | 22/24 sem `systemPrompt` | NÃO INICIADO | FALTA-CONSTRUIR | Média | AMBOS | AUDIT-3 A2 |
| AU-28 | F1 profiles não ligado | NÃO INICIADO | BUG | Média | CLAUDE | AUDIT-3 A3 |
| AU-29 | `PUBLIC_MODE` só serve `legal` | NÃO INICIADO | BUG | Média | DEV | AUDIT-3 A5 |
| AU-30 | `software`/jogos sem agentes → erro | NÃO INICIADO | BUG | Alta | CLAUDE | `Router.ts:4` |
| AU-31 | Resolução agente↔skill por nome | NÃO INICIADO | BUG | Média | CLAUDE | AUDIT-3 A7/A8 |
| AU-32 | `design-flow.plan.yaml` sem `vertical` | NÃO INICIADO | BUG | Baixa | CLAUDE | AUDIT-3 A9 |
| AU-33 | 4 taxonomias de áreas | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV | AUDIT-3 §3.4 |
| AU-34 | Router por primeiro match | NÃO INICIADO | BUG | Média | CLAUDE | `Router.ts:10` |
| AU-35 | Nichos sem área nem agentes | NÃO INICIADO | FALTA-CONSTRUIR | Alta | DEV | AUDIT-3 §3.3 |
| AU-36 | 3 nomenclaturas de marketing | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS | AUDIT-3 §3.2 |
| AU-37 | `CORE-MAPPING` desactualizado | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE | AUDIT-4 §4.1 |
| AU-38 | 18 módulos órfãos + 3 timers | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | AUDIT-4 §4.4 |
| AU-39 | Import/export HITL sem chamadores | NÃO INICIADO | FALTA-LIGAR | Média | CLAUDE | AUDIT-4 §4.3 |
| AU-40 | Repos de memória órfãos + Redis | NÃO INICIADO | FALTA-DECIDIR | Baixa | AMBOS | AUDIT-4 §4.4 |
| AU-41 | `MCPServer` TS não montado | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | AUDIT-4 §4.4 |
| AU-42 | MFA fixo em código morto | NÃO INICIADO | BUG | Baixa | CLAUDE | `SecurityManager.ts:239` |
| AU-43 | `getHitlStats` MOCK | NÃO INICIADO | BUG | Baixa | CLAUDE | `ExecutionService.ts:96` |
| AU-44 | Análise de reels sem template nem ponte | NÃO INICIADO | FALTA-LIGAR | Média | AMBOS | `STATUS.md:239-240` |
| AU-45 | Colisões de IDs | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE | `STATUS.md:104` vs `:305` |
| AU-46 | `OPEN-ITEMS.md` desactualizado | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE | `OPEN-ITEMS.md:32-54` |
| AU-47 | keep-alive 5/5 falhados | NÃO INICIADO | BUG | Alta | DEV | Runs #1–#5 |
| AU-48 | `query_database` SQL arbitrário (= A4) | EM CURSO | BUG | Média | CLAUDE | `ToolPolicy.ts:51` |
| AU-49 | Orçamento de tokens não aplicado | NÃO INICIADO | FALTA-CONSTRUIR | Alta | CLAUDE | `Orchestrator.ts:273` |
| AU-50 | `agent_id` composto no t6 | NÃO INICIADO | BUG | Baixa | CLAUDE | SELECT |

### Itens existentes em aberto (STATUS + EX)

| ID | Título | Estado | Tipo | Sev. | Quem | Evidência |
|---|---|---|---|---|---|---|
| S29 | Memória L4 | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV | grep vazio |
| M6 (=EX-B13) | GeminiProvider + Planner | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | `LLMService.ts:98` |
| M4 (=EX-B6) | HITL durável Postgres | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | `STATUS.md:76` |
| M3 (=EX-B5) | e2e HITL Py→Node→Py | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS | `STATUS.md:75` |
| EX-B3 | `apps/api` contra infra real | NÃO INICIADO | FALTA-TESTE | Alta | AMBOS | Previsão: falha em AU-13 |
| EX-C2 | TS vs Python MCP | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV | = AU-07/41 |
| S20 | Chave antiga na VM Oracle | NÃO INICIADO (não verificável) | BUG | Alta | DEV | `STATUS.md:41` |
| B3 / B4 | Trading / gamedev | NÃO INICIADO | FALTA-CONSTRUIR | Alta | DEV | 0 ficheiros |
| D6 | `max_cost_usd` | NÃO INICIADO | FALTA-CONSTRUIR | Alta | CLAUDE | grep 0 |
| D5 / D7 | `model_tier`; dashboards reais | NÃO INICIADO | FALTA-CONSTRUIR/LIGAR | Média | CLAUDE | grep 0 |
| EX-B7 | Expor langgraph/edit no MCP | NÃO INICIADO | FALTA-LIGAR | Média | CLAUDE | `tools_impl.py:69` |
| E1–E7 | Conectores de ingestão | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS | 0 deps |
| A9 | Lockfile Python | NÃO INICIADO | FALTA-CONSTRUIR | Média | AMBOS | 0 lockfiles |
| A13 | RBAC | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | 0 chamadas |
| B2b / B2c | Ferramentas de segurança / triagem | EM CURSO | FALTA-TESTE / FALTA-DECIDIR | Média | AMBOS | `STATUS.md:28-29` |
| S24 | Cobertura TS restante | EM CURSO | FALTA-TESTE | Média | CLAUDE | `STATUS.md:43` |
| M5 (=EX-B12) | Mover órfãos (lista = AU-38) | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | AUDIT-4 |
| M7 | Piloto real de marketing | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | — |
| S13 (=A23) | CORS | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | `server.ts:36` |
| S19 / S27 | Oracle (uso / limites) | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | `STATUS.md:40,45` |
| S32 / F7 | Descoberta entre agentes / PMO | NÃO INICIADO | FALTA-DECIDIR | Média | DEV | `STATUS.md:70,402` |
| D3 / D4 | DeepEval / Ragas | NÃO INICIADO | FALTA-TESTE | Média | DEV / AMBOS | `STATUS.md:88-89` |
| EX-C3 / EX-C4 / B16=G7 | AgentMesh / Cedar / receipts ADR-001 | NÃO INICIADO | FALTA-DECIDIR | Média/Baixa | DEV | `OPEN-ITEMS.md:51-52` |
| INIT-093 / INIT-094 | google/skills / harnesses | NÃO INICIADO | FALTA-DECIDIR | Média/Baixa | AMBOS/CLAUDE | `STATUS.md:158-177` |
| P6 | Multi-provider arquivado (contradiz M6) | OBSOLETO | DOC-ERRADO | Média | DEV | `STATUS.md:123` |
| B11 / B12 | Script `knowledge_sources` / `knowledge_log` | NÃO INICIADO / EM CURSO | FALTA-CONSTRUIR / DOC-ERRADO | Média/Baixa | CLAUDE | grep; SELECT |
| S5 | Consistência no CI (já feito, não fechado) | FECHADO-VERIFICADO | DOC-ERRADO | Baixa | CLAUDE | `ci.yml:103` |
| S14, S17, S21, S28, B1, B5, B6, G6, A1b, A12, A15, A19 | (ver AUDIT-5) | NÃO INICIADO / OBSOLETO | vários | Baixa | DEV/CLAUDE | AUDIT-5 §5.2, §5.4 |
| G1.1–G1.14, G2.1–G2.4, G3.x, G4.x, H1–H4, I1–I11, J1–J7 | Backlog de nichos e ferramentas | NÃO INICIADO / OBSOLETO (J) | FALTA-DECIDIR | Baixa–Alta | DEV | `EXECUTION-PROMPTS.md:1618-2428` |

### "Done" reverificados

| Grupo | IDs | Estado |
|---|---|---|
| **Só no papel** | **C8, keep-alive, S33, S15b** | **FECHADO-SÓ-NO-PAPEL** |
| Verificados | S1, S2a, S2b-1..3, S3, S4, S4b, S6a, S7, S8, S9, S10\*, S11\*, S12, S15a, S18, S22, S23, S30, S31, S34\*, S35, S36, M1, M2\*, M8, B2\*, B7, B8, B9, B10, B13\*, B14, B15, B17\*, B18, C1, C2, C5, C8a-1, C8a-2, C8b, C8c, C8d, C8e\*, G2, G3, G4, G5, G-skill-1..5\* | FECHADO-VERIFICADO (\* = com ressalva registada na AUDIT-5 §5.3) |
| Não verificáveis daqui | S16, C3, C6, C7 | FECHADO — NÃO VERIFICÁVEL |

---

## 7.3 PRIORIDADES — top 10 `[PEDIDO]`

Ordenadas pelo que desbloqueia mais da visão com menos esforço. As decisões vêm antes da construção.

| # | O quê | Porquê agora | Itens | Quem |
|---|---|---|---|---|
| 1 | **Decidir o maestro** (ADR: Python + worker, TS desbloqueado, ou router do MCP) | Tudo o resto (delegação, nichos, HITL, tools) depende desta escolha | AU-07, EX-C2, AU-41 | **DEV** (Claude redige o ADR com as 3 opções e os custos) |
| 2 | **Consertar o RAG**: tabela canónica + retrieve que a lê + teste ingest→retrieve | O conhecimento ingerido hoje é inacessível; é a base do grounding (menos tokens) | AU-19, AU-11, AU-06, B11 | **AMBOS** |
| 3 | **Keep-alive**: secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` + tabela `keepalive` | Risco operacional imediato (pausa do Supabase), e é barato | AU-47, S15b | **DEV** (secrets) → CLAUDE (SQL/verificação) |
| 4 | **Medir tokens**: somar por passo, persistir num ledger, aplicar orçamento | Sem medição, o objectivo n.º 1 é inverificável | AU-16, AU-49, D6, D5 | **CLAUDE** |
| 5 | **Provider de custo zero** (Gemini) | Premissa "custo zero"; hoje só OpenAI; reconciliar com o P6 arquivado | M6, P6 | **AMBOS** |
| 6 | **Worker do modo `external`** (lê `request.json`, chama o LLM barato, escreve `result.json`, respeita HITL e orçamento) | Sem ele nenhum agente Python corre sozinho; se o maestro for Python, é a peça central | AU-23 | **AMBOS** |
| 7 | **Registo único de áreas** + router com confiança e fallback | Pré-requisito da delegação por área e dos 3 nichos | AU-33, AU-34, AU-26, AU-30 | **DEV** desenha → **CLAUDE** implementa |
| 8 | **Se o TS ficar:** corrigir Q1–Q4 e o teste falso-verde, e só depois correr o EX-B3 | 5 correcções pequenas que tornam o `/chat` testável | AU-13, AU-14, AU-15, AU-17, EX-B3 | **CLAUDE** (AU-13: AMBOS) |
| 9 | **Decidir a memória L4** (in-house pelo contrato vs mem0, que o utilizador testou) | "Memória persistente" é pilar; a decisão está bloqueada desde 09-20 | S29, L6 | **DEV** |
| 10 | **Teste e2e no CI** (TS `/chat` + testes lentos Python + ingest→retrieve) | Impede que as quebras voltem sem ninguém notar | L1, AU-09, AU-17 | **CLAUDE** |

**Fora do top 10, mas urgente operacionalmente:** S20 (chave antiga na VM Oracle; o bridge-worker falha com 401) e S27 (limites do Oracle Free Tier). São DEV, fora do código.

**Barato e com retorno imediato em tokens de bootstrap:** AU-45, AU-46, AU-37 e AU-12 (higiene de docs). CLAUDE, cerca de 1–2 h.

---

## 7.4 MELHORIAS ACRESCENTADAS PELO AUDITOR `[PEDIDO]`

Secções e verificações que o brief não pedia, acrescentadas por terem valor real:

| O quê | Onde | Porque acrescentei |
|---|---|---|
| **Verificação do build de produção** (`tsc` por pacote → `TS6059`) | AUDIT-1 §1.4 | Decide se o TS é deployável; mudou a prioridade de R4/R5/R8 |
| **Sondas de execução** do pipeline `/chat` (fora do repo, LLM/HITL mockados) | AUDIT-2 Q1, Q5 | Transformou "parece bloqueado" em "bloqueado, com output real"; descobriu que o teste de integração é falso-verde |
| **Motor Python corrido de facto** (stub native/langgraph, external, resume, smoke MCP) | AUDIT-2 §2.3, §2.5 | Separar "está no código" de "funciona" |
| **Cadeia RAG verificada ao vivo** (SELECT de contagens, definição das RPCs) | AUDIT-2 §2.4 | Encontrou a quebra mais grave para a visão (AU-19), invisível a qualquer leitura de um só repo |
| **Datação git das contradições** (`git log -S`, ordem de commits) | AUDIT-2 Q1-origem; AUDIT-4 §4.1 | Distingue "classificação errada desde o início" de "documento que ficou para trás" |
| **Script de resolução agente↔skill** sobre os 58 steps dos 12 templates | AUDIT-3 §3.3 | Mediu a delegação Python real (12/35 alcançáveis; 7 lacunas de nome) |
| **Condições que nunca se tornam verdadeiras** (tabela) | AUDIT-2 §2.6 | Generaliza o caso `toolsAllowed` pedido para todo o caminho |
| **Varrimento completo do core** com classificação corrigida + alcançabilidade | AUDIT-4 §4.5 | Base objectiva para M5/AU-38 (substitui a lista "~14" desactualizada) |
| **Runs reais do GitHub Actions** | AUDIT-5 | Descobriu o keep-alive 5/5 falhado e o ruído Dependabot do `tests/package.json` |
| **Reverificação de todos os "Done"** com evidência própria | AUDIT-5 §5.3 | O brief pedia "Done ≠ funciona"; 4 caíram para "só no papel" |
| **Colisões de IDs** entre documentos (e dentro do STATUS) | AUDIT-5 AU-45 | Risco real de decidir sobre o item errado (ex.: "B3") |
| **Checklist de segurança de 20 itens reverificada** | AUDIT-5 §5.5 | Duas notas erradas (#10 "Supabase Auth", #13 sem excepção `query_database`) |
| **Lacunas L7–L10** (maestro inexistente, tokens não medidos, nenhum agente corre sozinho, infra frágil) | AUDIT-6 §6.1 | São as lacunas que mais pesam na visão, e não estavam na lista do brief |
| **Resolução de "Deep Hardness Obsidian"** (sem correspondência; 2 candidatos com evidência) | AUDIT-6 §6.5 | Não inventar; mostrar o que existe |
| **Conflito mem0 vs. decisão registada** (FASE4 "não adoptar") | AUDIT-6 §6.5 | O utilizador está a testar algo que o próprio repo desaconselhou; precisa de decisão consciente |
| **Correcção do "23 agentes de marketing"** → 27 desenhados / 17 / 11 / 3 | AUDIT-3 §3.2 | Correcção de classificação pedida pelo brief ("correcções onde o inventário esteja errado") |

---

## Fases divididas e pontos NÃO VERIFICÁVEIS

**Nenhuma fase foi dividida.** Todas couberam num documento. As tabelas longas da Fase 5 foram organizadas em 5 secções (5.1–5.5), mas é o mesmo ficheiro.

**NÃO VERIFICÁVEL daqui** (requer acesso que esta sessão não tem):

| Ponto | Requer |
|---|---|
| Q2/AU-14 contra Postgres real (conclusão por semântica documentada do Prisma) | BD Postgres |
| Build `docker`/`docker-compose` | Docker |
| S16 (disco Windows), S20/S27 (VM Oracle), S21 (screenshots), C6 (Vercel), C3/C7 (conteúdo no repo MCP além do `route.js`) | Máquina local, SSH, consolas |
| RLS das tabelas (checklist #4) | Não relido nesta auditoria |
| G–J item a item | Só os títulos foram inventariados |
| Contagem de agentes de produção do MCP | Veio de um doc gerado a 2026-08-19, não do `lib/agents.js` actual |

---

## Estado git no fecho

- **Commits desta auditoria** (branch `claude/audit-completo`): `fb1ba73`, `96aa9ec`, `dcca4d0`, `ec3b637`, `e3cc0ee`, `b2ae5e9` e o commit deste ficheiro ("audit: completo consolidado").
- **Ficheiros alterados:** só os 7 em `docs/audit/`. Nenhum ficheiro fora de `docs/audit/` foi modificado (os artefactos temporários do `tsc` foram removidos e confirmados com `git status` limpo antes de cada commit).
