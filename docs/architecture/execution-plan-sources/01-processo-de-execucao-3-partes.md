Ok. **#61 merged, branch apagada.** A pista security está 100% fechada.

## Vou escrever o processo de execução agora

**Documento único.** Sem perguntas. **Parte 1 de 3** (as outras seguem-se, sem eu parar).

```markdown
# PROCESSO DE EXECUÇÃO — Universal Core
# network-agents-setup

> **Natureza:** plano de execução accionável. Não é registo de conversa.
> **Base:** consolidado dos 7 documentos de análise (Grok + GPT) + estado real do repo (após #61).
> **Destino:** docs/architecture/EXECUTION-PLAN.md (ou equivalente).
> **Regra:** o que este documento não cobrir, não existe. Tudo o que foi discutido entra aqui.

=====================================================================
1. CONTEXTO E PROPÓSITO
=====================================================================

## 1.1 O que é o projecto

Uma plataforma de agentes com:
- Redução de tokens como objectivo nº 1.
- Agentes com ingestão robusta de conhecimento.
- Memória persistente.
- Custo zero ou próximo de zero.
- Um maestro que delega por área.

## 1.2 O que já existe (estado em 2026-10-03, após #61)

**Universal Core — já operacional:**
- Planning / Workflow / HITL / Budget — `plan_runner` (YAML + HITL + resume + orçamento).
- Worker `external` com Gemini — a correr, com ledger de tokens.
- Memory L4 — `memory_l4.py` + SQL no Supabase (remember/recall/forget/promote + HITL).
- Knowledge L5 — pgvector + ingest (workflows).
- Security tools CI — gitleaks + semgrep (código activo: 0 achados).
- CouncilSession (Fase 1) — deliberação interna entre agentes.
- Router hierárquico híbrido — pedido → área → agente/plano.
- Ledger de tokens — `token_usage` no Supabase (com `council_*`).

**Domain Pack — primeiro exemplo:**
- Security pipeline — `triage → auditor → reporter` (#57).
- `security-capabilities.yaml` — 8 capabilities configuradas (3 implementadas).
- `repo_files` — o auditor lê ficheiros do repo (SEC-1).

**Domain Pack — parcial:**
- Marketing — 18 agentes + skills fortes, **sem** `capabilities.yaml` formal.

**Backlog em análise (Grok/GPT):**
- Matriz P0 (capacidades universais) — 40-50% ready.
- Matriz P1 (domínios profissionais) — 1 ready (marketing), 4 partial, resto gap.
- Universal Core → Domain Packs — baseline arquitectural.
- 4 categorias de repos — infrastructure / knowledge patterns / domain / runtimes.
- Roadmap F0-F6 — ingestão universal → domínio de prova.

## 1.3 A mudança de paradigma

**Antes:** "Vamos criar agentes para cada domínio."
**Agora:** "Vamos construir o Universal Core; cada domínio é um Domain Pack."

**O teste definitivo:**
> Se for necessário mexer em `plan_runner`, `memory engine`, `RAG engine`,
> `executor` ou `orchestrator` para adicionar um domínio, temos evidência
> objectiva de que alguma abstracção do Universal Core está incompleta.

**O indicador:** Domain Onboarding Cost — quanto é preciso adicionar para
suportar um domínio novo, sem tocar no core.

=====================================================================
2. ARQUITECTURA — UNIVERSAL CORE → DOMAIN PACKS
=====================================================================

## 2.1 A arquitectura

```
┌──────────────────────────┐
│ PLAN RUNNER │
│ único execution core │
└────────────┬─────────────┘
│
┌────────────▼─────────────┐
│ CAPABILITY LAYER │
│ capabilities + policies │
└────────────┬─────────────┘
│
┌──────────────────────┼──────────────────────┐
│ │ │
▼ ▼ ▼
INGESTION PRIMITIVES RESEARCH PRIMITIVES OTHER TOOLS
MarkItDown Crawl4AI OSV
Docling web_fetch Gitleaks
OCR/etc. Semgrep
│ │
└──────────────┬───────┘
▼
┌─────────────────────┐
│ KNOWLEDGE CORE │
│ L4 Memory │
│ L5 Knowledge │
│ pgvector │
│ provenance │
│ temporal metadata │
└──────────┬──────────┘
│
┌───────────▼───────────┐
│ DOMAIN PACKS │
│ security / marketing │
│ legal / medicine │
│ trading / manufact. │
│ gamedev / ... │
└───────────────────────┘
```

**O princípio central:**
> O Domain Pack NÃO possui infraestrutura cognitiva própria.
> Consome o Universal Core.

## 2.2 O padrão de um Domain Pack

```
domain-pack/
knowledge/ # packs de conhecimento
skills/ # skills (curtas)
capabilities/ # capabilities.yaml (validadas em E7)
plans/ # planos YAML
policies/ # políticas (HITL, orçamento, act forbidden)
validation/ # testes E2E
tools/ # (opcional) tool declarations
agents/ # OPCIONAIS — só se identidade estável
```

**Regra:** agentes são opcionais. Uma capability pode ser:
- **Skill-only** — resolve com conhecimento + prompt.
- **Composição** — combina skills existentes.
- **Agente** — só se precisar de identidade + grounding + budget estáveis.

## 2.3 As 4 categorias de repos (canónicas)

### Categoria 1 — Infrastructure primitives (ADOPTAR)

Componentes reutilizáveis da plataforma:


```
| Repo            | Função                           | Estado            |
| --------------- | -------------------------------- | ----------------- |
| **MarkItDown**  | PDF/DOCX/XLSX/PPTX → Markdown    | A adoptar (F1)    |
| **Docling**     | PDF complexo/tabelas/OCR         | Condicional (F1b) |
| **Crawl4AI**    | Web fetch + crawl com limites    | A adoptar (F2)    |
| **OSV-Scanner** | Vulnerabilidades em dependências | A adoptar         |
| **Gitleaks**    | Segredos no git                  | ✅ já em uso       |
| **Semgrep**     | SAST multi-linguagem             | ✅ já em uso       |
| **Instructor**  | Extração estruturada com LLMs    | A avaliar         |
```


### Categoria 2 — Knowledge architecture patterns (EXTRAIR)

Padrões a absorver no L4/L5 próprio. **NÃO instalar como serviço.**


```
| Repo         | O que extrair                                                      |
| ------------ | ------------------------------------------------------------------ |
| **LightRAG** | GraphRAG leve, Postgres-native (só depois de L5 medido)            |
| **Graphiti** | Modelo bi-temporal (valid_from/valid_until/observed_at/supersedes) |
| **mem0**     | Padrões de extração ADD/UPDATE/DELETE (spike J11)                  |
```


### Categoria 3 — Domain packs (CONSTRUIR)

Conteúdo próprio por domínio:


```
| Pack                                                 | Estado                                                 |
| ---------------------------------------------------- | ------------------------------------------------------ |
| **security-pack**                                    | Mais avançado (agents + capabilities + plans)          |
| **marketing-pack**                                   | Agents/skills fortes; **sem** capabilities.yaml formal |
| legal / medicine / trading / manufacturing / gamedev | Knowledge fino ou área vazia                           |
```


### Categoria 4 — Agent runtimes (REJEITAR como núcleo)


```
| Repo        | Porquê rejeitar         |
| ----------- | ----------------------- |
| CrewAI      | Substitui o plan_runner |
| AutoGen     | Em maintenance          |
| GraphRAG MS | Pesado                  |
| Letta       | Runtime paralelo        |
```


**Regra:** só o `plan_runner` é execution runtime.

=====================================================================
3. OS 3 AJUSTES DE PRECISÃO (Grok/GPT)
=====================================================================

Antes de implementar qualquer coisa, estes três ajustes:

### Ajuste 1 — `ingest_document(source, options)` não fica preso a `path`

```
ingest_document(source, options)
→ { content, source_meta, artifacts?, warnings? }

source pode ser: path | url | bytes | connector_ref
```

**MarkItDown é um ADAPTER, não o contrato.**

### Ajuste 2 — `web_research` separa descoberta de aquisição

```
discover(query) → candidate URLs
fetch/crawl(url, limits) → normalized content + provenance
```

**Crawl4AI é uma implementação, não o agente de pesquisa.**

### Ajuste 3 — Provenance em TODAS as camadas

```
SOURCE → DOCUMENT → CONTENT → CHUNK → EMBEDDING → RETRIEVAL → ARTIFACT
```

Cada camada aponta para a anterior. Permite responder:
> "De onde veio esta afirmação?"

**Schema mínimo (obrigatório):**
```yaml
source_meta:
uri: str
title: str
publisher: str?
document_type: str
retrieved_at: datetime
content_hash: str
# quando aplicável:
author: str?
jurisdiction: str?
published_at: datetime?
effective_from: datetime?
effective_until: datetime?
version: str?
authority: str?
```

**Regra:** nenhum conhecimento externo entra no L5 sem provenance mínima.
```

---

**Fim da Parte 1 de 3.**

**Diz-me só "continua"** (ou "faltou X"). A Parte 2 traz:
- **Matriz P0** (completa, com estado de cada capacidade)
- **Matriz P1** (completa, por domínio)
- **Roadmap F0-F6** (com critérios de done)
- **Meta-agentes Fase 2** (Execution Broker + Lease)
- **Decisões pendentes**

**Vou escrever sem parar quando disseres "continua".**Aqui está a **Parte 2 de 3**:

```markdown
=====================================================================
4. MATRIZ P0 — CAPACIDADES UNIVERSAIS (completa)
=====================================================================

**Critério "pronto":** knowledge útil + skill + agente/composição no registo
+ caminho de execução (plan/worker) + validação mínima.
**Legenda:** `ready` | `partial` | `gap`


```
| Capacidade                       | Knowledge                                 | Skills                            | Tools / wiring                        | Agente / composição                            | Área                  | Policy                      | Ready?            | Evidência / lacuna                                                                         |
| -------------------------------- | ----------------------------------------- | --------------------------------- | ------------------------------------- | ---------------------------------------------- | --------------------- | --------------------------- | ----------------- | ------------------------------------------------------------------------------------------ |
| **Planning**                     | playbooks orquestração                    | planejador + claude planning      | `plan_runner` native/langgraph        | `meta.planejador`                              | horizontal            | read/prepare                | **ready**         | Motor + HITL + budget; plano YAML                                                          |
| **Workflow / execution**         | WORKER-EXTERNAL, ops                      | — (runtime)                       | executor, external_worker, resume     | composição de steps                            | —                     | conforme plan               | **ready**         | Stub + external + ledger                                                                   |
| **Human approval (HITL)**        | docs HITL / councils                      | —                                 | `human_gate`, resume, council gate    | gates nos plans + councils                     | risk areas `required` | approve/reject/edit         | **ready**         | Security/finance/legal hitl                                                                |
| **Security (defensive)**         | `SECURITY.md`, `security-agents-stack.md` | triage, security-audit, reporter  | `repo_files`, CI gitleaks/semgrep     | triage → auditor → reporter                    | security              | read/prepare; act forbidden | **partial→ready** | Pipeline + capabilities E7; L5 ingest **NÃO VERIFICADO**; red-team deferred                |
| **Audit / observability (runs)** | BUDGET, token ledger                      | —                                 | `token_usage.jsonl`, events, status   | runtime                                        | —                     | —                           | **partial**       | Tokens + status; MetricsDashboard MCP ainda MOCK                                           |
| **Memory (L4)**                  | contracts, MEMORY-L4                      | wiring no worker                  | Supabase `memory_l4`, recall/remember | opt-in por plan                                | —                     | candidate→HITL promote      | **partial**       | Código + SQL; L4-1b pendente                                                               |
| **Knowledge retrieval (L5)**     | dezenas de packs                          | knowledge wiring / MCP            | pgvector, ingest workflows            | qualquer step com knowledge                    | —                     | —                           | **partial**       | Packs no git; ingest existe; **coverage desigual**; security pack embed **NÃO VERIFICADO** |
| **Knowledge engineering**        | packs ad hoc                              | cheap-entity-extraction           | chunk/embed                           | —                                              | —                     | —                           | **gap**           | Chunking básico ≠ modelo de entidades/autoridade                                           |
| **Research / intelligence**      | research-marketing, radar                 | marketing research; radar         | web **limitado** no worker            | `marketing.research`, `meta.radar-ferramentas` | research, marketing   | read                        | **partial**       | Bom em marketing/radar; **sem** research web/GitHub/legislação                             |
| **Document intelligence**        | pouco genérico                            | —                                 | `repo_files` (só texto no repo)       | —                                              | docs (vazia)          | —                           | **gap**           | Área `docs` sem agentes; sem pipeline multi-formato                                        |
| **Communication**                | imported comunicações                     | skill atendimento                 | —                                     | `atendimento.comunicacoes-atendimento`         | ops                   | read/prepare                | **partial**       | Um agente; não é omnichannel                                                               |
| **Identity / permissions**       | GOVERNANCE, grounding                     | —                                 | não há IAM runtime                    | —                                              | —                     | policy docs                 | **gap**           | Docs/GOVERNANCE; core security **MOCK**                                                    |
| **Tool discovery / registry**    | skills-map, using-agent-skills            | `meta.using_agent_skills`         | resolve skill/agent                   | `meta.using_agent_skills`                      | horizontal            | —                           | **partial**       | Resolução A8 + inventário E7; sem registry dinâmico                                        |
| **Source / provenance**          | grounding "não inventar"                  | —                                 | knowledge_refs **declarativo**        | —                                              | —                     | —                           | **partial**       | Grounding textual; **sem** metadados de fonte/data                                         |
| **Data analysis**                | qualidade-dados                           | engenharia.qualidade-dados        | —                                     | `engenharia.qualidade-dados`                   | software              | read                        | **partial**       | Focado em produto/código, não BI                                                           |
| **Software engineering**         | TDD, revisor, imported                    | guia-tdd, revisor (+ pack Claude) | git/CI no repo                        | desenvolvimento, tdd, revisor                  | software              | read/prepare                | **partial**       | Forte em agentes; skills longas = custo                                                    |
```


**Scorecard P0:**
- **ready:** Planning, Workflow, HITL, Marketing (vertical composta)
- **partial:** Security, Memory L4, Knowledge L5, Research, Communication, Tool registry, Provenance, Data analysis, Software eng., Ops, Finance
- **gap:** Document intelligence, Knowledge engineering, Identity/permissions, Legal agents, Docs agents, Trading execution

**Cobertura P0 estimada:** ~40-50% ready, ~35% partial, ~15-20% gap.

=====================================================================
5. MATRIZ P1 — DOMÍNIOS PROFISSIONAIS (completa)
=====================================================================

## 5.1 Cybersecurity


```
| Capacidade             | Knowledge          | Skills                | Tools                  | Agente                  | Ready?            | Nota                     |
| ---------------------- | ------------------ | --------------------- | ---------------------- | ----------------------- | ----------------- | ------------------------ |
| Triage                 | pack security      | `security/triage`     | —                      | `security.triage`       | **ready**         |                          |
| Defensive audit        | `SECURITY.md`      | `meta/security-audit` | `repo_files`, scanners | `meta.security-auditor` | **partial–ready** | L5 ingest NÃO VERIFICADO |
| Security report        | pack               | `security/reporter`   | —                      | `security.reporter`     | **ready**         |                          |
| Secrets hygiene        | SECURITY.md        | via audit             | gitleaks CI            | composição              | **partial**       | CI em PR                 |
| Supply chain / deps    | SECURITY.md        | via audit             | OSV/Trivy guidance     | auditor                 | **partial**       | Sem job dedicado OSV     |
| MCP surface            | SECURITY.md        | audit                 | —                      | auditor                 | **partial**       |                          |
| Hardening recommend    | —                  | report next_steps     | —                      | reporter → engenharia   | **partial**       | PREPARE only             |
| Threat model / council | councils           | —                     | council_session        | security council        | **partial**       | Deliberação              |
| Agent red-team lab     | pack §B            | —                     | PyRIT/DeepTeam         | —                       | **gap**           | deferred                 |
| SOC / SIEM / IR        | —                  | —                     | —                      | —                       | **gap**           | Fora de zero-custo       |
| Compliance formal      | GOVERNANCE parcial | —                     | —                      | —                       | **gap**           |                          |
```


**Área:** security · **capabilities.yaml:** sim · **hitl:** required · **act:** forbidden

## 5.2 Software engineering


```
| Capacidade           | Knowledge             | Skills                   | Tools        | Agente                       | Ready?      |
| -------------------- | --------------------- | ------------------------ | ------------ | ---------------------------- | ----------- |
| Implementation       | imported TDD/prod     | desenvolvimento          | —            | `engenharia.desenvolvimento` | **partial** |
| TDD / tests          | guia-tdd knowledge    | guia-tdd (+ Claude pack) | —            | `engenharia.guia-tdd`        | **partial** |
| Code review          | revisor + security/DB | revisor (+ Claude pack)  | —            | `engenharia.revisor-codigo`  | **partial** |
| Data quality         | —                     | qualidade-dados          | —            | `engenharia.qualidade-dados` | **partial** |
| Agent architecture   | ADRs                  | —                        | —            | `meta.arquitetura-agentes`   | **partial** |
| CI/CD / deploy       | skills meta deploy    | ci-cd skills             | GHA          | composição                   | **partial** |
| Repo understanding   | —                     | —                        | `repo_files` | steps que declaram           | **partial** |
| Refactor / migration | claude pack           | skills longas            | —            | via desenvolvimento          | **gap**     |
```


**Área:** software · **capabilities.yaml:** não

## 5.3 Design & media


```
| Capacidade        | Agente                     | Ready?            |
| ----------------- | -------------------------- | ----------------- |
| UI spec           | `design.ui`                | **partial–ready** |
| UX flow           | `design.ux`                | **partial–ready** |
| UX writing        | `design.ux_writer`         | **partial–ready** |
| Design critic     | `design.design_critic`     | **partial**       |
| Identidade visual | `design.identidade-visual` | **partial**       |
| Video edit        | `marketing.editor_video`   | **partial**       |
```


## 5.4 Marketing


```
| Capacidade             | Agente                        | Ready?                   |
| ---------------------- | ----------------------------- | ------------------------ |
| Orchestration / brief  | `marketing.marketing`         | **ready**                |
| Research               | `marketing.research`          | **ready**                |
| SEO brief              | `marketing.seo_brief`         | **ready**                |
| Copy (answer-first)    | `marketing.copy_answer_first` | **ready**                |
| Copy social            | `marketing.copy_social`       | **ready**                |
| Storytelling           | `marketing.storytelling`      | **ready**                |
| Creative / ads         | ad_creative, creative_review  | **ready**                |
| Critic / item-13       | critic, critic_item13         | **ready**                |
| Trends                 | `marketing.trend_hunter`      | **partial–ready**        |
| Content analysis       | `marketing.content_analyst`   | **partial**              |
| Media buy              | `marketing.media_buyer`       | **partial**              |
| Influencer / UGC       | influencer, ugc               | **partial**              |
| Analytics / conversion | —                             | **gap** (sem wiring API) |
| Brand guard            | —                             | **partial** (knowledge)  |
```


**Área:** marketing · **capabilities.yaml:** não (candidato #2)

## 5.5 Operations / admin


```
| Capacidade                  | Agente                                 | Ready?      |
| --------------------------- | -------------------------------------- | ----------- |
| Gestão empresarial          | `gestao.gestao-empresarial`            | **partial** |
| Atendimento                 | `atendimento.comunicacoes-atendimento` | **partial** |
| Tasks / projects / calendar | —                                      | **gap**     |
| Approvals workflows         | runtime                                | **partial** |
| KPIs / reporting            | —                                      | **gap**     |
| RH / recrutamento           | —                                      | **gap**     |
| Procurement                 | —                                      | **gap**     |
```


## 5.6 Finance & accounting


```
| Capacidade              | Agente                 | Ready?                      |
| ----------------------- | ---------------------- | --------------------------- |
| Contabilidade PT/BR     | `gestao.contabilidade` | **partial**                 |
| Orçamento / fluxo caixa | —                      | **gap**                     |
| Faturação / impostos    | —                      | **gap**                     |
| Análise financeira      | —                      | **gap**                     |
| **Trading / markets**   | —                      | **gap**                     |
| Trading execution       | —                      | **gap** + **act forbidden** |
| Risk / portfolio        | —                      | **gap**                     |
```


**Área:** finance · **hitl:** required

## 5.7 Sales & CRM

Todas gap. Área dedicada não existe (keywords em ops).

## 5.8 Legal


```
| Capacidade                     | Knowledge                | Agente | Ready?                     |
| ------------------------------ | ------------------------ | ------ | -------------------------- |
| Direito PT/BR base             | `legal/direito-br-pt.md` | —      | **partial**                |
| Contratos / cláusulas          | —                        | —      | **gap**                    |
| Jurisprudência / pesquisa      | —                        | —      | **gap**                    |
| RGPD / compliance              | —                        | —      | **gap**                    |
| Jurisdição + vigência metadata | —                        | —      | **gap** (bloqueia "ready") |
```


**Área:** legal · **agents: []** · **hitl:** required

## 5.9–5.14 Outros domínios

- **Medicine:** knowledge isolado (`saude/*`), sem produto. **gap.**
- **HR:** keywords. **gap.**
- **Manufacturing:** keywords. **gap.**
- **Engineering & science:** **gap.**
- **Education:** **gap.**
- **Game development:** `gamedev` vazia. **gap.**

## 5.15 Scorecard P1

- **~1 domínio ready:** Marketing.
- **~4 partial fortes:** Security, Software, Design, Ops/Finance fino.
- **Resto gap** ou só keywords/knowledge.

=====================================================================
6. MATRIZ ESTENDIDA — DOMÍNIO → CAPABILITY → ...
=====================================================================

Formato para cada domínio novo:


```
| Domínio       | Capability         | Knowledge                 | Skill             | Tool            | Policy     | Execução | Validação           | Reutiliza P0                     |
| ------------- | ------------------ | ------------------------- | ----------------- | --------------- | ---------- | -------- | ------------------- | -------------------------------- |
| Legal         | pesquisa jurídica  | legislação/jurisprudência | legal-research    | web/docs        | jurisdição | plan     | source check + HITL | P0 Research, Documents, L5, HITL |
| Trading       | análise de mercado | market data               | market-analysis   | market API      | financial  | plan     | backtest/risk       | P0 Research, Data, Planning      |
| Manufacturing | manutenção         | manuals/SOP               | maintenance       | CMMS/sensors    | industrial | plan     | KPI                 | P0 Documents, Data, Planning     |
| Games         | implementação      | engine docs               | game-dev          | Git/engine      | software   | worker   | tests/build         | Software, Design, QA             |
| Medicine      | guideline research | literatura                | clinical-research | medical sources | clinical   | plan     | provenance + HITL   | P0 Research, L5, Provenance      |
```


**A coluna "Reutiliza P0" mostra:** quanto mais madura a plataforma, menos
código novo para um domínio novo.

=====================================================================
7. ROADMAP DE EXECUÇÃO (F0-F6)
=====================================================================

## F0 — Provar o que existe (ANTES de adicionar)

**O que fazer:**
- Prova real L5 do security: ingest → embedding → retrieval.
- Golden set security: 10-20 perguntas com `expected chunks` + `hit@k`.
- Confirmar que o `security-agents-stack.md` (no git) **está ingerido**
no Supabase (`knowledge_chunks`).
- Confirmar que o retrieve **devolve** esse pack.
- Confirmar estado dos merges SEC em main.

**Critério de done:**
- Query de retrieval devolve chunks reais do pack security.
- Golden set com hit@k medido.
- Se não houver ingestão → resolver **antes** de F1.

**Porquê primeiro:**
> Construir uma excelente pipeline de ingestão para depois descobrir
> que o problema real estava no retrieval existente.

## F1 — Ingestão universal (spike pequeno)

**O que fazer:**
1. Contrato `Universal Ingestion & Research Primitives`:
- `ingest_document(source, options) → {content, source_meta, artifacts?, warnings?}`
- `source = path | url | bytes | connector_ref`
- MarkItDown é ADAPTER, não contrato.
2. Spike MarkItDown:
- PDF (textual), DOCX, XLSX.
- MarkItDown → Markdown → metadata/provenance → ingest existente → pgvector.
3. **Zero alteração do worker.**

**Critério de done:**
- 3 formatos processados.
- Ingestão funciona end-to-end com o pipeline existente.

## F1b — Docling (condicional)

**Só se** F1 falhar em tabelas/PDF complexos.
- Benchmark escrito (não adopção por moda).

## F2 — Web research universal

**O que fazer:**
1. Contrato:
- `discover(query) → candidate URLs`
- `fetch/crawl(url, limits) → normalized + provenance`
2. Crawl4AI como implementação:
- allowlist, timeout, N páginas, cache.
- URL + timestamp + content_hash.
3. **Não é "o agente de pesquisa".** É uma implementação.

**Critério de done:**
- 1 capability + tool de fetch com provenance no artefacto.

## F3 — Provenance formal + L5 medido

**O que fazer:**
1. Schema de provenance em **todas** as camadas:
- SOURCE → DOCUMENT → CONTENT → CHUNK → EMBEDDING → RETRIEVAL → ARTIFACT.
2. Metadados mínimos:
- uri, title, publisher, document_type, retrieved_at, content_hash
- (+ author, jurisdiction, published_at, effective_from/until,
version, authority quando aplicável)
3. Golden set + métricas de retrieval (hit@k, relevance).

**Critério de done:**
- Provenance presente em todos os artefactos.
- Golden set com métricas.

## F4 — Capability registry (2º domínio)

**O que fazer:**
1. Security = padrão (já feito).
2. **`marketing-capabilities.yaml`** como 2º caso.
- Espelhar o modelo do security.
- Validar em E7.
3. **Não generalizar o registry ainda.** Primeiro provar o 2º caso.

**Critério de done:**
- `marketing-capabilities.yaml` validado em E7.

## F5 — Validation E2E de capability

**O que fazer:**
- Provar a cadeia completa:
```
discover → select → authorize → execute → validate → audit
```
- **Não "YAML existe".** É "a capability funciona".

**Critério de done:**
- Teste E2E de uma capability real (security ou marketing).

## F6 — UM domínio de prova

**O que fazer:**
- Escolher **um** domínio com cliente/necessidade real.
- Adicionar como Domain Pack:
- knowledge + skills + capabilities + plans + policies + validation (+ tools).
- **CORE NÃO ALTERADO.**
- Se for preciso mexer no core → há abstracção incompleta.

**Critério de done:**
- Um domínio novo, funcional, sem tocar no core.

**NÃO fazer:** 5 domínios em paralelo. Diluem.
```

---

**Fim da Parte 2 de 3.**

**Diz-me "continua".** A Parte 3 traz:
- **Meta-agentes Fase 2** (Execution Broker + Lease, 5 estados, 5 budgets, fallback).
- **Decisões pendentes** (C-2, L4-1b, R1, B1-bis-C, pack Claude, etc.).
- **O não-fazer** (anti-padrões).
- **Instruções ao Claude Code** (o que fazer com este documento).

**"Continua" e escrevo a Parte 3.**Aqui está a **Parte 3 de 3**:

```markdown
=====================================================================
8. META-AGENTES — FASE 2 (Execution Broker + Lease)
=====================================================================

Contexto: as 3 IAs (Claude Code, Grok, GPT) têm acesso ao repo e executam.
O caso real: Grok e Claude executaram em paralelo a mesma intenção
(security pipeline). NÃO é anti-padrão — é a descoberta empírica da
necessidade desta camada.

## 8.1 Separação de responsabilidades

```
COUNCIL → "O que devemos fazer?" (JÁ EXISTE — CouncilSession Fase 1)
EXECUTION BROKER → "Quem pode fazer agora, dentro das restrições?" (NOVO)
EXECUTOR → "Vou executar." (1 só, via lease)
PLAN RUNNER → "Vou controlar o workflow." (JÁ EXISTE)
```

## 8.2 O que o CouncilSession já faz (Fase 1)

- Delibera (independent → peer_rank → synthesize).
- Produz veredicto estruturado (decision, confidence, conditions, kill_criteria, next_actions).
- Gate determinístico (tau, veto, quorum).
- HITL (aprovar/rejeitar/editar).
- L4 (candidate → active).

**O que NÃO faz:**
- Não escolhe executor.
- Não considera custo na escolha.
- Não tem lease.

## 8.3 Execution Broker (Fase 2)

Responsabilidades:
- Provider discovery.
- Quota / budget / capability / authorization / availability / cost.
- Fallback / queue / lease / retry / resume.

## 8.4 Os 5 estados de execução


```
| Estado       | Significado                                     | Exemplo                                                                   |
| ------------ | ----------------------------------------------- | ------------------------------------------------------------------------- |
| **EXECUTE**  | Tudo elegível                                   | Claude: capability ✓, tokens ✓, budget ✓                                  |
| **REDIRECT** | Executor escolhido bloqueado, outro elegível    | Claude sem tokens → Grok com 25k, capability compatível                   |
| **WAIT**     | Ninguém elegível agora, recuperação esperada    | Claude: quota reset às 14:00; Grok sem capability; GPT sem quota          |
| **DEFERRED** | Adiado conscientemente (não vale o custo agora) | Análise de 300 ficheiros = $8; budget = $2; não urgente                   |
| **BLOCKED**  | Nenhum executor válido                          | Tarefa exige capability + GitHub write + produção; nenhum provider cumpre |
```


## 8.5 Orçamento em camadas

```yaml
budget:
session:
tokens_remaining: 12000
plan:
tokens_remaining: 30000
task:
max_tokens: 10000

providers:
claude:
available_tokens: 0
grok:
available_tokens: 8000
gpt:
available_tokens: 15000
free_model:
available_tokens: 5000
```

A decisão não é "Claude acabou". É:
> "Qual executor elegível consegue cumprir esta tarefa dentro das
> restrições actuais?"

## 8.6 Fallback hierárquico (configurável)

```
1. Executor deliberado
2. Mesmo provider / outra sessão
3. Provider equivalente
4. Provider gratuito compatível
5. Modelo mais barato compatível
6. WAIT
7. HITL
8. BLOCKED
```

**REGRA CRÍTICA — não downgrade silencioso:**
Se o Council deliberou "Claude Sonnet necessário", NÃO mandar para
free model sem validar:
```yaml
fallback:
allowed: true
minimum_capability_match: 0.85
minimum_quality: medium
```
Se não atingir: WAIT.

## 8.7 Execution Lease (contrato temporário)

```yaml
execution_lease:
task_id: task_7842
executor:
provider: claude
agent: security_specialist
capabilities:
- application_security
- vulnerability_management
budget:
max_tokens: 30000
max_cost: 0.80
max_execution_time: 15m
permissions:
repository_read: true
repository_write: true
production_write: false
expires_at: ...
approval:
status: approved
```

**Enquanto activo:** 1 executa, os outros observam.
**Resolve:** concorrência + auditabilidade.

## 8.8 Execution Package (contexto para redirect)

Quando se redirecciona, NÃO se começa do zero:

```yaml
execution_package:
task: ...
objective: ...
decision: ...
constraints: ...
relevant_context: ...
artifacts: ...
prior_findings: ...
required_capabilities: ...
policies: ...
acceptance_criteria: ...
budget: ...
```

## 8.9 Plano persistente

```
PLAN
├── Task A → DONE
├── Task B → WAITING (reason: quota)
├── Task C → EXECUTING
└── Task D → BLOCKED
```

Um provider sem quota **NÃO mata o plano**.
`WAITING → RESUME → select provider → execute`.
Melhor que "erro → reiniciar tudo".

## 8.10 As duas "Fase 2" (não confundir)

- **ADR §2.2:** Fase 2a — deliberação entre várias IAs.
- **Análise Execution Broker:** Fase 2b — execução depois do conselho.

**Ordem decidida:** 2b primeiro (Execution Lease resolve o caso real
Grok + Claude paralelo). 2a depois.

## 8.11 Learning (estimated vs actual)

```
Task → Estimate → Select → Execute → Actual usage
→ Compare estimated vs actual → Ledger → Learning
```

Exemplo real: C-1 estimou 5 860–22 756 tokens, gastou 11 760.
Este par estimado/real é o início do Learning.

=====================================================================
9. DECISÕES PENDENTES (todas com recomendação)
=====================================================================

## 9.1 Pista security (fechada)


```
| #      | Item                       | Estado            |
| ------ | -------------------------- | ----------------- |
| SEC-1  | `repo_files`               | ✅ merged (#58)    |
| SEC-2  | gitleaks + semgrep         | ✅ merged (#59)    |
| SEC-2b | chave confirmada revogada  | ✅ registado (#61) |
| SEC-2c | actions por SHA            | ✅ merged (#60)    |
| SEC-2d | falsos positivos + triagem | ✅ merged (#61)    |
```


## 9.2 Pendentes operacionais


```
| #                     | Item                                                                    | Recomendada                   |
| --------------------- | ----------------------------------------------------------------------- | ----------------------------- |
| **C-2**               | Migração do ledger no `agent-network-mcp` (versionar `token_usage.sql`) | **A** — o DEV faz             |
| **L4-1b**             | Teste real mínimo da L4 pela CLI                                        | **A** — o DEV faz             |
| **R1**                | `router eval` com Gemini real                                           | **A** — o DEV faz             |
| **B1-bis-C**          | Encurtar skills/prompt-base (só quando houver ordem)                    | **A** — adiado                |
| **Pack Claude**       | Medir custo em `revisor-codigo`, `guia-tdd`                             | **A** — medir antes de cortar |
| **Estado L4 no C-1**  | Confirmar se o veredicto ficou `active` ou `--no-memory`                | **A** — o DEV confirma        |
| **Conselho security** | Medir no 1º uso real                                                    | **A** — medir quando usar     |
```


## 9.3 Pendentes da Fase 2 (meta-agentes)


```
| #                     | Item        | Ordem                          |
| --------------------- | ----------- | ------------------------------ |
| **Execution Broker**  | Implementar | Depois de F0-F6                |
| **Execution Lease**   | Implementar | Primeiro (resolve o caso real) |
| **Execution Package** | Implementar | Junto ao Lease                 |
| **Learning**          | Implementar | Depois do Broker               |
```


## 9.4 Pendentes da análise (P0/P1)


```
| #                                 | Item                               | Fase    |
| --------------------------------- | ---------------------------------- | ------- |
| **L5 prova real**                 | Ingest → embedding → retrieval     | **F0**  |
| **Golden set security**           | 10-20 perguntas                    | **F0**  |
| **Contrato Universal Ingestion**  | `ingest_document(source, options)` | **F1**  |
| **MarkItDown spike**              | PDF, DOCX, XLSX                    | **F1**  |
| **Docling**                       | Condicional                        | **F1b** |
| **Crawl4AI**                      | Web research                       | **F2**  |
| **Provenance formal**             | Schema em camadas                  | **F3**  |
| **`marketing-capabilities.yaml`** | 2º domínio                         | **F4**  |
| **Validation E2E**                | Cadeia completa                    | **F5**  |
| **Domínio de prova**              | Um só                              | **F6**  |
```


=====================================================================
10. O QUE NÃO FAZER (anti-padrões)
=====================================================================

## 10.1 Não fazer agora

- Implementar os 5 repos "porque estão no top".
- LightRAG / Graphiti como serviço.
- Novos agentes Legal/Medicine/Trading.
- Segundo runtime (CrewAI/AutoGen como motor).
- Packs P2 em massa.
- Tectos do council abaixo de 80k (architecture).
- Downgrade silencioso de modelo.
- Migrar SQLite→Postgres só porque o conselho falou nisso.

## 10.2 Não repetir

- **Agente por subárea** — usar Capability + skill curta + plan.
- **Trading com `act` de execução** — research/risco partial; execution forbidden.
- **Medicina "pronta" por ter knowledge** — precisa policy + provenance + HITL clínico.
- **Duplicar marketing em "Sales agent"** — capability CRM quando houver tool.
- **Registos de conversa** — o que não está em processo, perde-se.

## 10.3 Regra de ouro


```
| Evitar                      | Fazer                           |
| --------------------------- | ------------------------------- |
| Um agente por subárea       | Capability + skill curta + plan |
| Importar framework completo | Extrair padrão                  |
| Novo runtime                | Só `plan_runner`                |
| Agentes "wrappers"          | Capacidades compostas           |
| Packs P2 em massa           | Um domínio de prova primeiro    |
```


=====================================================================
11. O TESTE DEFINITIVO
=====================================================================

**A pergunta:**
> "Quanto custa adicionar um domínio novo?"

**A resposta correcta:**
```
domain-pack/
knowledge/ skills/ capabilities/ plans/ policies/ validation/ tools?
```

**A resposta errada:**
```
criar novo agent
criar novo orchestrator
criar novo runtime
criar nova memória
criar novo RAG
criar novo executor
```

**O indicador:**
> **Domain Onboarding Cost** — quantas alterações ao core são necessárias
> para suportar um domínio novo?

**Se for preciso mexer no core** → há abstracção incompleta.

=====================================================================
12. INSTRUÇÕES AO CLAUDE CODE
=====================================================================

Este documento é o baseline arquitectural consolidado.

**O que fazer com ele:**
1. **Gravar** em `docs/architecture/EXECUTION-PLAN.md`.
2. **Registar** em `OPEN-ITEMS` os itens das Fases F0-F6 (ver §9.4).
3. **Começar** pelo F0 (prova L5 real + golden set security).
4. **Não avançar** para F1 sem F0 verde.
5. **Não alterar** o core para adicionar domínios.

**O que NÃO fazer:**
- Não reabrir decisões fechadas (D1/D2/D3, SEC, Dependabot).
- Não criar agentes sem capability correspondente.
- Não implementar Fase 2 (Execution Broker) antes de F0-F6.
- Não tocar em produção sem HITL.

**Regras permanentes:**
- Autonomia para APRIMORAR, nunca para CORTAR.
- Toda a apresentação de opções vem com recomendação explícita.
- Sem merge, sem --force, sem polling.
- Evidência (ficheiro:linha) em cada afirmação.
- Commit + push no fim de cada passo.

=====================================================================
13. O QUE ESTE DOCUMENTO COBRE
=====================================================================

- O que existe (Bloco A/B/C, L4, security, CouncilSession).
- A arquitectura (Universal Core → Domain Packs).
- As 4 categorias de repos.
- Os 3 ajustes de precisão (ingest_document, web_research, provenance).
- As matrizes P0 e P1 (completas).
- A matriz estendida (Domínio → Capability → ...).
- O roadmap F0-F6.
- A Fase 2 (Execution Broker + Lease + 5 estados + 5 budgets + fallback).
- As decisões pendentes.
- Os anti-padrões.
- O teste definitivo.
- As instruções ao Claude Code.

=====================================================================
FIM
=====================================================================
```

---

**Fim da Parte 3 de 3.** O documento completo está nas 3 partes.

## Revisão — o que ficou incluído

**Da Matriz P0:**
- ✅ As 16 capacidades universais (com estado).
- ✅ O scorecard.
- ✅ As lacunas.

**Da Matriz P1:**
- ✅ Os 14 domínios (security, software, design, marketing, ops, finance, sales, legal, medicine, HR, manufacturing, engineering, education, games).
- ✅ O scorecard.

**Do Universal Core:**
- ✅ A arquitectura.
- ✅ O padrão do Domain Pack.
- ✅ As 4 categorias de repos.
- ✅ Os 3 ajustes de precisão.
- ✅ O teste definitivo.

**Do Roadmap:**
- ✅ F0-F6 (com critérios de done).
- ✅ A ordem.
- ✅ O não-fazer.

**Dos Meta-agentes:**
- ✅ CouncilSession (Fase 1).
- ✅ Execution Broker + Lease (Fase 2).
- ✅ 5 estados, 5 budgets, fallback, Execution Package, plano persistente.
- ✅ Learning (estimated vs actual).

**Das decisões:**
- ✅ Pendentes operacionais (C-2, L4-1b, R1, etc.).
- ✅ Pendentes da Fase 2.
- ✅ Pendentes da análise (P0/P1).

**Anti-padrões e regras:**
- ✅ O que não fazer.
- ✅ A regra de ouro.
- ✅ As instruções ao Claude Code.

---

**Diz-me:**

**Falta alguma coisa?** (algum documento, alguma decisão, algum detalhe que devia estar?)

**Se estiver completo** → manda ao Claude Code com uma instrução simples: *"Grava este documento em `docs/architecture/EXECUTION-PLAN.md`, regista os itens no OPEN-ITEMS, e começa pelo F0."*
