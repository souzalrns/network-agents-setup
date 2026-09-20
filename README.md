# Network Agents Setup

**Núcleo do sistema** — motor de execução + governança + capacidades horizontais + RAG. Os verticais (agentes específicos de negócio/domínio) ligam-se como plug-in a partir do `agent-network-mcp`.

> **Mudança de escopo (2026-09-17):** este repo deixou de ser só o laboratório de método para se tornar o núcleo do produto. Ver [`docs/architecture/ECOSYSTEM.md`](./docs/architecture/ECOSYSTEM.md) para a visão completa e o antes/depois.

> **Motor de execucao:** [`runner/`](./runner/README.md) — `plan_runner`, um motor de planos YAML com HITL, crash recovery e external workers.

---

## O que é este repo

Não é a produção a servir clientes directamente — é onde se desenha, testa e depois liga (plug-in) os verticais. Contém 4 camadas, todas domain-agnostic:

| Camada | Onde vive | Tecnologia |
|---|---|---|
| **Motor** | [`runner/`](./runner/) | Python (`plan_runner`) |
| **Governança** | [`packages/core/`](./packages/core/) | TypeScript |
| **Horizontais** | [`skills/`](./skills/) + [`agents/`](./agents/) | Markdown |
| **RAG** | Supabase + Gemini (chamado a partir daqui) | pgvector + embeddings |

Os **verticais** (agentes por negócio/domínio) não vivem aqui — vêm do `agent-network-mcp` como plug-in. Ver [`docs/architecture/ECOSYSTEM.md`](./docs/architecture/ECOSYSTEM.md) secções 1–4 para o detalhe da relação setup ↔ MCP.

## Estado actual

**Feito:**
- RAG fechado (C8, 6/6): 110 chunks de 33 ficheiros ingeridos; pipeline completo markdown → chunk → embed (Gemini, 768 dims) → Supabase → retrieve via MCP.
- Governança mapeada por inteiro: 39 ficheiros em `packages/core/` — 5 REAL, 19 INCOMPLETO, 14 MOCK, 1 BARREL.
- Horizontais: 67 skills + 35 agentes já no setup, em 8 domínios (`marketing`, `design`, `meta`, `engenharia`, `gestao`, `atendimento`, `produto`, `_shared`).
- 3 documentos de mapeamento produzidos por leitura directa dos ficheiros: `CORE-MAPPING.md`, `MCP-MAPPING.md`, `ROADMAP-GOVERNANCE.md`.

**Falta:**
- Governança: Delegation Graph e Context Sync continuam por construir (Action Receipts já tem uma versão inicial — hash encadeado, ver `packages/mcp/src/tools/ActionReceipt.ts` — mas não o contrato completo do `ADR-001`, que exige identidade DID/AgentMesh e decisões de autorização Cedar/OPA ainda não adoptados).
- Adoptar AgentMesh (identidade/delegação) e Cedar (policy engine) — nenhum dos dois está integrado ainda no `agent-network-mcp` nem no `plan_runner`.

Detalhe completo e actualizado: [`docs/initiatives/STATUS.md`](./docs/initiatives/STATUS.md).

---

> **Nota de nomenclatura:** "Item 13" e o identificador histórico interno. O nome canónico e **AI Visibility** (SEO + GEO + AEO + LLMO). Ver [docs/item-13-ai-findability.md](./docs/item-13-ai-findability.md).

## Portfolio (começar aqui)

| Documento | Conteúdo |
|-----------|----------|
| **[docs/PORTFOLIO.md](./docs/PORTFOLIO.md)** | Narrativa completa: problema, solução, diagrama, diferenciais |
| **[docs/ONE-PAGER-MARKETING-AGENTS.md](./docs/ONE-PAGER-MARKETING-AGENTS.md)** | Resumo de 1 página (LinkedIn / proposta) |
| [docs/marketing-agency-agents.md](./docs/marketing-agency-agents.md) | System prompts + limites de todos os agentes |
| [docs/item-13-ai-findability.md](./docs/item-13-ai-findability.md) | **Item 13 — AI Findability** (playbook canónico P0/P1/P2) |
| [docs/knowledge/ai-findability.md](./docs/knowledge/ai-findability.md) | Item 13 knowledge operacional (50 chunks RAG) |
| [docs/knowledge/](./docs/knowledge/) | Knowledge packs por especialidade |
| [docs/CONCLUSAO-SETUP-MARKETING.md](./docs/CONCLUSAO-SETUP-MARKETING.md) | Fecho documental e próximos passos |

### Destaques do desenho

- **Horizontais** (SEO, AI Visibility, UI/UX, copy, mídia, UGC…) + **verticais** por cliente  
- **Orquestrador** que planeia e faz handoffs — não substitui o especialista  
- **Prompt ≠ knowledge** — checklists e anti-padrões por papel  
- **Item 13 — AI Findability** — estruturar projetos para IA encontrar e recomendar  
- Regras portáteis de harnesses (Ruflo / Hermes / Orca) sem lock-in de runtime  

```text
Objetivo → marketing-orquestrador → horizontais / verticais
                ↓
         [KNOWLEDGE] + [CLIENT]
```

---

## Outra documentação no repo

| Doc | Nota |
|-----|------|
| [docs/estrutura-geral-agentes.md](./docs/estrutura-geral-agentes.md) | Especificação ampla (providências / estrutura geral) |
| [docs/item-13-ai-findability.md](./docs/item-13-ai-findability.md) | Playbook operacional Item 13 (PASS/FAIL, bots, handoffs) |
| [docs/knowledge/ai-findability.md](./docs/knowledge/ai-findability.md) | Chunks RAG para agents responderem perguntas Item 13 |

---

## Plataforma (código / infra — monorepo)

> Alguns módulos podem conter stubs; ver [`docs/architecture/CORE-MAPPING.md`](./docs/architecture/CORE-MAPPING.md) para o mapeamento exacto de que está REAL, INCOMPLETO ou MOCK antes de usar em produção.

### Estrutura

```
network-agents-setup/
├── runner/            # motor (plan_runner, Python)
├── packages/          # governança + infra (TypeScript)
│   ├── core/
│   ├── memory/
│   ├── mcp/
│   ├── observability/
│   ├── websocket/
│   ├── langgraph/
│   └── shared/
├── skills/            # horizontais (marketing, claude, design, meta)
├── agents/            # horizontais (marketing, design, meta, engenharia, gestao, atendimento, produto)
├── docs/
│   └── architecture/  # ECOSYSTEM, CORE-MAPPING, MCP-MAPPING, governance/
├── apps/api/
├── config/
├── tests/
└── k8s/
```

### Requisitos

- Node.js 18+
- pnpm 8+
- PostgreSQL 16+
- Redis 7+
- Python 3.10+ (para o `runner/`)

### Instalação

```bash
pnpm install
cp .env.example .env
pnpm run build
pnpm run dev
```

### Licença

MIT

---

## Como usar (motor `plan_runner`)

Quickstart real (ver [`runner/README.md`](./runner/README.md) para a referência completa de CLI):

```bash
cd runner

# 1. Instalar (motor nativo, mínimo)
pip install -r requirements.txt

# 2. Instalar (com engine LangGraph — recomendado)
pip install -r requirements-langgraph.txt

# 3. Correr um plano de exemplo
python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml --mode stub --out ../pilots/demo
```

Depois de correr, ver `../pilots/demo/status.json` (estado final), `events.jsonl` (log completo) e `artifacts/` (o que foi gerado).

---

## Nota de maturidade

- **Documentação da agência multi-agente (portfolio):** pronta para partilha e testes com o padrão `[SYSTEM]+[KNOWLEDGE]+[CLIENT]+[TASK]`.
- **Código da plataforma neste repo:** inclui módulos MOCK/INCOMPLETO — ver [`CORE-MAPPING.md`](./docs/architecture/CORE-MAPPING.md) antes de assumir que algo está pronto para produção.
- **Verticais (agentes por negócio/domínio):** vivem no repo plug-in `agent-network-mcp` — ver [`MCP-MAPPING.md`](./docs/architecture/MCP-MAPPING.md).

## Referências

- [`docs/architecture/ECOSYSTEM.md`](./docs/architecture/ECOSYSTEM.md) — visão geral do ecossistema, a ler primeiro
- [`docs/architecture/CORE-MAPPING.md`](./docs/architecture/CORE-MAPPING.md) — os 39 ficheiros de `packages/core/`
- [`docs/architecture/MCP-MAPPING.md`](./docs/architecture/MCP-MAPPING.md) — os 33 agentes do `agent-network-mcp`
- [`docs/architecture/governance/ROADMAP-GOVERNANCE.md`](./docs/architecture/governance/ROADMAP-GOVERNANCE.md) — cronograma da camada de governança
- [`docs/initiatives/STATUS.md`](./docs/initiatives/STATUS.md) — pendências consolidadas, o que está feito e o que falta

---

*LRNSdigital*
