# Ecossistema — visão geral

Como as peças se encaixam depois da mudança de escopo. Antes deste documento, o entendimento implícito era: setup = laboratório de método, MCP = produção. Isso mudou.

**Correcção do escopo (registada aqui para não se perder):**

| | Antes | Agora |
|---|---|---|
| `network-agents-setup` | Lab (método + runner) | **Núcleo do produto** (motor + governança + horizontais + RAG) |
| `agent-network-mcp` | Produção (33 agentes) | **Plug-in** (traz os verticais) |
| Governança | Produção | Setup |
| Horizontais | — | Setup |
| Verticais | — | MCP |

## 1. O que é este repo (`network-agents-setup`)

É o **núcleo do sistema** — não a produção a servir clientes directamente, é o sítio onde se desenha, testa e depois liga (plug-in) os verticais.

Contém:
- **Motor** — `plan_runner` (Python): executa planos declarativos, com gates humanos e trilha de auditoria.
- **Governança** — `packages/core/` (TypeScript): política, confiança, propostas de arquitectura, compliance, segurança.
- **Horizontais** — `skills/` + `agents/` (markdown): capacidades reutilizáveis por qualquer vertical (marketing, SEO, revisão de código, TDD, etc.).
- **RAG** — pipeline próprio (Supabase + Gemini): já construído e a funcionar (ver secção 5).

## 2. O que é o `agent-network-mcp`

É o **plug-in de verticais** — não é o produto, é a fonte dos agentes específicos de cada negócio/domínio.

Tem 33 agentes ao todo, de que **13 são horizontais** (candidatos a migrar para o setup, ver `MCP-MAPPING.md`) e os restantes **20 são verticais genuínos** — proprietários, de conhecimento com ingestão, ou de triagem por design (ver `MCP-MAPPING.md` secções 3.1–3.6 para a repartição exacta).

*(Nota: o pedido original desta tarefa referia "12 horizontais / 21 verticais" — o `MCP-MAPPING.md`, corrigido numa tarefa anterior desta mesma sessão, tem 13/20. Usei os números corrigidos.)*

## 3. A relação setup ↔ MCP

- O setup é o **"sistema operativo"**: motor, governança e horizontais vivem aqui, domain-agnostic.
- O MCP é um **"plug-in"** de verticais: conhecimento e contexto específicos de cada negócio/domínio.
- Os **13 horizontais** identificados no MCP migram para o setup (limpos de qualquer termo privado — ver G4).
- Os **20 verticais** ficam no MCP, ou chegam ao setup como plug-in externo, nunca como código embutido no núcleo.

Isto está alinhado com a visão de 3 camadas já registada em `plug-in-agents.md` (Orquestração / Agentes plug-in / Horizontais) — com uma diferença a assinalar: essa visão descreve cada agente-cliente a viver **no seu próprio repo**; a realidade actual tem os 20 verticais todos centralizados num único repo (`agent-network-mcp`, `lib/agents.js`). É uma simplificação pragmática da visão mais distribuída, não uma contradição dela.

## 4. As camadas

| Camada | Onde vive | Tecnologia | Domain-agnostic? |
|---|---|---|---|
| Motor | `network-agents-setup/runner/` | Python | Sim |
| Governança | `network-agents-setup/packages/core/` | TypeScript | Sim |
| Horizontais | `network-agents-setup/skills/` + `agents/` | Markdown | Sim |
| RAG | Supabase + Gemini (chamado por `network-agents-setup`) | Postgres/pgvector + API Gemini | Sim (dados são o que varia) |
| Verticais | `agent-network-mcp` | JavaScript (`lib/agents.js`) | Não — específico por negócio |

## 5. O que já está feito

- **Motor**: `plan_runner` com modos dry-run, stub, external, e HITL (`hitl.py`, contrato v1).
- **RAG**: 110 chunks de 33 ficheiros ingeridos; pipeline completo markdown → chunk → embed (Gemini, 768 dims) → Supabase → retrieve via `McpKnowledge` (C8, fechado 6/6).
- **Governança**: mapeada por inteiro — 39 ficheiros em `packages/core/`, dos quais 5 REAL, 19 INCOMPLETO, 14 MOCK, 1 BARREL (ver `CORE-MAPPING.md`).
- **Horizontais**: 50 skills + 21 agentes já no setup (contagem directa, 2026-09-17).
- **Mapeamento**: 3 documentos produzidos por leitura directa dos ficheiros — `CORE-MAPPING.md`, `MCP-MAPPING.md`, `ROADMAP-GOVERNANCE.md`.

## 6. O que falta

- ~~**G2**: 16 skills novas em `skills/meta/`~~ — **feito**.
- **G3**: migrar os 5 knowledge packs verticais com ingestão (cardiologia, dermatologia, oftalmologia, direito-br-pt, imobiliario-digital) do MCP para o setup.
- **G4**: limpar termos privados dos 13 horizontais antes de os trazer para o setup.
- **S9**: integração do `hitl.py` em `engine.py`/`langgraph_engine.py`/`cli.py`.
- **Governança**: construir o que o AGT (Microsoft) não cobre — Delegation Graph, Action Receipts, Context Sync (ver `ROADMAP-GOVERNANCE.md`).
- **AGT**: integração do Agent Governance Toolkit no `agent-network-mcp` e no `plan_runner`.
- *(Fora desta lista, mas relevante para o quadro geral: `memory-integration.md` descreve LightRAG + Cognee como camada de memória opcional por cliente — é um documento de design, "não implementado". Não confundir com o RAG já construído e fechado na secção 5, que é outra coisa.)*

## 7. Referências

- [`CORE-MAPPING.md`](./CORE-MAPPING.md) — os 39 ficheiros de `packages/core/`
- [`MCP-MAPPING.md`](./MCP-MAPPING.md) — os 33 agentes do `agent-network-mcp`
- [`governance/ROADMAP-GOVERNANCE.md`](./governance/ROADMAP-GOVERNANCE.md) — cronograma da camada de governança
- [`plug-in-agents.md`](./plug-in-agents.md) — visão original das 3 camadas (orquestração / agentes plug-in / horizontais)
- [`memory-integration.md`](./memory-integration.md) — design (não implementado) de LightRAG + Cognee como memória semântica/episódica por cliente
