# CODE_MAP — gerado automaticamente

> **Não editar à mão.** Regenerar com:
> `pnpm --filter @network-agents/scripts docs:code-map`
>
> Gerado em: 2026-08-19
> Repo: network-agents

## Árvore de topo

```
apps/
config/
docker-compose.yml
Dockerfile
docs/
k8s/
package.json
packages/
pnpm-workspace.yaml
scripts/
setup.sh
tests/
tsconfig.json
```

## Packages e apps

| Package | Path | Scripts |
|---------|------|---------|
| `@network-agents/api` | `apps/api` | (ver package.json) |
| `@network-agents/core` | `packages/core` | — |
| `@network-agents/langgraph` | `packages/langgraph` | — |
| `@network-agents/mcp` | `packages/mcp` | — |
| `@network-agents/memory` | `packages/memory` | — |
| `@network-agents/observability` | `packages/observability` | — |
| `@network-agents/scripts` | `packages/scripts` | ingest*, validate*, docs*, smoke-test |
| `@network-agents/shared` | `packages/shared` | — |
| `@network-agents/websocket` | `packages/websocket` | — |

## Entrypoints relevantes

- `packages/core/src/index.ts`
- `packages/core/src/orchestrator/Orchestrator.ts`
- `packages/core/src/agents/AgentFactory.ts`
- `apps/api/src/index.ts`
- `apps/api/src/server.ts`
- `config/agents.config.ts`
- `packages/memory/prisma/schema.prisma`

## Scripts de documentação e validação

- `pnpm --filter @network-agents/scripts validate:consistency`
- `pnpm --filter @network-agents/scripts docs:code-map`
- `pnpm --filter @network-agents/scripts docs:agents`
- `pnpm --filter @network-agents/scripts docs:all`
- `pnpm --filter @network-agents/scripts smoke-test`

---
*Mapa gerado a partir do filesystem — não substitui docs/STATUS.md.*
