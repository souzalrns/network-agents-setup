# Status — pendências consolidadas

> Gerado em: 2026-09-13
> Base: leitura do repo + cruzamento com sessões
> Método: tudo o que foi discutido e não está feito, classificado
>
> **Regra de IDs:** itens fechados vão para a secção `## Done` — não são apagados.
> IDs nunca são reciclados. O próximo ID livre na série C é **C8**.
> O ID **C5** pertence ao item antigo (auth do `mcp/route.js`, já em `Done`).
> O item "alimentar RAG" passa a ser **C8** (estava duplicado como C5).
> O ID **S6** pertence ao módulo `hitl.py` (S6a, feito em `cdae963`+`3445229`).
> A integração (S6b) passa a ser **S9**.
> O ID **S2** está dividido: **S2a** (Python) feito; **S2b** (Node) feito em `4d14f8f`+`6c87b42`+`c468081`.

## 🔴 Crítico (bloqueia outras coisas ou é risco real)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **C4** | **T6 ingestão é stub** — 33 knowledge packs de marketing não estão em RAG nenhum → **ver C8** (mesmo item, consolidado) | 1 dia | RAG funcional | Auditoria Claude |
| **C8** | **Alimentar RAG continuamente** (T6 é stub) — C8d + C8a-1 feitos; falta C8a-2 (embed), C8b (Supabase), C8c (workflow), C8e (McpKnowledge) | 1 dia | RAG funcional | Nossa |

## 🟠 Alto (resolve problema real, valor claro)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **S5** | **Fase 1.5** — `validate:consistency` + wiring marketing + import runner (provavelmente já feito — `ci.yml` corre `validate:consistency`) | 1h | Consistência | Auditoria Claude |
| **S9** | **Fase A.2b** — integração do `hitl.py` em `engine.py`/`langgraph_engine.py`/`cli.py` (dupla-escrita; aditivo) | 3-4h | HITL durável | Nosso |

## 🟡 Médio (valor claro, sem urgência)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **M1** | **Session search** (FTS5 sobre `events.jsonl`) | 4h | Nada | Nossa |
| **M2** | **Fase A.3** — lado TypeScript (`HitlManager.importFromFile/exportToFile`) | 1 dia | HITL sync | Nosso |
| **M3** | **Fase A.4** — teste end-to-end HITL (Python → Node → Python) | 0.5 dia | Validação | Nosso |
| **M4** | **Fase 2 (Claude)** — HITL durável em Postgres | 3-4 dias | Produção | Auditoria Claude |
| **M5** | **Fase 3 (Claude)** — mover ~14 módulos sem consumidor para `packages/experimental/` | 3-5 dias | Clareza | Auditoria Claude |
| **M6** | **Fase 4 (Claude)** — GeminiProvider (custo zero) + Planner com scope/unknowns/pre_mortem/not_doing | 2-3 dias | Custo zero | Auditoria Claude |
| **M7** | **Fase 5 (Claude)** — piloto real de marketing (`seo-article` em modo external com caso real) | 1 semana | Prova de valor | Auditoria Claude |

## 🟢 Baixo (nice to have)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **B1** | **Fase 6 (Claude)** — expansão para 2.º domínio (agents + skills + templates + wiring) | 1 semana | Nada | Auditoria Claude |
| **B2** | **Agente de cibersegurança** (defensivo, NIST + OWASP isolado) | 2-3 dias | Nada | Nossa |
| **B3** | **Agente de trading** (simulação only, sem ordens) | 3-5 dias | Nada | Nossa |
| **B4** | **Agente gamedev** (GDD, loop, engine) | 3-5 dias | Nada | Nossa |
| **B5** | **Hermes como runtime** (não interface) — worker para browser/vision | 1-2 dias | Nada | Nossa |
| **B6** | **MiroFish para simulação** (repo isolado, AGPL — uso interno) | 1 dia | Nada | Nossa |

## ⏸️ Arquivado (não fazer agora)

| ID | Item | Razão |
|---|---|---|
| **P1** | `INIT-100` — PCU Constitution | Formalismo, não resolve problema real |
| **P2** | `INIT-101` — META Compiler / MCL | Over-engineering |
| **P3** | `INIT-102` — AR-000 a AR-015 | Idem |
| **P4** | A2A (agentes a conversar) | Complexidade prematura |
| **P5** | UI visual (Langflow, n8n) | Sem dor real |
| **P6** | Multi-provider LLM | Só quando houver necessidade |

---

## 🔒 Segurança (checklist de 20 itens)

> Origem: checklist externa (reel `_danielllcruz`)
> Aplica-se sobretudo ao `agent-network-mcp` (produção)
> Classificação: ✅ feito · ⚠️ parcial/verificar · ❌ falta · N/A não aplica

| # | Item | Estado | Onde / Nota |
|---|---|---|---|
| 1 | Esconder API Keys | ✅ | `.env` + `.gitignore` |
| 2 | Limpar secrets do git | ✅ | Nunca foi commitado secret |
| 3 | Public Key DB | N/A | Não usas JWT próprio |
| 4 | Ativar RLS | ⚠️ verificar | Postgres/Supabase — confirmar se RLS está ativo |
| 5 | Criptografia de dados | ❌ | Dados sensíveis (processos jurídicos) em repouso |
| 6 | Auth server-side | ✅ | `auth.ts` fail-closed (commit `1a3e613`) |
| 7 | Restringir acessos (RBAC) | ❌ | Falta roles no `auth.ts` |
| 8 | Bloquear Mass Assignment | ❌ | Zod valida, mas endpoints aceitam campos extra |
| 9 | Proteger cookies | ⚠️ verificar | `httpOnly`/`secure`/`sameSite` |
| 10 | Hash nas senhas | ✅ | Supabase Auth |
| 11 | Rate limit | ❌ | Não existe |
| 12 | Bot protection | ❌ | Não existe |
| 13 | Queries parametrizadas | ✅ | Prisma faz automaticamente |
| 14 | Validação dos inputs | ⚠️ | Zod (Node) + YAML (Python) |
| 15 | Vazar conteúdo | ⚠️ | Mensagens de erro podem revelar stack traces |
| 16 | Restringir uploads | ❌ | Produção tem `extrair-imagem` |
| 17 | Trim respostas | ⚠️ | Depende — `plan_runner` devolve JSON estruturado |
| 18 | Add security headers | ❌ | CSP, X-Frame-Options, etc. |
| 19 | Forçar HTTPS | ✅ | Vercel faz por defeito |
| 20 | Scam de dependências | ⚠️ | Dependabot ativo; `audit-tools.yml` corre |

**Prioridade para produção (`agent-network-mcp`):**
- 🔴 Rate limit (11), Bot protection (12), Security headers (18)
- 🟠 RBAC (7), Cookies (9), Criptografia (5)
- 🟡 Mass assignment (8), Trim (17), Dependências (20)

---

## 🧰 Harnesses multi-provider (2026)

> Origem: reels `sebastianhardy_` (setembro 2026)
> Contexto: 2026 é o ano dos harnesses multi-provider. Todos competem em "qualquer modelo, qualquer IDE, multi-agente".

| Projeto | Stars | O que é | Relevância |
|---|---|---|---|
| **`deepseek-ai/deepseek-harness`** | 200k | MIT. "Everything is a plugin." Cresceu 54k em 10 dias | Alto — modelo de referência |
| **`omnigent-ai/omnigent`** | 9k | Meta-harness: camada sobre Claude Code, Codex, Cursor, OpenCode, Pi | **Alto** — alinha com `plan_runner` (orquestra, não executa) |
| **`lidge-jun/opencodex`** | 12k | Proxy universal: corre Gemini, Grok, DeepSeek, Ollama dentro do Codex CLI | **Alto** — resolve bloqueio DeepSeek no `agent-network-mcp` |
| **`yc-software/qm`** | 14k | Harness multiplayer (Slack + browser) — "agentes que a equipa partilha" | Médio — referência para multi-user |
| **`XiaomiMiMo/MiMo-Code`** | 13k | Terminal agent da Xiaomi | Baixo — sem caso de uso |
| **`xai-org/grok-build`** | 26k | Harness xAI, Apache 2.0 | Médio — referência |
| **`anywhere-labs/dsh-desktop`** | 21k | Desktop para DeepSeek Harness | Baixo — UI, sem dor |

**`INIT-094: Avaliar harnesses multi-provider`**
- `opencodex` → resolve bloqueio DeepSeek no `agent-network-mcp` (usa Claude Pro + Ollama + Gemini)
- `omnigent` → modelo "camada sobre harnesses" que alinha com o teu `plan_runner`
- Esforço: 1 dia de investigação
- Valor: **alto** — resolve 2 problemas concretos

---

## 📦 `google/skills` — 132 manuais oficiais (Apache 2.0)

> Origem: reels `99hud` (setembro 2026)
> Repo: `github.com/google/skills` — oficial do Google, **19k estrelas**, Apache 2.0

**O que contém:**
- **132 manuais** para: Ads, Analytics, Gemini, Cloud, Firebase, BigQuery, GKE, etc.
- **13 skills só de Google Ads** — incluindo `google-ads-api-account-diagnostics` (diagnostica contas: queda de conversão, verba travada, anúncio perdendo impressão)
- **MCP oficial do Google Ads** — ligas o Claude à tua conta, perguntas em português
- Skills escritas por quem fez a ferramenta

**Aplicação no teu projeto:**
- **`media_buyer`** → usar as skills oficiais de Ads
- **`ad_creative`** → idem
- **`marketing`** → enriquecer knowledge packs

**`INIT-093: Adoptar google/skills (132 skills oficiais, Apache 2.0)`**
- Fonte: `github.com/google/skills`
- Licença: **Apache 2.0** ✅ (uso comercial, sem contaminação)
- Esforço: 1-2 dias (ingerir + adaptar ao modelo de `SKILL.md` do lab)
- Valor: **alto** — skills oficiais, mantidas pelo Google

---

*Adicionado em: 2026-09-13*
*Origem: screenshots de reels partilhados pelo utilizador*

---

## Done

> Itens fechados. Regra: nada e apagado sem ser feito; ao fechar, mover para aqui.

| ID | Item | Fecho | Commit |
|---|---|---|---|
| **S1** | CI bloqueia se vitest falhar | vitest e gate no CI (sem continue-on-error) | `108314c` |
| **S4** | `pnpm-lock.yaml` gerado e commitado | lockfileVersion 6.0, 10 workspaces, --frozen-lockfile validado | `6f70b3b` |
| **S4b** | CI: install usa --frozen-lockfile e e gate | step install sem continue-on-error, comentarios limpos | `be139f4` |
| **S8** | `.gitignore` sem regra Node/node_modules | secao Node/pnpm adicionada (node_modules, dist, .turbo, coverage) | `ae24b7b` |
| **C1** | Fase 0.4 -- marcar A4/A5/A6 do `ITEM13-MARKETING-ROADMAP.md` com link do run | evidencia commitada em `pilots/evidence/`, links adicionados ao roadmap | `9994ea6` |
| **B7** | `patterns-from-mcp` -- documentar o MCP server | tools-catalog + governance-pipeline + README com "Ficheiros deste pacote" | `3366faa` |
| **B8** | `patterns-from-codebase-memory` -- documentar o codebase-memory-mcp | README + tools-catalog (15 tools) + evidence-tiers (Scout/Verify/Auditor) | `b7ef2f2` |
| **B9** | `node-platform.md` -- documentar a plataforma Node | apps/api + packages/core, boot sequence, HITL Node, auth fail-closed | `0231c5d` |
| **C2** | Modo external falha silenciosamente se `--out` fora de `pilots/` | guard `_validate_out_dir` nos 2 engines; testes alinhados; 76 verdes | `33310bb` + `4ec1ccf` |
| **C3** | `auth.ts` fail-closed tambem no `agent-network-mcp` | `session.js` `assertSecret()` (>=16 chars); login+5 endpoints devolvem 503 | `613c634` (agent-network-mcp) |
| **C5** | Auth do endpoint `app/api/mcp/route.js` (`agent-network-mcp`) | `withAuth()` com Bearer `MCP_API_KEY` (>=16 chars); fail-closed 503 sem env; constant-time compare | `69aec8c` (agent-network-mcp) |
| **C6** | Configurar `MCP_API_KEY` na Vercel (`agent-network-mcp`) | Vercel Production; redeploy de 69aec8c; verificado: 401 sem header, 405 com header | Vercel `agent-network-mcp-oddn` |
| **S6a** | Fase A.2 — `runner/plan_runner/hitl.py` (lado Python do contrato v1) | módulo isolado + 15 testes de contrato; 105 verdes; aditivo (engine/cli intocados); S6b (integração) movido para S9 | `cdae963` + `3445229` |
| **S7** | Working memory (`MEMORY.md` curado por cliente, ~1300 tokens) | `runner/plan_runner/working_memory.py` + 14 testes; convenção `memory/<client_id>/MEMORY.md`; limite suave 1300 tokens | `caabec6` |
| **C7** | Vulnerabilidades Dependabot no `agent-network-mcp` (era 16, agora 6→0) | `npm audit` 6→0; `next` 15.5.23→16.3.5 (major, build verde); Dependabot 0 Open | `6482cd4` (agent-network-mcp) |
| **C8d** | Fase A.2 — `runner/plan_runner/knowledge.py` (L5 retrieve_knowledge) | `KnowledgeBackend` protocol + `NullKnowledge` + `MockKnowledge` + `retrieve_knowledge` + `grounding_block`; 18 testes; contrato `memory.retrieve_knowledge` | `4d6fac4` |
| **keep-alive** | Manter Supabase ativo (free tier pausa após 7 dias) | `.github/workflows/keep-alive.yml`: GET `/rest/v1/keepalive` a cada 3 dias; ANON_KEY + RLS; fail-closed | `3634504` |
| **C8a-1** | Fase A.2 — `runner/plan_runner/chunking.py` (T6 §6, markdown chunking) | `chunk_markdown()` por secções H2/H3; ~200-600 tokens; output compatível com `retrieve_knowledge` (C8d); 14 testes | `32a5881` |
| **S3** | Teste do runner no CI (5 templates dry-run + 1 stub) | **Superado** — `test_real_plans.py` cobre 6 planos reais (compile-graph + run stub + HITL); corre no `runner-tests.yml` | (já existia) |
| **S2a** | Testes do caminho crítico — lado Python (Executor, Engine, HITL) | **Já feito** — `test_executor.py` + `test_engine_native.py` + `test_engine_external.py` + `test_langgraph_flow.py` + `test_hitl_contract.py` | (já existia) |
| **S2b-1** | Testes do caminho crítico — `HitlManager` (Node) | `tests/unit/HitlManager.test.ts`: 10 testes; **2 bugs corrigidos** em `HitlManager.ts` (`expireRequest` usava `request` indefinido; pedido expirado não era guardado) | `4d14f8f` |
| **S2b-2** | Testes do caminho crítico — `Router` (Node) | `tests/unit/Router.test.ts`: 12 testes; sem bugs encontrados | `6c87b42` |
| **S2b-3** | Testes do caminho crítico — `Planner` (Node) | `tests/unit/Planner.test.ts`: 10 testes; **1 bug corrigido** em `Planner.ts` (faltava `return {` — não compilava; `ci:typecheck` tem `continue-on-error`) | `c468081` |

---

## Como usar este ficheiro

- **Adicionar item**: nova linha na categoria correta
- **Mudar estado**: mover de 🔴 para 🟠, ou 🟠 para 🟢
- **Fechar item**: mover a linha para a secção `## Done` (nunca apagar)
- **Reclassificar**: se um item ganha urgência, sobe de categoria

**Regra**: nenhum item é apagado sem ser feito. Só muda de categoria.

---

## Ordem sugerida (próximas 3 sessões)

### Sessão 1 (1-2h)
- Fechada: S1, S4, C1, B7, B8, B9 todos em Done

### Sessão 2 (1 dia)
- Fechada: C6, C7 (MCP_API_KEY + audit)

### Sessão 3 (1-2 dias)
- Fechada: S6a (`hitl.py`), S7 (working memory), C8d (`knowledge.py`), C8a-1 (`chunking.py`), S3, S2a, S2b (HitlManager + Router + Planner)

**Próximos passos:**
- **STATUS.md** atualizado (esta sessão)
- **Decidir embedder** (Ollama / Gemini / HuggingFace) → desbloqueia C8a-2
- **S9** (integração `hitl.py`) ou **M1** (session search)

---

## 📌 Sessão 2026-09-14 — adições completas

### 🔧 Ferramentas (F1-F22)

| ID | Item | Estado | Nota |
|---|---|---|---|
| F1 | `agent-skills` (Addy Osmani) | backlog | Skill pack Claude Code, `/plugin` manual |
| F2 | `Graphify` | research | Grafo de código via MCP; avaliar vs `codebase-memory-mcp` |
| F3 | `OmniRoute` | research | Gateway multi-provider (352); resolve bloqueio DeepSeek |
| F4 | `Obscura` | backlog | Playwright alternativo (30MB vs 200MB RAM) |
| F5 | Plugin segurança Anthropic | backlog | Audit multi-agente; alinha com checklist 20 |
| F6 | `Caveman` | N/A | Já integrado no OmniRoute |
| F7 | `Ruflo` | parked | 290 de 300 tools são stubs |
| F8 | `gstack` | backlog | 23 ferramentas review/ship/QA (YC) |
| F9 | `ScrapeGraphAI` | backlog | Scraping via linguagem natural (GDPR cuidado) |
| F10 | Obsidian/Logseq | candidate | Working memory `.md` por cliente |
| F11 | **SOUL.md** | research | Identidade de agente (identidade + personalidade + limites + contexto) |
| F12 | **Soup** (fine-tuning) | **parked** | Fine-tuning LLM; **só após C8 (RAG alimentada)** |
| F13 | **MarkItDown** (Microsoft) | candidate | Ingestão PDF/DOCX/XLSX/imagens → Markdown. MIT |
| F14 | **Trafilatura** | candidate | Extração de sites (melhor que BeautifulSoup). Apache 2.0 |
| F15 | **Andrej Karpathy Skills** | candidate | Guidelines Claude Code; reduz erros 41%→11% |
| F16 | **Plugin segurança Anthropic** | candidate | (unificar com F5) |
| F17 | **Obscura + obscura-mcp** | research | (unificar com F4) |
| F18 | **Crawl4AI / Scrapling** | research | Crawling em profundidade |
| F19 | **Frameworks financeiros open source** (Condor, QuantClaw, TradingAgents, ai-hedge-fund, qlib, ffn, pyfolio, TA-Lib) | research | Para B10/B12. Verificar licenças |
| F20 | **World Monitor** (`koala73/worldmonitor`) | candidate | **AGPL-3.0** — usar via MCP/REST, **não integrar**. 500+ feeds, CII, financial radar |
| F21 | **Finance News Aggregator** (`areed1192/finance-news-aggregator`) | candidate | 8 providers, `pip install fin-news` |
| F22 | **Agente jornalístico** (horizontal) | **a desenhar** | Conteúdo para marketing + análise para investidor. Fontes: F20 + F21 |

### 🟢 Agentes (B10-B14)

| ID | Item | Estado | Nota |
|---|---|---|---|
| B10 | Agente de operação financeira | backlog | Fluxo de caixa, contas a pagar/receber, conciliação. Não é trading nem contabilidade |
| B11 | Interface de avatar por agente | backlog | Representação visual (avatar, voz, presença) |
| B12 | Agente de investimentos (separado de B10) | backlog | Análise, backtest, sem ordens |
| B13 | Agente financeiro com análise de volatilidade | backlog | Liga F20 + F21 a B10 |
| B14 | Ligação jornalismo → investidor | backlog | World Monitor → análise de volatilidade → alerta |

### 🎨 Telas / UI (U1-U9)

| ID | Item | Estado | Depende de |
|---|---|---|---|
| U1 | Tela 1 — Grafo de memória (Obsidian-style) | backlog | F10 |
| U2 | Tela 2 — Avatares de agentes normais | backlog | B11 + S7 |
| U3 | Tela 3 — Agentes financeiros | backlog | B10 |
| U4 | Tela 4 — Integração/Dashboard | backlog | U1 + U2 + U3 |
| U5 | Grafo de conexões entre agentes | backlog | — |
| U6 | Avatar tipo "boneco" (2D/3D animado) | backlog | — |
| U7 | Avatar do agente financeiro | backlog | B10 |
| U8 | **JARVIS** (interface global unificada) | backlog | U1-U7 |
| U9 | **VOS** (a definir) | backlog | Clarificar |

### 📌 Dependências críticas

| Item | Depende de |
|---|---|
| F12 (Soup) | C8 (RAG alimentada) |
| U1 (Tela 1) | F10 (Obsidian) |
| U2 (Tela 2) | B11 + S7 |
| U3 (Tela 3) | B10 |
| U4 (Tela 4) | U1 + U2 + U3 |
| U8 (JARVIS) | U1-U7 |
| B14 (jornalismo→investidor) | F20 + F21 + F22 + B12 |

---

*Adicionado em: 2026-09-14*
*Origem: sessões múltiplas + auditorias externas*

---

*Adicionado em: 2026-09-15*
*Fecho: S6a, S7, C7, C8d, C8a-1, keep-alive, S3, S2a, S2b (1, 2, 3). S9 criado (integração `hitl.py`).*