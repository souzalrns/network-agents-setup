# Status — pendências consolidadas

> Gerado em: 2026-09-13
> Base: leitura do repo + cruzamento com sessões
> Método: tudo o que foi discutido e não está feito, classificado

## 🔴 Crítico (bloqueia outras coisas ou é risco real)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **C4** | **T6 ingestão é stub** — 33 knowledge packs de marketing não estão em RAG nenhum | 1 dia | RAG funcional | Auditoria Claude |
| **C5** | **Auth do endpoint `app/api/mcp/route.js`** (`agent-network-mcp`) nao coberta por C3 | 30 min | Exposicao prod | C3 |

## 🟠 Alto (resolve problema real, valor claro)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **S2** | **Fase 1.2** — testes do caminho crítico (Router, Planner, Executor, HitlManager) — ≥20 casos | 2-3h | Refactor seguro | Auditoria Claude |
| **S3** | **Fase 1.3** — teste do runner no CI (5 templates dry-run + 1 stub) | 1h | Runner gate | Auditoria Claude |
| **S5** | **Fase 1.5** — `validate:consistency` + wiring marketing + import runner | 1h | Consistência | Auditoria Claude |
| **S6** | **Fase A.2** — `runner/plan_runner/hitl.py` (lado Python do contrato v1) | 1 dia | HITL durável | Nosso |
| **S7** | **Working memory** (`MEMORY.md` curado por cliente, ~1300 tokens) | 1 dia | Contexto sem RAG | Nossa |

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
| 20 | Scam de dependências | ⚠️ | Dependabot? `audit-tools.yml` corre, mas não `npm audit` no CI |

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
- **`media_buyer`** (criado ontem) → usar as skills oficiais de Ads
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

---

## Como usar este ficheiro

- **Adicionar item**: nova linha na categoria correta
- **Mudar estado**: mover de 🔴 para 🟠, ou 🟠 para 🟢
- **Fechar item**: apagar a linha (ou mover para uma secção "Done" no fim)
- **Reclassificar**: se um item ganha urgência, sobe de categoria

**Regra**: nenhum item é apagado sem ser feito. Só muda de categoria.

---

## Ordem sugerida (próximas 3 sessões)

### Sessão 1 (1-2h)
- Fechada: S1, S4, C1, B7, B8, B9 todos em Done

### Sessão 2 (1 dia)
- S2 (testes do caminho crítico) — 2-3h
- S3 (teste do runner no CI) — 1h
- S5 (consistência) — 1h

### Sessão 3 (1-2 dias)
- S6 (`hitl.py`) — 1 dia
- S7 (working memory) — 1 dia
- M1 (session search) — 4h

**Depois disto**: Fase 1 fechada. O motor tem rede de segurança.
