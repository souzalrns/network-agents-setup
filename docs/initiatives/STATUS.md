# Status — pendências consolidadas

> Gerado em: 2026-09-13
> Base: leitura do repo + cruzamento com sessões
> Método: tudo o que foi discutido e não está feito, classificado

## 🔴 Crítico (bloqueia outras coisas ou é risco real)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **C1** | **Fase 0.4** — marcar A4/A5/A6 do `ITEM13-MARKETING-ROADMAP.md` como `[x]` com link do run | 5 min | Nada | Auditoria Claude |
| **C2** | **Modo external do `plan_runner`** falha silenciosamente se `--out` fora de `pilots/` | 1h | Pilotos reais | `INIT-012` |
| **C3** | **`auth.ts` fail-closed** também no `agent-network-mcp` (produção) | 30 min | Segurança prod | Auditoria Claude |
| **C4** | **T6 ingestão é stub** — 33 knowledge packs de marketing não estão em RAG nenhum | 1 dia | RAG funcional | Auditoria Claude |

## 🟠 Alto (resolve problema real, valor claro)

| ID | Item | Esforço | Bloqueia | Origem |
|---|---|---|---|---|
| **A1** | **Fase 1.1** — CI bloqueia se vitest falhar (`continue-on-error: false`) | 5 min | Rede de segurança | Auditoria Claude |
| **A2** | **Fase 1.2** — testes do caminho crítico (Router, Planner, Executor, HitlManager) — ≥20 casos | 2-3h | Refactor seguro | Auditoria Claude |
| **A3** | **Fase 1.3** — teste do runner no CI (5 templates dry-run + 1 stub) | 1h | Runner gate | Auditoria Claude |
| **A4** | **Fase 1.4** — gerar e commitar `pnpm-lock.yaml` | 5 min | Builds reprodutíveis | Auditoria Claude |
| **A5** | **Fase 1.5** — `validate:consistency` + wiring marketing + import runner | 1h | Consistência | Auditoria Claude |
| **A6** | **Fase A.2** — `runner/plan_runner/hitl.py` (lado Python do contrato v1) | 1 dia | HITL durável | Nosso |
| **A7** | **Working memory** (`MEMORY.md` curado por cliente, ~1300 tokens) | 1 dia | Contexto sem RAG | Nossa |

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
| **B7** | **`patterns-from-mcp`** — documentar o que existe no MCP server | 1h | Nada | Nossa |
| **B8** | **`patterns-from-codebase-memory`** — documentar o `codebase-memory-mcp` | 1h | Nada | Nossa |
| **B9** | **`node-platform.md`** — documentar a plataforma Node (`HitlManager`, rotas, tools) | 2h | Nada | Nossa |

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

## Como usar este ficheiro

- **Adicionar item**: nova linha na categoria correta
- **Mudar estado**: mover de 🔴 para 🟠, ou 🟠 para 🟢
- **Fechar item**: apagar a linha (ou mover para uma secção "Done" no fim)
- **Reclassificar**: se um item ganha urgência, sobe de categoria

**Regra**: nenhum item é apagado sem ser feito. Só muda de categoria.

---

## Ordem sugerida (próximas 3 sessões)

### Sessão 1 (1-2h)
- C1 (Fase 0.4) — 5 min
- A1 (CI bloqueia vitest) — 5 min
- A4 (`pnpm-lock.yaml`) — 5 min
- B7-B9 (documentar o que existe) — 2h

### Sessão 2 (1 dia)
- A2 (testes do caminho crítico) — 2-3h
- A3 (teste do runner no CI) — 1h
- A5 (consistência) — 1h
- C2 (modo external com erro explícito) — 1h

### Sessão 3 (1-2 dias)
- A6 (`hitl.py`) — 1 dia
- A7 (working memory) — 1 dia
- M1 (session search) — 4h

**Depois disto**: Fase 1 fechada. O motor tem rede de segurança.