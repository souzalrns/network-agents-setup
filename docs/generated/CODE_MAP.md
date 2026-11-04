# CODE_MAP — gerado automaticamente

> **Não editar à mão.** Regenerar com:
> `pnpm --filter @network-agents/scripts docs:code-map`
>
> Gerado em: 2026-11-04
> Repo: network-agents @ 1.0.0

## Árvore de topo

```
AGENTS.md
CLAUDE.md
Dockerfile
LICENSE
README.md
SECURITY.md
agents/
apps/
config/
docker-compose.yml
docs/
k8s/
mcp/
memory/
oss/
package.json
packages/
pilots/
pnpm-lock.yaml
pnpm-workspace.yaml
runner/
scripts/
setup.sh
skills/
tests/
tsconfig.json
tsconfig.typecheck.json
vendor/
vitest.config.ts
```

## Packages e apps

| Package | Path | Scripts |
|---------|------|---------|
| `@network-agents/api` | `apps/api` | build, dev, start |
| `@network-agents/core` | `packages/core` | build, dev |
| `@network-agents/langgraph` | `packages/langgraph` | build, dev |
| `@network-agents/mcp` | `packages/mcp` | build, dev |
| `@network-agents/memory` | `packages/memory` | build, dev, postinstall, prisma:generate, prisma:migrate, prisma:studio |
| `@network-agents/observability` | `packages/observability` | build, dev |
| `@network-agents/scripts` | `packages/scripts` | ingest, ingest:br, ingest:pt, ingest:juris, ingest:doctrine, ingest:embeddings, validate:completeness, validate:agents, validate:consistency, docs:code-map, docs:agents, docs:skills, docs:all, monitor:quality, smoke-test, smoke-test:quick |
| `@network-agents/shared` | `packages/shared` | build, dev |
| `@network-agents/websocket` | `packages/websocket` | build, dev |

## Entrypoints detectados

### @network-agents/api

- `apps/api/src/index.ts`
- `apps/api/src/server.ts`

### @network-agents/core

- `packages/core/src/agents/AgentFactory.ts`
- `packages/core/src/index.ts`
- `packages/core/src/orchestrator/Orchestrator.ts`

### @network-agents/langgraph

- `packages/langgraph/src/index.ts`

### @network-agents/mcp

- `packages/mcp/src/index.ts`

### @network-agents/memory

- `packages/memory/src/index.ts`

### @network-agents/observability

- `packages/observability/src/index.ts`

### @network-agents/scripts

- `packages/scripts/src/ingest/index.ts`

### @network-agents/shared

- `packages/shared/src/index.ts`

### @network-agents/websocket

- `packages/websocket/src/index.ts`

## Scripts de documentação e validação

- `pnpm --filter @network-agents/scripts ingest`
- `pnpm --filter @network-agents/scripts ingest:br`
- `pnpm --filter @network-agents/scripts ingest:pt`
- `pnpm --filter @network-agents/scripts ingest:juris`
- `pnpm --filter @network-agents/scripts ingest:doctrine`
- `pnpm --filter @network-agents/scripts ingest:embeddings`
- `pnpm --filter @network-agents/scripts validate:completeness`
- `pnpm --filter @network-agents/scripts validate:agents`
- `pnpm --filter @network-agents/scripts validate:consistency`
- `pnpm --filter @network-agents/scripts docs:code-map`
- `pnpm --filter @network-agents/scripts docs:agents`
- `pnpm --filter @network-agents/scripts docs:skills`
- `pnpm --filter @network-agents/scripts docs:all`
- `pnpm --filter @network-agents/scripts monitor:quality`
- `pnpm --filter @network-agents/scripts smoke-test`
- `pnpm --filter @network-agents/scripts smoke-test:quick`

---
*Mapa gerado a partir do filesystem — não substitui docs/STATUS.md.*
