# AUDIT-1 — Estrutura de repos, pacotes e organização

> **Base:** commit `3dc3b25` (`main`), branch de trabalho `claude/audit-completo`.
> **Data:** 2026-09-29.
> **Método:** leitura directa dos ficheiros + comandos reais (grep de imports, `tsc`, `pnpm install`, `ci:typecheck`) num clone Linux do GitHub (Node 22, pnpm 8.15.9). Não é a cópia local Windows — ver "Limites" no fim.
> **Regra:** cada afirmação tem `ficheiro:linha` ou comando reproduzível; o que não foi verificável está marcado.

## Resumo

O repo tem **dois runtimes independentes** que não se chamam um ao outro: um **motor Python** (`runner/plan_runner`, ~3.2k LOC, com testes e CI próprios) e uma **plataforma TypeScript** (`apps/api` + 8 pacotes, ~19.5k LOC, dos quais 12.7k em `packages/core`). Três unidades estão **mortas** (`apps/web`, `packages/langgraph`, `tests/package.json`) e o **build de produção TS não funciona**: `pnpm build`, o `Dockerfile` e o `setup.sh` dependem de um `tsc` por pacote que falha com `TS6059`, verificado. O CI só passa porque usa um `tsconfig.typecheck.json` agregado com `--noEmit`, que nunca produz artefactos. Há três duplicações estruturais (ingestão ×2, LangGraph ×2, superfície MCP ×2) e documentação muito volumosa: 226 ficheiros, com o `STATUS.md` corrente a 95 KB.

---

## Convenções usadas neste documento

| Marca | Significado |
|---|---|
| **REAL** | Existe, é consumido por algo que corre (import, CI, CLI) e foi verificado |
| **MORTO** | Sem consumidor, não compila, ou fora de qualquer pipeline |
| **AMBÍGUO** | Existe e pode funcionar, mas o papel/consumidor não é claro ou é só parcial |
| **SÓ-NO-PAPEL** | Configuração/infra que descreve um deploy que nunca foi produzido |
| `[PEDIDO]` | Secção pedida no brief |
| `[ACRESCENTADO PELO AUDITOR]` | Secção/achado não pedido, adicionado por ter valor |

---

## 1.1 Repos e pacotes — REAL / MORTO / AMBÍGUO `[PEDIDO]`

### Repositórios

| Repo | Papel declarado | Classificação | Evidência |
|---|---|---|---|
| `network-agents-setup` (este) | Núcleo (motor + governança + horizontais + RAG) | **REAL** | `CLAUDE.md` (identidade); `docs/architecture/ECOSYSTEM.md:9` |
| `agent-network-mcp` | Plug-in de verticais (33 agentes em `lib/agents.js`) | **REAL** (fora deste repo) | `ECOSYSTEM.md:10,29`. Ligação a este repo: `MCP_API_KEY`/`MCP_URL` lidos em `runner/plan_runner/` (grep de `os.environ`) — detalhe na Fase 2 |
| Outros (`mesaflow-api`, `vianna-gestao`, `viannalegal-site`) | Produtos | Fora de âmbito | `CLAUDE.md` tabela "Onde está o resto"; `docs/architecture/REPOSITORY-MAP.md:9-16` |

### Unidades de código deste repo

LOC = linhas de `.ts/.tsx/.py` excluindo `tests/` (comando `find … | xargs cat | wc -l`).

| Unidade | Runtime | LOC | Classificação | Evidência |
|---|---|---|---|---|
| `runner/plan_runner/` | Python | 3157 | **REAL** | 20 módulos, 24 ficheiros de teste; CI `runner-tests.yml` e `release.yml` |
| `mcp/plan_runner/` | Python | 511 | **REAL** | Wrapper MCP stdio sobre o `runner`: `tools_impl.py:15-16` injecta `runner/` no `sys.path`, `:69,:102` chamam `plan_runner.engine`. Não é duplicado |
| `scripts/*.py` (`ingest_apply.py`, `ingest_delta.py`) | Python | 594 | **REAL** | Corre em CI: `.github/workflows/ingest-knowledge.yml` (passos "Dry-run delta" e "Apply delta") |
| `apps/api/` | TS | 1169 | **REAL** (para dev/teste), **não construível** para produção | Entrypoint `apps/api/src/index.ts:27-131`. Build falha — ver 1.4 |
| `packages/core/` | TS | 12689 | **REAL** (importado), conteúdo misto | Importado por `apps/api/src/index.ts:3-12`, `packages/scripts`. Conteúdo: ver `CORE-MAPPING.md` e Fase 4 |
| `packages/mcp/` | TS | 1346 | **REAL** (ToolRegistry/tools) + **AMBÍGUO** (`MCPServer`/`MCPClient`) | Tools montadas em `apps/api/src/index.ts:44-51`. `MCPServer.createHttpHandler()` sem superfície HTTP montada (registado em `docs/initiatives/STATUS.md:57`, S11) |
| `packages/memory/` | TS | 383 | **REAL** (importado) | `packages/core/src/orchestrator/Executor.ts:3`, `Orchestrator.ts:6`, `apps/api/src/index.ts:13` |
| `packages/observability/` | TS | 350 | **REAL** | 51 imports no repo (grep `from '@network-agents/observability`) |
| `packages/shared/` | TS | 234 | **REAL** | Tipos: `Planner.ts:3`, `Executor.ts:5-6`, `config/agents.config.ts:1` |
| `packages/websocket/` | TS | 472 | **REAL** | `apps/api/src/websocket.ts:2`, montado em `apps/api/src/index.ts:107` |
| `packages/scripts/` | TS | 3006 | **REAL** (docs/validate/smoke) + **AMBÍGUO** (`src/ingest/*`) | CI corre `validate:consistency` e `ci:smoke-test` (`ci.yml`). O pipeline `src/ingest/*` (jurídico, dependência `openai` em `packages/scripts/package.json`) é paralelo ao pipeline Python/Gemini que corre em CI |
| `packages/langgraph/` | TS | 391 | **MORTO** | Zero importadores (grep `@network-agents/langgraph\|packages/langgraph`: só `package.json`, `vitest.config.ts:20`, `apps/api/package.json:16` — declarado, nunca importado). **Excluído** do `tsconfig.typecheck.json` (lista `include` não o tem) → nunca é type-checked. 0% cobertura (`STATUS.md:43`, S24). O LangGraph que corre é o Python (`runner/plan_runner/langgraph_engine.py`) |
| `apps/web/` | TSX | 92 | **MORTO** | Sem `package.json` (não é pacote do workspace, apesar de `pnpm-workspace.yaml:3`). `Dashboard.tsx:3` usa `useState` sem import; `:15-17` usam `MetricCard`/`BarChart`/… nunca definidos; `useWebSocket.ts:2` importa `@websocket/WebSocketClient`, alias que não existe em nenhuma config. Não compila; fora do typecheck |
| `tests/` (TS) | TS | — | **REAL** | `ci.yml:99` corre `vitest run tests/unit` |
| `tests/package.json` | — | — | **MORTO** | Fora do workspace (`pnpm-workspace.yaml:2-3` só cobre `packages/*`, `apps/*`). Declara `vitest ^1.0.0` (`tests/package.json:13`) contra `^4.1.11` da raiz. Nunca instalado nem usado |
| `config/agents.config.ts` | TS | — | **REAL** | Importado em `apps/api/src/index.ts:25` e registado em `:61` |

### Conteúdo não-código

| Unidade | Classificação | Evidência / nota |
|---|---|---|
| `agents/` (39 `.md`) | **REAL como documentação**, ligação ao runtime a verificar | Fase 3 |
| `skills/marketing\|design\|meta` | **REAL** | Resolvidos pelo `runner` (`executor.py`, S34 em `STATUS.md:46`) |
| `skills/claude/` (30 ficheiros) | **AMBÍGUO — cópia vendored** | Cópia das skills addyosmani vindas do `agent-network-mcp` via `scripts/sync-skills-from-prod.sh`. O script devia pôr o cabeçalho `COPIA de agent-network-mcp` em cada ficheiro; **0/30** o têm (grep) → a cópia não foi feita pelo script tal como está, e a proveniência não está marcada |
| `.specify/` + `.github/skills/speckit-*` | **AMBÍGUO** | Spec-kit 1.0.4 para **Copilot** com scripts **PowerShell** (`.specify/init-options.json`). Referenciado só em docs (`docs/architecture/spec-kit/`, `patterns-from-*`). Nenhum uso verificado |
| `docs/` (226 ficheiros, 112 em `architecture/`) | **REAL mas sobredimensionado** | Ver 1.2 e 1.3 |
| `pilots/` | **REAL** (evidência de pilotos) | `pilots/evidence/*/status.json` |
| `k8s/` (8 manifests) | **SÓ-NO-PAPEL** | `k8s/api.yaml:18` usa `network-agents/api:latest`, imagem que nenhum workflow constrói nem publica. `k8s/secrets.yaml:1-3` admite pipeline de substituição "TODO: confirmar" |
| `Dockerfile` | **MORTO (quebrado)** | `:5-6` achatam todos os `package.json` num único destino (`./packages/`); `:9` `pnpm build` falha (ver 1.4); `:22` `CMD` aponta para `dist/apps/api/src/index.js`, mas cada pacote compila para o seu próprio `dist/`. `docker build` **não corrido** (sem Docker no sandbox) |
| `docker-compose.yml` | **AMBÍGUO** | `:4` `postgres:16` **sem pgvector**, mas o schema usa `Unsupported("vector")` (`packages/memory/prisma/schema.prisma:123,162`) → a migração provavelmente falha. **NÃO VERIFICADO** (sem Docker); o CI usa `pgvector/pgvector:pg16`, o que é consistente com esta leitura |
| `setup.sh` | **Quebrado a meio** | Corre `pnpm build`, que falha (1.4) |

---

## 1.2 Organização actual — o que vive onde `[PEDIDO]`

### Mapa de camadas (real, não declarado)

```
┌─────────────────────── RUNTIME PYTHON ───────────────────────┐
│ runner/plan_runner  ← motor de planos YAML (native + LangGraph)│
│   ├─ skills/**/SKILL.md + agents/**/*.agent.md (resolvidos)    │
│   ├─ hitl.py (ficheiros jsonl)                                  │
│   ├─ mcp_knowledge.py → agent-network-mcp (retrieve RAG)       │
│   └─ supabase_writer.py                                         │
│ mcp/plan_runner     ← expõe o runner como MCP stdio            │
│ scripts/ingest_*.py ← ingestão RAG (Gemini → Supabase), CI      │
└───────────────────────────────────────────────────────────────┘
            ▲  só se tocam por ficheiros (hitl-requests.jsonl)
            ▼  — M2 (HitlManager.importFromFile), STATUS.md:74
┌─────────────────────── RUNTIME TYPESCRIPT ───────────────────┐
│ apps/api  ← Express + WS; monta Orchestrator/Planner/Executor │
│   └─ packages/core (orquestrador + governança + 30+ módulos)   │
│        ├─ packages/mcp (ToolRegistry, tools, MCPServer*)       │
│        ├─ packages/memory (Prisma + Redis)                     │
│        └─ packages/observability / shared / websocket          │
│ packages/scripts ← docs/validate/smoke + ingest TS (paralelo)  │
│ packages/langgraph ← MORTO   apps/web ← MORTO                  │
└───────────────────────────────────────────────────────────────┘
```

### Fronteiras entre pacotes (grafo de imports verificado)

| Pacote | Importa (`@network-agents/*`) |
|---|---|
| `apps/api` | core, mcp, memory, observability, websocket (declara também `langgraph` e `shared`, que **não importa**) |
| `packages/core` | mcp, memory, observability, shared |
| `packages/scripts` | core, mcp, memory, observability |
| `packages/langgraph` | core, observability (mas ninguém o importa) |
| `packages/mcp` | observability |
| `packages/websocket` | observability |
| `packages/memory`, `observability`, `shared` | — (folhas) |

Sem ciclos. Mas `core` não é uma camada de "governança" no sentido estrito: contém o orquestrador, o planner, o LLM, a segurança, a UX, os produtos e a simulação, 39 ficheiros e 12.7k LOC (`CORE-MAPPING.md:7`). O nome esconde que é o **motor TS inteiro**, e não só governança como o `README.md:18` e o `ECOSYSTEM.md:21` o descrevem.

### Duplicações estruturais

| Capacidade | Implementação A | Implementação B | Qual corre de facto |
|---|---|---|---|
| Orquestração | Python `plan_runner` (planos YAML) | TS `Orchestrator`/`Planner`/`Executor` (`apps/api`) | Ambas, **desligadas entre si** |
| LangGraph | Python `langgraph_engine.py` | TS `packages/langgraph` | Só Python |
| Ingestão RAG | Python `scripts/ingest_*.py` (Gemini, CI) | TS `packages/scripts/src/ingest/*` (jurídico, `openai`) | Python em CI; TS só manual (não verificado se corre) |
| Superfície MCP | Python `mcp/plan_runner` (stdio, real) | TS `packages/mcp/src/server/MCPServer.ts` (não montado) | Só Python |

---

## 1.3 Sugestões de retificação de estrutura `[PEDIDO]`

Quem: **CLAUDE** (executável por Claude sem decisão nova), **DEV** (precisa decisão humana ou acesso), **AMBOS** (DEV decide, Claude executa). Na dúvida, DEV.

| ID | Acção | O quê | Porquê | Impacto | Quem |
|---|---|---|---|---|---|
| R1 | **Eliminar** | `apps/web/` | Não compila, sem `package.json`, sem consumidor (1.1). Decidir primeiro se há intenção real de frontend: se sim, recriar a partir de zero com toolchain própria | Baixo (limpeza) | AMBOS |
| R2 | **Eliminar** (ou mover para `packages/experimental/`) | `packages/langgraph/` | Morto, fora do typecheck, duplica o LangGraph Python que corre de facto | Baixo | AMBOS |
| R3 | **Eliminar/fundir** | `tests/package.json` | Manifest órfão fora do workspace, com versões obsoletas; a raiz já declara `vitest`/`supertest` | Baixo | CLAUDE |
| R4 | **Criar** | `tsconfig.json` por pacote (ou project references) | Sem isto `pnpm build`, o `Dockerfile` e o `setup.sh` falham (1.4); a API não tem artefacto de produção | **Alto** — bloqueia qualquer deploy TS | AMBOS |
| R5 | **Corrigir ou marcar** | `Dockerfile`, `k8s/` | Descrevem um deploy que nunca aconteceu. Ou corrigir (depende de R4), ou mover para `deploy/_templates/` com um README "não usado" | Médio | DEV |
| R6 | **Fundir — decidir fonte única** | Ingestão RAG Python vs TS | Duas pipelines com modelos de embedding diferentes (Gemini 768d vs `openai`) → o risco é ter embeddings incompatíveis na mesma tabela. Ligado à visão "ingestão robusta" | **Alto** | DEV |
| R7 | **Partir** | `packages/core/` → `orchestrator` / `governance` / `experimental` | O nome "core = governança" é enganador; 14 MOCK misturados com o caminho crítico. É a mesma intenção do M5 (`STATUS.md:77`) | Médio | AMBOS (M5 já exige aprovação da lista) |
| R8 | **Decidir o papel** | Motor Python vs motor TS | Dois orquestradores sem ponte (1.2). A visão pede **um** maestro. Sem decisão, todo o trabalho de delegação por área (Fase 3) duplica-se | **Alto** — decisão de arquitectura | DEV |
| R9 | **Mover/marcar** | `skills/claude/` → `skills/vendor/addyosmani/` (ou pôr os cabeçalhos) | Proveniência não marcada (0/30 cabeçalhos); arrisca-se editar cópias que o sync apaga (`sync-skills-from-prod.sh` faz `rm -rf`) | Baixo | CLAUDE |
| R10 | **Arquivar/partir** | `docs/STATUS.md` → `docs/archive/`; secção Done do `initiatives/STATUS.md` (95 KB) → ficheiro próprio | O ficheiro corrente tem 95 KB, o que custa tokens em cada bootstrap (contra o objectivo central da visão) | Médio | AMBOS |
| R11 | **Decidir** | `.specify/` + `.github/skills/speckit-*` | Spec-kit para Copilot/PowerShell sem uso verificado; o repo trabalha com Claude Code | Baixo | DEV |
| R12 | **Corrigir** | `.env.example` | Faltam 17 variáveis lidas pelo código, entre elas `GEMINI_API_KEY`, `MCP_API_KEY`, `MCP_URL`, `MCP_SERVER_KEYS` e `PLAN_RUNNER_MCP_*` (grep `os.environ`/`process.env`). Declara `ANTHROPIC_API_KEY` e `GOOGLE_API_KEY`, que **nenhum código lê** | Médio — um setup novo falha sem saber porquê | CLAUDE |
| R13 | **Criar** | `docs/archive/` + regra "um só índice" | Há 2 `item-13-ai-findability.md` diferentes (`docs/` 6.3 KB vs `docs/knowledge/` 1.4 KB), 2 `STATUS.md` e vários `README.md` de índice | Baixo | CLAUDE |

---

## 1.4 Verificação do build de produção `[ACRESCENTADO PELO AUDITOR]`

Não estava pedido, mas decide se o motor TS é deployável, e isso muda a prioridade de R4, R5 e R8.

| Passo | Comando | Resultado |
|---|---|---|
| Instalar | `corepack pnpm install --frozen-lockfile --ignore-scripts` | OK |
| Prisma client | `npx prisma generate` (em `packages/memory`) | OK |
| Type-check CI | `pnpm run ci:typecheck` (`tsc -p tsconfig.typecheck.json --noEmit`) | **OK, exit 0** |
| Build pacote folha | `cd packages/shared && npx tsc` | **FALHA** — `TS6059: File '…/apps/api/src/index.ts' is not under 'rootDir' '…/src'` |
| Build API | `cd apps/api && npx tsc` | **FALHA** — mesmo erro |

**Causa:** nenhum pacote tem `tsconfig.json` próprio (`ls packages/*/tsconfig.json` sem resultados). O `tsc` sobe até ao `tsconfig.json` da raiz, que tem `rootDir: ./src` (`tsconfig.json:8`), uma pasta que não existe na raiz, e inclui por omissão o repo inteiro. O próprio `tsconfig.typecheck.json` (campo `"//"`) admite isto: "só o script `tsc` no package.json, que falha sozinho sem config local".

**Consequência:** `package.json:8` (`build`), `:9` (`start: node apps/api/dist/index.js`), `Dockerfile:9,22` e `setup.sh` (passo "Compilando projeto") nunca produzem um artefacto. O CI está verde porque só faz type-check e testes a partir de `src/`, via aliases (`vitest.config.ts:9-22`).

**Efeito colateral a registar:** o `tsc` falhado **emite** `.js`, `.d.ts` e `.map` ao lado das fontes (506 ficheiros gerados nesta verificação). Foram removidos logo a seguir com `git clean`, depois de confirmar num dry-run que eram exactamente os 506 artefactos do `tsc` e nada mais. Quem correr `pnpm build` localmente suja a árvore da mesma forma.

---

## 1.5 Outros achados estruturais `[ACRESCENTADO PELO AUDITOR]`

| ID | Achado | Evidência | Nota |
|---|---|---|---|
| E1 | O CI Python **nunca corre os testes lentos** | `runner/pytest.ini:4` `addopts = -m "not slow"`; `runner-tests.yml:48` e `release.yml:34` correm `pytest tests/` sem `-m slow` | 34 testes (planos reais, LangGraph, crash recovery) nunca correm em CI nem no gate de release. É o caminho end-to-end do motor |
| E2 | Comentários de CI desactualizados | `ci.yml:56` diz `pnpm@8.0.0` (é `8.15.9`, `package.json`); `ci.yml:92` diz "passam 50/50" (hoje há 189+ testes, `STATUS.md:72`) | DOC-ERRADO, baixo |
| E3 | Path alias para ficheiro inexistente | `tsconfig.typecheck.json:25` mapeia `@network-agents/scripts` para `packages/scripts/src/index.ts`, que não existe | Inócuo hoje (ninguém importa `@network-agents/scripts`) |
| E4 | Schema da tabela RAG definido em dois sítios | `packages/memory/prisma/schema.prisma:138-171` (`knowledge_sources`, `knowledge_chunks_t6`) **e** `scripts/create_t6_chunks_table.sql:5-23` | Fonte de verdade ambígua; o B11 (`STATUS.md:105`) diz que `knowledge_sources` foi criada à mão no Supabase |
| E5 | `system_inventory` modelado no Prisma deste repo | `schema.prisma:173-181` | O `CLAUDE.md` descreve-o como inventário **do Supabase partilhado** entre repos. Qual repo é dono do schema? A decidir |
| E6 | O diagrama do README não mostra `mcp/`, `scripts/`, `pilots/`, `.specify/` nem `apps/web` | `README.md:86-105` | DOC-ERRADO, baixo |
| E7 | Nomes de variáveis Supabase não normalizados | O código não lê nenhuma `SUPABASE_*` (acede por `DATABASE_URL`); o `CREDENTIALS-INVENTORY.md` regista `SUPABASE_SERVICE_KEY` vs `SUPABASE_SERVICE_ROLE_KEY` | Quem escrever um teste novo (ex.: mem0 com `SUPABASE_DB_CONNECTION_STRING`) está a inventar um nome que o repo não usa; o canónico aqui é `DATABASE_URL` |

---

## Limites desta fase

- **Clone do GitHub, não a cópia local.** O HEAD confere (`3dc3b25`), mas o que exista só na máquina Windows (ex.: `.env`, ficheiros não commitados) não foi visto.
- **Docker não disponível no sandbox:** o `Dockerfile` e o `docker-compose.yml` foram avaliados por leitura. A falha do `pnpm build` foi verificada directamente (é o passo `Dockerfile:9`).
- **Ambiente:** Node 22 aqui, Node 20 no CI (`ci.yml`, `setup-node` `node-version: 20`). Não deve afectar as conclusões de estrutura.
