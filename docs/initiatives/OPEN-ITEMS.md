# Itens em Aberto — Relatório Consolidado (2026-09-20)

Produzido na Tarefa 5 da auditoria autónoma desta sessão. Fontes lidas por completo: `STATUS.md` (446 linhas), `EXECUTION-PROMPTS.md` (2448 linhas, todos os Grupos A-J), `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md` (192 linhas).

**Método:** todo item ainda **não fechado** nos 2 documentos, cruzado (os dois têm séries de ID independentes com os mesmos prefixos — ver nota de colisão em `STATUS.md` linha 5-14; itens equivalentes são marcados `(=X)`). Agrupado por **quem bloqueia**: 100% Claude (posso avançar sozinho), Precisa humano (decisão ou acção só do utilizador), Bloqueado por ambiente (hardware/rede/toolchain desta máquina).

Itens já fechados (Done/JÁ FEITO/N/A confirmado) **não estão nesta lista** — ver `## Done` em `STATUS.md` e as notas "Status em..." em `EXECUTION-PROMPTS.md` para o histórico completo. Este documento cobre só o que resta.

---

## 🟢 100% Claude — posso executar sem depender de decisão humana nem de infra externa

| ID | Descrição | Origem | Prioridade |
|---|---|---|---|
| **B7** (EXEC) | Expor `engine: "langgraph"` + `decision: "edit"` na superfície MCP (`tools_impl.py`) — hoje só `native`/`approve\|reject` são acessíveis via MCP, apesar do motor `langgraph` já suportar ambos | `agents-audit/FASE2-AGENTES.md` §1 | 🟠 Alto — fecha um gap real de capacidade já construída mas não exposta |
| **B13** (EXEC, =M6) | `GeminiProvider` (interface `LLMProvider`) + estender `Planner.ts` com `scope`/`unknowns`/`pre_mortem`/`not_doing` | STATUS.md M6 | 🟡 Médio |
| **D5** | Ler `model_tier` de facto (hoje só existe no schema, campo morto) — via LiteLLM Router | STATUS.md, achado da auditoria de Evaluation | 🟡 Médio |
| **D6** | Implementar `budget.max_cost_usd` (só `max_replans`/`max_steps` existem hoje) | STATUS.md, achado da auditoria de Evaluation | 🟡 Médio |
| **D7** | `MetricsDashboard`/`SelfAwareness` com dados reais (hoje têm comentários placeholder "Em produção, consulta...") | `packages/core/src/observability/SelfAwareness.ts:357-425` | 🟡 Médio |
| **E1-E7** | Adoptar Crawl4AI+Trafilatura, MarkItDown, Docling (condicional), ligar `yt-dlp`+`whisper` ao RAG, `gitingest` (com reservas), reavaliar ScrapeGraphAI, avaliar `google/skills` — pesquisa já feita (`AUDIT-INGESTION.md`), falta só a adopção de código | `ingestion-audit/AUDIT-INGESTION.md` | 🟡 Médio (mecânico, baixo risco arquitectural, mas adiciona dependências novas — considerar 1 confirmação rápida antes de instalar) |
| **E8** (=B11 em STATUS.md) | Script de criação versionado para `knowledge_sources` (hoje só existe manualmente no Supabase) | Achado durante A2 | 🟠 Alto — dívida de controlo de versão real |
| **E9** (=B12 em STATUS.md) | Investigar/documentar a tabela `knowledge_log` (RLS já activo, mas sem dono/propósito documentado) | Achado durante A2 | 🟡 Médio |
| **F8** (=INIT-094) | Reavaliar os 6 harnesses multi-provider (`deepseek-harness` etc.) com o mesmo rigor das auditorias desta sessão — a tabela actual nunca foi reverificada | STATUS.md, secção Harnesses | 🟢 Baixo |
| **S24** (novo, Tarefa 4 desta auditoria) | Escrever testes para `packages/mcp/src/server/MCPServer.ts` (hoje 0% de cobertura) — pode avançar já para os caminhos que **não** dependem da chave real de auth (ver A8 abaixo para a parte que depende de humano) | `docs/architecture/TEST-COVERAGE.md` | 🟠 Alto |

---

## 🟠 Precisa humano — decisão ou acção que só o utilizador pode dar

| ID | Descrição | O que falta decidir/fazer | Prioridade |
|---|---|---|---|
| **S17/S20** | VM Oracle (`130.61.213.226`) com `SUPABASE_SERVICE_ROLE_KEY` provavelmente ainda antiga | SSH + `pm2 restart --update-env` — **explicitamente fora do âmbito de qualquer sessão Claude nesta máquina** (instrução repetida do utilizador) | 🔴 Crítico |
| **S15a** | GitHub Actions de `agent-network-mcp` (7 workflows) ainda com a `SUPABASE_SERVICE_ROLE_KEY` antiga | Actualizar a secret no GitHub Actions desse repo (utilizador já confirmou que vai fazer) | 🔴 Crítico |
| **S21** | Screenshots da migração GCP→Oracle podem conter a chave antiga ou a nova | Confirmar timing (antes/depois de 2026-09-19) | 🟡 Médio |
| **A1b** | Passo de deploy real do `k8s/` (Secret + resolução de `${...}`) | Decidir pipeline (`kubectl`/Helm/Kustomize) e criar o Secret real fora do git | 🟢 Baixo (só relevante quando `k8s/` for aplicado a um cluster real) |
| **A8** (=S11) | Autenticação em `MCPServer.ts` — hoje zero verificação de header antes de `executeTool` | Desenvolvedor define/distribui a `MCP_SERVER_KEY` real; Claude implementa o middleware fail-closed | 🔴 Crítico — é o mesmo achado que **S11** já regista como bloqueando o C1 ser útil de facto |
| **A9** | Lockfile Python (`uv.lock`/`poetry.lock`) — zero lockfile hoje | `uv lock` pode falhar por rede da sandbox — precisa de ambiente com rede real ou confirmação de que a rede está liberada | 🟠 Alto |
| **A10** (=B2b) | Rodar as 8 ferramentas completas do `security_auditor` (só ~5 correram) | Rede liberada para `api.osv.dev`/`mirror.gcr.io` (Trivy `vuln`, OSV-Scanner ficaram bloqueados) | 🟡 Médio |
| **A11** (=B2c) | Triar todos os achados de segurança num backlog rastreável com dono/estado | Desenvolvedor confirma prioridade final de cada achado | 🟡 Médio |
| **A12** | Criptografia de dados em repouso | Confirmar se há mesmo dado sensível nesta camada (provavelmente não — decisão a registar explicitamente) | 🟢 Baixo |
| **A13** | Modelo RBAC real (`SecurityManager.checkRBAC()` existe, mas zero chamada em `apps/api`) | Desenvolvedor aprova papéis fixos vs. ABAC antes da implementação | 🟠 Alto |
| **A15** | Flags de cookie — **item não tem alvo real** (autenticação é 100% via `x-api-key`, sem cookies) | Decisão: fechar como N/A, ou desenhar sessão por cookie de raiz (mudança de arquitectura) | 🟢 Baixo |
| **A19** | Restringir uploads — **item aponta para o repo errado** (`extrair-imagem` só existe em `agent-network-mcp`) | Decisão: mover o item para esse repo, ou remover do plano deste | 🟢 Baixo |
| **A22** (=M8) | 9 alertas Dependabot (3 críticas + 1 alta em dev; 5 moderadas incl. `uuid`, único pacote de produção) | Confirmar changelogs antes do bump; `uuid` precisa de teste de regressão em `apps/api` | 🟠 Alto |
| **A23** (=S13) | CORS totalmente aberto (`app.use(cors())` sem opções) — contradiz o CORP do helmet já corrigido (A20) | Desenvolvedor confirma a lista de origens legítimas — sem isso não há o que configurar | 🟠 Alto |
| **B3** | Correr `apps/api` contra Postgres/OpenAI reais (nunca validado) | Desenvolvedor fornece `.env` real ou de staging | 🟠 Alto — é a peça que fecha "o pipeline TS funciona ponta-a-ponta?" |
| **B5** (=M3) | Teste e2e HITL Python→Node→Python | **Depende de B3** (precisa da API `apps/api` real a correr) — sem isso fica só desenhado, não executável | 🟠 Alto |
| **B6** (=M4) | HITL durável em Postgres (Supabase) | Depende de B5 fechado primeiro (não migrar de ficheiro para BD sem o e2e provado) | 🟡 Médio |
| **B12** (=M5) | Mover módulos sem consumidor para `packages/experimental/` | Desenvolvedor aprova a lista final antes de qualquer `git mv` (a lista original de "~14" está desactualizada desde a correcção do `Orchestrator.ts` não-mock — precisa de recontagem) | 🟢 Baixo |
| **C2** | Decisão TS vs. Python MCP (duplicação de implementação) | Desenvolvedor escolhe: TS fino delegando a Python / descontinuar TS / coexistência documentada — registar como ADR | 🟠 Alto — decisão estrutural que outros itens (C3, C4, S11) dependem indirectamente de conhecer |
| **C3** | Adoptar AgentMesh (identity/delegation) | Desenvolvedor aprova nova dependência de produção antes do merge | 🟡 Médio |
| **C4** | Adoptar Cedar (policy engine) | Idem | 🟡 Médio |
| **F7** | Decisão PMO/Project Director (queixa original que abriu a auditoria de Agentes) | Nenhum dos ~45 projectos avaliados resolve isto — é decisão de arquitectura organizacional pura, não técnica | 🟡 Médio |
| **S12** | Adicionar `.strict()` aos schemas Zod do `mcp-handler` — repo `agent-network-mcp` (separado) | Requer sessão dedicada nesse outro repo | 🟠 Alto (mas fora deste repo) |
| **G1-G4/H/I** (~40 itens) | Clusters de trabalho futuro: agente financeiro (14), gamedev (4), avatar (3), grafo de memória (2), integração final (4), backlog de pesquisa não triado (10) | Decisões de escopo/prioridade humanas antes de qualquer execução — ver `EXECUTION-PROMPTS.md` para o detalhe item a item | 🟢 Baixo — deliberadamente deixado para depois de A-F fechados |

---

## 🔴 Bloqueado por ambiente — esta máquina não consegue avançar sem mudança de infra

| ID | Descrição | Bloqueio exacto | Desbloqueio |
|---|---|---|---|
| **D3** | DeepEval via pytest (judge local via Ollama) | ~1GB RAM livre nesta máquina; menor modelo Ollama precisa de ~1.5GB | Máquina com mais RAM, ou Ollama remoto via HTTP |
| **D4** | Ragas `ToolCallAccuracy`/`ToolCallF1` | `pip install ragas` falha a compilar `scikit-network` — precisa de MSVC Build Tools (C++), sem wheel para Python 3.14/Windows | Visual Studio Build Tools, ou Python 3.11/3.12 (wheels disponíveis), ou ambiente Linux |
| **S19** | Oracle Free Tier como infraestrutura alternativa (24GB RAM, 4 OCPU ARM) desbloquearia D3+D4 | Requer confirmar IP público, acesso SSH e decidir âmbito — **já confirmado activo (S17)**, mas âmbito de uso ainda por decidir pelo utilizador | Ver S17/S20 acima — mesma VM, uso ainda por decidir |

---

## Ordem de execução sugerida

1. **Crítico de segurança primeiro** (fora do controlo directo desta sessão, mas é o que desbloqueia mais coisas): S15a + S17/S20 (rotação de credenciais, ambos já em curso pelo utilizador).
2. **100% Claude, alto valor, sem dependência:** B7 (expor langgraph+edit via MCP), E8 (script `knowledge_sources`), S24 (testes de `MCPServer.ts` na parte não-auth).
3. **Decisões humanas rápidas que desbloqueiam mais trabalho:** A23/S13 (CORS — 1 lista de origens), C2 (ADR TS-vs-Python, desbloqueia clareza sobre C3/C4/S11), A8 (key real do MCPServer — desbloqueia S11 e a parte crítica do S24).
4. **Cadeia B3→B5→B6** (precisa do `.env` real do Desenvolvedor) — uma vez desbloqueada, é a validação mais importante pendente ("o pipeline TS funciona ponta-a-ponta?").
5. **Resto do Grupo D (D5-D7)** — 100% Claude, sem pressa.
6. **Grupo E restante (E1-E7, E9)** — mecânico, baixo risco, pode ser feito em qualquer ordem.
7. **A9/A10** — assim que houver uma janela com rede liberada.
8. **Grupos G1-J** — só depois de A-F genuinamente fechados; G1 (financeiro) sozinho é maior que todo o Grupo A.

---

## Nota sobre completude

Cruzado contra `EXECUTION-PROMPTS.md` linha a linha (todos os 23+13+7+10+9+10+14+4+3+2+4+11+7 itens dos Grupos A-J, mais S15a/S15b/S18) e contra `STATUS.md` (secções 🔴🟠🟡🟢, checklist de 20 itens, mapeamento G1-G7, `## Done`). Nenhum item pendente de `EXECUTION-PROMPTS.md` ficou de fora desta lista — os únicos omitidos são os já fechados (Done/JÁ FEITO/N/A confirmado) e os ~30 itens dos Grupos G1-J que são resumidos como um bloco único (detalhe item-a-item preservado no documento original, não duplicado aqui para manter este relatório legível).

**Auto-crítica:** não recontei manualmente cada um dos ~40 itens dos Grupos G1-J individualmente neste documento (resumidos em bloco) — se algum deles tiver uma dependência ou prioridade especial não capturada no resumo, só está visível no `EXECUTION-PROMPTS.md` original.

---

## Actualização 2026-09-30 — regra A/B/C

A partir de 2026-09-30 nenhuma decisão humana fica em aberto: cada uma tem opções A/B/C e uma **recomendada** que se executa se o Dev não responder em 7 dias (`docs/audit/PLANO-DE-ACAO.md` §0).

- **Fechadas nesta data:** D1, D2, D3, RAG canónico (`knowledge_chunks`), `areas.yaml` v1, keep-alive (secrets + tabela), AU-13 (sobe ao ligar a deliberação), DB Plano B — ver `PLANO-DE-ACAO.md` §13.1.
- **Criados:** `docs/architecture/adr/ADR-META-AGENTS.md`, `docs/architecture/adr/ADR-DB-PLAN-B.md`, `config/areas.yaml`; campo `kind` em todos os agentes.
- **Em aberto com recomendação por omissão:** E1–E11 em `PLANO-DE-ACAO.md` §13.2 (ex.: E7 validação do `areas.yaml` em CI → recomendada A, script Python + passo no `runner-tests.yml`).
- Os itens das tabelas acima que dependiam das decisões D1–D3 seguem a classificação de `docs/audit/DECISAO-4-ordem.md` §4.2–4.4.
- **Acrescentados em 2026-09-30 (2.ª ronda):** J5-b, J5-c, E12, E13, E14, E15 em `PLANO-DE-ACAO.md` §13.2, todos com recomendada e prazo de 7 dias. `ADR-META-AGENTS.md` ganhou as secções 9–13 (desenho). O `runner/` do `agent-network-mcp` foi apagado; o material do J11 está em `runner/tests/test_mem0_connection.py` deste repo.

## Bloco A (parcial) — 2026-09-30

- **Fechados:** A8 (`8a1daca`, 21 agentes, também o A9), ruff do runner (`77bd6e2`), e2e (`cef2f24`, 3/3 com a API local + `E2E_API_KEY`). A8 e e2e estão só na `claude/audit-completo`; o ruff também está na `main` (PR #31).
- **J7: FEITO** — PR #30 merged (`7696ceb`), fecha o Dependabot #11.
- **J1: FEITO** (2026-09-30) — tabela + secrets; run #6 do keep-alive verde (30/09 17:31 UTC).
- **E15 (baixa prioridade):** quando aparecerem os originais do `CouncilSession`/`councils.yaml` (se existirem), substituir a reconstituição do ADR-META-AGENTS §12–13. E13 (C0–C3) e E14 (`active`) foram executados em 2026-09-30.

## J3 — RAG canónico (2026-09-30)

- **Código feito:** o ingest escreve na `knowledge_chunks` (`fbad7bb`); teste ingest → retrieve (`e3a404f`).
- **Migração: FEITA** (2026-09-30): 121 / 322 / 1 `match_knowledge` / `geo-agent.md` recuperável. PR #31 merged.
- **PENDENTE-DEV:** passos 3 e 5 de `docs/ops/RAG-CANONICAL.md` (ingest local, teste real no MCP) e depois apagar a t6 (passo 6, irreversível, com backup).
- ~~Até ao merge para a `main`, um push que toque em `docs/**/*.md` continua a ingerir na t6~~ — resolvido: o writer corrigido está na `main` desde o PR #31.

## Fecho de 2026-09-30

- **Fechados hoje:** J3 (RAG canónico, PR #31), J7 (PR #30), J1 (keep-alive verde), J6 (ledger de tokens em produção, PR #8 do `agent-network-mcp`), bug das 9 tools MCP (PR #9 do `agent-network-mcp`, em produção desde 27/09 até ao fix). Detalhe e evidência em `STATUS.md`, secção "Fecho das sessões de 2026-09-30".
- **Em aberto:**
  - J6: confirmar a 1.ª linha real em `token_usage` (passo 4 de `agent-network-mcp/docs/ops/TOKEN-LEDGER.md`; às 20:43 UTC havia 0 linhas porque ainda não tinha entrado nenhum pedido).
  - J3: passos 3 e 5 do RAG-CANONICAL e depois apagar a t6.
  - `log_execution` do MCP perde 4 campos (`capacidade_id`, `fast_path`, `custo_estimado`, `justificativa_full_cycle`): PR em curso.
  - **Integrar a `claude/audit-completo` na `main`:** 37 commits (A8, e2e, auditoria, ADRs, `areas.yaml`, `kind`, docs). Decisão do maestro.

## Dependabot — ronda de 2026-10-01

- **#25 (uuid 11 → 14 só no `apps/api`): ENTROU POR MERGE (não ficou fechado), por engano ou em simultâneo** com o fecho pedido. Merge `da0a894`, a 2026-10-01 às 00:28:17Z. O `package.json` passou a `uuid ^14` e o lockfile ficou em `^11.1.1`, por isso o `pnpm install --frozen-lockfile` falhava. A `main` ficou vermelha (CI run 36796345114) até à correção (a). A correção acabou por ser o merge do #29 (`3016466`, 00:29:47Z), que trouxe o lockfile atualizado: o CI run 36796468154 está verde e o `--frozen-lockfile` passa. Não houve revert. A branch foi apagada pelo Dependabot.
- **#28 (`psycopg[binary]` >=3.3.5 → >=3.3.6, runner): MERGED** (`45a401a`), depois do rebase manual pelo maestro.
- **#29 (uuid 11 → 14 + vitest 4.1.11 → 5.0.2): MERGED** (`3016466`, 2026-10-01 00:29:47Z). Estava marcado como bloqueado pelo S29-bis, mas entrou na `main`.
  - ~~**S29-bis:** alinhar `@vitest/coverage-v8` com o vitest 5.x e verificar que a cobertura volta a > 0%.~~ **RESOLVIDO** na branch `fix/coverage-v8-vitest5` (commit `5917392`).
    - **O problema:** em `3016466` o `@vitest/coverage-v8` estava em 4.1.11 e o `vitest` em 5.0.2. Os 195/195 testes passavam, mas a cobertura dava 0% e o comando saía com código 1 (`Expected string coverage payload`). O CI não corria cobertura e não deu por isso.
    - **A correção:**
      - `@vitest/coverage-v8` e `vitest` passam a `^5.0.3` (`package.json:24`, `:30`). O coverage-v8 5.0.3 exige o vitest 5.0.3 como peer, por isso ficar em `^5.0.2` voltava a misturar versões;
      - o lockfile foi regenerado;
      - o `ci.yml` ganha um passo de cobertura dos `tests/unit` com mínimo de 25% em lines e statements.
    - **Verificado localmente** (Node 22):
      - `--frozen-lockfile` OK;
      - `tests/unit` 195/195;
      - cobertura de `tests/unit` 27,96% stmts e 28,62% lines;
      - `pnpm test:coverage` 196/196 e 34,44%.
  - O `uuid@14` (só ESM) funciona com `require` em Node 20.19+ e Node 22. O CI está em Node 22.

## Bloco B — worker do modo `external` (AU-23), 2026-10-01

- **Feito (PR #40, merged `7610921`):** `runner/plan_runner/external_worker.py`.
  - Executa com o Gemini (flash-lite) cada passo `external`, escreve `result.json` e regista os tokens no formato do `token_usage`.
  - Respeita o HITL.
  - Integrado no executor e no motor `native` (`--worker gemini`). Também tem uma CLI standalone para runs parados.
  - Como correr: `docs/ops/WORKER-EXTERNAL.md`.
- ~~**B1 (DEV): primeiro run real.**~~ **FEITO a 2026-10-01 (maestro):** `seo-article-demo` com `--worker gemini`, do início ao fim (`done`), 4 chamadas, **13 130 tokens**: research 1 893, seo_brief 3 415, copy 3 659, critic 4 163. Detalhe em `docs/ops/WORKER-EXTERNAL.md`.
- **B2: ledger central.** Com `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` (projecto `agent-network-memory`), as linhas entram também no Supabase. Escrever em produção é decisão do DEV.
- **B3: tools.** O worker não executa o `tools_allowed` (ex.: `web_search`). Depende do porte do `ToolExecutor` (D1, VIA A).
- **B4: engine langgraph.** O worker inline só funciona no `native`; no langgraph usa-se `python -m plan_runner.external_worker <run>` + `resume`.
- ~~**B5: orçamento de tokens por run.**~~ **Feito** (PR `feat/token-budget`, empilhado no router): tecto por run, plano ou área; pausa em `paused_budget`; retoma com `resume --max-tokens`. Ver `docs/ops/BUDGET.md`.
  - ~~**B5-bis: valores de `budget.max_tokens` por área.**~~ **APLICADO** (decisão do maestro, opção A): produção 80k, risco 40k, exploratórias 30k, horizontal 20k, em `config/areas.yaml`. Rever depois do B1-bis-C.

## Bloco B — router hierárquico híbrido (D2), 2026-10-01

- **Feito (PR `feat/router-hibrido`, sem merge):** `runner/plan_runner/router.py`.
  - A área é escolhida por keywords do `config/areas.yaml`, com embeddings opcionais.
  - O agente ou o plano é escolhido pelo Gemini, só entre os candidatos da área e os horizontais.
  - Clarificação, ou HITL nas áreas de risco; "sem especialista" + HITL nas áreas vazias.
  - Execução no `plan_runner` com o worker.
  - Como correr e afinar: `docs/ops/ROUTER.md`.
- **R1 (DEV): avaliação real.** `python -m plan_runner.router eval` com `GEMINI_API_KEY` (~10 chamadas grátis). Os testes provam a área e a canalização; a escolha do agente pelo Gemini real ainda não foi medida.
- **R2: agentes para legal, gamedev e docs.** Hoje vão sempre para HITL ("sem especialista"), por decisão do `areas.yaml`.
- **R3: clarificação com estado.** Hoje a resposta do utilizador é um novo `route`.
- **R4: robustez das keywords.** Não há negação nem pesos. Rever depois do R1 com casos reais.

## Bloco B — testes lentos no CI (PLANO item 10, parte Python), 2026-10-01

- **Feito (PR #43, merged `9a273d4`):** job `test-slow` no `runner-tests.yml`, em paralelo com o `test`. Corre os 34 testes `slow` (planos reais, LangGraph, crash recovery), que o `pytest.ini` exclui por omissão e que nenhum CI corria. O default local não muda.
- ~~**Falta no item 10:** ingest→retrieve contra uma BD real no CI.~~ **Feito (PR #44, merged `c4d02fe`):** job `test-rag` com o serviço `pgvector/pgvector:pg16`.
  - O teste parte de ficheiros markdown e passa pelo ingest real (`scripts/ingest_apply.py::apply_one`: chunk → embed → `replace_chunks`), com um embedder falso determinístico (sem Gemini, custo zero). O retrieve é o `match_knowledge`, chamado como o MCP o chama.
  - 6 testes: os 3 J3, que existiam mas nenhum CI corria, mais 3 ponta a ponta: 1 doc → devolve esse doc; 2 docs com `agent_id` diferentes → cada agente só vê o seu; reingest não duplica.
  - `RAG_TEST_REQUIRED=1`: sem BD, o job falha em vez de saltar.
- **✅ PLANO item 10 COMPLETO** (#43 + #44 merged): testes lentos + ingest→retrieve no CI. O `/chat` TS deixou de se aplicar (D1, VIA A).

## Bloco B — B1-bis: optimização de contexto do worker, 2026-10-01

- **Feito (PR #45, merged `810d1fe`):** `runner/plan_runner/context_policy.py`, modo `opt` por omissão.
  - Pin + resumos gerados na mesma chamada, com schema fixo.
  - Grounding `slim` em marketing, docs e research; o E7 recusa `slim` nas áreas de risco.
  - Sem frontmatter nem secções de documentação no prompt; JSON compacto.
  - `PLAN_RUNNER_CONTEXT=legacy` para A/B e rollback.
- **Projecção calibrada no B1** (`python -m plan_runner.token_projection`): `seo-article-demo` 13,1k → **11,1k (−16%)**, critic `tokens_in` **−33%**. 8 passos (pior caso): 41,3k → 28,3k (−31%).
- ~~**B1-bis-R (maestro): run real** legacy vs opt~~ **FEITO, sem exercitar o `opt`** (ver a secção L4 abaixo e `docs/ops/WORKER-EXTERNAL.md`).
- ~~**B1-bis-R2 (maestro): repetir só o run `opt`**~~ **FEITO (2026-10-03), com o modo `opt` confirmado nos 4 passos: −22% real** (12 998 → 10 136; ~−16% atribuível ao `opt` com as saídas normalizadas, porque o copy escreveu 523 tokens a menos). research −20%, seo_brief +9% (gera o resumo), copy −31%, critic −41% (entrada do critic −44%). `opt` fica a omissão, agora medido. A hipótese "só compensa em 4+ passos" fica refutada. Detalhe em `docs/ops/WORKER-EXTERNAL.md`, "Medição real (B1-bis-R2)".
- ~~**B1-bis-9k (decisão)**~~ **DECIDIDO: opção C (maestro, 2026-10-01).** Fica o modo `opt` (−16% projectado, não verificado), e o caminho para <9k passa a ser o item próprio **B1-bis-C — encurtar skills/prompt-base** (PLANO item 12). **Não começar sem ordem.**

## Bloco L4 — memória persistente (D3), 2026-10-01

- **Feito (#47, merged `a941147`, 8 checks verdes):** L4 própria sobre o Supabase. Detalhe e operação em `docs/ops/MEMORY-L4.md`.
  - SQL: `scripts/create_memory_l4_table.sql` e `scripts/create_recall_l4_rpc.sql`.
  - Código: `runner/plan_runner/memory_l4.py` (`remember`/`recall`/`forget`/`promote` + HITL de promoção + CLI) e `memory_wiring.py` (worker).
  - 29 testes contra Postgres + pgvector, a correr no CI no job `test-rag`.
- ~~**L4-1 (DEV): correr os 2 SQL**~~ **FEITO (maestro, 2026-10-01)** no projecto `agent-network-memory`: tabela `memory_l4` e RPC `recall_l4` criadas, RLS activa, `anon`/`authenticated` com 0 privilégios na tabela, `anon` sem `EXECUTE` em `recall_l4`. Verificação 4/4 (tabela=1, rls=true, anon=0, rpc=1). Registo em `docs/ops/MEMORY-L4.md`.
- **L4-1b (DEV): teste real mínimo** da secção "Pôr em produção", passo 3 (`remember` → `recall --candidates` → `promote` → `recall` → `forget` em `project:teste-l4`, pela CLI, com o `DATABASE_URL` do projecto). Ainda não foi reportado.
- **L4-2: spike comparativo do mem0 (J11).** Fica para depois, por decisão D3, e é condição para qualquer auto-extracção (com flag).
- **L4-3: ligar o MCP de produção à L4** (ADR-M7). Hoje só o runner a usa.
- **B1-bis-R (maestro):** **FEITO, mas o braço `opt` correu com o prompt `legacy`**: −2,6% é variância da saída, não efeito do `opt`. Prompts-base idênticos ao token nos 4 passos (incluindo o `research`, sem inputs, que no `opt` perde 34% dos caracteres); o critic recebeu o brief completo; o seo_brief não gerou resumo. Tabela por passo e análise em `docs/ops/WORKER-EXTERNAL.md`, "Medição real (B1-bis-R)". A projecção (−16%) fica **não verificada**. O padrão "research/seo_brief gastam mais no opt" e a hipótese "o opt só compensa em 4+ passos" ficam registados como **hipóteses não confirmadas**, com contra-evidência. **Decisão do maestro: `opt` continua a omissão.** Lição de método em `docs/ops/WORKER-EXTERNAL.md`: só decidir com `usageMetadata` real ou `countTokens`, **e verificar o modo de cada braço antes de comparar**.

## Fecho do dia 2026-10-01

- **Bloco A (auditoria, ADRs, `areas.yaml`, `kind`, descrições J4, validador E7): FECHADO.**
- **Bloco B: FECHADO.**
  - Worker `external` (#40), router hierárquico híbrido (#41) e orçamento de tokens com pausa/resume (#42).
  - Optimização de contexto B1-bis (#45; o run real B1-bis-R não exercitou o `opt`) e tectos por área B5-bis (#46).
  - Testes lentos no CI (#43) e ingest→retrieve no CI (#44).
- **Bloco D, L4 (memória persistente): FECHADO** (#47) **e em produção** (L4-1 feito: SQL corrido, verificação 4/4). Falta o teste real mínimo (L4-1b).
- **"Pernas": todas as condições do PLANO §10 fechadas** (4 junções + 3 decisões + 4 construções = 11/11; o maestro conta-as como 6/6). Tabela com a evidência em `docs/audit/PLANO-DE-ACAO.md` §10, "Fecho de 2026-10-01".
- **Registado:** a tabela por passo do B1-bis-R (com a análise acima) e o L4-1 (4/4).
- **Por registar:** o R1 (`router eval` com o Gemini real) e o L4-1b (teste real mínimo). O B1-bis-R2 e o C-1 ficaram registados a 2026-10-03.
- **Próximo item: BLOCO C — CouncilSession** (deliberação interna entre meta-agentes, Fase 1 do ADR-META-AGENTS; PLANO J5-c). Decisão do maestro, 2026-10-01.
  - **Em PR #54** (sem merge): `runner/plan_runner/council_session.py`, `config/councils.yaml`, `agents/meta/chairman.agent.md`; operação em `docs/ops/COUNCIL.md`. **DONE com mock** cumprido: conselho `architecture` de ponta a ponta, veredicto estruturado, HITL aprovado, L4 candidate → active.
  - **Merged** (#54).
  - ~~**C-1 (maestro): custo real.**~~ **FEITO (2026-10-03):**
    - `countTokens`: entrada fixa 5 860, intervalo 5 860–22 756;
    - 1 ronda real: **11 760 tokens** (in 9 502, out 2 258), **14,7% do tecto de 80k**; 2 rondas ≈ 29% (extrapolação);
    - veredicto real `conditional` 0,85, gate `pass`, HITL `approve` (`human:souza`), `done`.

    Viável sem cortes. Detalhe em `docs/ops/COUNCIL.md`, "Custo medido (C-1)".
  - **C-2 (DEV): migração do ledger** no Supabase (`scripts/alter_token_usage_council_kinds.sql`). Até lá, as linhas do conselho ficam só no `token_usage.jsonl` local.
- **B1-bis-C (encurtar skills/prompt-base): próximo-grande, NÃO agora.** Com os tectos por área, o custo actual não é problema. Base medida no B1-bis-R2: 10 136, a 1 136 da meta de <9k. **Não abrir só porque não está <9k** (análise do Grok, 2026-10-03): o ganho real já apareceu.
- **Regra de uso do conselho (maestro, 2026-10-03):** 1 conselho ≈ 1 SEO. Não disparar por omissão: só para uma decisão estrutural (architecture / security / product) ou quando o router escala. Em `docs/ops/COUNCIL.md` e `docs/ops/BUDGET.md`.
- **Não fazer agora (análise do Grok, 2026-10-03):**
  - migrar os checkpoints SQLite → Postgres por causa do veredicto do C-1: é `conditional`, as condições não foram validadas, e o SQLite serve um só processo;
  - baixar o tecto dos conselhos para 15k.
- Outros candidatos, sem ordem: L4-2 (spike mem0), L4-3 (MCP de produção → L4).
- **Novo, para o B1-bis-C:** medir com o endpoint `countTokens` da API Gemini (contagem exacta da entrada sem gerar texto) em vez de projecções por caracteres.

## Meta-agentes, Fase 2: Execution Broker (registo, 2026-10-03; NÃO implementar)

Contrato arquitectural em `docs/architecture/META-AGENTS-PHASE-2.md`, a partir da análise do GPT (transcrita sem alterações). Vem **depois** do `CouncilSession` (Fase 1, `docs/ops/COUNCIL.md`): o conselho delibera e entrega uma **Decision**; a Fase 2 decide **quem executa** e garante que **só um** executa.

- **Fase 2: Execution Broker.** Escolhe o executor e decide entre EXECUTE / REDIRECT / WAIT / DEFER / BLOCK.
  - Usa um registo de *Execution Providers* (agent, skill, tool, workflow, modelo, serviço externo ou humano), com capabilities, ferramentas, quotas, custo e disponibilidade.
  - A selecção é por Execution Selection Score, sem ranking fixo de modelos.
  - O fallback é configurável e **sem downgrade silencioso** (`minimum_capability_match`).
  - Ao redireccionar, entrega um Execution Package ao novo executor.
  - Grava a selecção no ledger: `selected_executor`, `selection_reason`, `estimated_cost`, `selection_confidence`, `alternatives`.
  - Base existente: o registo de agentes por `kind` (`external_ai` está reservado), o tecto de tokens verificado antes de cada chamada, os estados retomáveis do `plan_runner` e o HITL para o BLOCK.
- **Fase 2: Execution Lease.** Um só executor por tarefa, com claim → lease (com expiração) → execute → observe → validate → release; os outros providers ficam a observar. Hoje nada impede dois executores com escrita de actuarem sobre a mesma intenção.
- **Fase 2: Learning (estimated vs actual).** Guardar a estimativa (`countTokens`) e o real (`usageMetadata`) por tarefa e provider, e comparar. O 1.º dado já existe: no C-1, o estimado era 5 860–22 756 e o real foi 11 760.
- **Teste de validação: o caso Grok + Claude em paralelo.** Os dois executaram a mesma intenção no mesmo projecto. Com a lease, um executa e o outro observa; uma execução sem lease é recusada e registada. Critérios em `META-AGENTS-PHASE-2.md`, "Teste de validação".
- **Pré-requisitos já registados:** o ledger J6 (existe) e a migração do `call_kind` dos conselhos no Supabase (C-2).

## Security pipeline v1: Capability First (branch `feat/security-pipeline-v1`, 2026-10-03)

- **Feito no branch (sem merge):**
  - pipeline `security.triage` → `meta.security-auditor` → `security.reporter` → HITL;
  - `config/security-capabilities.yaml` com 8 capabilities sobre 3 agentes; plano demo; `docs/architecture/SECURITY-AGENTS.md`.
- **Revisão e correcções (2026-10-03):**
  - E7 valida as capabilities e os `skill:` declarados (`runner/plan_runner/capabilities.py`), com 28 testes;
  - `--inventory` lista agente ↔ skill;
  - teste de ponta a ponta do pipeline (`tests/test_security_pipeline.py`, stub + external com Gemini falso);
  - o `report` recebe a triagem completa (`context.full`): sem resumo inútil;
  - a skill do reporter escreve o JSON só em rodapé;
  - os limites e as regras de segredos ficam documentados.
- ~~**SEC-1 (decisão): dar ficheiros do repo ao auditor em `--mode external`.**~~ **FEITO (opção A, 2026-10-03):** campo `repo_files` por passo (opt-in, só leitura, máx. 50 KB, exclusões fixas de segredos e credenciais), em `runner/plan_runner/repo_files.py`. O demo de security declara 5 ficheiros e o prompt do auditor passa de 641 para 11 436 caracteres. 36 testes novos. Regras em `docs/ops/WORKER-EXTERNAL.md` e `docs/architecture/SECURITY-AGENTS.md`. O `knowledge_refs` continua sem ser lido (AU-22).
- **SEC-2 (DEV): J10, `gitleaks`/`semgrep` no CI.** É o caminho para a capability `secrets_hygiene` (hoje `partial`), sem mandar ficheiros a um LLM.
- **SEC-3: pentest/red-team (`agent_redteam_lab`).** Continua `deferred` e fora do runner de produção.

### SEC-2: CI de segurança (gitleaks + semgrep), 2026-10-03

- **SEC-2: FEITO (opção A).** `.github/workflows/security-scan.yml`: gitleaks no histórico completo (bloqueia fugas novas) e semgrep (bloqueia achados novos ERROR/WARNING num PR; relatório no `main`). Versões e regras fixadas; actions fixadas por SHA. Linha de base e triagem em `docs/architecture/SECURITY-AGENTS.md`, "CI de segurança". Substitui o item "SEC-2 (DEV): J10" acima.
  - Fragmento da antiga `SUPABASE_SERVICE_ROLE_KEY` removido do `STATUS.md` actual; as 2 ocorrências do histórico estão no `.gitleaksignore`, com o motivo.
- **SEC-2b (DEV): confirmar no Supabase que a chave cujo fragmento estava no `STATUS.md` (S20) foi mesmo revogada.** O registo diz "rotacionada e apagada em 2026-09-19", mas o repo é público e o fragmento continua no histórico.
- ~~**SEC-2c: fixar por SHA as 20 actions dos workflows existentes**~~ **FEITO (2026-10-03):** as 17 `uses:` por tag (ci.yml 4, runner-tests.yml 7, release.yml 4, ingest-knowledge.yml 2; o keep-alive.yml não usa actions) ficaram fixadas por SHA, no commit actual de cada tag móvel (sem mudar de versão) e com a versão em comentário. Os 20 achados do semgrep eram 17 `uses:`; 3 contavam 2× (regra de tag mutável + regra de third-party). `actionlint` e semgrep (github-actions): 0 achados nos 6 workflows. Total do repo: 85 → 65.
- **SEC-2d: triagem da linha de base do semgrep** (65 achados depois do SEC-2c: 11 ERROR falsos positivos, 43 WARNING de código, 11 INFO): marcar os falsos positivos (`# nosemgrep: <regra>` com motivo) para o relatório do `main` ficar só com o que é real.

