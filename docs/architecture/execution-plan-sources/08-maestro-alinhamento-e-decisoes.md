# Maestro — alinhamento e decisões

A mudança de enquadramento está **correcta**. O Top 5 deixa de ser “fechar gaps de área” e passa a ser **primitives do Universal Core**. Isso é coerente com Capability First (security), com as matrizes P0–P2 e com a regra de não importar outro runtime.

---

## O que fica fechado

| Ideia | Decisão |
|-------|---------|
| Gargalo actual | **Infra de ingestão + research + knowledge + tools**, não mais agentes |
| MarkItDown / Docling / Crawl4AI / OSV / Instructor | **Infrastructure primitives** (candidatos a plataforma) |
| LightRAG / Graphiti / mem0 | **Knowledge architecture patterns** — EXTRAIR conceitos; **não** instalar agora |
| Domain packs | knowledge + skills + capabilities + plans + policies + validation (+ tools); **agentes opcionais** |
| plan_runner | **Único** execution runtime |
| GraphRAG MS / Letta / CrewAI como núcleo | **REJEITAR** |
| Ordem LightRAG | Só **depois** de L5 medido + provenance |

---

## Quatro categorias (canónicas daqui em diante)

1. **Infrastructure primitives** — MarkItDown, Docling (se necessário), Crawl4AI, OSV-Scanner, Gitleaks, Semgrep, Instructor  
2. **Knowledge architecture patterns** — LightRAG, Graphiti, mem0 (padrões → L4/L5 próprios)  
3. **Domain packs** — security (já), marketing (próximo), legal/medicine/… quando houver cliente  
4. **Agent runtimes** — só o vosso; resto rejeitado como motor  

---

## Universal Core vs Domain Packs (mapa ao repo)

| Universal Core (já / partial) | Onde está |
|-------------------------------|-----------|
| Planning / Workflow / HITL / Budget | `plan_runner` |
| Memory L4 | `memory_l4` + contracts |
| Knowledge L5 | pgvector + ingest (prova incompleta) |
| Security tools CI | gitleaks/semgrep (PRs) |
| Capability registry | **só** `security-capabilities.yaml` |
| Provenance / metadata rico | **gap** (prioridade sobe) |
| Document ingestion / Web research | **gap** → Fase 1–2 |

| Domain pack | Estado |
|-------------|--------|
| security-pack | Mais avançado (agents + capabilities + plans) |
| marketing-pack | Agents/skills fortes; **sem** capabilities.yaml formal |
| legal / medicine / trading / manufacturing / gamedev | Knowledge fino ou área vazia |

---

## Provenance — subida de prioridade (fechada)

Schema mínimo a adoptar no contrato de chunk/source (não precisa de Graphiti):

```text
source: uri, title, publisher?, author?, jurisdiction?,
        document_type, published_at?, effective_from?, effective_until?,
        retrieved_at, version?, authority?, content_hash
```

Isto bloqueia Legal/Medicine “sérios” mais do que a falta de um `.agent.md`.

L4 já tem ideias próximas (`supersedes`, candidate, scopes) — **absorver** `valid_from` / `observed_at` no contrato L4 quando fizerem o próximo ADR de memória, **sem** novo produto.

---

## Fases (ordem obrigatória — afinada ao que já corre)

| Fase | Conteúdo | Done when |
|------|----------|-----------|
| **0** | Auditoria: L5 real, security merges, runner, skills órfãs | Query retrieval prova chunks; SEC PRs em main |
| **1** | **Ingestão universal** — spike MarkItDown → MD → ingest existente | 3 tipos de doc → knowledge path estável |
| **1b** | Docling **só se** MarkItDown falhar em tabelas/PDF críticos | Benchmark escrito, não adopção por moda |
| **2** | **Web research universal** — Crawl4AI (allowlist, timeout, N páginas, cache, URL+timestamp) | 1 capability/tool + evidência no artefacto |
| **3** | L5 + **metadata/provenance** + avaliação de retrieval | Métricas mínimas (hit rate em golden set pequeno) |
| **4** | Capability registry: security = padrão; **marketing = 2.º** | `marketing-capabilities.yaml` + E7 |
| **5** | Validation de capability (“funciona”, não “YAML existe”) | Testes tipo security pipeline e2e |
| **6** | Domain packs de prova **um de cada vez** com uso real | Não Legal+Trading+Medicina+Games em paralelo |

**Correcção à Fase 6 da tua lista:** cinco domínios de prova em simultâneo **diluem**. Escolher **um** vertical com cliente/necessidade real; os outros ficam packs vazios ou só knowledge.

---

## Multi-worker / budget (visão que descreveste)

Correcta como **norte**:

```text
TASK → CAPABILITY → eligible workers → budget/auth → dispatch → validate
```

**Hoje:** budget por área + Gemini external + HITL.  
**Não** abrir scheduler multi-IA na mesma sprint que MarkItDown. Registar como **Fase 2 meta** (já tinham deliberação multi-IA no ADR); primitives de ingestão primeiro.

---

## O que **não** fazer agora

- Implementar os 5 repos “porque estão no top”  
- LightRAG / Graphiti como serviço  
- Novos agentes Legal/Medicine/Trading  
- Segundo runtime  
- Packs P2 em massa  

---

## Próximo entregável concreto (uma linha)

**Contrato de primitive universal** + **spike MarkItDown**:

1. ADR ou doc curto: *Universal Ingestion & Research Primitives*  
   - interface: `ingest_document(path) → {markdown, source_meta}`  
   - interface: `web_research(url|query, limits) → {markdown, source_meta}`  
   - proibido: substituir plan_runner; obrigatório: provenance fields  
2. PR spike: MarkItDown no caminho de ingest (CLI ou script em `scripts/`), **sem** mudar o worker de steps  
3. Em paralelo Fase 0: prova L5 dos packs security já no git  

---

## Teste definitivo (o teu — adoptado)

Um domínio novo deve parecer:

```text
domain-pack/
  knowledge/  skills/  capabilities/  plans/  policies/  validation/  tools?
```

e **não** novo orchestrator / memória / RAG / executor.

**Resumo:** a pesquisa dos repos serve; a **arquitectura** é Universal Core (primitives + L4/L5 + provenance + capability registry) → Domain packs. Próximo passo operacional = **Fase 0 prova L5** + **Fase 1 MarkItDown** + **contrato de primitive**, não top-5 instalado de uma vez.
