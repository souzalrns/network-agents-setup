# Matriz P0 — `network-agents-setup` (main actual)

**Critério “pronto”:** knowledge útil + skill (ou equivalente) + agente/composição no registo + caminho de execução (plan/worker) + validação mínima.  
**Legenda:** `ready` | `partial` | `gap`  
**Fonte:** `config/areas.yaml`, `config/security-capabilities.yaml`, `agents/`, `skills/`, `docs/knowledge/`, `runner/plan_runner/` (estado conhecido pós-#57+SEC).

---

## 1. Capacidades universais P0 (núcleo)

| Capacidade | Knowledge | Skills | Tools / wiring | Agente / composição | Área | Policy | **Ready?** | Evidência / lacuna |
|------------|-----------|--------|----------------|---------------------|------|--------|------------|-------------------|
| **Planning** | playbooks orquestração | planejador + skills claude planning | `plan_runner` nativo/langgraph | `meta.planejador` | horizontal | read/prepare | **ready** | Motor + HITL + budget; plano YAML |
| **Workflow / execution** | WORKER-EXTERNAL, ops | — (runtime) | executor, external_worker, resume | composição de steps | — | conforme plan | **ready** | Stub + external + ledger |
| **Human approval (HITL)** | docs HITL / councils | — | `human_gate`, resume, council gate | gates nos plans + councils | risk areas `required` | approve/reject/edit | **ready** | Security/finance/legal hitl |
| **Security (defensive)** | `SECURITY.md`, `security-agents-stack.md` | triage, security-audit, reporter | `repo_files`, CI gitleaks/semgrep (PRs) | triage → auditor → reporter | security | read/prepare; act forbidden | **partial→ready*** | Pipeline + capabilities E7; L5 ingest **NÃO VERIFICADO**; red-team deferred |
| **Audit / observability (runs)** | BUDGET, token ledger | — | `token_usage.jsonl`, events, status | runtime | — | — | **partial** | Tokens + status; MetricsDashboard MCP ainda MOCK/incompleto |
| **Memory (L4)** | contracts, MEMORY-L4 | wiring no worker | Supabase `memory_l4`, recall/remember | opt-in por plan | — | candidate→HITL promote | **partial** | Código + SQL; L4-1b / runs reais pendentes |
| **Knowledge retrieval (L5)** | dezenas de packs (forte marketing/design) | knowledge wiring / MCP knowledge | pgvector, ingest workflows | qualquer step com knowledge | — | — | **partial** | Packs no git; pipeline ingest existe; **coverage desigual**; security pack no git mas embed **NÃO VERIFICADO** |
| **Knowledge engineering** (entidades, vigência, jurisdição, conflitos) | packs ad hoc | cheap-entity-extraction (meta) | chunk/embed | — | — | — | **gap** | Chunking básico ≠ modelo de entidades/autoridade |
| **Research / intelligence** | research-marketing, radar opensource | marketing research; radar | web **limitado** no worker (sem tools genéricas) | `marketing.research`, `meta.radar-ferramentas` | research, marketing | read | **partial** | Bom em marketing/radar tech; **sem** research web/GitHub/legislação com provenance unificado |
| **Document intelligence** (PDF/Office/OCR multi) | pouco genérico | — | `repo_files` (texto no repo); sem Docling/Unstructured no runner | — | docs (área vazia) | — | **gap** | Área `docs` sem agentes; sem pipeline multi-formato de plataforma |
| **Communication** (email/atendimento) | imported comunicações | skill atendimento | — | `atendimento.comunicacoes-atendimento` | ops | read/prepare | **partial** | Um agente; não é canal omnichannel |
| **Identity / permissions** | GOVERNANCE, grounding | — | não há IAM runtime completo | — | — | policy docs | **gap** | Docs/GOVERNANCE; packages/core security **MOCK** |
| **Tool discovery / registry** | skills-map, using-agent-skills | `meta.using_agent_skills` | resolve skill/agent por action | `meta.using_agent_skills` | horizontal | — | **partial** | Resolução A8 + inventário E7; não há registry de tools MCP dinâmico no runner |
| **Source / provenance / verification** | grounding “não inventar” | — | knowledge_refs **declarativo** (AU-22 limitado); repo_files com paths | — | — | — | **partial** | Grounding textual; **sem** metadados de fonte/data/autoridade no chunk |
| **Data analysis** | qualidade-dados | engenharia.qualidade-dados | — | `engenharia.qualidade-dados` | software | read | **partial** | Focado em dados de produto/código, não BI genérico |
| **Software engineering** | TDD, revisor, imported | guia-tdd, revisor (+ pack Claude longo) | git/CI no repo; dispatch MCP noutro sítio | desenvolvimento, tdd, revisor, arquitectura | software | read/prepare | **partial** | Forte em agentes; skills longas = custo; não é “capability registry” formal como security |

\*Security está **operacional no runner** se merges SEC estão em main; “ready” pleno exige prova de L5 + CI verde em main.

---

## 2. Áreas P0 profissionais (cobertura vs matriz)

| Domínio P0/P1 leve | Área yaml | Agents | Capability yaml | Knowledge | **Ready?** |
|--------------------|-----------|--------|-----------------|-----------|------------|
| Marketing | marketing | 18 | **não** | forte | **ready** (composição por agents, não por capability file) |
| Software / coding | software | 10 | **não** | médio | **partial** |
| Security / cyber | security | 3 | **sim** | médio (docs); RAG ? | **partial–ready** |
| Research | research | 1 (radar) | **não** | fino | **partial** |
| Ops / administração | ops | 2 | **não** | fino | **partial** |
| Finance | finance | 1 (contabilidade) | **não** | fino | **partial** (trading = gap) |
| Legal | legal | **0** | **não** | `legal/direito-br-pt.md` | **gap** (hitl reserved) |
| Docs | docs | **0** | **não** | — | **gap** |
| Gamedev | gamedev | **0** | **não** | — | **gap** |
| Medicine / HR / Sales CRM… | — | — | — | saúde packs isolados | **fora / gap** |

---

## 3. Scorecard P0 (resumo)

| Estado | Capacidades |
|--------|-------------|
| **ready** | Planning, Workflow, HITL; Marketing como vertical composta |
| **partial** | Security, Memory L4, Knowledge L5, Research, Communication, Tool registry, Provenance, Data analysis, Software eng., Ops, Finance |
| **gap** | Document intelligence multi-formato, Knowledge engineering rico, Identity/permissions runtime, Legal agents, Docs agents, Trading execution |

**Estimativa grosseira de cobertura P0 universal:** ~**40–50% ready**, ~**35% partial**, ~**15–20% gap** — não “plataforma universal pronta”; **núcleo de orquestração pronto**, **cognição transversal e knowledge depth desiguais**.

---

## 4. O que a matriz implica (prioridade de ingestão / build)

**Não** abrir 20 agentes novos. Fechar partials do núcleo:

1. **L5:** ingest + prova retrieval de `SECURITY.md` + `security-agents-stack.md` (+ marketing já forte).  
2. **Capability registry genérico** (padrão security) só quando uma área tiver ≥2 capabilities estáveis — marketing pode ser o 2.º ficheiro.  
3. **Research:** uma capability + skill curta + tool de fetch com provenance (antes de Legal/Medicina).  
4. **Document intelligence:** capacidade de plataforma (tool), não `docs.agent` vazio.  
5. **Legal:** knowledge com jurisdição/data **antes** de agente.  
6. **Identity:** não priorizar até packages/core deixar de ser MOCK ou houver policy no runner.

---

## 5. Como ler esta matriz

- **Agente no `areas.yaml` ≠ capacidade pronta.**  
- **Só security tem `*-capabilities.yaml` validado no E7.**  
- **Knowledge no git ≠ knowledge no vector store** (sempre assinalar NÃO VERIFICADO se não houver query de retrieval).  
- **HITL/budget/router** são o que mais se aproxima do “nível 0 universal” já utilizável.

Se quiseres o passo seguinte em ficheiro no repo: `docs/architecture/UNIVERSAL-CAPABILITY-MAP-P0.md` com esta tabela versionada e dono por linha (ready/partial/gap).
