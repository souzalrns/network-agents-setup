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

## Plano de execução (2026-10-03)

| Documento | Conteúdo |
|---|---|
| [`EXECUTION-PLAN.md`](./EXECUTION-PLAN.md) | **Plano de execução aprovado pelo maestro (2026-10-03, D-EP1..9 = A).** Universal Core → Domain Packs, matrizes P0/P1/P2 corrigidas com evidência, roadmap F0–F6 (o F0 revalida o L5 existente), Fase 2 só como norte, governança do próprio plano. Diz o que deve acontecer e porquê; o estado vivo continua em `docs/initiatives/STATUS.md` / `OPEN-ITEMS.md` |
| [`execution-plan-sources/`](./execution-plan-sources/README.md) | Fontes do plano, arquivadas tal como foram escritas (análises do maestro e externas) |
| [`MASTER-PLAN.md`](./MASTER-PLAN.md) | **Histórico** (2026-09-18, anterior à D1). Substituído pelo EXECUTION-PLAN (D-EP7) |

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
| [`MASTER-PLAN.md`](./MASTER-PLAN.md) | Diagrama completo FEITO/ALTERAR/CRIAR + repos a acoplar vs. extrair. **Histórico desde 2026-10-03:** ver [`EXECUTION-PLAN.md`](./EXECUTION-PLAN.md) |
| [`memory/FASE1-MEMORIA.md`](./memory/FASE1-MEMORIA.md), [`FASE2`](./memory/FASE2-MEMORIA.md), [`FASE3`](./memory/FASE3-MEMORIA.md), [`FASE4-SINTESE`](./memory/FASE4-SINTESE.md) | Auditoria de memória/federação (dsh-long-memory, Graphiti, Cognee, LightRAG, Mem0, Hindsight, MELD, Stigmem, ai-memory-mcp, sandbox, observabilidade) |
| [`governance/audit/GOV-FASE1.md`](./governance/audit/GOV-FASE1.md) a [`GOV-FASE3.md`](./governance/audit/GOV-FASE3.md), [`AUDIT-GOVERNANCE.md`](./governance/audit/AUDIT-GOVERNANCE.md) | Auditoria de governança (ADR-001, AGT/AgentMesh, agentgateway, ContextForge, Cedar/OPA, SPIFFE/SPIRE) |
| [`agents-audit/FASE1-AGENTES.md`](./agents-audit/FASE1-AGENTES.md) + [`agents-audit/deep/*.md`](./agents-audit/deep/) | Auditoria de agentes (2026-09-18, Fase 1): estado real do runtime próprio (TS `orchestrator/` + Python `plan_runner/`) + Microsoft Agent Framework, Google ADK, OpenAI Agents SDK, LlamaIndex, DSPy, smolagents — complementa `patterns-from-orchestrators/`, já existente e não refeito |
| [`agents-audit/FASE2-AGENTES.md`](./agents-audit/FASE2-AGENTES.md) | Auditoria de agentes, Fase 2 (2026-09-18): Tool Use (achado interno — superfície MCP mais estreita que o runtime), Agent Communication (A2A/ACP — ACP morto, A2A na Agentic AI Foundation), ecossistema MCP (FastMCP, mcp-agent, MCP Registry oficial, spec 2026-07-28). Skills e Observability não refeitos — já cobertos por `patterns-from-hermes/` e `memory/FASE3-MEMORIA.md` |
| [`agents-audit/FASE3-AGENTES.md`](./agents-audit/FASE3-AGENTES.md) | Auditoria de agentes, Fase 3: Knowledge/Ingestion (Crawl4AI, MarkItDown, gitingest, yt-dlp/faster-whisper já existentes mas desligados do RAG) |
| [`agents-audit/FASE4-AGENTES.md`](./agents-audit/FASE4-AGENTES.md) | Auditoria de agentes, Fase 4: Evaluation (DeepEval, Ragas — pendência da auditoria de memória resolvida) + Testing (mocking determinístico, replay) |
| [`agents-audit/FASE5-AGENTES.md`](./agents-audit/FASE5-AGENTES.md) | Auditoria de agentes, Fase 5: Coding/Research Agents (OpenHands split app/SDK, SWE-agent, Aider, browser-use) + Agentes Especializados (`AgentConfig.profile` ainda não implementado) |
| [`agents-audit/AUDIT-AGENTS.md`](./agents-audit/AUDIT-AGENTS.md) | **Síntese final** da auditoria de agentes: matriz de ~45 projetos classificados, achado central (peças reais desligadas, repetido 5x), roadmap de integração |
| [`ingestion-audit/AUDIT-INGESTION.md`](./ingestion-audit/AUDIT-INGESTION.md) | **Reescrito em padrão ouro (2026-09-19).** Pipeline interno lido por completo (989 linhas); L5 já religado (S10) mas bloco `knowledge:` fora do Plan.schema.json; CVEs reais em Crawl4AI/Firecrawl/MarkItDown/Docling/gitingest/yt-dlp (SSRF, RCE, zip bomb) — gitingest revisto de ADOPT para ADAPT (órfão >13 meses, PAT leak aberto) |
| [`tools-mcp-audit/AUDIT-TOOLS-MCP.md`](./tools-mcp-audit/AUDIT-TOOLS-MCP.md) | **Reescrito em padrão ouro (2026-09-19).** Leitura completa de `packages/mcp/src/` (todos os ficheiros) — achados novos e críticos: `query_database` executa SQL arbitrário do agente (mesma classe de falha que descontinuou o servidor Postgres oficial da Anthropic), `http_request` sem proteção SSRF (3 CVEs reais citados), `filesystem.ts` com bug clássico de path traversal (a correção já existe no lado Python do mesmo repo) |
| [`orchestration-audit/AUDIT-ORCHESTRATION.md`](./orchestration-audit/AUDIT-ORCHESTRATION.md) | **Reescrito em padrão ouro (2026-09-19) — corrige um erro repetido em 4 documentos:** `Orchestrator.ts` (TS) **não é mock**, liga Router→Planner→Executor de facto (480 linhas, pipeline real de 14 passos), com entry point real em `apps/api/src/index.ts`. O erro veio de `CORE-MAPPING.md`, citado sem reverificação por `GOV-FASE1.md` e pela auditoria de Agentes. Ver secção 0 (errata completa) |
| [`security-audit-2026/AUDIT-SECURITY-2026.md`](./security-audit-2026/AUDIT-SECURITY-2026.md) | Extensão do B2 (`SECURITY-AUDIT-FULL.md`) — 3 achados novos e acionáveis: senha hardcoded em `k8s/secrets.yaml`, falta RLS em `knowledge_chunks_t6`, Python sem lockfile (LLM04 estruturalmente inverificável) |
| [`evaluation-audit/AUDIT-EVALUATION.md`](./evaluation-audit/AUDIT-EVALUATION.md) | Extensão da Fase 4 de Agentes: `model_tier` é só schema (zero implementação); LiteLLM Router+Budget Manager como resposta a LLM06 (Unbounded Consumption) |
| [`observability-audit/AUDIT-OBSERVABILITY.md`](./observability-audit/AUDIT-OBSERVABILITY.md) | Correção a `GOV-FASE1.md`: observability em TS não está "ausente" — existe (`packages/observability/Tracer.ts`), é hand-rolled, tem um bug real e memory leak; proposta de wiring OTel mínima |
| [`meta-validation/AUDIT-META-VALIDATION.md`](./meta-validation/AUDIT-META-VALIDATION.md) | Validação cruzada de 7 recomendações anteriores. **Item 3 (33 agentes) reverificado por clone directo de `agent-network-mcp`** (antes só citado) — contagem e 3 amostras confirmadas linha a linha. Achado transversal: nenhuma das 7 foi exagerada; o padrão real é peças prontas nunca ligadas/indexadas/regeneradas — **e um erro real encontrado à parte** (ver `orchestration-audit/AUDIT-ORCHESTRATION.md`) mostra que nem a documentação interna deste repo é imune a precisar da mesma verificação |
| [`AGENTS.md`](../../AGENTS.md) (raiz) | Regras de skill-orchestration: como o `plan_runner` resolve `steps[].action` para `skills/**/SKILL.md`+`agents/**/*.agent.md`, grounding obrigatório, credenciais, onde vivem as skills. **Indexado em 2026-09-20 (F5)** — gap conhecido desde `meta-validation/AUDIT-META-VALIDATION.md` secção 5 |
| [`docs/generated/AGENTS.md`](../generated/AGENTS.md) | Catálogo **auto-gerado** de `config/agents.config.ts` (regenerar com `pnpm --filter @network-agents/scripts docs:agents`, nunca editar à mão). **Indexado em 2026-09-20 (F5)** — mesmo gap; nota: à data desta indexação o ficheiro ainda dizia "Total: 22 agentes", desactualizado (real: 24) — ver F6 |
| [`CREDENTIALS-INVENTORY.md`](./CREDENTIALS-INVENTORY.md) | Inventário de todas as credenciais dos 6 repos locais: onde vivem, duplicação, inconsistências de nome. Produzido em 2026-09-20 (S22), durante a rotação de credenciais |
| [`REPOSITORY-MAP.md`](./REPOSITORY-MAP.md) | Mapa dos 6 clones git locais (3 repos GitHub reais): remote, branch, última actividade, cópias múltiplas e o achado de branches divergentes em `viannalegal-site`. Produzido em 2026-09-20 (S23) |
| Este ficheiro | Índice de bootstrap |

## Para a próxima sessão

Se estiveres a ler isto porque seguiste o bootstrap do `CLAUDE.md`: já estás no sítio certo. Lê `docs/initiatives/STATUS.md` a seguir para as pendências correntes.
