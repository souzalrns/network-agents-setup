# AUDIT-5 — Inventário de itens: fechado, aberto, morto

> **Base:** commit `3dc3b25`. **Data:** 2026-09-29.
> **Fontes:** `docs/initiatives/STATUS.md` (468 linhas, lido por inteiro), `docs/initiatives/OPEN-ITEMS.md` (86 linhas, lido por inteiro), títulos dos grupos G–J de `EXECUTION-PROMPTS.md`, e os achados das Fases 1–4 desta auditoria.
> **Verificações de apoio feitas nesta fase:**
> - suite Python completa (`pytest -m ""`): **195/195** em 1m45s;
> - suite TS: **196/196** (Fase 2);
> - `pnpm audit`: **0 vulnerabilidades**;
> - runs do GitHub Actions no `main`: CI #387 ✅, ingest #129 ✅, **keep-alive 5/5 ❌**;
> - `SELECT`s read-only no Supabase;
> - leitura read-only do `origin/main` do `agent-network-mcp` para S12/C5.

## Resumo

**~175 itens inventariados:** 96 IDs do `STATUS.md`, os itens do `OPEN-ITEMS.md` e dos grupos G–J do `EXECUTION-PROMPTS.md`, os 20 da checklist de segurança e **50 achados novos (`AU-01…AU-50`)**.

**Dos itens "Done" reverificados, 4 estão FECHADOS-SÓ-NO-PAPEL:**

| Item | Porquê |
|---|---|
| **C8** | O retrieve não lê o que é ingerido |
| **keep-alive** | Falhou em todos os runs |
| **S33** | As tools continuam sem chegar a um LLM |
| **S15b** | Afirma que o keep-alive funciona |

**Os 5 achados novos mais graves:**

| Achado | O que é | Sev. |
|---|---|---|
| AU-13 | A deliberação bloqueia todos os pedidos | Crítica |
| AU-14 | `update` sem `create` | Crítica |
| AU-19 | RAG com tabelas trocadas | Crítica |
| AU-07 | Dois maestros sem ponte | Crítica |
| AU-47 | Keep-alive morto | Alta |

**O `OPEN-ITEMS.md` está desactualizado** (AU-46): ainda dá como abertos S11, S15a, S12 e M8. E há **colisões de IDs** entre documentos (AU-45).

---

## Convenções

- **Série do ID:** `S*`/`M*`/`B*`/`C*`/`G*`/`P*`/`D3`/`D4` sem prefixo = série do `STATUS.md`. **`EX-`** = série de `EXECUTION-PROMPTS.md`/`OPEN-ITEMS.md`, **quando colide** com um ID do STATUS de significado diferente (ex.: `B3` = "agente de trading" no STATUS, `EX-B3` = "correr `apps/api` contra infra real"). **`AU-nn`** = achado novo desta auditoria.
- **Estado:** FECHADO-VERIFICADO · FECHADO-SÓ-NO-PAPEL · EM CURSO · NÃO INICIADO · MORTO · OBSOLETO. Para itens fechados cuja prova está noutra máquina ou repo: "FECHADO — NÃO VERIFICÁVEL daqui".
- **Quem:** CLAUDE · DEV · AMBOS (DEV decide ou dá acesso, Claude executa). Critério conservador: na dúvida, DEV. A justificação está na Fase 7.
- **Tipo:** BUG · FALTA-LIGAR · FALTA-DECIDIR · FALTA-CONSTRUIR · DOC-ERRADO · FALTA-TESTE. "—" quando fechado.

---

## 5.1 Achados novos desta auditoria (`AU-*`) `[PEDIDO: "novo ID para achados sem ID"]`

| ID | Título | Estado | O que falta fazer | Tipo | Sev. (porquê) | Bloqueio | Quem | Evidência |
|---|---|---|---|---|---|---|---|---|
| **AU-01** | Build TS de produção não funciona | NÃO INICIADO | Criar `tsconfig.json` por pacote (ou project references) com `rootDir`/`outDir` próprios; validar `pnpm build` + `node apps/api/dist/index.js` | FALTA-CONSTRUIR | **Alta** — nenhum artefacto deployável | nada | AMBOS | AUDIT-1 §1.4 (TS6059) |
| **AU-02** | `Dockerfile` quebrado; `k8s/` descreve deploy inexistente | NÃO INICIADO | Decidir se há deploy TS; se sim, corrigir `COPY`/`CMD` (depende de AU-01) e criar pipeline de imagem; se não, mover para `deploy/_templates/` | BUG | Média — engana quem tentar deploy | decisão | DEV | `Dockerfile:5-6,9,22`; `k8s/api.yaml:18` |
| **AU-03** | `apps/web` morto (não compila) | MORTO | Apagar, ou recriar com toolchain própria se houver intenção de frontend | FALTA-DECIDIR | Baixa — só ruído | decisão | AMBOS | `Dashboard.tsx:3,15`; sem `package.json` |
| **AU-04** | `packages/langgraph` morto (0 importadores, fora do typecheck) | MORTO | Apagar ou mover para `experimental/` | FALTA-DECIDIR | Baixa — ruído | decisão | AMBOS | AUDIT-1 §1.1 |
| **AU-05** | `tests/package.json` órfão (fora do workspace) **e gera PRs do Dependabot** | MORTO | Apagar (a raiz já declara `vitest`/`supertest`) | BUG | Baixa — ruído no Dependabot ("npm_and_yarn in /tests") | nada | CLAUDE | `pnpm-workspace.yaml:2-3`; runs Dependabot #38, #42 |
| **AU-06** | Duas pipelines de ingestão (Python/Gemini em CI; TS/`openai` manual) | EM CURSO (ambas existem) | Escolher a fonte única; desactivar ou apagar a outra; garantir um só modelo de embedding por tabela | FALTA-DECIDIR | **Alta** — embeddings incompatíveis e trabalho duplicado | decisão | DEV | AUDIT-1 §1.2 |
| **AU-07** | Dois orquestradores sem ponte (Python `plan_runner` vs TS `Orchestrator`); o maestro não está escolhido | NÃO INICIADO | ADR: qual é o maestro; o outro passa a cliente ou é descontinuado (engloba **EX-C2**) | FALTA-DECIDIR | **Crítica** — bloqueia a delegação por área (visão central) | decisão | DEV | AUDIT-1 R8; AUDIT-3 §3.4 |
| **AU-08** | `.env.example` omite 17 variáveis lidas pelo código; declara 2 que ninguém lê | NÃO INICIADO | Acrescentar `GEMINI_API_KEY`, `MCP_API_KEY`, `MCP_URL`, `MCP_SERVER_KEYS`, `MCP_CLIENT_KEY`, `MCP_POLICY_*`, `PLAN_RUNNER_MCP_*`, `ALLOW_UNAUTHENTICATED`, `MCP_AUDIT_LOG_PATH`, `MCP_RECEIPTS_LOG_PATH`; remover `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY` ou marcá-las como futuras | DOC-ERRADO | Média — um setup novo falha sem pista | nada | CLAUDE | AUDIT-1 R12 |
| **AU-09** | O CI Python nunca corre os 34 testes lentos (end-to-end do motor) | NÃO INICIADO | `-m ""` no `runner-tests.yml` e no `release.yml`, ou um job `slow` separado | FALTA-TESTE | Média — o gate de release ignora o caminho e2e | nada | CLAUDE | `runner/pytest.ini:4`; `runner-tests.yml:48`; `release.yml:34` |
| **AU-10** | `skills/claude/` sem proveniência (0/30 cabeçalhos do sync) | NÃO INICIADO | Mover para `skills/vendor/…` ou pôr os cabeçalhos | DOC-ERRADO | Baixa | nada | CLAUDE | AUDIT-1 §1.1 |
| **AU-11** | Schema da tabela RAG definido em dois sítios (Prisma + SQL avulso) | NÃO INICIADO | Escolher uma fonte (Prisma migration **ou** SQL versionado) e gerar a outra; inclui `knowledge_sources` (B11) | FALTA-DECIDIR | Média | decisão | DEV | `schema.prisma:138-171`; `scripts/create_t6_chunks_table.sql` |
| **AU-12** | O STATUS corrente tem 95 KB e há 226 docs; o bootstrap custa tokens | NÃO INICIADO | Partir `STATUS.md` (Done → arquivo); arquivar `docs/STATUS.md`; um só índice | FALTA-DECIDIR | Média — vai contra o objectivo "reduzir tokens" | decisão | AMBOS | AUDIT-1 R10/R13 |
| **AU-13** | **Deliberação bloqueia 100% dos pedidos** (escala 0–1 vs 0–10) | NÃO INICIADO | Pôr os critérios do `Orchestrator` na escala 0–10 (ou normalizar no motor); **decidir** que classes de pedido exigem HITL; teste que prove que um pedido "normal" passa | BUG | **Crítica** — o runtime TS não produz nenhuma resposta | decisão de política HITL | AMBOS | AUDIT-2 Q1 (sonda); `Orchestrator.ts:253-258`; `DeliberationEngine.ts:37,94` |
| **AU-14** | `executions.update` sem `create` prévio (P2025) | NÃO INICIADO | Criar o registo `Execution` no início (`ChatController` ou `Executor`) ou usar `upsert`; teste contra Postgres | BUG | **Crítica** — a próxima quebra depois de AU-13 | infra de teste (Postgres) | CLAUDE | AUDIT-2 Q2; `Executor.ts:54-57` |
| **AU-15** | `finalOutput` nunca preenchido → resposta vazia | NÃO INICIADO | Definir o resultado final (último passo ou `finalConsolidator`) e atribuí-lo | BUG | **Alta** — o utilizador receberia `""` | nada | CLAUDE | AUDIT-2 Q3; `Executor.ts:44` |
| **AU-16** | Tokens nunca somados (custo sempre 0) | NÃO INICIADO | Somar `step.tokens` em `results.metadata.totalTokens`; propagar `usage` real do provider | BUG | **Alta** — impossível medir a redução de tokens (objectivo central) | nada | CLAUDE | AUDIT-2 Q4 |
| **AU-17** | Teste de integração falso-verde (`toBeDefined`) | NÃO INICIADO | Asserções sobre `agentId`, `content`, chamadas ao LLM e passos executados | FALTA-TESTE | **Alta** — escondeu AU-13..16 | nada | CLAUDE | `ExecutionFlow.test.ts:47-48` |
| **AU-18** | Sem retoma depois da aprovação HITL; polling de 5 min em RAM a bloquear o pedido HTTP | NÃO INICIADO | Modelo assíncrono: devolver `waiting_hitl` + endpoint de retoma que continue a execução; persistir o pedido (liga M4) | FALTA-CONSTRUIR | **Alta** | decisão (modelo de retoma) | AMBOS | AUDIT-2 P14/Q6 |
| **AU-19** | **RAG: ingere para `knowledge_chunks_t6`, o retrieve lê `knowledge_chunks`** | NÃO INICIADO | Decidir a tabela canónica; criar uma RPC `match_knowledge_t6` (ou unificar) e apontar o `retrieve_knowledge` para ela; teste e2e ingest→retrieve | BUG | **Crítica** — a memória de conhecimento do setup está inacessível | decisão + acesso Supabase/MCP | AMBOS | AUDIT-2 §2.4 (SELECT ao vivo) |
| **AU-20** | `toolsAllowed` sem fonte; `agent.tools` nunca lido | NÃO INICIADO | Escolher a fonte (config do agente, schema do Planner ou plano declarativo) e implementar | FALTA-DECIDIR | **Alta** — as tools nunca chegam a um LLM | decisão | AMBOS | AUDIT-2 §2.2 |
| **AU-21** | Streaming SSE/WS só no papel | NÃO INICIADO | Chamar `onStepStart`/`onStepComplete` a partir do Executor | FALTA-CONSTRUIR | Baixa | nada | CLAUDE | `Orchestrator.ts:385-406` |
| **AU-22** | Campos de plano mortos: `max_steps` ausente no engine `langgraph`; `max_replans`/`done_when`/`on_fail`/`knowledge_refs` ignorados | NÃO INICIADO | Aplicar `max_steps` no `langgraph`; implementar ou remover os outros (e documentar) | BUG | Média — o plano promete garantias que não existem | nada | CLAUDE | AUDIT-2 Y7–Y9 |
| **AU-23** | Nenhum worker executa o modo `external` | NÃO INICIADO | Worker que leia `request.json` e chame um LLM de custo zero (ex.: Gemini Flash Lite) e escreva `result.json`; com HITL e orçamento | FALTA-CONSTRUIR | **Alta** — sem ele nenhum agente Python corre sozinho | decisão (LLM/custo) | AMBOS | AUDIT-2 Y6 |
| **AU-24** | Anti-injecção por regex com falsos positivos | NÃO INICIADO | Afinar os padrões (`/act as/`, `/override/`, `/system prompt/`) ou usar um classificador | BUG | Baixa | nada | CLAUDE | `SecurityManager.ts:277-296` |
| **AU-25** | `mcp/plan_runner` em `moderate` autoriza `run_plan` sem chave | EM CURSO (aviso existe) | Decidir a omissão `strict` fora de stdio local | FALTA-DECIDIR | Baixa — só stdio local | decisão | DEV | smoke da Fase 2; relacionado com B2 (`policy.py:73`) |
| **AU-26** | 8 agentes da config sem `domain` são inalcançáveis | NÃO INICIADO | Dar ao Planner os horizontais e meta além do domínio, ou atribuir domínios | BUG | **Alta** — horizontais nunca usados | decisão (desenho) | AMBOS | AUDIT-3 A1 |
| **AU-27** | 22/24 agentes da config sem `systemPrompt` | NÃO INICIADO | Ligar à fonte de prompts (`agents/*.agent.md`) ou escrevê-los | FALTA-CONSTRUIR | Média | decisão (fonte única de prompts) | AMBOS | AUDIT-3 A2 |
| **AU-28** | F1 (profiles) não ligado: `resolveAgentPrompt` sem chamadores | NÃO INICIADO | Chamar `resolveAgentPrompt(agent)` no `Executor.ts:167` | BUG | Média — o placeholder `{{…}}` iria literal ao LLM | nada | CLAUDE | AUDIT-3 A3 |
| **AU-29** | `PUBLIC_MODE` só consegue servir o domínio `legal` | NÃO INICIADO | Decidir o que a demo pública deve servir; dar domínio a agentes públicos | BUG | Média | decisão | DEV | AUDIT-3 A5 |
| **AU-30** | Domínio `software` (jogos incluídos) sem agentes → erro | NÃO INICIADO | Fallback para horizontais/meta quando o domínio está vazio; depois, agentes de software/jogos | BUG | **Alta** — o nicho "jogos" falha logo à entrada | nada (o fallback) | CLAUDE | `Router.ts:4`; AUDIT-3 §3.3 |
| **AU-31** | Resolução agente↔skill só por nome de pasta; 7 skills sem agente; `skill:` do frontmatter ignorado | NÃO INICIADO | Resolver pelo frontmatter `skill:`/`action:` ou normalizar nomes | BUG | Média | nada | CLAUDE | AUDIT-3 A7/A8 |
| **AU-32** | `design-flow.plan.yaml` (template) sem `vertical:` → 4 steps não resolvem | NÃO INICIADO | Acrescentar `vertical: design` aos 4 steps (como no demo, S34) | BUG | Baixa | nada | CLAUDE | AUDIT-3 A9 |
| **AU-33** | 4 taxonomias de áreas sem registo único | NÃO INICIADO | Registo de áreas consumido por router, config e runner | FALTA-DECIDIR | **Alta** — pré-requisito da delegação por área | decisão | DEV | AUDIT-3 §3.4 |
| **AU-34** | Router por primeiro match; `routeWithConfidence` órfão; omissão silenciosa `business` | NÃO INICIADO | Usar confiança + fallback explícito (ou router LLM, como no MCP) | BUG | Média | nada | CLAUDE | `Router.ts:10-33` |
| **AU-35** | Nichos financeiro/trader, jogos e segurança sem área nem agentes | NÃO INICIADO | Mapear e criar as áreas (necessidades em AUDIT-3 §3.4); **o desenho é trabalho separado** | FALTA-CONSTRUIR | **Alta** — são 3 dos objectivos declarados | decisão de escopo | DEV | AUDIT-3 §3.3 |
| **AU-36** | 3 nomenclaturas para os mesmos agentes de marketing | NÃO INICIADO | Tabela de correspondência e um id canónico | FALTA-DECIDIR | Média | decisão | AMBOS | AUDIT-3 §3.2 |
| **AU-37** | `CORE-MAPPING.md` desactualizado (Orchestrator "MOCK"; `verifyPassword` "sempre true"); README/ECOSYSTEM citam 5/19/14 | NÃO INICIADO | Errata no `CORE-MAPPING.md` e contagens corrigidas (a correcção já está no STATUS `:464`, mas não chegou aos docs de origem) | DOC-ERRADO | Média — induziu erros em 4+ docs | nada | CLAUDE | AUDIT-4 §4.1 |
| **AU-38** | 18 módulos do core órfãos (6 039 LOC) + 3 timers em background | NÃO INICIADO | Aprovar a lista (esta recontagem substitui a de M5) e mover para `experimental/` ou desligar os timers | FALTA-DECIDIR | Média — custo de manutenção e ruído | decisão | DEV | AUDIT-4 §4.4 |
| **AU-39** | `HitlManager.importFromFile/exportToFile` (M2) sem chamadores | NÃO INICIADO | Ligar à ponte Python↔Node (parte do M3) | FALTA-LIGAR | Média | depende de M3/AU-18 | CLAUDE | AUDIT-4 §4.3 |
| **AU-40** | Repositórios `users`/`conversations`/`metrics` e `RedisCache` órfãos | NÃO INICIADO | Decidir o uso (memória de conversa?) ou remover | FALTA-DECIDIR | Baixa | decisão | AMBOS | AUDIT-4 §4.4 |
| **AU-41** | `MCPServer` TS construído e testado mas não montado | NÃO INICIADO | Decidir (EX-C2): montar em `apps/api` ou descontinuar | FALTA-DECIDIR | Média | decisão | DEV | AUDIT-4 §4.4 |
| **AU-42** | MFA fixo `'123456'` em subsistema de utilizadores sem uso | NÃO INICIADO | Remover o subsistema ou implementar TOTP | BUG | Baixa — código morto, mas perigoso se for ligado | nada | CLAUDE | `SecurityManager.ts:239` |
| **AU-43** | `ExecutionService.getHitlStats` devolve zeros fixos | NÃO INICIADO | Ler do `HitlManager` | BUG | Baixa | nada | CLAUDE | `ExecutionService.ts:96-99` |
| **AU-44** | Análise de conteúdo (reels): a skill `transcript_analysis` + o agente `content_analyst` existem, mas **nenhum template os usa** e não há ponte para o `transcribe.yml`/`transcripts` do MCP | NÃO INICIADO | Template `content-analysis.plan.yaml` + passo que leia `transcripts` (Supabase) + ingestão das transcrições no RAG (E4 = yt-dlp→RAG) | FALTA-LIGAR | Média | decisão (onde corre) | AMBOS | G-skill-1/2 (`STATUS.md:239-240`); AUDIT-3 A11 |
| **AU-45** | Colisões de IDs: STATUS vs EXEC/OPEN-ITEMS (`B3`, `B5`, `B6`, `B7`, `B12`, `B13`, `C2`, `C3`, `C4`, `S24`…) **e dentro do STATUS** (`B10`–`B14` significam coisas diferentes em `:99-107` e `:301-309`) | NÃO INICIADO | Prefixar a série (ex.: `EX-`) ou renumerar; registar a regra no topo do STATUS | DOC-ERRADO | Média — gera decisões sobre o item errado | nada | CLAUDE | `STATUS.md:104-107` vs `:305-309`; `OPEN-ITEMS.md:46-50` |
| **AU-46** | `OPEN-ITEMS.md` desactualizado: lista como abertos S11/A8, S15a, S12, A22/M8, EX-S24 | NÃO INICIADO | Regenerar a partir do STATUS (ou apagar e apontar para o STATUS) | DOC-ERRADO | Média | nada | CLAUDE | `OPEN-ITEMS.md:24,32-36,44,54` vs STATUS |
| **AU-47** | **`keep-alive` falhou em 100% dos runs** (5/5): secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` vazias neste repo, e a tabela `keepalive` não existe | NÃO INICIADO | Configurar as 2 secrets no GitHub deste repo; criar a tabela `keepalive` (ou apontar para uma que exista); confirmar um run verde | BUG | **Alta** — risco de o Supabase free-tier pausar (hoje só a actividade de ingest o mantém vivo) | acesso (secrets GitHub) | DEV | Runs #1–#5 (2026-09-16→28); log `SUPABASE_URL:` vazio; `information_schema` sem `keepalive` |
| **AU-48** | `query_database` aceita SQL arbitrário (mitigado pelo gate `MUTATING`) | EM CURSO | Restringir a leitura (transacção `READ ONLY`/allowlist), como pede o A4 | BUG | Média | nada | CLAUDE | `database.ts:7,19`; `ToolPolicy.ts:51-52`; `EXECUTION-PROMPTS.md:131` sem fecho |
| **AU-49** | Orçamento de tokens TS alocado e nunca aplicado | NÃO INICIADO | Comparar uso com orçamento no Executor; abortar ou degradar; depende de AU-16 | FALTA-CONSTRUIR | **Alta** — objectivo central (tokens) | nada | CLAUDE | `Orchestrator.ts:273`; AUDIT-4 §4.2 |
| **AU-50** | `agent_id` composto (`marketing+produto-tech-transversal`) em `knowledge_chunks_t6` | NÃO INICIADO | Normalizar na ingestão (um id por chunk ou coluna array) | BUG | Baixa | nada | CLAUDE | SELECT ao vivo (AUDIT-2 §2.4) |

---

## 5.2 Itens do `STATUS.md` ainda abertos `[PEDIDO]`

| ID | Título | Estado | O que falta fazer | Tipo | Sev. | Bloqueio | Quem | Evidência |
|---|---|---|---|---|---|---|---|---|
| B2b | Correr as 8 ferramentas do `security_auditor` | EM CURSO (~5/8) | Trivy `vuln` e OSV-Scanner precisam de rede para `api.osv.dev`/`mirror.gcr.io` | FALTA-TESTE | Média | rede | AMBOS | `STATUS.md:28` |
| B2c | Triar os achados B2/B2b num backlog | EM CURSO | Converter `SECURITY-AUDIT*.md` em itens com dono e estado | FALTA-DECIDIR | Média | decisão de prioridade | AMBOS | `STATUS.md:29` |
| S17 | Doc da VM (Oracle) ainda diz GCP | NÃO INICIADO | Actualizar `CONFIGURACAO_VM_BRIDGE_WORKER.md` (repo MCP) | DOC-ERRADO | Baixa | nada (outro repo) | CLAUDE | `STATUS.md:38` |
| S19 | Oracle Free Tier como infra alternativa | NÃO INICIADO | Decidir o âmbito; acesso SSH | FALTA-DECIDIR | Média | acesso VM | DEV | `STATUS.md:40` |
| S20 | Chave antiga no `pm2` da VM Oracle | NÃO INICIADO — NÃO VERIFICÁVEL daqui | SSH + `pm2 restart --update-env` | BUG | **Alta** — o bridge-worker falha com 401 | acesso SSH | DEV | `STATUS.md:41` |
| S21 | Screenshots podem conter a chave | NÃO INICIADO | Confirmar se foram tiradas antes ou depois da rotação | FALTA-DECIDIR | Baixa | confirmação humana | DEV | `STATUS.md:42` |
| S24 | Cobertura TS: achados | EM CURSO | `MCPServer.ts` já está em 77% (S11); faltam `packages/langgraph` (morto, AU-04) e `packages/scripts/src/ingest` (0%); o e2e continua sem servidor | FALTA-TESTE | Média | nada | CLAUDE | `STATUS.md:43,57` |
| S27 | Oracle A1 reduzido para 2 OCPU/12 GB | NÃO INICIADO — NÃO VERIFICÁVEL daqui | Ver a config da VM na consola | FALTA-DECIDIR | Média — risco de custo | acesso consola | DEV | `STATUS.md:45` |
| S5 | `validate:consistency` + wiring + import runner | **FECHADO-VERIFICADO** (o STATUS não o fechou) | Mover para Done | DOC-ERRADO | Baixa | nada | CLAUDE | `ci.yml:103` corre-o; CI #387 verde |
| S29 | Memória L4 (`remember`/`recall`/`forget`) | NÃO INICIADO (0 código, confirmado) | Decidir a abordagem (Python própria vs padrões DSH); contrato de dados | FALTA-DECIDIR | **Alta** — "memória persistente" é objectivo da visão | decisão | DEV | grep vazio; `contracts.md:7-68` |
| S25 | Autorização por identidade (caller) | OBSOLETO (defer consciente) | — até haver caso multi-tenant | — | Baixa | decisão (2026-09-27) | DEV | `STATUS.md:62` |
| S13 | CORS aberto | NÃO INICIADO | Lista de origens legítimas | FALTA-DECIDIR | Média — só relevante com frontend | decisão | DEV | `server.ts:36` (verificado) |
| S32 | Agentes não se descobrem entre si (por desenho) | NÃO INICIADO | Confirmar ou reverter `AGENTS.md:15` | FALTA-DECIDIR | Média — liga a AU-07/AU-33 | decisão | DEV | `STATUS.md:70` |
| M3 | Teste e2e HITL Python→Node→Python | NÃO INICIADO | Escrita de decisões do lado Node (não existe) + AU-18 + AU-39 | FALTA-CONSTRUIR | **Alta** | depende de AU-13/AU-14 | AMBOS | `STATUS.md:75,80` |
| M4 | HITL durável em Postgres | NÃO INICIADO | Schema + migração + onde corre | FALTA-CONSTRUIR | **Alta** — HITL em RAM (AUDIT-4) | infra | AMBOS | `STATUS.md:76` |
| M5 | Mover módulos sem consumidor para `experimental/` | NÃO INICIADO | **Lista recontada nesta auditoria: 18 módulos** (AU-38); falta a aprovação | FALTA-DECIDIR | Média | decisão | DEV | `STATUS.md:77,82` |
| M6 | `GeminiProvider` + Planner com scope/unknowns/… | NÃO INICIADO | Especificar o contrato; implementar o provider (só existe `OpenAIProvider`) | FALTA-CONSTRUIR | **Alta** — custo zero é premissa | decisão (spec) | AMBOS | `LLMService.ts:98` |
| M7 | Piloto real de marketing | NÃO INICIADO | Caso real do utilizador | FALTA-DECIDIR | Média | dados reais | DEV | `STATUS.md:91` |
| D3 | DeepEval (judge Ollama) | NÃO INICIADO | Máquina com mais RAM ou Ollama remoto | FALTA-TESTE | Média | ambiente | DEV | `STATUS.md:88` |
| D4 | Ragas `ToolCallAccuracy` | NÃO INICIADO | O bloqueio é **só da máquina Windows** (Python 3.14 sem wheel); em Linux/CI há wheels manylinux, o que o torna desbloqueável no CI | FALTA-TESTE | Média | ambiente local | AMBOS | `STATUS.md:89` |
| S14 | Migrar `Tracer.ts` para o SDK OTel | NÃO INICIADO | Aprovar a dependência de produção | FALTA-DECIDIR | Baixa | decisão | DEV | `packages/observability/package.json` sem otel |
| S28 | Warning de cache no `transcribe.yml` (MCP) | NÃO INICIADO | Investigar o `tar` exit 2 | BUG | Baixa | nada (outro repo) | CLAUDE | `STATUS.md:98` |
| B1 | Expansão para o 2.º domínio | NÃO INICIADO | Depende de AU-07/AU-33 | FALTA-CONSTRUIR | Média | decisão | DEV | `STATUS.md:99` |
| B3 | Agente de trading (simulação) | NÃO INICIADO (0 ficheiros) | Ver G1.x; necessidades em AUDIT-3 §3.4 | FALTA-CONSTRUIR | **Alta** (nicho declarado) | decisão de escopo | DEV | `STATUS.md:100` |
| B4 | Agente gamedev | NÃO INICIADO (0 ficheiros) | Ver G2.x | FALTA-CONSTRUIR | **Alta** (nicho declarado) | decisão de escopo | DEV | `STATUS.md:101` |
| B5 | Hermes como runtime | NÃO INICIADO | Avaliar (pode ser o worker de AU-23) | FALTA-DECIDIR | Baixa | decisão | DEV | `STATUS.md:102` |
| B6 | MiroFish (AGPL) | NÃO INICIADO | Avaliar a licença e o isolamento | FALTA-DECIDIR | Baixa | decisão | DEV | `STATUS.md:103` |
| B11 | Script de criação de `knowledge_sources` | NÃO INICIADO (confirmado: não há `CREATE TABLE knowledge_sources` no repo) | SQL versionado (liga AU-11) | FALTA-CONSTRUIR | Média | nada | CLAUDE | grep vazio |
| B12 | Investigar `knowledge_log` | EM CURSO | **Existe no Supabase (7 colunas)**, sem dono documentado; ver quem escreve (provavelmente o MCP) | DOC-ERRADO | Baixa | nada | CLAUDE | SELECT `information_schema` |
| B16 / G7 | `ActionReceipt` com contrato ADR-001 completo | NÃO INICIADO | Depende de C3/C4 (EX) | FALTA-CONSTRUIR | Baixa | EX-C3/EX-C4 | AMBOS | `STATUS.md:110,201` |
| G6 | Contradição `imobiliario-digital` no `MCP-MAPPING.md` | NÃO INICIADO | Decidir 3.2 vs 3.6 | DOC-ERRADO | Baixa | decisão | DEV | `STATUS.md:200` |
| INIT-093 | Adoptar `google/skills` | NÃO INICIADO | Avaliar e seleccionar skills (`media_buyer`, `ad_creative`) | FALTA-DECIDIR | Média | decisão | AMBOS | `STATUS.md:173-177` |
| INIT-094 (=EX-F8) | Avaliar os 6 harnesses multi-provider | NÃO INICIADO | Reavaliação rigorosa | FALTA-DECIDIR | Baixa | nada | CLAUDE | `STATUS.md:158-169` |
| P1–P5 | Constitution, META Compiler, AR-000…015, A2A, UI visual | OBSOLETO (arquivados) | — | — | Baixa | — | DEV | `STATUS.md:118-122` |
| **P6** | Multi-provider LLM | OBSOLETO (arquivado) — **contradiz M6** | Desarquivar ou reconciliar: custo zero exige um provider não-OpenAI (Gemini), o que já **é** multi-provider | DOC-ERRADO | Média — conflito de decisão | decisão | DEV | `STATUS.md:123` vs M6 |

---

## 5.3 Itens do `STATUS.md` dados como "Done": reverificação `[PEDIDO: "Done no doc ≠ funciona"]`

| ID | Título | Estado verificado | Nota / o que falta | Evidência desta auditoria |
|---|---|---|---|---|
| S1 | CI bloqueia se vitest falhar | FECHADO-VERIFICADO | — | `ci.yml:99` sem `continue-on-error`; CI #387 ✅ |
| S2a / S2b-1..3 / S3 | Testes do caminho crítico (Py + Node) | FECHADO-VERIFICADO | Mas ver AU-17 (o teste de integração é fraco) | 195/195 Py; 196/196 TS |
| S4 / S4b | Lockfile + `--frozen-lockfile` | FECHADO-VERIFICADO | — | `pnpm install --frozen-lockfile` OK |
| S6a | `hitl.py` contrato v1 | FECHADO-VERIFICADO | — | Suite Py |
| S7 | Working memory | FECHADO-VERIFICADO | Só leitura (AUDIT-4) | Suite Py |
| S8 | `.gitignore` Node | FECHADO-VERIFICADO | — | `.gitignore:71` |
| S9 | Integração HITL em engine/langgraph/cli | FECHADO-VERIFICADO | — | Run `stub` escreve `hitl-requests.jsonl`; `resume` → `done` |
| S10 | L5 ligado à execução de planos | FECHADO-VERIFICADO (wiring) | **Mas lê a tabela errada (AU-19)** | `knowledge_wiring.py`; AUDIT-2 §2.4 |
| S11 (=EX-A8) | Identidade real no MCPServer | FECHADO-VERIFICADO (código) | `MCPServer` não montado (AU-41) | `McpAuth.ts`; testes |
| S12 | `.strict()` nos schemas do MCP | FECHADO-VERIFICADO | O STATUS diz "nada commitado", mas **está commitado** (`024e0ee`) | `git show origin/main:app/api/mcp/route.js` (13 × `.strict()`) |
| S15a | Secret rotacionada no MCP | FECHADO-VERIFICADO | — | `transcripts`: 1 registo de `Dcg6uPDSoK6` a 2026-09-20 |
| **S15b** | "`keep-alive.yml` continua funcional" | **FECHADO-SÓ-NO-PAPEL** | A decisão N/A sobre a ANON_KEY é razoável; **a afirmação de que o keep-alive funciona é falsa** (AU-47) | Runs keep-alive 5/5 ❌ |
| S16 | Chave antiga apagada do disco | FECHADO — NÃO VERIFICÁVEL daqui | Disco Windows local | — |
| S18 | README actualizado (67 skills / 35 agentes) | FECHADO-VERIFICADO | O diagrama continua incompleto (AUDIT-1 E6) | `find` = 67 / 35 |
| S22 / S23 | Inventário de credenciais / mapa de repos | FECHADO-VERIFICADO (docs existem) | Conteúdo local NÃO VERIFICÁVEL | `docs/architecture/CREDENTIALS-INVENTORY.md`, `REPOSITORY-MAP.md` |
| S30 | Memória do cliente ligada ao motor | FECHADO-VERIFICADO | — | `test_client_memory_wiring.py` na suite |
| S31 | `plan_runner search` | FECHADO-VERIFICADO | Pesquisa por run, não global | `cli.py:38`; suite |
| **S33** | "Tools chegam a um LLM real" | **FECHADO-SÓ-NO-PAPEL** | O fio `ToolRegistry`→`Executor` e o fix `tool_call_id` são reais, mas **o objectivo do título não se cumpre**: `toolsAllowed` sem fonte (AU-20) e o Executor nunca é alcançado (AU-13) | AUDIT-2 §2.2 |
| S34 | `vertical` lido do plano | FECHADO-VERIFICADO | O template `design-flow.plan.yaml` não foi corrigido (AU-32) | Script de resolução |
| S35 | Catálogo de skills gerado | FECHADO-VERIFICADO | — | `docs/generated/SKILLS.md` |
| S36 / M8 (=EX-A22) | Dependabot remediado | FECHADO-VERIFICADO | — | `pnpm audit`: 0 |
| M1 | Session search FTS5 | FECHADO-VERIFICADO | — | Suite Py |
| M2 | `HitlManager` import/export | FECHADO-VERIFICADO (código) | **Sem chamadores** (AU-39) | grep |
| B2 | Agente `security_auditor` | FECHADO-VERIFICADO (ficheiros) | Não é resolúvel pelo runner (AU-31, A8 da Fase 3) | `agents/meta/security_auditor.agent.md` |
| B7/B8/B9 (STATUS) | Docs de padrões MCP / codebase-memory / node-platform | FECHADO-VERIFICADO | — | Ficheiros existem |
| B10 | `prisma generate` automatizado | FECHADO-VERIFICADO | — | `packages/memory/package.json` `postinstall` |
| B13/D9 | Testes lentos isolados | FECHADO-VERIFICADO | **Efeito colateral: o CI nunca os corre (AU-09)** | `pytest.ini:4` |
| B14 | Auditoria de escopo do EXEC | FECHADO-VERIFICADO (doc) | — | `AUDIT-SCOPE-2026-09-19.md` |
| B15/F10 | pnpm 8.15.9 | FECHADO-VERIFICADO | O comentário do CI diz 8.0.0 (AUDIT-1 E2) | `package.json` |
| B17 | Mock do teste de integração | FECHADO-VERIFICADO | O teste passa, mas por um motivo errado (AU-17) | Suite TS |
| B18 | `supertest` | FECHADO-VERIFICADO | O e2e precisa de servidor | `package.json` root |
| C1 | Evidência A4/A5/A6 | FECHADO-VERIFICADO | — | `pilots/evidence/` |
| C2 (STATUS) | Guard `--out` fora de `pilots/` | FECHADO-VERIFICADO | — | Erro real na Fase 2 |
| C3 / C5 / C6 / C7 (STATUS, repo MCP) | Auth e Dependabot no MCP | C5 FECHADO-VERIFICADO (`withAuth`); C3/C6/C7 FECHADO — NÃO VERIFICADO aqui | — | `git show origin/main:…route.js` |
| C8a-1 / C8b / C8d | Chunking, schema, backend retrieve | FECHADO-VERIFICADO | — | Suite; tabelas existem (SELECT) |
| C8a-2 | Pipeline de ingestão T6 | FECHADO-VERIFICADO | — | 110 chunks, última escrita 2026-09-29 |
| C8c | Workflow ingest com apply | FECHADO-VERIFICADO | — | Runs #127–#129 ✅ |
| C8e (=G1) | `McpKnowledge` | FECHADO-VERIFICADO (componente) | Aponta para `knowledge_chunks` (AU-19) | 13 testes; `lib/knowledge.js:54` |
| **C8** | "Pipeline completo markdown→…→retrieve" | **FECHADO-SÓ-NO-PAPEL** | O retrieve não lê o que é ingerido; só 1/33 fontes coincide | AUDIT-2 §2.4 |
| **keep-alive** | "Manter Supabase activo" | **FECHADO-SÓ-NO-PAPEL** | Nunca funcionou (AU-47) | 5/5 runs ❌ |
| G2 / G3 / G4 / G5 | Skills meta, knowledge packs, agentes migrados, correcções MCP-MAPPING | FECHADO-VERIFICADO | — | 21 meta skills; 5 packs; 35 agentes |
| G-skill-1..5 | `transcript_analysis`, `content_analyst`, `cheap-entity-extraction`, `skill-self-optimization`, `ai-code-review-checklist` | FECHADO-VERIFICADO (ficheiros) | 1 e 2 sem uso (AU-44) | 5/5 ficheiros |

---

## 5.4 Itens de `OPEN-ITEMS.md` / `EXECUTION-PROMPTS.md` (série EX) `[PEDIDO]`

Só os que **não** são duplicados de linhas já acima (os `=X` estão indicados).

| ID | Título | Estado | O que falta fazer | Tipo | Sev. | Bloqueio | Quem | Evidência |
|---|---|---|---|---|---|---|---|---|
| EX-B7 | Expor `engine: langgraph` + `decision: edit` no MCP `plan_runner` | NÃO INICIADO (confirmado) | Parâmetros em `run_plan`/`resume_plan` | FALTA-LIGAR | Média | nada | CLAUDE | `tools_impl.py:69,76,94` só `engine.run_plan` |
| EX-B13 | = **M6** | ver M6 | | | | | | |
| D5 | `model_tier` lido de facto | NÃO INICIADO (0 usos em código) | Implementar (LiteLLM Router ou equivalente) | FALTA-CONSTRUIR | Média — controlo de custo | nada | CLAUDE | grep: 0 |
| D6 | `budget.max_cost_usd` | NÃO INICIADO (0 usos) | Implementar (depende de AU-16) | FALTA-CONSTRUIR | **Alta** — custo | nada | CLAUDE | grep: 0 |
| D7 | `MetricsDashboard`/`SelfAwareness` com dados reais | NÃO INICIADO | Ligar a métricas reais (depende de AU-16) | FALTA-LIGAR | Média | nada | CLAUDE | `OPEN-ITEMS.md:19` |
| E1–E7 | Crawl4AI, Trafilatura, MarkItDown, Docling, yt-dlp+whisper→RAG, gitingest, ScrapeGraphAI | NÃO INICIADO (0 deps nos `requirements`) | Adopção, uma a uma, com revisão de CVEs (AUDIT-INGESTION) | FALTA-DECIDIR | Média | confirmação de dependências | AMBOS | grep `requirements*.txt` = 0 |
| E8 / E9 | = B11 / B12 | | | | | | | |
| EX-S24 | Testes de `MCPServer.ts` | FECHADO-VERIFICADO (via S11: 0% → 77.58%) | Remover do OPEN-ITEMS (AU-46) | — | — | — | — | `STATUS.md:57` |
| S17/S20, S15a, S21 | ver 5.2/5.3 | | | | | | | |
| A1b | Deploy real do `k8s/` | NÃO INICIADO | Decidir o pipeline; Secret fora do git (liga AU-02) | FALTA-DECIDIR | Baixa | decisão | DEV | `k8s/secrets.yaml:1-3` |
| A4 | Restringir `query_database` | EM CURSO | = **AU-48** | | | | | |
| A8 | = S11 (fechado) | | | | | | | |
| A9 | Lockfile Python | NÃO INICIADO (0 lockfiles) | `uv lock` com rede | FALTA-CONSTRUIR | Média — supply chain | rede | AMBOS | `ls runner/uv.lock` vazio |
| A10 / A11 | = B2b / B2c | | | | | | | |
| A12 | Criptografia em repouso | NÃO INICIADO | Decidir se há dado sensível | FALTA-DECIDIR | Baixa | decisão | DEV | `OPEN-ITEMS.md:40` |
| A13 | RBAC real | NÃO INICIADO (`checkRBAC`/`checkPermission`: 0 chamadas) | Aprovar o modelo de papéis | FALTA-DECIDIR | Média | decisão | DEV | grep |
| A15 | Flags de cookie | OBSOLETO (sem cookies) | Fechar como N/A | DOC-ERRADO | Baixa | decisão | DEV | `OPEN-ITEMS.md:42` |
| A19 | Restringir uploads | OBSOLETO neste repo (alvo no MCP) | Mover o item para o MCP | DOC-ERRADO | Baixa | decisão | DEV | `OPEN-ITEMS.md:43` |
| A22 / A23 | = M8 (fechado) / S13 | | | | | | | |
| EX-B3 | Correr `apps/api` contra Postgres/OpenAI reais | NÃO INICIADO | **Previsão desta auditoria: falha em AU-13, depois AU-14.** Corrigir essas duas primeiro e só depois correr | FALTA-TESTE | **Alta** | `.env` real + AU-13/14 | AMBOS | AUDIT-2 |
| EX-B5 / EX-B6 / EX-B12 | = M3 / M4 / M5 | | | | | | | |
| EX-C2 | TS vs Python MCP | NÃO INICIADO | ADR (engloba AU-07 e AU-41) | FALTA-DECIDIR | **Alta** | decisão | DEV | `OPEN-ITEMS.md:50` |
| EX-C3 / EX-C4 | AgentMesh / Cedar | NÃO INICIADO | Aprovar dependências | FALTA-DECIDIR | Média | decisão | DEV | `OPEN-ITEMS.md:51-52` |
| F7 | PMO / Project Director | NÃO INICIADO | Decisão organizacional | FALTA-DECIDIR | Média — liga ao "maestro" | decisão | DEV | `STATUS.md:402,433` |

### Grupos G–J (backlog de nichos e ferramentas; o OPEN-ITEMS resumiu-os num só bloco)

Todos **NÃO INICIADOS**, tipo **FALTA-DECIDIR** (escopo antes de construir), bloqueio **decisão humana**, quem **DEV** (salvo nota). Evidência: títulos em `EXECUTION-PROMPTS.md:1618-2428`.

| ID | Título | Sev. | Nota |
|---|---|---|---|
| G1.1 | Pesquisa padrão ouro de repos de trading/simulação | Alta | Pode ser CLAUDE (pesquisa) |
| G1.2 | World Monitor + Finance News Aggregator (=F20/F21) | Média | Licença AGPL a avaliar |
| G1.3 | Competências dos papéis financeiros | Alta | Necessidades em AUDIT-3 §3.4 |
| G1.4 | Contratos de dados entre papéis | Alta | = D7 da Fase 3 (handoff) |
| G1.5 | Isolar credenciais / garantir ausência de execução real | **Crítica** para o nicho | Pré-requisito de "ordens autónomas com budget" |
| G1.6 | MiroFish e repos de simulação (=B6) | Baixa | |
| G1.7 | Agente de trading, simulação (=B3) | Alta | |
| G1.8 | Agente de investimentos (=B12 da secção 09-14) | Média | Colisão de ID (AU-45) |
| G1.9 | Análise de volatilidade (=B13 da secção 09-14) | Média | Colisão de ID |
| G1.10 | Agente jornalístico → investidor (=F22+B14) | Baixa | |
| G1.11 | Operação financeira, orquestrador do cluster (=B10 da secção 09-14) | Alta | É o "maestro" da área |
| G1.12 | Tela de agentes financeiros (=U3) | Baixa | |
| G1.13 | Avatar financeiro (=U7) | Baixa | |
| G1.14 | Critério de "pronto" do cluster | Alta | |
| G2.1 | Pesquisa padrão ouro gamedev (GDD, engine, loop) | Alta | Pode ser CLAUDE |
| G2.2 | Escopo: documento vs. protótipo jogável | Alta | |
| G2.3 | Engine-alvo | Alta | Liga "multijogador até 3D" |
| G2.4 | Implementar | Alta | |
| G3.1–G3.3 | Avatar (infra, genérico, skin) | Baixa | |
| G4.1 | Obsidian vs. Logseq (=F10=I8) | Média | Ver 6.5 da Fase 6 |
| G4.2 | Grafo de memória (=U1) | Média | |
| H1–H4 | Dashboard, JARVIS, VOS, grafo de conexões (=U4/U8/U9/U5) | Baixa | VOS "clarificar" |
| I1–I11 | agent-skills, Graphify, OmniRoute, Obscura, plugin segurança Anthropic, Ruflo, gstack, Obsidian/Logseq, SOUL.md, Karpathy Skills, Soup (=F1–F16) | Baixa–Média | I4/I5 duplicam F16/F17 |
| J1–J7 | = P1–P6 + Caveman (F6) | — | OBSOLETO (arquivados) |

### Secção "Sessão 2026-09-14" do STATUS (F1–F22, B10–B14, U1–U9)

As F1–F22 são candidatas de ferramentas, cobertas em I1–I11/G1.2 e na Fase 6 §6.5. As B10–B14 desta secção são **agentes financeiros/avatar** e **colidem** com B10–B14 da secção 🟢 (AU-45); estão cobertas em G1.x/G3.x. As U1–U9 são telas, cobertas em G/H. Estado: **NÃO INICIADO** · FALTA-DECIDIR · DEV.

---

## 5.5 Checklist de segurança (20 itens, `STATUS.md:133-154`) `[PEDIDO]`

| # | Item | Estado (STATUS) | Estado verificado | Nota |
|---|---|---|---|---|
| 1, 2 | API keys / secrets no git | ✅ | FECHADO-VERIFICADO | `.gitignore`; sem `.env` no clone |
| 3 | Public key DB | N/A | OBSOLETO | |
| 4 | RLS | ✅ | FECHADO — NÃO VERIFICADO aqui | Policies não relidas nesta auditoria |
| 5 | Criptografia de dados | ❌ | NÃO INICIADO | = A12 |
| 6 | Auth server-side | ✅ | FECHADO-VERIFICADO | `auth.ts:55-95` |
| 7 | RBAC | ❌ | NÃO INICIADO | = A13 |
| 8 | Mass assignment | ❌→N/A | FECHADO-VERIFICADO (no MCP, via S12) | |
| 9 | Cookies | ⚠️ | OBSOLETO | = A15 |
| 10 | Hash de senhas | ✅ ("Supabase Auth") | FECHADO-VERIFICADO — **mas a nota está errada**: o hash deste repo é bcrypt no `SecurityManager` (sem uso) | AU-37 |
| 11 | Rate limit | ✅ | FECHADO-VERIFICADO | `server.ts:26-50` |
| 12 | Bot protection | N/A | OBSOLETO | |
| 13 | Queries parametrizadas | ✅ | FECHADO-VERIFICADO **com excepção**: `query_database` corre SQL arbitrário do agente | AU-48 |
| 14 | Validação de inputs | ⚠️ | EM CURSO | |
| 15 | Vazamento de erros | ✅ | FECHADO-VERIFICADO | `toClientError` em uso (`ChatController.ts:38`) |
| 16 | Uploads | ❌ | OBSOLETO aqui | = A19 |
| 17 | Trim respostas | ⚠️ | NÃO INICIADO | |
| 18 | Security headers | ✅ | FECHADO-VERIFICADO | `server.ts:35` |
| 19 | HTTPS | ✅ | NÃO VERIFICÁVEL daqui | Vercel (repo MCP) |
| 20 | Dependências | ⚠️ | FECHADO-VERIFICADO (TS: 0 vulns); **Python sem lockfile** | A9 |

---

## Contagens

| Estado | N.º aprox. |
|---|---|
| FECHADO-VERIFICADO | ~55 |
| FECHADO-SÓ-NO-PAPEL | **4** (C8, keep-alive, S33, S15b) |
| FECHADO — NÃO VERIFICÁVEL daqui | ~6 |
| EM CURSO | ~9 |
| NÃO INICIADO | ~85 (incluindo 44 dos 50 AU) |
| MORTO | 3 (AU-03, AU-04, AU-05) |
| OBSOLETO | ~17 (P1–P6, J1–J7, A15, A19, S25 e N/A da checklist) |

*(Aproximadas porque há itens duplicados entre séries, marcados `=X`; cada item é contado uma vez, na sua linha principal.)*

## Limites desta fase

- Os itens de outras máquinas (VM Oracle, disco Windows, consola Vercel) estão marcados como NÃO VERIFICÁVEL.
- Os itens G–J foram inventariados pelos títulos. O corpo de cada um no `EXECUTION-PROMPTS.md` não foi relido linha a linha (o próprio OPEN-ITEMS admite o mesmo limite, `:86`).
- "FECHADO-VERIFICADO (doc)" significa que o documento existe. Não significa que o conteúdo tenha sido reauditado.
