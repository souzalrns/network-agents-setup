# Network Agents Setup

Arquitetura e documentação de **redes multi-agente** — com foco portfolio na **agência de marketing** (papéis, knowledge packs, AI Findability).

> **One-liner:** especialistas com limites claros + conhecimento operacional + playbook para marcas serem encontradas e recomendadas por IA.

---

## Portfolio (começar aqui)

| Documento | Conteúdo |
|-----------|----------|
| **[docs/PORTFOLIO.md](./docs/PORTFOLIO.md)** | Narrativa completa: problema, solução, diagrama, diferenciais |
| **[docs/ONE-PAGER-MARKETING-AGENTS.md](./docs/ONE-PAGER-MARKETING-AGENTS.md)** | Resumo de 1 página (LinkedIn / proposta) |
| [docs/marketing-agency-agents.md](./docs/marketing-agency-agents.md) | System prompts + limites de todos os agentes |
| [docs/item-13-ai-findability.md](./docs/item-13-ai-findability.md) | **Item 13 — AI Findability** (playbook canónico P0/P1/P2) |
| [docs/knowledge/](./docs/knowledge/) | Knowledge packs por especialidade |
| [docs/knowledge/item-13-ai-findability.md](./docs/knowledge/item-13-ai-findability.md) | Item 13 knowledge (RAG) |
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

**Estado:** documentação de sistema **completa**. Runtime de produção vive à parte (`agent-network-mcp`). Piloto live e wiring de skills = fase seguinte.

---

## Outra documentação no repo

| Doc | Nota |
|-----|------|
| [docs/estrutura-geral-agentes.md](./docs/estrutura-geral-agentes.md) | Especificação ampla (providências / estrutura geral) |
| [docs/item-13-ai-findability.md](./docs/item-13-ai-findability.md) | Playbook operacional Item 13 (PASS/FAIL, bots, handoffs) |

---

## Plataforma (código / infra — monorepo)

> Alguns módulos podem conter stubs; ver nota de maturidade abaixo antes de uso em produção.

### Estrutura

```
network-agents/
├── packages/
│   ├── core/           # Núcleo (Orquestrador, Executor, Planner)
│   ├── memory/         # Memória (PostgreSQL + Redis)
│   ├── mcp/            # MCP
│   ├── observability/
│   ├── websocket/
│   ├── langgraph/
│   └── shared/
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

### Instalação

```bash
pnpm install
cp .env.example .env
pnpm run build
pnpm run dev
```

### Docker / Kubernetes

```bash
docker-compose up -d
kubectl apply -f k8s/
```

### Endpoints principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/chat` | POST | Mensagem para a rede |
| `/chat/stream` | POST | Streaming |
| `/agents` | GET | Lista agentes |
| `/health` | GET | Health check |
| `/ws` | WebSocket | Tempo real |

### Testes

```bash
pnpm test
```

### Licença

MIT

---

## Nota de maturidade

- **Documentação da agência multi-agente (portfolio):** pronta para partilha e testes com o padrão `[SYSTEM]+[KNOWLEDGE]+[CLIENT]+[TASK]`.
- **Código da plataforma neste repo:** pode incluir implementações simplificadas/stub (ex.: MFA, scanners externos, partes de simulação). Tratar antes de produção.
- **Produção operacional de agentes:** repo separado `agent-network-mcp` (não sobrescrito por este setup paralelo).

---

*LRNSdigital*
