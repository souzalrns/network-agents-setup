# AUDIT-6 — Lacunas estruturais, retificações, inclusões, ligações e ferramentas pendentes

> **Base:** commit `3dc3b25`. **Data:** 2026-09-29.
> **Método:** síntese das Fases 1–5, mais um varrimento de 45 nomes de ferramentas em docs vs. código/dependências (`grep -rliE` em `*.md` vs. `runner/ packages/ apps/ mcp/ scripts/`). Leitura das avaliações existentes (`memory/FASE2-MEMORIA.md`, `memory/FASE4-SINTESE.md`, `evaluation-audit/AUDIT-EVALUATION.md`) para não refazer veredictos já tomados.
> **Regra:** a coluna "Estado" distingue **ligado** (corre em código ou CI), **existe mas desligado** e **não existe**. As sugestões de bibliotecas externas que não estão avaliadas em nenhum doc do repo vão marcadas **"sugestão — a validar"**: não foram verificadas nesta auditoria.

## Resumo

O que separa o repo da visão (poupar tokens, ingestão robusta, memória persistente, custo zero, um maestro que delega por área) não é falta de peças. São **quatro junções partidas**:

1. o pedido nunca chega ao LLM (AU-13);
2. o RAG escreve numa tabela e lê de outra (AU-19);
3. há dois maestros sem ponte (AU-07);
4. os tokens nunca são contados (AU-16).

À volta delas: memória L4 inexistente, HITL volátil, zero agentes para os 3 nichos novos e nenhum worker para executar o que o motor Python planeia. Das 45 ferramentas externas pesquisadas, **nenhuma está em código ou dependências deste repo**: as 4 ocorrências encontradas (LightRAG, Cognee, AgentMesh, Cedar) são comentários (`working_memory.py:4`, `ActionReceipt.ts:11`). Algumas estão ligadas **noutro sítio**: yt-dlp/whisper no MCP, CodeQL/Dependabot no GitHub.

---

## 6.1 Lacunas estruturais (buracos, não itens) `[PEDIDO]`

| # | Lacuna | Confirmação desta auditoria | Porquê é crítica | O que implicaria resolver | Impacto |
|---|---|---|---|---|---|
| L1 | **Não há teste end-to-end** | Confirmado. O e2e TS (`tests/e2e/api.test.ts`) precisa de servidor e nunca corre em CI. O teste de integração é falso-verde (AU-17). O e2e Python (34 testes lentos) existe e passa (195/195), mas **o CI não o corre** (AU-09) | Q1–Q4 (Fase 2) sobreviveram por falta dele | (a) job CI com Postgres+pgvector (já existe no `ci.yml`) + `apps/api` a arrancar + um pedido `/chat` com LLM mockado por HTTP; (b) `-m ""` no CI Python; (c) teste ingest→retrieve (AU-19) | **Crítico** |
| L2 | **"Auth é `return true`"** | **Refutado para o caminho real, com nuance.** A API HTTP é fail-closed com `API_KEY` (`auth.ts:55-95`); o `verifyPassword` já é bcrypt (`d00cad5`). **Continua verdade:** MFA fixo `'123456'` (`SecurityManager.ts:239`, código sem uso); **uma só chave partilhada**, sem identidade por chamador na API; `mcp/plan_runner` em `moderate` autoriza mutate sem chave; o `MCPServer` TS tem auth real, mas não está montado | A lacuna real é de **identidade e autorização**, não de autenticação | RBAC/identidade (A13, S25, EX-C3/C4) só quando houver multi-tenant; remover o MFA morto (AU-42) | Médio |
| L3 | **HITL não durável no caminho real** | Confirmado. `HitlManager` = 5 `Map`s (`:90-94`); polling de 5 min que bloqueia o pedido HTTP; **não há retoma depois do `approve`** (AU-18); a ponte para ficheiros (M2) não tem chamadores. O HITL **Python** é durável (ficheiros jsonl + `resume`, verificado) | O objectivo "ordens autónomas com budget" (trader) **exige** HITL durável e retomável | M4 (Postgres) + modelo assíncrono (AU-18) + M3 (e2e); **ou** adoptar o HITL Python como o único (se o maestro for Python, AU-07) | **Crítico** |
| L4 | **`toolsAllowed` nunca gerado** | Confirmado (AUDIT-2 §2.2). No Python existe como campo declarativo, mas é só informativo | Sem tools, os agentes não actuam no mundo (dados de mercado, repos, web) | Decidir a fonte (AU-20) e aplicar no boundary (Python: validar no worker; TS: no Executor) | **Alto** |
| L5 | **Ingestão de conhecimento fragmentada** | Confirmado. 2 pipelines (Python/Gemini em CI; TS/`openai` jurídico manual); 2 definições de schema (Prisma + SQL); 2 tabelas de chunks (`knowledge_chunks` MCP, 210; `knowledge_chunks_t6` setup, 110) **e o retrieve lê a errada** (AU-19); as transcrições de reels (`transcripts`, MCP) não entram no RAG (AU-44); E1–E7 (web/PDF/código) por adoptar | "Ingestão robusta" é pilar da visão; hoje o que se ingere não se recupera | Uma pipeline, uma tabela canónica (ou RPC por tabela), um modelo de embedding; teste ingest→retrieve; conectores novos um a um (E1–E7) | **Crítico** |
| L6 | **Memória persistente não unificada** | Confirmado. Há 6 "memórias" sem ponte: L1 `events.jsonl` (por run); `session_search` (FTS por run); `MEMORY.md` por cliente (só leitura, manual); L4 (**0 código**, S29); L5 RAG (partido, L5 acima); Prisma `conversations`/`messages` (órfãos, AU-40); e ainda o `transcripts`/`project_state` do MCP | Sem L4 não há "lembrar" entre sessões, que é pilar da visão | Decidir S29 (**a síntese FASE4 recomenda L4 próprio, pequeno, no contrato `contracts.md`**) e reconciliar com o teste de mem0 do utilizador (6.5); definir que camada é a fonte de verdade | **Alto** |
| L7 | **Não existe um maestro** `[ACRESCENTADO]` | TS bloqueado (AU-13); Python sem planeador dinâmico nem worker (AU-23); o router real vive no MCP (Gemini), fora deste repo | É o centro da visão | ADR (AU-07/EX-C2) + registo de áreas (AU-33) + router com confiança (AU-34) + worker (AU-23) | **Crítico** |
| L8 | **Os tokens não são medidos, logo não se pode reduzir o que não se mede** `[ACRESCENTADO]` | `totalTokens` nunca somado (AU-16); orçamento não aplicado (AU-49); `TokenEconomy` MOCK; `model_tier`/`max_cost_usd` só no schema (D5/D6); só OpenAI (`gpt-4-turbo` por omissão) | O objectivo n.º 1 da visão não tem instrumento | Ledger de tokens por passo e agente (persistido); orçamento aplicado; provider barato (M6); cache de respostas e RAG com grounding em vez de contexto inteiro | **Crítico** |
| L9 | **Nenhum agente corre sozinho** `[ACRESCENTADO]` | TS: bloqueado. Python: `external` espera worker; `stub` escreve placeholders | "Vários agentes por área" pressupõe execução | Worker de custo zero (AU-23) ou desbloquear o TS (AU-13/14/15) | **Crítico** |
| L10 | **Infra de persistência frágil** `[ACRESCENTADO]` | O keep-alive nunca funcionou (AU-47); a VM Oracle com chave antiga (S20); o build TS não gera artefacto (AU-01) | O free-tier do Supabase pausa com inactividade | Secrets do keep-alive + tabela; S20; AU-01 | Alto |

---

## 6.2 Retificações de estrutura — lista priorizada `[PEDIDO]`

Consolida a Fase 1 §1.3 (R1–R13) com os achados das Fases 2–5, ordenada pelo que serve a visão.

| Prio. | ID | Retificação | Serve a visão em… | Quem |
|---|---|---|---|---|
| 1 | R8 / AU-07 | **Escolher o maestro** (Python `plan_runner` + planeador + worker, **ou** TS `Orchestrator` desbloqueado, **ou** o router do MCP) e registar num ADR | Maestro + delegação | DEV |
| 2 | AU-19 / R6 | **Uma pipeline, uma tabela e um retrieve para o RAG**; desligar a pipeline TS ou a Python | Ingestão + tokens (grounding) | AMBOS |
| 3 | AU-33 | **Registo único de áreas** (`config/areas.*`) consumido por router, config e runner | Delegação por área | DEV decide, CLAUDE implementa |
| 4 | AU-13/14/15/16 | Desbloquear o caminho TS (se for mantido) — 4 correcções pequenas e testáveis | Maestro TS | CLAUDE (AU-13: AMBOS) |
| 5 | AU-23 | **Criar o worker** do modo `external` (LLM de custo zero) | Custo zero + execução | AMBOS |
| 6 | L8 | Ledger de tokens + orçamento aplicado + provider barato (M6/D5/D6) | Tokens + custo zero | AMBOS |
| 7 | R4 / AU-01 | `tsconfig` por pacote → `pnpm build` funcional (só se o TS ficar) | Deploy | AMBOS |
| 8 | R7 / AU-38 | Partir `packages/core`: `orchestrator/`, `governance/` (reais) e `experimental/` (18 órfãos) | Clareza; menos contexto a ler (tokens) | DEV aprova, CLAUDE move |
| 9 | R1–R3, R5, R9, R11 | Limpeza: `apps/web`, `packages/langgraph`, `tests/package.json`, `Dockerfile`/`k8s`, `skills/claude`, `.specify` | Menos ruído | AMBOS/CLAUDE |
| 10 | R10 / R13 / AU-12 / AU-45 / AU-46 | Documentação: arquivar `docs/STATUS.md`; partir o STATUS de 95 KB; um só índice; resolver colisões de IDs; regenerar o OPEN-ITEMS; errata no `CORE-MAPPING` (AU-37) | **Tokens no bootstrap** (cada sessão lê estes ficheiros) | CLAUDE |
| 11 | AU-31 / AU-32 | Resolução agente↔skill por frontmatter; corrigir o template de design | Delegação Python | CLAUDE |
| 12 | R12 / AU-08 | `.env.example` completo | Onboarding | CLAUDE |

---

## 6.3 Sugestões de inclusão — o que o projecto devia ter e não tem `[PEDIDO]`

| Inclusão | Tipo | Justificação | Quem |
|---|---|---|---|
| **Teste e2e em CI** (Postgres/pgvector + `apps/api` + LLM mockado por HTTP) | Testes | L1; teria apanhado Q1–Q4 | CLAUDE |
| **Teste ingest→retrieve** contra o Supabase de staging (ou pgvector local) | Testes | L5; teria apanhado AU-19 | AMBOS (acesso) |
| **Job CI para os testes lentos do runner** | Testes/CI | AU-09 | CLAUDE |
| **`config/areas.yaml`** (registo de áreas: id, palavras-chave/descrição, agentes, skills, tools, orçamento, política HITL) | Pacote/config | AU-33; base para o router e para a delegação | DEV desenha, CLAUDE implementa |
| **Ledger de tokens** (tabela `token_usage`: run, step, agente, modelo, tokens in/out, custo) | Dados | L8; mede o objectivo n.º 1 | CLAUDE |
| **Worker de custo zero** para `pending_steps/` (ex.: Gemini Flash Lite, já usado no MCP) | Runtime | L9/AU-23 | AMBOS |
| **ADRs para as decisões pendentes** (maestro, RAG, memória L4, provider) em `docs/architecture/adr/` (hoje só existe `ADR-001`) | Docs | Várias decisões bloqueiam há semanas (S29, EX-C2, M5, S13…) | CLAUDE redige, DEV decide |
| **Área de segurança com dono** (agente orquestrador de segurança + gate de CI: gitleaks/semgrep, que já constam no B2b) | Segurança | Nicho declarado; hoje o `security_auditor` nem é resolúvel pelo runner (AU-31) | AMBOS |
| **Lockfile Python** (`uv.lock`) | Supply chain | A9; o lado Python é inverificável | AMBOS (rede) |
| **Gerador do STATUS** (a partir de ficheiros por item, em vez de um markdown de 95 KB editado à mão) | Docs/processo | AU-12/AU-45/AU-46: colisões e desactualização recorrentes | CLAUDE |
| **`CODEOWNERS`/dono por área** — sugestão, a validar | Processo | Hoje "Claude/Dev" decide ad hoc; com várias áreas é preciso dono | DEV |
| **Contrato de handoff maestro→agente** (entrada, saída, tools, orçamento, critério de feito) | Contrato | AUDIT-3 D7 | AMBOS |

---

## 6.4 Repositórios, skills e ferramentas a ligar, por área `[PEDIDO]`

Legenda: **L** = ligado · **D** = existe no repo mas desligado ou só documentado · **N** = não existe.

### Transversal (maestro, memória, custo, observabilidade)

| Necessidade | Já existe no repo (estado) | Falta criar/ligar | Externo (estado da avaliação) |
|---|---|---|---|
| Router/maestro | `Router.ts` (L, keywords, bloqueado por Q1); `routeWithConfidence` (D); router Gemini do MCP (L, fora do repo) | Registo de áreas; router com confiança/LLM | — |
| Provider LLM custo zero | `OpenAIProvider` (L); Gemini só para embeddings (`embedder.py`, L) | `GeminiProvider` (M6) | **LiteLLM Router + Budget Manager: ADOPT** (`AUDIT-EVALUATION.md:42`), **não instalado** (D) |
| Memória L4 | Contrato `memory/contracts.md` (D) | Implementação (S29) | mem0/LightRAG/Cognee/Graphiti avaliados: **"não adoptar nada agora"** (`FASE4-SINTESE.md:18`) |
| RAG L5 | Ingest Python (L), `McpKnowledge` (L, tabela errada) | RPC/tabela canónica (AU-19) | — |
| Observabilidade | `Tracer.ts` (L, OTLP opcional); `Metrics` em RAM (L) | Ledger de tokens | OpenTelemetry SDK (S14, D); Langfuse (avaliado, D) |
| Avaliação | Golden set? **N** | Harness de avaliação | DeepEval **ADOPT** (D, bloqueado por RAM, D3); Ragas ADAPT (D, D4) |

### Marketing

| Necessidade | Já existe (estado) | Falta | Externo |
|---|---|---|---|
| Agentes/skills | 17 agentes + 16 skills + 9 templates (L no Python via worker); 3 agentes na config TS (bloqueados) | Unificar nomes (AU-36); worker | `google/skills` (INIT-093, D, "valor alto") |
| Ingestão web/doc | — (N) | Conectores | Crawl4AI/Trafilatura/MarkItDown/Docling/gitingest (E1–E7, D, com CVEs registados em `AUDIT-INGESTION.md`) |
| Análise de conteúdo (reels) | `transcript_analysis` + `content_analyst` (D); `transcribe.yml` + tabela `transcripts` no MCP (L, outro repo) | Template + leitura de `transcripts` + ingestão no RAG (AU-44) | yt-dlp/faster-whisper (L no MCP; D aqui) |
| AI Visibility (Item 13) | Playbook + knowledge (L como docs); `AIVisibilityEngine` (MOCK, órfão) | Medição real | — |

### Financeiro / Trader (nicho novo)

| Necessidade | Já existe (estado) | Falta | Externo |
|---|---|---|---|
| Área + agentes | `financial-analyst` (D, sem prompt); `investimentos-brasil` (L no MCP, só análise); `agents/gestao/contabilidade` (D) | Área `finance` no registo; papéis de AUDIT-3 §3.4 | — |
| Dados de mercado | **N** | Conector de dados (tool) | Fontes em G1.2 (World Monitor/Finance News, AGPL: licença a avaliar); APIs de cotações B3/globais — **sugestão, a validar** |
| Simulação / paper trading | **N** | Motor de simulação + backtest | MiroFish (B6, AGPL, D); bibliotecas de backtesting — **sugestão, a validar** |
| Ordens com orçamento | `DeliberationEngine` (L, reutilizável para gates); HITL Python (L) | Guardião de orçamento; **isolamento de credenciais (G1.5)**; HITL durável | API de corretora **só em modo paper** até decisão — **sugestão, a validar** |

### Jogos (nicho novo)

| Necessidade | Já existe (estado) | Falta | Externo |
|---|---|---|---|
| Área + agentes | Router envia "jogo" para `software` (L, **0 agentes → erro**, AU-30); desenho P-AG-019 (D) | Área `games`; papéis de AUDIT-3 §3.4 | — |
| Engine / GDD | **N** | G2.1–G2.3 (pesquisa, escopo, engine) | Godot/Unity/Unreal — **sugestão, a validar** (G2.3) |
| Multijogador | **N** | Netcode/servidor | Servidores de jogo open-source — **sugestão, a validar** |
| Imagens → 3D | **N** | Pipeline de assets | Geração 2D/3D e validação glTF — **sugestão, a validar**; o `audit-tools.yml` do MCP já vigia a categoria "image/video generation" (L lá) |

### Segurança (nicho novo — "responsável por todos os itens")

| Necessidade | Já existe (estado) | Falta | Externo |
|---|---|---|---|
| Área + dono | `security_auditor.agent.md` (D, **não resolúvel**, AU-31); skills `security-audit` e `security-and-hardening` (D) | Área `security`; orquestrador de segurança; backlog triado (B2c) | — |
| Scanners | CodeQL (L, "Push on main" ✅); Dependabot (L); 5/8 ferramentas corridas uma vez (B2) | Gate de CI (gitleaks/semgrep/bandit/OSV/Trivy) | As 8 do B2b (D; Trivy/OSV bloqueados por rede) |
| Guardas de runtime | `ToolPolicy`, `SsrfGuard`, `ActionReceipt`, `McpAuth` (L em TS, mas o `MCPServer` não está montado); `policy.py` (L em Python) | `query_database` read-only (AU-48); identidade (EX-C3), políticas (EX-C4) | AgentMesh/Cedar (D, por aprovar) |

### Restantes áreas (design, engenharia, gestão, jurídico, saúde, construção, atendimento, produto)

As peças estão listadas em AUDIT-3 §3.3. O padrão é o mesmo em todas: há **knowledge ou agentes `.md` (D)** e verticais reais **no MCP (L, fora)**, mas **faltam template, entrada no registo de áreas e agente com prompt no runtime escolhido**. As tools jurídicas TS (`brazilian-law`, `portuguese-law`) estão **L**, com fallback simulado honesto e base vazia até se correr o `pnpm ingest` (AUDIT-4 §4.2).

---

## 6.5 Ferramentas pendentes — instalar, analisar, avaliar `[PEDIDO]`

**Sobre "Deep Hardness Obsidian":** **não existe nenhuma referência com esse nome** no repo (grep `hardness|deep harness`: 0). As correspondências prováveis estão abaixo em duas linhas separadas: **Obsidian/Logseq** (F10 = G4.1 = I8) e **deepseek-harness** / `dsh-long-memory` (INIT-094 = EX-F8; opção do S29). **NÃO VERIFICADO:** confirmar com o utilizador qual das duas (ou outra) era a pretendida.

| Ferramenta | O que é | Para que serve aqui | Estado actual | Quem decide | Evidência |
|---|---|---|---|---|---|
| **Obsidian vs. Logseq** | Editores de notas em grafo | Grafo de memória / U1 | **Pendente de decisão** (REAL segundo o `AUDIT-SCOPE`) | DEV | `EXECUTION-PROMPTS.md:2050`; `AUDIT-SCOPE-2026-09-19.md:131` |
| **deepseek-harness / `dsh-long-memory`** | Harness multi-provider; plugin de memória longa | L4 (opção do S29); harness (INIT-094) | **Em análise.** O `dsh-long-memory` "não é biblioteca instalável" (é padrão a reescrever) | DEV | `FASE4-SINTESE.md:10`; `STATUS.md:162` |
| **mem0** | Memória semântica para agentes | L4 | **Avaliado: não adoptar agora** (exige vector store externo). **Conflito:** o utilizador testou-o localmente (`runner/tests/test_mem0_connection.py`, fora do repo, com `SUPABASE_DB_CONNECTION_STRING`, nome que o repo não usa; o canónico é `DATABASE_URL`) | DEV (reconciliar com S29) | `FASE2-MEMORIA.md:29-44`; `FASE4-SINTESE.md:18,52` |
| LightRAG / Cognee | RAG em grafo / memória episódica | Memória por cliente | **Só design** ("não implementado"); citados num comentário de `working_memory.py:4` | DEV | `memory-integration.md`; `ECOSYSTEM.md:68` |
| Graphiti, Hindsight, MELD, Stigmem, ai-memory-mcp | Memória | L4/L6 | Avaliados; MELD sem implementação | DEV | `FASE4-SINTESE.md:26` |
| **LiteLLM** | Router de modelos + orçamento | Custo zero, `model_tier` (D5), orçamento (D6) | **ADOPT recomendado, não instalado** | DEV (nova dependência) | `AUDIT-EVALUATION.md:15,42` |
| **DeepEval** | Avaliação de agentes (pytest) | Qualidade e regressão | **ADOPT recomendado**, bloqueado por RAM (D3) | DEV (infra) | `STATUS.md:88` |
| Ragas | Métricas de tool-use | Avaliação | ADAPT; bloqueado só em Windows (D4) | AMBOS | `STATUS.md:89` |
| Langfuse | Observabilidade LLM | Custo e traces | Avaliado; não instalado | DEV | `FASE3-MEMORIA.md` §5 |
| OpenTelemetry SDK | Tracing padrão | Substituir o `Tracer.ts` | Pendente de decisão (S14) | DEV | `STATUS.md:90` |
| AgentMesh / Cedar | Identidade / políticas | ADR-001, B16 | Pendente de aprovação (EX-C3/C4) | DEV | `OPEN-ITEMS.md:51-52` |
| AGT (Microsoft Agent Governance Toolkit) | Governança | Roadmap de governança | Só roadmap (16 docs, 0 código) | DEV | `ECOSYSTEM.md:67`; `ROADMAP-GOVERNANCE.md` |
| Crawl4AI, Trafilatura, MarkItDown, Docling, gitingest, ScrapeGraphAI, Firecrawl | Ingestão web/doc/código | L5 | **Pesquisados** (E1–E7, com CVEs), **não instalados** | AMBOS (confirmar deps) | `AUDIT-INGESTION.md`; `OPEN-ITEMS.md:20` |
| yt-dlp + faster-whisper | Transcrição | Reels → RAG (AU-44) | **Ligados no MCP**, não aqui | AMBOS | `STATUS.md:426,429` |
| GLiNER2 | Extracção barata de entidades | Skill `cheap-entity-extraction` | Skill escrita (D); o código `tools/gliner2` está no MCP | AMBOS | G-skill-3 |
| SkillOpt | Auto-optimização de skills | Skill `skill-self-optimization` | Skill escrita (D) | AMBOS | G-skill-4 |
| `google/skills` | 132 manuais oficiais | Marketing (`media_buyer`, `ad_creative`) | Pendente (INIT-093, "valor alto") | AMBOS | `STATUS.md:173-177` |
| Graphify | Grafo de código | Consulta de código barata em tokens | Usado localmente no MCP (gitignored); aqui F2/I2 "research" | DEV | `STATUS.md:279` |
| spec-kit (`.specify/`) | Spec-driven para Copilot | Processo | **Instalado** (ficheiros), uso não verificado; PowerShell/Copilot | DEV | `.specify/init-options.json` |
| uv | Gestor Python | Lockfile (A9) | Pendente | AMBOS | `docs/architecture/uv/README.md` |
| Hermes | Runtime/worker | Possível worker (AU-23) | Pendente (B5) | DEV | `STATUS.md:102` |
| Ruflo, OmniRoute, Obscura(-mcp), gstack, Karpathy Skills, SOUL.md, Soup, Caveman | Diversos (F1–F17) | Vários | backlog / research / parked / N/A | DEV | `STATUS.md:278-299` |
| World Monitor, Finance News Aggregator, MiroFish | Dados/simulação financeira | Nicho trader | candidate / backlog (AGPL a avaliar) | DEV | `STATUS.md:297-298`; B6 |
| Ollama | LLM local | Judge DeepEval; custo zero offline | Pendente (RAM) | DEV | D3 |
| 6 harnesses multi-provider (deepseek-harness, omnigent, opencodex, qm, grok-build, dsh-desktop) | Harnesses | Multi-provider | Por reavaliar (INIT-094) | CLAUDE (pesquisa) | `STATUS.md:158-169` |
| A2A | Protocolo agente-agente | — | REFERENCE, não adoptar (P4) | — | `STATUS.md:413` |

**Pendência operacional obsoleta:** `docs/pending/2026-09-07-git-pull-and-docs.md` pede um `git pull` local, mas o `REPOSITORY-MAP.md:14` já confirma as cópias sincronizadas a 2026-09-20. Pode ser fechada (CLAUDE).

---

## Limites desta fase

- As sugestões externas marcadas "a validar" não foram pesquisadas nesta auditoria. Servem para mapear **tipos** de dependência, não para escolher bibliotecas.
- O varrimento "docs vs. código" é por nome (grep). Uma ferramenta referida sob outro nome escapa.
