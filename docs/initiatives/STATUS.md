# Status — pendências consolidadas

> Gerado em: 2026-09-13
> Base: leitura do repo + cruzamento com sessões
> Método: tudo o que foi discutido e não está feito, classificado
>
> **Regra de IDs:** itens fechados vão para a secção `## Done` — não são apagados.
> IDs nunca são reciclados. O próximo ID livre na série C é **C9**.
> O ID **C5** pertence ao item antigo (auth do `mcp/route.js`, já em `Done`).
> O item "alimentar RAG" é **C8** (estava duplicado como C5).
> O ID **S6** pertence ao módulo `hitl.py` (S6a, feito). A integração (S6b) é **S9**.
> O ID **S2** está dividido: **S2a** (Python) feito; **S2b** (Node) feito.
> **C8 está 5/6 feito:** C8a-1, C8a-2, C8b, C8c, C8d feitos; falta **C8e** (`McpKnowledge`).
> **Tabela exclusiva:** `knowledge_chunks_t6` (NÃO partilhar com `agent-network-mcp`).

## 🔴 Crítico (bloqueia outras coisas ou é risco real)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **C8** | **Alimentar RAG continuamente** (T6) — 5/6 feito; falta **C8e** (`McpKnowledge`) | 2-3h | RAG completo | Nossa |
| **C8e** | **`McpKnowledge`** — backend que chama o `agent-network-mcp` via HTTP | 2-3h | RAG completo | Nossa |

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
| 1 | Esconder API Keys | ✅ | `.env` + `.gitignore` (protegido) |
| 2 | Limpar secrets do git | ✅ | Nunca foi commitado secret |
| 3 | Public Key DB | N/A | Não usas JWT próprio |
| 4 | Ativar RLS | ✅ | `knowledge_chunks` tem policy `anon_deny` (verificado 2026-09-16) |
| 5 | Criptografia de dados | ❌ | Dados sensíveis em repouso |
| 6 | Auth server-side | ✅ | `auth.ts` fail-closed |
| 7 | Restringir acessos (RBAC) | ❌ | Falta roles |
| 8 | Bloquear Mass Assignment | ❌ | Zod valida, mas aceita campos extra |
| 9 | Proteger cookies | ⚠️ verificar | `httpOnly`/`secure`/`sameSite` |
| 10 | Hash nas senhas | ✅ | Supabase Auth |
| 11 | Rate limit | ❌ | Não existe |
| 12 | Bot protection | ❌ | Não existe |
| 13 | Queries parametrizadas | ✅ | Prisma + psycopg |
| 14 | Validação dos inputs | ⚠️ | Zod (Node) + YAML (Python) |
| 15 | Vazar conteúdo | ⚠️ | Mensagens de erro podem revelar stack traces |
| 16 | Restringir uploads | ❌ | Produção tem `extrair-imagem` |
| 17 | Trim respostas | ⚠️ | Depende |
| 18 | Add security headers | ❌ | CSP, X-Frame-Options, etc. |
| 19 | Forçar HTTPS | ✅ | Vercel faz por defeito |
| 20 | Scam de dependências | ⚠️ | Dependabot ativo |

---

## 🧰 Harnesses multi-provider (2026)

| Projeto | Stars | O que é | Relevância |
|---|---|---|---|
| **`deepseek-ai/deepseek-harness`** | 200k | MIT. "Everything is a plugin." | Alto |
| **`omnigent-ai/omnigent`** | 9k | Meta-harness sobre Claude Code, Codex, Cursor | **Alto** |
| **`lidge-jun/opencodex`** | 12k | Proxy universal (Gemini, Grok, DeepSeek, Ollama no Codex CLI) | **Alto** |
| **`yc-software/qm`** | 14k | Harness multiplayer | Médio |
| **`xai-org/grok-build`** | 26k | Harness xAI | Médio |
| **`anywhere-labs/dsh-desktop`** | 21k | Desktop para DeepSeek | Baixo |

**`INIT-094: Avaliar harnesses multi-provider`** — 1 dia de investigação.

---

## 📦 `google/skills` — 132 manuais oficiais (Apache 2.0)

Repo: `github.com/google/skills` — 19k estrelas.
Aplicação: `media_buyer`, `ad_creative`, `marketing`.
`INIT-093: Adoptar google/skills` — 1-2 dias. Valor **alto**.

---

## Done

> Itens fechados. Regra: nada e apagado sem ser feito; ao fechar, mover para aqui.

| ID | Item | Fecho | Commit |
|---|---|---|---|
| **S1** | CI bloqueia se vitest falhar | vitest e gate no CI | `108314c` |
| **S4** | `pnpm-lock.yaml` gerado e commitado | lockfileVersion 6.0, 10 workspaces | `6f70b3b` |
| **S4b** | CI: install usa --frozen-lockfile | step install sem continue-on-error | `be139f4` |
| **S8** | `.gitignore` sem regra Node/node_modules | secao Node/pnpm adicionada | `ae24b7b` |
| **C1** | Fase 0.4 — marcar A4/A5/A6 do roadmap | evidencia commitada em `pilots/evidence/` | `9994ea6` |
| **B7** | `patterns-from-mcp` — documentar MCP server | tools-catalog + governance-pipeline + README | `3366faa` |
| **B8** | `patterns-from-codebase-memory` | README + tools-catalog (15 tools) + evidence-tiers | `b7ef2f2` |
| **B9** | `node-platform.md` — documentar plataforma Node | apps/api + packages/core, boot sequence | `0231c5d` |
| **C2** | Modo external falha se `--out` fora de `pilots/` | guard `_validate_out_dir` nos 2 engines | `33310bb` + `4ec1ccf` |
| **C3** | `auth.ts` fail-closed no `agent-network-mcp` | `session.js` `assertSecret()` (>=16 chars) | `613c634` (agent-network-mcp) |
| **C5** | Auth do endpoint `app/api/mcp/route.js` | `withAuth()` com Bearer `MCP_API_KEY` | `69aec8c` (agent-network-mcp) |
| **C6** | Configurar `MCP_API_KEY` na Vercel | Vercel Production; redeploy verificado | Vercel `agent-network-mcp-oddn` |
| **S6a** | `runner/plan_runner/hitl.py` (contrato v1) | módulo isolado + 15 testes; aditivo; S6b → S9 | `cdae963` + `3445229` |
| **S7** | Working memory (`MEMORY.md` por cliente) | `working_memory.py` + 14 testes; convenção `memory/<client_id>/` | `caabec6` |
| **C7** | Vulnerabilidades Dependabot no MCP (era 16) | `npm audit` 6→0; `next` 15.5.23→16.3.5; Dependabot 0 Open | `6482cd4` (agent-network-mcp) |
| **C8d** | `runner/plan_runner/knowledge.py` (L5 retrieve) | `KnowledgeBackend` + `NullKnowledge` + `MockKnowledge` + `grounding_block`; 18 testes | `4d6fac4` |
| **keep-alive** | Manter Supabase ativo | `keep-alive.yml`: GET `/rest/v1/keepalive` a cada 3 dias | `3634504` |
| **C8a-1** | `runner/plan_runner/chunking.py` (markdown chunking) | `chunk_markdown()` por secções H2/H3; 14 testes | `32a5881` |
| **S3** | Teste do runner no CI (5 templates + 1 stub) | **Superado** — `test_real_plans.py` cobre 6 planos | (já existia) |
| **S2a** | Testes do caminho crítico — Python | **Já feito** — `test_executor.py` + engines + HITL | (já existia) |
| **S2b-1** | `HitlManager` (Node) | 10 testes; **2 bugs corrigidos** em `HitlManager.ts` | `4d14f8f` |
| **S2b-2** | `Router` (Node) | 12 testes; sem bugs | `6c87b42` |
| **S2b-3** | `Planner` (Node) | 10 testes; **1 bug corrigido** (faltava `return {`) | `c468081` |
| **C8b** | Schema Prisma T6 (Supabase) | `KnowledgeSource`, `KnowledgeChunk`, `SystemInventory`; tabelas criadas via SQL | `08f05cd` |
| **C8a-2** | Pipeline de ingestão T6 | `embedder.py` (Gemini 768 dims) + `supabase_writer.py` + `ingest_apply.py`; tabela exclusiva `knowledge_chunks_t6`; **110 chunks** de 33 ficheiros | `c76e541` + `a6bd836` + `ceca890` |
| **C8c** | Workflow `ingest-knowledge` com `--apply` | Apply real no push (secrets `DATABASE_URL` + `GEMINI_API_KEY` no GitHub) | `76d7aeb` |

---

## Como usar este ficheiro

- **Adicionar item**: nova linha na categoria correta
- **Mudar estado**: mover de 🔴 para 🟠, ou 🟠 para 🟢
- **Fechar item**: mover a linha para a secção `## Done` (nunca apagar)

**Regra**: nenhum item é apagado sem ser feito. Só muda de categoria.

---

## Ordem sugerida (próximas 3 sessões)

### Sessão 1 (1-2h)
- Fechada: S1, S4, C1, B7, B8, B9

### Sessão 2 (1 dia)
- Fechada: C6, C7, S6a, S7, C8d, C8a-1, C8b, C8a-2, C8c

### Sessão 3 (1-2 dias)
- **C8e** (`McpKnowledge`) — fecha o C8
- **S9** (integração `hitl.py`)
- **M1** (session search)

---

## 📌 Sessão 2026-09-14 — adições completas

### 🔧 Ferramentas (F1-F22)

| ID | Item | Estado |
|---|---|---|
| F1 | `agent-skills` (Addy Osmani) | backlog |
| F2 | `Graphify` | research |
| F3 | `OmniRoute` | research |
| F4 | `Obscura` | backlog |
| F5 | Plugin segurança Anthropic | backlog |
| F6 | `Caveman` | N/A |
| F7 | `Ruflo` | parked |
| F8 | `gstack` | backlog |
| F9 | `ScrapeGraphAI` | backlog |
| F10 | Obsidian/Logseq | candidate |
| F11 | **SOUL.md** | research |
| F12 | **Soup** (fine-tuning) | **parked** (só após C8) |
| F13 | **MarkItDown** (Microsoft) | candidate |
| F14 | **Trafilatura** | candidate |
| F15 | **Andrej Karpathy Skills** | candidate |
| F16 | **Plugin segurança Anthropic** | candidate |
| F17 | **Obscura + obscura-mcp** | research |
| F18 | **Crawl4AI / Scrapling** | research |
| F19 | **Frameworks financeiros** | research |
| F20 | **World Monitor** (AGPL-3.0) | candidate |
| F21 | **Finance News Aggregator** | candidate |
| F22 | **Agente jornalístico** | a desenhar |

### 🟢 Agentes (B10-B14)

| ID | Item | Estado |
|---|---|---|
| B10 | Operação financeira | backlog |
| B11 | Interface de avatar | backlog |
| B12 | Agente de investimentos | backlog |
| B13 | Análise de volatilidade | backlog |
| B14 | Jornalismo → investidor | backlog |

### 🎨 Telas / UI (U1-U9)

| ID | Item | Depende de |
|---|---|---|
| U1 | Grafo de memória | F10 |
| U2 | Avatares normais | B11 + S7 |
| U3 | Agentes financeiros | B10 |
| U4 | Integração/Dashboard | U1 + U2 + U3 |
| U5 | Grafo de conexões | — |
| U6 | Avatar boneco | — |
| U7 | Avatar financeiro | B10 |
| U8 | JARVIS | U1-U7 |
| U9 | VOS | Clarificar |

### 📌 Dependências críticas

| Item | Depende de |
|---|---|
| F12 (Soup) | C8 (RAG alimentada) ✅ **desbloqueado** |
| U1 | F10 |
| U2 | B11 + S7 |
| U3 | B10 |
| U4 | U1 + U2 + U3 |
| U8 | U1-U7 |
| B14 | F20 + F21 + F22 + B12 |

---

*Adicionado em: 2026-09-14*
*Origem: sessões múltiplas + auditorias externas*

---

*Adicionado em: 2026-09-16*
*Fecho: C8a-1, C8a-2, C8b, C8c, C8d, keep-alive, S2b (1, 2, 3), S3, S6a, S7, C7. C8 está 5/6 — falta C8e.*
*Tabela exclusiva `knowledge_chunks_t6` (não partilha com agent-network-mcp).*
*110 chunks de 33 ficheiros de conhecimento no Supabase.*