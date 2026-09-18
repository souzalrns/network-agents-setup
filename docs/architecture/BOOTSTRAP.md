# Bootstrap — onde está cada fonte de verdade

Documento produzido para corrigir a causa raiz da "amnésia entre sessões": o bootstrap (`CLAUDE.md`) apontava para um ficheiro de estado desactualizado, e nada apontava para os documentos de arquitectura/governança/segurança produzidos em 2026-09-18.

## O achado: 3 sistemas de estado paralelos, sem se conhecerem

| Sistema | Última actualização | Estado |
|---|---|---|
| `docs/STATUS.md` + `docs/STATUS-PROJETOS.md` + `docs/STATUS-ECOSSISTEMA.md` (rollup de 9 repos) | 18/08/2026 | Histórico — não editar sem necessidade, mantém a arquitectura PCU original |
| Supabase `agent-network-memory` (`mpsuurqilnhsvbnjmrpm`), tabelas `system_inventory`/`pendencias_negocio` | **12-18/08/2026** — confirmado por query directa | **Mais desactualizado que o próprio ficheiro que o cita como "fonte canónica"** — não é uma fonte mais actual, é uma terceira cópia igualmente parada |
| `docs/initiatives/STATUS.md` | 2026-09-18 (hoje) | **Fonte corrente para este repo** |

Nenhum dos três sabia da existência dos outros dois antes desta correcção.

## Decisão tomada (Opção 1 — aditiva, não substitutiva)

Manter os 3 sistemas como estão (não fundir, não apagar — o rollup de 9 repos e a arquitectura PCU histórica ficam intactos). Corrigir só o **ponteiro**:

- `docs/STATUS.md` ganhou uma nota no topo a dizer que é histórico e a apontar para `docs/initiatives/STATUS.md`.
- `CLAUDE.md` (bootstrap) passou a listar `ECOSYSTEM.md` → `docs/initiatives/STATUS.md` → `GOVERNANCE.md` como os 3 primeiros ficheiros a ler, antes do rollup de 9 repos.
- Este ficheiro (`BOOTSTRAP.md`) é o índice que faltava.

## Os 11 documentos de arquitectura produzidos em 2026-09-18

| Documento | Conteúdo |
|---|---|
| [`ECOSYSTEM.md`](./ECOSYSTEM.md) | Visão geral — setup como núcleo, `agent-network-mcp` como plugin de verticais |
| [`CORE-MAPPING.md`](./CORE-MAPPING.md) | 39 ficheiros de `packages/core/`: 5 REAL, 19 INCOMPLETO, 14 MOCK, 1 BARREL |
| [`MCP-MAPPING.md`](./MCP-MAPPING.md) | 33 agentes do `agent-network-mcp`: 13 horizontais (migrados), 20 verticais (ficam lá) |
| [`GOVERNANCE.md`](./GOVERNANCE.md) | Camada de governança consolidada |
| [`governance/ROADMAP-GOVERNANCE.md`](./governance/ROADMAP-GOVERNANCE.md) | Cronograma — AGT, Delegation Graph, Action Receipts, Context Sync |
| [`adr/ADR-001-governance-runtime.md`](./adr/ADR-001-governance-runtime.md) | Contratos e pipeline de 10 passos da Governance Runtime |
| [`SECURITY.md`](./SECURITY.md) | Frameworks (OWASP LLM Top 10 2026, NIST AI RMF, MITRE ATLAS, MAESTRO) + 8 ferramentas |
| [`SECURITY-AUDIT.md`](./SECURITY-AUDIT.md) / [`SECURITY-AUDIT-FULL.md`](./SECURITY-AUDIT-FULL.md) | Auditorias reais correlaes contra este repo |
| [`RATE-LIMITS.md`](./RATE-LIMITS.md) | Causa raiz confirmada da falha do `ingest-knowledge` (quota Gemini) |
| [`MASTER-PLAN.md`](./MASTER-PLAN.md) | Diagrama completo FEITO/ALTERAR/CRIAR + repos a acoplar vs. extrair |
| [`memory/FASE1-MEMORIA.md`](./memory/FASE1-MEMORIA.md), [`FASE2`](./memory/FASE2-MEMORIA.md), [`FASE3`](./memory/FASE3-MEMORIA.md) | Auditoria de memória/federação (dsh-long-memory, Graphiti, Cognee, LightRAG, Mem0, Hindsight, MELD, Stigmem, ai-memory-mcp, sandbox, observabilidade) |
| Este ficheiro | Índice de bootstrap |

## Para a próxima sessão

Se estiveres a ler isto porque seguiste o bootstrap do `CLAUDE.md`: já estás no sítio certo. Lê `docs/initiatives/STATUS.md` a seguir para as pendências correntes.
