# Status — pendências consolidadas

> **⚠️ Verificar a secção "📋 Prompts pendentes" no início de cada sessão.** Vários prompts já pedidos ficaram sem execução completa e sem registo — ver essa secção antes de assumir que algo está feito.

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
> **C8 fechado (6/6):** C8a-1, C8a-2, C8b, C8c, C8d, C8e feitos. RAG alimentado (110 chunks) + retrieve via MCP (`McpKnowledge`) + pipeline completo (markdown → chunk → embed → Supabase → retrieve).
> **Tabela exclusiva:** `knowledge_chunks_t6` (NÃO partilhar com `agent-network-mcp`).
> **Nova série de IDs `G` (Governança/Mapeamento), a partir de 2026-09-17:** próximo ID livre é **G6**.
> Os 3 documentos de mapeamento (CORE-MAPPING, MCP-MAPPING, ROADMAP-GOVERNANCE) vivem em `docs/architecture/` — ver secção "Mapeamento" abaixo.

## 📋 Prompts pendentes

Prompts já pedidos nesta sessão que ficaram sem execução completa e não tinham sido registados até agora.

| ID | Descrição | Estado | Prioridade | Dependência |
|---|---|---|---|---|
| **B2b** | Rodar o `security_auditor` (B2) por completo no `network-agents-setup` — as 8 ferramentas (Bandit, Semgrep, Gitleaks, OSV-Scanner, mcpguard, offsec-ai, Trivy, detect-secrets), não só as ~5 já corridas | Não feito | 🔴 Alta | B2 (feito, ver Done) |
| **B2c** | Integrar os resultados da auditoria B2/B2b — decidir o que entra no backlog real (Crítico/Alto/Médio) em vez de ficar só documentado em `SECURITY-AUDIT.md`/`SECURITY-AUDIT-FULL.md` | Parcial (2 achados do CodeQL já corrigidos; os da auditoria B2 original, não) | 🟡 Média | B2b |

## 🔴 Crítico (bloqueia outras coisas ou é risco real)

*(nada crítico pendente de momento — C8/C8e fechados, ver `## Done`)*

## 🟠 Alto (resolve problema real, valor claro)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **S5** | **Fase 1.5** — `validate:consistency` + wiring marketing + import runner (provavelmente já feito — `ci.yml` corre `validate:consistency`) | 1h | Consistência | Auditoria Claude |
| **S9** | **Fase A.2b** — integração do `hitl.py` em `engine.py`/`langgraph_engine.py`/`cli.py` (dupla-escrita; aditivo) | 3-4h | HITL durável | Nosso |
| **S11** | **A8/C2 — Propagar identidade real (caller/providedKey) para o `ToolExecutor` desde `MCPServer.ts`/`MCPClient.ts`.** Sem isto, o C1 autoriza com `caller='unknown'` por omissão — inútil em produção. | 1-2 dias | Torna o C1 útil de facto | Novo (2026-09-19, achado durante C1) |
| **S12** | **A14 no `agent-network-mcp`: adicionar validação estrita aos schemas Zod do `mcp-handler`.** `app/api/mcp/route.js` define schemas como `shape` passados a `server.tool()`; por omissão o Zod usa modo `"strip"` (remove chaves desconhecidas). Objectivo: modo `"strict"` (rejeitar) — via opção do `mcp-handler` se existir, ou `z.object(shape).strict().parse(args)` dentro de cada handler. Repo: `agent-network-mcp` (separado). Ver checklist de 20 itens acima. | 1 dia | Fecha A14 de facto | Novo (2026-09-19, achado durante A14) |
| **S13** | **Restringir CORS a origens conhecidas.** `apps/api/src/server.ts:25` — `app.use(cors())` sem opções, aceita qualquer origem. Contradição detectada no A20: CORP do helmet (agora `cross-origin`) + CORS totalmente aberto. Acção: definir lista de origens legítimas (frontend próprio?), aplicar `{ origin: [...] }` no `cors()`. Requer decisão humana: que origens são legítimas? Ver `EXECUTION-PROMPTS.md` A20. | 2-4h | Fecha o gap real de CORS | Novo (2026-09-19, achado durante A20) |

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
| **M8** | **Vulnerabilidades Dependabot** (9 alertas reportados no push do commit `2d03b4b`: 3 críticas + 1 alta — todas em dependências de dev, `vitest`/`vite`/`esbuild`/`launch-editor`; 5 moderadas incluindo 2× `uuid`, único pacote de produção, prioridade dentro deste item). Ver [github.com/souzalrns/network-agents-setup/security/dependabot](https://github.com/souzalrns/network-agents-setup/security/dependabot) | 1h | Nada | Novo (2026-09-19) |

## 🟢 Baixo (nice to have)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **B1** | **Fase 6 (Claude)** — expansão para 2.º domínio (agents + skills + templates + wiring) | 1 semana | Nada | Auditoria Claude |
| **B3** | **Agente de trading** (simulação only, sem ordens) | 3-5 dias | Nada | Nossa |
| **B4** | **Agente gamedev** (GDD, loop, engine) | 3-5 dias | Nada | Nossa |
| **B5** | **Hermes como runtime** (não interface) — worker para browser/vision | 1-2 dias | Nada | Nossa |
| **B6** | **MiroFish para simulação** (repo isolado, AGPL — uso interno) | 1 dia | Nada | Nossa |
| **B10** | **Documentar/automatizar `prisma generate`** — passo em falta depois de `pnpm install`; sem ele `.prisma/client/default` não existe e testes com Prisma falham a carregar (achado durante A3: `tests/integration/ExecutionFlow.test.ts`) | 0.5h | Nada | Novo (2026-09-19, achado durante A3) |
| **B11** | **Criar script de criação para `knowledge_sources`** — hoje só existe `scripts/create_t6_chunks_table.sql` (cria `knowledge_chunks_t6`, referencia `knowledge_sources` via FK mas não a cria); `knowledge_sources` existe no Supabase mas foi criada manualmente, fora do repo/controlo de versões | 1h | Nada | Novo (2026-09-19, achado durante A2) |
| **B12** | **Investigar `knowledge_log`** — tabela descoberta durante o A2 (já tem RLS + policy `anon_deny`, mesmo padrão de `knowledge_chunks`), mas sem documentação no repo: quem escreve nela, com que propósito, e porque não aparece em nenhum ficheiro deste projecto | 2h | Nada | Novo (2026-09-19, achado durante A2) |
| **B13** | **Isolar testes lentos da suite unitária do runner** — `tests/test_crash_recovery.py`/`tests/test_real_plans.py` não estão bloqueados (ambos passam), mas são responsáveis pela maior parte dos 12 minutos da suite completa (172 testes), lentidão fácil de confundir com bloqueio sob um timeout curto (achado durante A7). Mover para marca `@pytest.mark.integration` (ou pasta própria) e excluir por omissão do `pytest` rápido | 15 min | Nada | Novo (2026-09-19, achado durante A7) |
| **B14** | **Auditoria de escopo do `EXECUTION-PROMPTS.md`** — revalidar todos os itens restantes contra o código real antes de executar. 5 itens desta sessão revelaram-se diferentes do plano ao verificar (C6 redundante, A1 já resolvido antes de escrito, A21 já corrigido em commit anterior, A14 N/A neste repo, A18 com 7× o escopo real). Objectivo: eliminar falsas pendências do plano antes de continuarem a consumir sessões futuras | 1-2h | Nada | Novo (2026-09-19, achado durante A18) |

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
| 4 | Ativar RLS | ✅ | `knowledge_chunks` tem policy `anon_deny` (verificado 2026-09-16); `knowledge_chunks_t6`/`knowledge_sources` (T6, este repo) RLS activado + policy `anon_deny` em 2026-09-19 (A2, ver `AUDIT-SECURITY-2026.md` secção 6) |
| 5 | Criptografia de dados | ❌ | Dados sensíveis em repouso |
| 6 | Auth server-side | ✅ | `auth.ts` fail-closed |
| 7 | Restringir acessos (RBAC) | ❌ | Falta roles |
| 8 | Bloquear Mass Assignment | ❌ | Zod valida, mas aceita campos extra. *(2026-09-19: A14 — VERIFICADO: N/A neste repo. Zod não existe em nenhum package.json. Aplica-se ao `agent-network-mcp` (ver S12).)* |
| 9 | Proteger cookies | ⚠️ verificar | `httpOnly`/`secure`/`sameSite` |
| 10 | Hash nas senhas | ✅ | Supabase Auth |
| 11 | Rate limit | ❌ | Não existe |
| 12 | Bot protection | ❌ | Não existe |
| 13 | Queries parametrizadas | ✅ | Prisma + psycopg |
| 14 | Validação dos inputs | ⚠️ | Zod (Node) + YAML (Python) |
| 15 | Vazar conteúdo | ✅ | Mensagens de erro podem revelar stack traces. *(2026-09-19: A18 — RESOLVIDO. 29 sítios em 11 ficheiros corrigidos via helpers `toClientError` — escopo real 7× o estimado no brief (citava 4 ficheiros). Ver `AUDIT-SECURITY-2026.md` LLM02 e `EXECUTION-PROMPTS.md` A18.)* |
| 16 | Restringir uploads | ❌ | Produção tem `extrair-imagem` |
| 17 | Trim respostas | ⚠️ | Depende |
| 18 | Add security headers | ✅ | CSP, X-Frame-Options, etc. *(2026-09-19: A20 — VERIFICADO: `helmet()` já estava activo em `apps/api/src/server.ts:24` com 12 headers, incluindo CSP/X-Frame-Options/HSTS — este item estava desactualizado. Ajuste real aplicado: `crossOriginResourcePolicy` para `'cross-origin'` (o omissão `'same-origin'` contradizia o `cors()` aberto). S13 registado para o CORS em si. Ver `AUDIT-SECURITY-2026.md` e `EXECUTION-PROMPTS.md` A20/S13.)* |
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

## 🗺️ Mapeamento (2026-09-17)

Três documentos novos, produzidos por leitura directa dos ficheiros (não por inferência), em `docs/architecture/`:

| Documento | Cobre | Resultado |
|---|---|---|
| `CORE-MAPPING.md` | 39 ficheiros `.ts` de `packages/core/src/` | 5 REAL, 19 INCOMPLETO, 14 MOCK, 1 BARREL |
| `MCP-MAPPING.md` | 33 agentes de `lib/agents.js` (`agent-network-mcp`) | 13 Horizontal+genérico (setup), 5 Vertical+genérico com ingestão (setup), 9 Vertical+proprietário (fica no MCP), 2 Mistos (dividir), 2 casca por design (fica no MCP), 3 casca razão não documentada; 16 skills novas extraíveis |
| `ROADMAP-GOVERNANCE.md` | Cronograma da camada de governança, integrando AGT (Microsoft) + o que falta construir | 8–12 sessões; gaps identificados: Delegation Graph, Action Receipts, Context Sync |

### 🗺️ Próximos passos do mapeamento

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **G1** | Fechar **C8e** (`McpKnowledge`) — ver secção 🔴 Crítico, já rastreado lá | 2-3h | RAG completo | (já existente, referenciado aqui) |
| **G2** | Criar as **16 skills novas** de `skills/meta/` listadas no `MCP-MAPPING.md` (blocos genéricos extraídos de agentes verticais — Prisma, NestJS, React, API REST, tratamento de erros, SEO técnico, A11y, Vite env vars, escrita de artigos, React Native/Expo, PHI, Python, deploy, MCP/Zod, GitHub Actions, Objetivo→Plano→Teste→Execução→Revisão→Evidência) | 3-5 dias | Reuso horizontal | MCP-MAPPING |
| **G3** | Migrar os **5 knowledge packs verticais com ingestão** (cardiologia, dermatologia, oftalmologia, direito-br-pt, imobiliario-digital) do MCP para o setup | 1-2 dias | Catálogo público | MCP-MAPPING |
| **G4** | Limpar termos privados dos **13 agentes "Horizontal + genérico"** antes de os trazer para o setup (lista completa na secção 3.1 do `MCP-MAPPING.md`) | 1 dia | G2/G3 | MCP-MAPPING |
| **G5** | Corrigir **2 achados não resolvidos** do `MCP-MAPPING.md`: `apps-produto` não está classificado em nenhuma das 6 secções de detalhe (só na tabela principal); coluna Privacidade de `hvac` diz "Proprietário" mas está agrupado em "casca por design" (genérico) — contradição entre colunas, precisa de decisão | 1h | Integridade do mapeamento | MCP-MAPPING |

## Done

> Itens fechados. Regra: nada e apagado sem ser feito; ao fechar, mover para aqui.

| ID | Item | Fecho | Commit |
|---|---|---|---|
| **S1** | CI bloqueia se vitest falhar | vitest e gate no CI | `108314c` |
| **S10** | Ligar o L5 (`retrieve_knowledge`/`McpKnowledge`) à execução real de planos | `knowledge_wiring.py` (novo, aditivo) — bloco `knowledge:` opcional por step no plan.yaml, lido de `step.raw` (sem tocar em `models.py`); escreve `pending_steps/<id>/knowledge_context.md` ao lado do que `executor.py` já escreve, sem tocar em `executor.py`; falha do MCP nunca aborta o step. Ligado em `engine.py` (run_plan+resume_run) e `langgraph_engine.py` (3 pontos de execução). Testado com servidor MCP real local (sucesso) e sem `MCP_API_KEY` (falha graciosa), + plano real (`seo-article-demo-s9.plan.yaml`) em stub, + 172/172 testes (167 antigos + 5 novos). **Nota:** isto foi chamado "S9" por engano em `FASE1-MEMORIA.md`/`FASE4-SINTESE.md` — o **S9** real é a integração do `hitl.py` (linha acima), continua por fazer; este trabalho é **S10** | ver commits de `knowledge_wiring.py`, `engine.py`, `langgraph_engine.py`, `test_s9_knowledge_wiring.py` |
| **B2** | Agente de cibersegurança (`security_auditor` + skill `security-audit` + `SECURITY.md`) | Defensivo, isolado, referencia OWASP LLM Top 10 2026/NIST AI RMF/MITRE ATLAS/MAESTRO | ver commits de `docs/architecture/SECURITY.md`, `skills/meta/security-audit/`, `agents/meta/security_auditor.agent.md` |
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
| **C8e** | `McpKnowledge` (backend Python que chama o `agent-network-mcp`) | `retrieveKnowledgeHits()` em `lib/knowledge.js` (aditiva); tool `retrieve_knowledge` em `route.js` (9.ª tool); `mcp_knowledge.py` + 13 testes; `mcp==1.30.0` em `requirements.txt`; 2 bugs reais apanhados ao testar contra servidor MCP real (`streamable_http_client` devolve triplo; erros de rede em `BaseExceptionGroup`) | `8858b35` (mcp_knowledge.py) + `e5e0384` (testes) + `577a33b` (requirements.txt) + `ffe5a60` (knowledge.js, agent-network-mcp) + `7c4d85e` (route.js, agent-network-mcp) |
| **C8** | **Alimentar RAG continuamente (T6) — fechado 6/6** | Todos os sub-itens concluídos (C8a-1, C8a-2, C8b, C8c, C8d, C8e). C8 fechado. RAG alimentado (110 chunks) + retrieve via MCP (`McpKnowledge`) + pipeline completo (markdown → chunk → embed → Supabase → retrieve). | ver sub-itens acima |
| **C8c** | Workflow `ingest-knowledge` com `--apply` | Apply real no push (secrets `DATABASE_URL` + `GEMINI_API_KEY` no GitHub) | `76d7aeb` |
| **G-skill-1** | Skill `transcript_analysis` (genérica, `skills/marketing/`) | Dispatch→poll→leitura de datastore→recomendação, sem dado de produção | `skills/marketing/transcript_analysis/SKILL.md` |
| **G-skill-2** | Agente `content_analyst` (`agents/marketing/`) | Liga ao skill acima | `agents/marketing/content_analyst.agent.md` |
| **G-skill-3** | Skill `cheap-entity-extraction` (`skills/meta/`) | Técnica GLiNER2, genérica | `skills/meta/cheap-entity-extraction/SKILL.md` |
| **G-skill-4** | Skill `skill-self-optimization` (`skills/meta/`) | Técnica SkillOpt (Microsoft Research), genérica | `skills/meta/skill-self-optimization/SKILL.md` |
| **G-skill-5** | Skill `ai-code-review-checklist` (`skills/meta/`) | Checklist RLS/IDOR/segredos/onboarding, genérico | `skills/meta/ai-code-review-checklist/SKILL.md` |

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


## 📊 Estado do mapeamento

| Inventário | Contagem | Fonte |
|---|---|---|
| `packages/core/src/` (ficheiros `.ts`) | 39 | `CORE-MAPPING.md` |
| `lib/agents.js` (`agent-network-mcp`) | 33 agentes | `MCP-MAPPING.md` |
| `skills/` (`network-agents-setup`) | 50 (marketing 16, claude 26, design 4, meta 4) | Contagem directa via API, 2026-09-17 |
| `agents/` (`network-agents-setup`) | 21 (marketing 16, design 4, meta 1) | Contagem directa via API, 2026-09-17 |

*Nota: a contagem de `skills/` (50) e `agents/` (21) foi verificada directamente nesta sessão — os números "~40" e "~20" do pedido original eram estimativas; ficam substituídos pela contagem real.*

*Adicionado em: 2026-09-16*
*Fecho: C8a-1, C8a-2, C8b, C8c, C8d, keep-alive, S2b (1, 2, 3), S3, S6a, S7, C7. C8 está 5/6 — falta C8e.*
*Tabela exclusiva `knowledge_chunks_t6` (não partilha com agent-network-mcp).*
*110 chunks de 33 ficheiros de conhecimento no Supabase.*
<!-- test: ingest apply -->


## 📋 Resumo do dia 2026-09-17

**C8 fechado (6/6):** RAG alimentado (110 chunks, 33 ficheiros) + retrieve via MCP (`McpKnowledge`, C8e) — pipeline completo markdown → chunk → embed → Supabase → retrieve.

**Mapeamento completo, 3 documentos** (por leitura directa dos ficheiros, não inferência): `CORE-MAPPING.md` (39 ficheiros de `packages/core/`, 5 REAL/19 INCOMPLETO/14 MOCK/1 BARREL), `MCP-MAPPING.md` (33 agentes do `agent-network-mcp`), `governance/ROADMAP-GOVERNANCE.md` (cronograma de governança, verificação externa do AGT/AgentMesh).

**G2 — 16 skills novas em `skills/meta/`** extraídas dos agentes verticais (Prisma, NestJS, React, API REST, error handling, SEO técnico, a11y, Vite, article writing, React Native, PHI, Python, deploy, MCP patterns, GitHub Actions, meta-workflow).

**G3 — 5 knowledge packs verticais migrados** para `docs/knowledge/` (cardiologia, dermatologia, oftalmologia, direito-br-pt, fipezap), termos privados removidos.

**G4 — 13 agentes horizontais migrados** de `agent-network-mcp` para `agents/<domínio>/`, termos privados genericizados (2 achados extra: um Supabase project ID real e uma métrica de negócio real, ambos removidos).

**B2 — Agente de segurança criado e usado**: `security_auditor` (defensivo, não ofensivo) + skill `security-audit` (OWASP LLM Top 10 2026, NIST AI RMF, MITRE ATLAS, MAESTRO) + `SECURITY.md`. Primeira auditoria real corrida (`SECURITY-AUDIT.md`) — achado real corrigido parcialmente (`mcp/plan_runner/policy.py:73`, aviso adicionado; fecho completo bloqueado por um teste existente que fixa o comportamento inseguro como esperado).

**Causa raiz do `ingest-knowledge` confirmada e parcialmente corrigida:** HTTP 429 do Gemini (quota excedida), não o conteúdo dos commits. Corrigido: retry+backoff exponencial + `--max-chunks` em `ingest_apply.py`, `concurrency`+`cancel-in-progress` no workflow. **Ainda falha** mesmo após a correcção (confirmado nos runs mais recentes, 23:16–23:17) — consistente com quota diária esgotada, não só por minuto; o retry de segundos não resolve esse caso. Ver `RATE-LIMITS.md`.

**Dependabot:** `ignore` de major version updates adicionado aos 6 blocos de `.github/dependabot.yml` (21 PRs abertos incluíam majors perigosos — langgraph 0.x→1.x, `@prisma/client` 5→7, TypeScript 5→7, `@types/node` 20→26). Não fecha os PRs já abertos, só impede novos.

**CodeQL — 2 alertas de `missing-workflow-permissions` fechados** (`ci.yml`, `runner-tests.yml`, `keep-alive.yml`, `ingest-knowledge.yml` — os 4 receberam `permissions:` explícito, mínimo necessário por workflow). **2 alertas reais ainda abertos, não corrigidos** (fora do âmbito desta tarefa, exigem autorização para tocar em `packages/core/`):
- `#5` — `packages/core/src/security/SecurityManager.ts:486` — hash de password com SHA-256 sem salt (`js/insufficient-password-hash`). Correcção proposta: bcrypt/Argon2 + corrigir `verifyPassword()` (que hoje devolve sempre `true`, ignorando o hash).
- `#6` — `packages/scripts/src/docs/generate-agents-doc.ts:85` — escaping incompleto ao gerar tabela Markdown (`js/incomplete-sanitization`). Risco real baixo (dados internos, não input externo). Correcção proposta: escapar `\` antes de `|`. *(2026-09-19: RESOLVIDO — na verdade já estava, desde o commit `a828bf2` no mesmo dia 2026-09-17 21:17, minutos depois deste resumo ter sido escrito. `escapeMdCell()` já escapa backslash antes de pipe, correcto, e já tinha extracção própria; só faltava teste dedicado — `tests/unit/generate-agents-doc.test.ts` confirma 4/4 a passar, cobrindo exactamente este caso. Ver `EXECUTION-PROMPTS.md` A21.)*

**Números de teste corrigidos:** `README.md` (raiz) já não tinha o número errado (removido numa tarefa anterior). `runner/README.md` tinha "51 testes, 83% cobertura" — confirmado por `pytest` real: **167 testes, todos a passar, 87% de cobertura**. Corrigido.

*Nota: os números "skills/ = 50" e "agents/ = 21" registados acima (bloco de 2026-09-16) estão desactualizados pelo trabalho de hoje (G2 +16 skills, G4 +13 agentes, B2 +1 agente) — não recalculados nesta tarefa, fica como pendência de inventário.*


## 📋 Resumo do dia 2026-09-18 (auditoria de agentes, Fase 1)

**Auditoria de Agentes iniciada** (`docs/architecture/agents-audit/`), mesma disciplina de Master Plan/Governança/Memória (código real > README). Escopo desta fase: Agent Frameworks + Multi-Agent Architectures + Runtime/Execution Engine + Planning.

**Achado de arrancada:** `docs/architecture/patterns-from-orchestrators/` já cobria 8 frameworks (LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AG2, Haystack) com 18 padrões extraídos (O01–O18) — não refeito. A Fase 1 cobriu só o que faltava: **Microsoft Agent Framework, Google ADK, OpenAI Agents SDK, LlamaIndex (agentes/workflows), DSPy, smolagents**, 1 auditoria completa por framework via subagentes paralelos, código real verificado (não marketing). Ver `agents-audit/FASE1-AGENTES.md` (síntese) e `agents-audit/deep/*.md` (detalhe por framework).

**Classificação final: os 6 são EXTRACT** (nenhum ADOPT/ADAPT) — todos são frameworks opinativos completos, incompatíveis com a regra de não substituir o runtime Plan-Execute/MCP próprio por um framework externo. 33 padrões novos extraídos (O26–O58), destaque para **O48** (`BootstrapFewShot` do DSPy — gerar traces reais do próprio agente, filtrar por métrica, usar como few-shot; aplicável directamente com o `events.jsonl` já existente).

**Achado decisivo (corrigido após primeira entrega — faltava auditar o próprio repo primeiro, como `GOV-FASE1`/`FASE1-MEMORIA` fizeram):** este repo já tem **dois runtimes de agentes**, não zero. TypeScript (`packages/core/src/orchestrator/`): `Router.ts`/`Planner.ts`/`Executor.ts` são **REAL** (`Planner.ts` chama LLM de facto para escolher agentes e decompor em passos), mas `Orchestrator.ts` que devia ligar os três é **MOCK** — peças reais, desligadas. Python (`runner/plan_runner/`): motor "native" sequencial sem LLM-planning nem checkpoint; motor "langgraph" (opt-in) já tem **checkpoint real via `SqliteSaver`** e **execução paralela por ondas** — o padrão O03 de `patterns-from-orchestrators` já está implementado em código, não é só "a estudar". `budget_max_replans` existe no schema do plano e nunca é lido em lado nenhum — campo morto. HITL `edit` só tem efeito real no motor `langgraph` (via `--payload-file`), não no motor `native` (aceite mas ignorado). "Multi-agente" hoje é, na prática, um humano/Claude a resolver `pending_steps/request.json` → `result.json` manualmente — não há chamada agente→agente automática em lado nenhum. Ver `agents-audit/FASE1-AGENTES.md` secção 1.

**Achado que cruza com `GOV-FASE1.md`:** o Google ADK teve o mesmo bug que o nosso `HitlManager.ts` tem hoje (recusa humana não bloqueava a tool, corrigido só recentemente) — e esta fase encontrou o paralelo ainda mais próximo, no próprio `runner/plan_runner/`: o motor `native` aceita a decisão `edit` sem lhe dar efeito. Confirma que o padrão de enforcement no boundary (O26/O34) precisa de disciplina própria, não vem "grátis" nem das implementações de referência das grandes empresas.

**Achado de processo (fora do escopo técnico, mas registado por pedido explícito):** a queixa de "falta de direcionamento/planejamento — algo que defina escopo, desmembre em fases, execute uma a uma" foi investigada. Já existe `agents/meta/planejador.agent.md` (Fast-Path/Full Cycle) e `agents/meta/arquitetura-agentes.agent.md`, mas **nenhum cobre o papel de PMO/Project Director** (gestão de portfólio de iniciativas, não de uma tarefa). É lacuna real de arquitectura organizacional, não resolvida por nenhum dos 14 frameworks já auditados (8 de `patterns-from-orchestrators` + 6 desta fase) — nenhum se propõe a ser um PMO. Decisão pendente humana.

**Pendente:** Fase 2 (Skills/Tool Use/MCP/Communication — verificar sobreposição com `patterns-from-hermes/`/`patterns-from-mcp/` antes de nova pesquisa) e Fase 3 (Coding/Research agents, Evaluation, Testing).


## 📋 Resumo do dia 2026-09-18 (auditoria de agentes, Fase 2)

**Fase 2 concluída** (`agents-audit/FASE2-AGENTES.md`). Escopo: Tool Use + Agent Communication (A2A/ACP) + ecossistema MCP sob perspectiva de agentes. Skills (2.7) e Observability (2.11) **não foram refeitos** — já cobertos por `patterns-from-hermes/` (ciclo de vida candidate→active→patched→archived) e por `memory/FASE3-MEMORIA.md` secção 5 (Langfuse, OpenTelemetry, RAGAS), respectivamente.

**Achado interno (Tool Use), por leitura directa, sem pesquisa externa:** a tool MCP `run_plan` só invoca o motor "native" do `plan_runner` (nunca o motor "langgraph", que tem checkpoint real e execução paralela — achado da Fase 1); e `resume_plan` só aceita `approve|reject`, não `edit` (que o motor langgraph já suporta via `--payload-file`). A superfície MCP exposta é mais estreita do que a capacidade real do runtime por baixo.

**Agent Communication:** ACP (IBM/BeeAI) está **morto** — arquivado desde ago/2025, fundido no A2A. A2A (Google→Linux Foundation→Agentic AI Foundation, ago/2026) é maduro (25,6k★, spec 1.0, 6 SDKs oficiais, adoptado de facto por Google ADK e Microsoft Agent Framework) mas classificado **REFERENCE**, não ADOPT — resolve comunicação entre agentes de organizações diferentes, um problema que o PCU não tem hoje (o `pending_steps/request.json` → `result.json` é IPC dentro da mesma confiança, não cross-org). Achado extra: a alegação de "OpenAI Agents SDK suporta A2A", repetida por vários blogs, foi **contradita** por verificação directa (issues #472/#1374 fechadas sem PR).

**Ecossistema MCP — achado mais importante desta fase:** verificado por leitura de código que `mcp-agent` (lastmile-ai, ~8.5k★, a implementação de referência mais citada dos padrões "Building Effective Agents" da Anthropic) **também não verifica scope/capacidade antes de chamar uma tool** — a mesma lacuna que `packages/mcp/ToolExecutor.ts` tem hoje (`GOV-FASE1.md`). Confirma que não existe framework cliente maduro que resolva isto por nós; a correção continua a ser interna (portar o pipeline sanitize→auth→rate→scope→execute→audit já testado em `mcp/plan_runner/policy.py`). Achado à parte, fora do conhecimento base do modelo (verificado por fetch directo, recomenda-se confirmação humana): a spec MCP oficial já avançou para **2026-07-28**, que deprecia Sampling/Roots/Logging e Dynamic Client Registration.

**11 novos padrões (O59–O69)**, destaque para O66 (agente-como-servidor MCP, confirmado em 3 implementações independentes — Microsoft Agent Framework, mcp-agent, FastMCP — elevado a **ADOPT como princípio de desenho**, não como dependência).

**Pendente (à data):** Fase 3 (Coding/Research agents, Evaluation, Testing, Agentes especializados por domínio) — **concluída ainda no mesmo dia, ver bloco seguinte.**


## 📋 Resumo do dia 2026-09-18/19 (auditoria de agentes, Fases 3-6 — CONCLUÍDA)

**Auditoria de Agentes concluída de ponta a ponta.** Fases 3-5 (Knowledge/Ingestion, Evaluation+Testing, Coding/Research Agents + Agentes Especializados) e Fase 6 (síntese final) executadas em sequência, sem pausa para confirmação, a pedido explícito. Ficheiros: `agents-audit/FASE3-AGENTES.md`, `FASE4-AGENTES.md`, `FASE5-AGENTES.md`, e a síntese **`agents-audit/AUDIT-AGENTS.md`**.

**Achado central da síntese final:** o mesmo padrão — peças reais e funcionais, desligadas umas das outras — repetiu-se em **5 fases diferentes**, sem ter sido procurado deliberadamente: `Orchestrator.ts` MOCK apesar de Router/Planner/Executor REAL (Fase 1); superfície MCP mais estreita que o runtime (Fase 2); `yt-dlp`/`faster-whisper` já em produção mas nunca ligados ao RAG (Fase 3); `budget_max_replans` como campo morto (Fase 1); `AgentConfig` sem campo `profile` apesar do exercício de extração já ter sido feito manualmente em `MCP-MAPPING.md` (Fase 5). Conclusão da síntese: o trabalho de maior retorno imediato é ligar peças já construídas, não adotar mais nenhum dos ~45 projetos avaliados nas 5 fases — nenhum foi classificado ADOPT/ADAPT como substituto de runtime.

**Achados por fase:**
- **Fase 3 (Knowledge/Ingestion):** recomendação mínima = Crawl4AI (web) + MarkItDown (documentos) + gitingest (GitHub código). `yt-dlp`+`faster-whisper` já existem no repo irmão, só falta ligação.
- **Fase 4 (Evaluation/Testing):** DeepEval classificado **ADOPT** (nativo pytest, local via Ollama, cobre trajetória de tool-use). Pendência da auditoria de memória sobre o Ragas **resolvida** — o projeto existe e tem métricas de agente reais.
- **Fase 5 (Coding Agents):** achado de metodologia — `OpenHands/OpenHands` (88.401★, citado na auditoria de memória) **já não é o runtime do agente**, é hoje uma app Electron de controlo; o loop real vive em `OpenHands/software-agent-sdk`, só 1.134★. SWE-agent classificado **ADAPT** (windowed editor com 2x SWE-Bench comprovado). Confirmado por código: `config/agents.config.ts` continua uma lista plana de 24 agentes, sem campo `profile` — a recomendação central da revisão de arquitetura discutida no início desta auditoria ainda não tem nenhuma implementação.

**Fecho da queixa de "falta de direcionamento/planejamento" que abriu esta auditoria:** confirmado na síntese final (secção 10) que nenhum dos ~45 projetos auditados resolve isto — não é lacuna técnica, é decisão humana de arquitetura organizacional (PMO/Project Director), já registada como tal desde a Fase 1.

**Nada commitado ainda** — todos os ficheiros estão no working tree do clone local (`C:\Users\souza\Claude Code\network-agents-setup`), sessão sem push configurado (clone anónimo/read-only).


## 📋 Resumo do dia 2026-09-19 — Ronda de auditorias adicionais (Ingestion, Tools/MCP, Orchestration, Security, Evaluation, Observability) + validação cruzada de 7 recomendações anteriores

**6 novos domínios de auditoria + 1 documento de validação cruzada**, todos em pastas próprias sob `docs/architecture/`: `ingestion-audit/`, `tools-mcp-audit/`, `orchestration-audit/`, `security-audit-2026/`, `evaluation-audit/`, `observability-audit/`, `meta-validation/`. Metodologia igual às anteriores — código real > README, verificação directa antes de qualquer classificação.

**Achado transversal desta ronda (confirma e estende o padrão já visto na auditoria de Agentes):** validei as 7 "recomendações supostamente exageradas" pedidas (Governança/AGT, HITL/contrato-v1, 33-agentes, 50-skills, Bootstrap/CLAUDE.md, Segurança/B2, RAG/L5) e **nenhuma delas era, de facto, exagerada** — as auditorias anteriores já eram precisas e auto-críticas. O padrão real, repetido em quase todas as 7: peças reais e bem desenhadas, que ficaram por ligar/indexar/regenerar depois de prontas.

**Achados mais importantes desta ronda:**
- **HITL (S9):** `runner/plan_runner/hitl.py` existe e tem testes, mas **zero** ligação a `engine.py`/`langgraph_engine.py`/`cli.py` — confirmado por busca de código. M2 (TS) e M3 (teste end-to-end) dependem de S9, que continua por fazer.
- **RAG/L5 (S10):** ao contrário do que a pergunta presumia, **já não está desligado** — `knowledge_wiring.py` liga-o de facto a `engine.py`. Falta só propagação: apenas 1 dos 12 templates de plano usa o bloco `knowledge:`.
- **Tools/MCP:** verificação linha-a-linha confirma `packages/mcp/ToolExecutor.ts`/`MCPServer.ts` sem qualquer autorização/autenticação — e nenhuma biblioteca externa madura (FastMCP, mcp-agent) resolve isto por nós; a correcção é portar o pipeline já testado em `mcp/plan_runner/policy.py` (Python) para TypeScript. *(2026-09-19: path traversal de `filesystem.ts` (A3), regex DoS de `scrape_webpage` (A6), falta de autorização em `ToolExecutor.ts` (C1, via `ToolPolicy.ts` novo) e SSRF de `http_request` (A5, via `SsrfGuard.ts` novo — `ssrf-req-filter` revelou-se incompatível com o `fetch` global, ver nota na secção 2) RESOLVIDOS; autenticação HTTP de `MCPServer.ts` continua pendente — ver `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secções 2/3/4 e `EXECUTION-PROMPTS.md` A3/A5/A6/C1.)*
- **Segurança:** 3 achados novos e acionáveis — senha `network123` **hardcoded** (não placeholder) em `k8s/secrets.yaml`; `knowledge_chunks_t6` **sem Row Level Security**, qualquer código com `DATABASE_URL` lê/escreve chunks de qualquer agente; e o lado Python **não tem lockfile nenhum**, tornando o supply chain estruturalmente inverificável mesmo com rede livre (não é só bloqueio de sandbox). *(2026-09-19: item da senha `network123` resolvido do lado do repo — senha real rotacionada pelo Desenvolvedor fora do repo, no Supabase, durante esta sessão; ver `security-audit-2026/AUDIT-SECURITY-2026.md` secção 7 e `EXECUTION-PROMPTS.md` itens A1/A1b. RLS de `knowledge_chunks_t6` também RESOLVIDO — activado + policy `anon_deny`, aplicado directamente no Supabase; ver secção 6 e `EXECUTION-PROMPTS.md` item A2.)*
- **Evaluation/Custo:** `model_tier` (planner/executor/verifier) é só schema, zero implementação — mesma classe de "campo morto" que `budget_max_replans`. LiteLLM Router+Budget Manager recomendado (ADOPT) para fechar o gap de Unbounded Consumption (LLM06).
- **Observability:** correcção a `GOV-FASE1.md` — o lado TypeScript **não está ausente**, existe (`packages/observability/Tracer.ts`), mas é uma reimplementação manual com um **bug real** (`traceId`/`spanId` trocados) e memory leak, usada num único ponto do código. Recomenda-se substituir pelo SDK oficial OpenTelemetry.
- **Bootstrap:** `AGENTS.md` (raiz) e `docs/generated/AGENTS.md` nunca foram indexados em `BOOTSTRAP.md`; o segundo está desactualizado ("22 agentes", real são 24).

**Nada commitado, nada corrigido no código** — esta ronda é só auditoria/descoberta, como as anteriores. As correcções concretas (S9, RLS, lockfile Python, `Tracer.ts`, indexação do `BOOTSTRAP.md`) ficam registadas para decisão humana.


## 📋 Resumo do dia 2026-09-19 (parte 2) — Refeitura em padrão ouro de Ingestão/Tools-MCP/Orquestração + correção de um erro de 4 documentos

A pedido explícito do utilizador (as 3 auditorias acima tinham sido feitas por consolidação/citação, não por pesquisa externa nova — diferente do rigor das outras). Refeitas uma a uma com subagentes de pesquisa dedicados e leitura de código própria, sem reaproveitar texto anterior.

**Ingestão:** pipeline interno (989 linhas) lido por completo. CVEs reais encontrados em Crawl4AI (4 advisories 2026, uma delas CVSS 9.6), Firecrawl (2 SSRF históricos), MarkItDown (RCE via pdfminer.six + zip bomb aberto sem fix), Docling (RCE via PyYAML, mitigável por versão), gitingest (issue de segurança aberta — vazamento de PAT — e projeto órfão há 13+ meses, revisto de ADOPT para **ADAPT com reservas**), yt-dlp (16 CVEs reais catalogados, incluindo um CVSS 8.8, todos condicionais a flags perigosas). *(2026-09-19: `embedder.py` enviava a Gemini key por query param — RESOLVIDO, agora via header `x-goog-api-key`, confirmado com chamada real (768 dims) + suite completa do runner 172/172; ver `ingestion-audit/AUDIT-INGESTION.md` secção 6 e `EXECUTION-PROMPTS.md` A7.)*

**Tools/MCP:** leitura completa de todos os ficheiros de `packages/mcp/src/`. **3 achados novos e graves, não vistos antes:** `query_database` executa qualquer SQL do agente sem restrição (mesma classe de falha que descontinuou o servidor Postgres oficial da Anthropic); `http_request` sem proteção SSRF nenhuma (3 CVEs reais citados como precedente); `filesystem.ts` com bug clássico de path traversal — **cuja correção já existe no lado Python do mesmo repo** (`policy.py:sanitize_repo_path`), só nunca foi replicada para TypeScript. *(2026-09-19: path traversal de `filesystem.ts` RESOLVIDO — ver `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 3 e `EXECUTION-PROMPTS.md` item A3; `query_database`/`http_request`/autorização continuam pendentes.)*

**Orquestração — o achado mais importante desta sessão inteira:** `Orchestrator.ts` (TypeScript) **não é mock**. Confirmado por leitura completa (480 linhas): liga Router→Planner→Executor de facto, com lógica real de segurança/deliberação/orçamento, e há um entry point real e completo (`apps/api/src/index.ts`) que o instancia com os 24 agentes de `config/agents.config.ts`, tools MCP reais, Postgres, OpenAI. **Isto corrige um erro repetido em `CORE-MAPPING.md` → `GOV-FASE1.md` → toda a auditoria de Agentes (Fase 1, síntese final) → várias entradas deste STATUS.md.** A formulação correta: o código é real dos dois lados (TS e Python); a diferença é de maturidade **operacional** — Python tem 167 testes que correm de facto, TS tem código real nunca validado a correr contra infraestrutura verdadeira (Postgres/OpenAI), e um teste de integração (`ExecutionFlow.test.ts`) com um bug de assinatura de construtor (5 argumentos passados, 6 exigidos) ainda por confirmar se mascara alguma falha. *(2026-09-19: RESOLVIDO — `mockHitl` adicionado como 6º argumento + `vi` adicionado ao import de `vitest` (2º bug, encontrado durante a correcção). `tsc --noEmit` limpo para este ficheiro. Verificação por execução real ainda pendente de `prisma generate` — ver B10. Ver `orchestration-audit/AUDIT-ORCHESTRATION.md` secção 3 e `EXECUTION-PROMPTS.md` B2.)* Achado relacionado: `SecurityManager.verifyPassword()` já foi corrigido (bcrypt real) desde 17/09 às 21:18 — `GOV-FASE1.md`, escrito no dia seguinte, citou a versão antiga (sempre `true`) sem reverificar.

**Lição registada explicitamente nos documentos corrigidos:** nem a documentação interna deste repo (`CORE-MAPPING.md`) é imune a precisar de verificação directa antes de ser citada como facto — a mesma disciplina "código > README" aplica-se a "código > documento de mapeamento do próprio repo".

Documentos com errata visível adicionada (não apagados, corrigidos com nota no topo): `agents-audit/FASE1-AGENTES.md`, `agents-audit/AUDIT-AGENTS.md`. Documento com reescrita completa: `orchestration-audit/AUDIT-ORCHESTRATION.md`.
