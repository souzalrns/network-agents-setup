# Arquitectura — o que está onde

> Índice da pasta `docs/architecture/` (H-01, 2026-10-25). Regra: **um documento por papel**. O estado
> dos pendentes vive só no [`PENDENCIAS.md`](../initiatives/PENDENCIAS.md); o passado, no
> [`PENDENCIAS-HISTORICO.md`](../initiatives/PENDENCIAS-HISTORICO.md). Um documento ou pasta nova aqui
> tem de entrar neste índice: o `runner/tests/test_fonte_unica.py` falha se faltar.

## Vivos (por papel)

| Papel | Documento |
|---|---|
| O plano (o que fazer e porquê) | [`EXECUTION-PLAN.md`](./EXECUTION-PLAN.md) · fontes em [`execution-plan-sources/`](./execution-plan-sources/) |
| Visão do sistema | [`ECOSYSTEM.md`](./ECOSYSTEM.md) |
| Onde está cada fonte de verdade | [`BOOTSTRAP.md`](./BOOTSTRAP.md) |
| Governança | [`GOVERNANCE.md`](./GOVERNANCE.md) · [`governance/`](./governance/) (roadmap) |
| Decisões de arquitectura | [`adr/`](./adr/) |
| Contrato de planos (planwright ↔ plan_runner) | [`PLAN-CONTRACT.md`](./PLAN-CONTRACT.md) · cenário provado em [`CANONICAL-SCENARIO.md`](./CANONICAL-SCENARIO.md) · [`plan-execute/`](./plan-execute/) (schema e exemplo) |
| Executor de tools do worker (AU-20) | [`AU-20-TOOL-EXECUTOR.md`](./AU-20-TOOL-EXECUTOR.md) |
| Meta-agentes, fase 2 (Execution Broker) | [`META-AGENTS-PHASE-2.md`](./META-AGENTS-PHASE-2.md) |
| Motor de orquestração (LangGraph) | [`langgraph-lab/`](./langgraph-lab/) |
| HITL (contrato Python ↔ TypeScript) | [`hitl/`](./hitl/) |
| Memória | [`memory/`](./memory/) (arquitectura e fases) · [`memory-integration.md`](./memory-integration.md) |
| Segurança | [`SECURITY.md`](./SECURITY.md) (frameworks) · [`SECURITY-AGENTS.md`](./SECURITY-AGENTS.md) (pipeline defensivo) · [`agent-security/`](./agent-security/) (boas práticas) · [`code-verification/`](./code-verification/) |
| Limites de quota (Gemini) | [`RATE-LIMITS.md`](./RATE-LIMITS.md) |
| Agentes de várias plataformas | [`multi-platform/`](./multi-platform/) · [`plug-in-agents.md`](./plug-in-agents.md) |
| Ferramentas | [`uv/`](./uv/) (gestor de pacotes Python) · [`spec-kit/`](./spec-kit/) (rascunho de constituição) |

## Plataforma Node (TypeScript, arquivada pela D1)

O runtime é Python (D1, VIA A). Estes descrevem o `packages/` e o `apps/` arquivados:
[`node-platform.md`](./node-platform.md) · [`CORE-MAPPING.md`](./CORE-MAPPING.md) · [`TEST-COVERAGE.md`](./TEST-COVERAGE.md).

## Mapeamentos e inventários datados (fotografias, não estado)

[`MCP-MAPPING.md`](./MCP-MAPPING.md) (2026-09) · [`REPOSITORY-MAP.md`](./REPOSITORY-MAP.md) (2026-09-20) ·
[`CREDENTIALS-INVENTORY.md`](./CREDENTIALS-INVENTORY.md) (2026-09-20; só nomes, nunca valores).
Os números de hoje vêm de [`docs/generated/INVENTORY.md`](../generated/INVENTORY.md).

## Auditorias (evidência de itens; saem para o §13 do histórico quando os itens fecham, §9 passo 8)

| Tema | Pasta / documento |
|---|---|
| Agentes | [`agents-audit/`](./agents-audit/) (fases 1–5 e frameworks em `deep/`) |
| Ingestão e conhecimento | [`ingestion-audit/`](./ingestion-audit/) (sigla `AI:`) |
| Orquestração | [`orchestration-audit/`](./orchestration-audit/) |
| Memória | [`memory-audit/`](./memory-audit/) |
| Avaliação | [`evaluation-audit/`](./evaluation-audit/) |
| Observabilidade | [`observability-audit/`](./observability-audit/) |
| Tools e MCP | [`tools-mcp-audit/`](./tools-mcp-audit/) |
| Segurança | [`SECURITY-AUDIT.md`](./SECURITY-AUDIT.md) (2026-09-17) · [`SECURITY-AUDIT-FULL.md`](./SECURITY-AUDIT-FULL.md) (2026-09-18) · [`security-audit-2026/`](./security-audit-2026/) (2026-09-19) |
| Âmbito e funcionamento real | [`meta-validation/`](./meta-validation/) |

## Padrões estudados (referência; nada aqui é estado)

[`patterns-from-addy-agent-skills/`](./patterns-from-addy-agent-skills/) ·
[`patterns-from-codebase-memory/`](./patterns-from-codebase-memory/) ·
[`patterns-from-ecc/`](./patterns-from-ecc/) ·
[`patterns-from-harness/`](./patterns-from-harness/) ·
[`patterns-from-hermes/`](./patterns-from-hermes/) ·
[`patterns-from-marketing-p1/`](./patterns-from-marketing-p1/) ·
[`patterns-from-mcp/`](./patterns-from-mcp/) ·
[`patterns-from-orchestrators/`](./patterns-from-orchestrators/) ·
[`patterns-from-rag/`](./patterns-from-rag/) ·
[`patterns-from-ux-ui/`](./patterns-from-ux-ui/)
