# Inventário — contagens geradas

> **Não editar à mão.** Regenerar com: `cd runner && python -m plan_runner.inventory`
> O CI e `runner/tests/test_inventory.py` falham se este ficheiro ou os números citados
> nos documentos divergirem dos ficheiros de config. Fonte: `runner/plan_runner/inventory.py`.

## Resumo

| O quê | Quantos | Fonte |
|---|---:|---|
| Agentes do runner (`plan_runner`) | 82 | `config/areas.yaml` (validado contra `agents/**/*.agent.md`) |
| Áreas do router | 11 | `config/areas.yaml` |
| Skills | 117 | `skills/**/SKILL.md` |
| Planos de exemplo | 19 | `docs/orchestration/**/*.plan.yaml` |
| Agentes do MCP de produção | 34 | `config/mcp-agents.yaml` (cópia dos ids de `agent-network-mcp/lib/agents.js`) |
| … também no runner | 13 | `runtime:` preenchido |
| … só no MCP | 21 | `runtime: null` |
| Agentes no escritório (runner + só MCP) | 103 | `config/office.yaml` |
| Departamentos / alas / lugares do escritório | 18 / 2 / 44 | `config/office.yaml` |
| Agentes da plataforma Node (`apps/api`) | 24 | `config/agents.config.ts` (catálogo em `docs/generated/AGENTS.md`) |

Testes: não se contam aqui (mudam a cada PR). `cd runner && python -m pytest --collect-only -q`.

## Agentes do runner por área

| Área | Agentes |
|---|---:|
| `software` | 10 |
| `marketing` | 60 |
| `legal` | 0 |
| `ops` | 2 |
| `research` | 1 |
| `finance` | 1 |
| `trading` | 3 |
| `gamedev` | 0 |
| `security` | 3 |
| `docs` | 0 |
| `horizontal` | 2 |

## Skills por domínio

| Domínio | Skills |
|---|---:|
| `claude` | 26 |
| `design` | 4 |
| `marketing` | 58 |
| `meta` | 24 |
| `security` | 2 |
| `trading` | 3 |
