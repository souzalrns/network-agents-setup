# EXECUTION PLAN — Universal Core
# network-agents-setup (+ agent-network-mcp onde indicado)

> **Estado:** APROVADO pelo maestro em 2026-10-03 (D-EP1..D-EP9 = opção A, §9.5). Main de referência: `969d3ce` (pós-#61). Versão: consolidado v2 + refinamentos pré-gravação (§16.2).
> **Natureza:** plano de execução accionável. Não é registo de conversa.
> **Ficheiro:** `docs/architecture/EXECUTION-PLAN.md` (network-agents-setup). Fontes arquivadas em `docs/architecture/execution-plan-sources/` (§17).
> **Base:**
> - o "PROCESSO DE EXECUÇÃO" em 3 partes;
> - a revisão do Maestro (adendo §14);
> - a análise da outra IA (20 pontos, Parte 4 de governança);
> - as matrizes P0 e P1;
> - a análise "domínios de prova";
> - a análise "repos → primitives";
> - o "Maestro — alinhamento e decisões";
> - o "baseline" (3 ajustes);
> - a verificação contra o repo (main `969d3ce`, 2026-10-03).
>
> **Regra de completude:** o que este documento não cobrir, não existe. Tudo o que foi discutido entra aqui. (O original baseava-se nos "7 documentos de análise (Grok + GPT) + estado real do repo (após #61)"; ver §17.) **Mas este documento não é fonte de verdade do estado operacional** (ver §15.1).

**Convenções**
- `NAS:` = repo `network-agents-setup`; `ANM:` = repo `agent-network-mcp`. Evidência sempre em `ficheiro:linha`.
- **⚠ CORRIGIDO** = afirmação do rascunho original alterada pela verificação. O registo completo está em §16.
- **＋ NOVO** = acrescentado. Nada do original foi retirado: o que mudou foi corrigido e fica registado em §16.
- Estados (definição em §15.3): `verified` · `partial` · `unverified` · `gap` · `blocked` · `deferred`. Nas matrizes P0/P1 mantém-se a legenda de cobertura `ready | partial | gap`, mais a marca `UNVERIFIED` quando falta prova.

---

# PARTE 1 — CONTEXTO, ARQUITECTURA, AJUSTES

## 1. Contexto e propósito

### 1.1 O que é o projecto
Uma plataforma de agentes com:
- **redução de tokens como objectivo nº 1** (métrica operacional em §14.2);
- agentes com ingestão robusta de conhecimento;
- memória persistente;
- custo zero ou próximo de zero (restrições em §14.3);
- um maestro que delega por área.

### 1.2 O que já existe (estado em 2026-10-03, main `969d3ce`, depois do #61)

**Universal Core: operacional no runtime Python** (D1 VIA A; ver ⚠ sobre o TS no fim desta lista). **Operacional ≠ completo:** o runtime existe e executa; L4/L5/provenance estão partial, identity e knowledge engineering são gap (§4).

| Peça | Estado | Evidência |
|---|---|---|
| Planning / Workflow / HITL / Budget | `verified` | `NAS:runner/plan_runner/` (engine, executor, `hitl.py`, `paused_budget`); suite rápida 399 passed, 41 skipped |
| Worker `external` (Gemini) + ledger local | `verified` | `NAS:runner/plan_runner/external_worker.py`; `token_usage.jsonl` por run |
| Ledger `token_usage` no Supabase | `partial` ⚠ CORRIGIDO | A tabela existe (J6), mas o `CHECK` **recusa** `council_member/peer/chairman` (`ANM:memory/token_usage.sql:12`; `NAS:docs/ops/COUNCIL.md:42`). **C-2 por correr** |
| Memory L4 | `partial` | `NAS:scripts/create_memory_l4_table.sql` (`supersedes` :42, `expires_at` :47); `NAS:runner/plan_runner/memory_l4.py`. Pendente: L4-1b |
| Knowledge L5 | `partial` + `unverified` ⚠ CORRIGIDO | Ver o quadro "L5" a seguir |
| Security tools CI | `verified` | `NAS:.github/workflows/security-scan.yml`: gitleaks no histórico completo (PR + main); semgrep diff-aware nos PRs (ERROR/WARNING); relatório no main com 0 achados activos e 49 arquivados |
| CouncilSession (Fase 1) | `verified` (1 run real: C-1, 11 760 tokens) | `NAS:runner/plan_runner/council_session.py`; `NAS:docs/ops/COUNCIL.md` |
| Router hierárquico híbrido | `verified` | `NAS:runner/plan_runner/router.py`; `NAS:config/areas.yaml` |
| Validador E7 (áreas + conselhos + capabilities) | `verified` | `NAS:runner/plan_runner/areas.py`, `capabilities.py` |

**＋ NOVO — L5: o estado real (resolve a divergência "não verificado" vs "C8 fechado")**

| Facto | Evidência |
|---|---|
| O C8 foi dado como "fechado (6/6)", com 110 chunks de 33 ficheiros | `NAS:docs/initiatives/STATUS.md:17,236`; `NAS:README.md:27` |
| Esses 110 chunks foram para `knowledge_chunks_t6`, e o retrieve lia `knowledge_chunks`. **O RAG estava partido na junção** (AU-19) | `NAS:docs/audit/AUDIT-2-cadeia.md:16`; `NAS:docs/audit/AUDIT-6-lacunas.md:28` |
| O J3 (PR #31) tornou `knowledge_chunks` canónica. Migração corrida: 121 linhas do projecto, 322 no total, 1 só `match_knowledge` | `NAS:docs/ops/RAG-CANONICAL.md:1-3,35-42`; `NAS:runner/plan_runner/supabase_writer.py:30` |
| **Em aberto do J3:** passo 3 (confirmar que o ingest escreve na tabela certa), passo 5 (teste real no MCP), passo 6 (apagar a t6, irreversível) | `NAS:docs/initiatives/OPEN-ITEMS.md:111`; `NAS:docs/ops/RAG-CANONICAL.md:44-75` |
| O CI prova ingest → retrieve contra um Postgres descartável, com embedder falso (job `test-rag`) | `NAS:runner/tests/test_rag_canonical.py`; `NAS:docs/ops/RAG-CANONICAL.md:67` |
| **A lista de ingestão é fixa (38 ficheiros) e NÃO inclui o pack de security.** Ficam de fora ~31 ficheiros de `docs/knowledge/` (design/*, imported-from-production/*, marketing/*, `security-agents-stack.md`, `skills-map.md`, `imported-from-harnesses.md`) | `NAS:scripts/ingest_delta.py:32-71` |
| O retrieve devolve só `id, content, source, similarity` | `ANM:memory/schema.sql:45-58` |
| `metadata` vem sempre `None`, o `locator` vem sempre `None`, e os `filters` não têm efeito | `NAS:runner/plan_runner/mcp_knowledge.py:23-29` |
| O runner só consulta o L5 num passo com bloco `knowledge:` (S9, opt-in). **O plano demo de security não tem esse bloco** | `NAS:runner/plan_runner/knowledge_wiring.py:1-34`; `NAS:docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml` |
| Há **duas pipelines de ingestão**: T6 no runner (`ingest-knowledge.yml`, `.md`) e a do MCP (`ANM:.github/workflows/ingest.yml`, `ingestion/*.json`) | `NAS:docs/audit/AUDIT-6-lacunas.md:28` |

**Resumo L5:** o L5 existe e foi reparado (J3). Falta revalidá-lo no estado canónico actual (J3 passos 3 e 5), dar-lhe cobertura (lista de ingestão), dar-lhe um consumidor (bloco `knowledge:` nos planos) e medi-lo (golden set). **Não é preciso reconstruir o L5. É preciso revalidá-lo e ligá-lo.**

**Domain Pack — primeiro exemplo (security)**
- Pipeline `triage → auditor → reporter` (#57). Estado `verified` em testes com Gemini falso (`NAS:runner/tests/test_security_pipeline.py`). **Run real com Gemini: UNVERIFIED** (não há registo no repo).
- `NAS:config/security-capabilities.yaml`: 8 capabilities.
  - `implemented` (3): triage, defensive_audit, security_report (:20,:28,:36);
  - `partial` (4): secrets_hygiene, supply_chain, mcp_surface, hardening_recommend (:45,:54,:62,:70);
  - `deferred` (1): agent_redteam_lab (:78).
- `repo_files` (SEC-1, #58): o auditor lê ficheiros do repo, opt-in por passo, só leitura, 50 KB, com denylist (`NAS:runner/plan_runner/repo_files.py:34-41`).
- ⚠ CORRIGIDO: "Pista security 100% fechada" passa a **"Pista SEC-1/SEC-2 fechada (#57–#61). O Security Domain Pack ainda tem 4 capabilities partial e 1 deferred, e aguarda validação L5 e um run E2E real."**

**Domain Pack — parcial (marketing)**
- 18 agentes na área (17 de `agents/marketing` + `design.identidade-visual`), grounding `slim`. Não tem `capabilities.yaml` formal.
- **Prova com Gemini real só na cadeia SEO** (`research`, `seo_brief`, `copy_answer_first`, `critic_item13`, medida no B1-bis-R2). Os outros templates (social, paid, ugc, influencer) só correram em stub.

**＋ NOVO — Peças que já existem e estão desligadas** (padrão recorrente: "a peça existe, nunca foi ligada", `NAS:docs/architecture/agents-audit/FASE3-AGENTES.md:72`)

| Peça | Onde | Estado |
|---|---|---|
| Scraping web → Markdown (requests + BeautifulSoup, com Playwright de fallback) | `ANM:.github/workflows/scrape.yml` | Existe; não está ligado ao runner nem ao L5 |
| Transcrição (yt-dlp + faster-whisper → Supabase `transcripts`) | `ANM:.github/workflows/transcribe.yml` | Existe; **nunca ligado ao RAG** (AU-44, `NAS:docs/audit/PLANO-DE-ACAO.md:329`) |
| Ingestão JSON do MCP | `ANM:.github/workflows/ingest.yml` | 2.ª pipeline, paralela ao T6 |
| Engine `langgraph` + decisão `edit` | runtime Python | Não estão expostos na superfície MCP (B7, `NAS:docs/initiatives/OPEN-ITEMS.md:15`) |

**⚠ CORRIGIDO — O core TS não faz parte do Universal Core**
- `packages/` e `apps/` são TS **arquivado** pela D1 (VIA A).
- O `NAS:docs/architecture/CORE-MAPPING.md:11-13` dá 5 REAL / 19 INCOMPLETO / 14 MOCK. Uma auditoria posterior reclassificou `Orchestrator.ts` de MOCK para REAL (`NAS:docs/audit/AUDIT-4-modulos.md:10,24`).
- `MetricsDashboard.ts` é INCOMPLETO, não MOCK (`AUDIT-4-modulos.md:143`).
- O `TokenEconomy.ts` ("módulo do objectivo central", `AUDIT-4-modulos.md:39`) também está arquivado. O objectivo de tokens vive hoje no ledger e no budget Python.
- **Regra:** nada deste plano depende de `packages/core`.

**Backlog em análise (Grok/GPT): mantém-se, com as correcções das §4–§6**
- Matriz P0: a cobertura real é **~19% ready** (3/16), não 40–50% (§4.3).
- Matriz P1: em rigor, 1 domínio parcialmente ready (a cadeia SEO de marketing). Os restantes estão partial ou gap (§5.15).
- Universal Core → Domain Packs: baseline arquitectural.
- 4 categorias de repos.
- Roadmap F0–F6.

### 1.3 A mudança de paradigma
**Antes:** "Vamos criar agentes para cada domínio."
**Agora:** "Vamos construir o Universal Core; cada domínio é um Domain Pack."

**Novo objectivo** (análise "domínios de prova"): não "deixar Legal, Games, Medicine, Trading e Manufacturing prontos", mas **"construir um mecanismo pelo qual estes domínios possam ser adicionados sem alterar o núcleo"**.

**O teste definitivo:**
> Se for necessário mexer em `plan_runner`, no motor de memória, no motor RAG, no `executor` ou no orquestrador para adicionar um domínio, isso é evidência objectiva de que alguma abstracção do Universal Core está incompleta.
>
> **Evolução explícita do core (§11):** essa alteração não é proibida, mas é tratada como evolução do Universal Core: ADR aprovado pelo maestro, análise de impacto, teste de regressão e actualização do DOC (§15.9). O Claude Code não altera o core por iniciativa própria.

**O indicador:** Domain Onboarding Cost, formalizado em §15.9.

**＋ NOVO — consequência estratégica** (baseline): parar de procurar novos frameworks de agentes. A pergunta passa a ser **"que primitive madura podemos incorporar no Universal Core sem criar uma segunda arquitectura?"**

## 2. Arquitectura — Universal Core → Domain Packs

### 2.1 A arquitectura
```
                    ┌──────────────────────────┐
                    │       PLAN RUNNER        │
                    │   único execution core   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     CAPABILITY LAYER     │
                    │ capabilities + policies  │
                    └────────────┬─────────────┘
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
   INGESTION PRIMITIVES    RESEARCH PRIMITIVES     OTHER TOOLS
   MarkItDown              Crawl4AI / scrape.yml   OSV-Scanner
   Docling (cond.)         web_fetch               Gitleaks
   OCR/etc.                discover                Semgrep
   yt-dlp+whisper (existe)
          └──────────────┬───────┘
                         ▼
              ┌─────────────────────┐
              │   KNOWLEDGE CORE    │
              │ L4 Memory           │
              │ L5 Knowledge        │
              │ pgvector            │
              │ provenance          │
              │ temporal metadata   │
              └──────────┬──────────┘
                         ▼
             ┌───────────────────────┐
             │     DOMAIN PACKS      │
             │ security · marketing  │
             │ legal · medicine      │
             │ trading · manufact.   │
             │ gamedev · ...         │
             └───────────────────────┘
```
**Princípio central:** o Domain Pack **não tem** infraestrutura cognitiva própria. Consome o Universal Core.

**＋ NOVO — o que é Universal Core** (não pertence a nenhuma área): Planning, Workflow, HITL, Budget, Memory, Knowledge, Retrieval, Provenance, Research, Document ingestion, Tool registry, Identity, Permissions, Audit, Validation.

### 2.2 O padrão de um Domain Pack (layout lógico → paths reais)
Layout lógico (original, mantido tal como estava):
```
domain-pack/
  knowledge/       # packs de conhecimento
  skills/          # skills (curtas)
  capabilities/    # capabilities.yaml (validadas em E7)
  plans/           # planos YAML
  policies/        # políticas (HITL, orçamento, act forbidden)
  validation/      # testes E2E
  tools/           # (opcional) tool declarations
  agents/          # OPCIONAIS — só se identidade estável
```
⚠ CORRIGIDO: o layout `domain-pack/` **não existe** no repo. O padrão é lógico e mapeia para os paths reais (o E7 exige que o nome do ficheiro de capabilities seja igual ao id da área):

| Lógico | Path real (NAS) |
|---|---|
| `knowledge/` | `docs/knowledge/<d>/` (+ entrada em `scripts/ingest_delta.py` MANIFEST) |
| `skills/` | `skills/<d>/` (skills curtas) |
| `capabilities/` | `config/<d>-capabilities.yaml` (validado pelo E7, `runner/plan_runner/capabilities.py`) |
| `plans/` | `docs/orchestration/<d>/templates/` (+ `examples/`) |
| `policies/` | `config/areas.yaml` (hitl, budget, grounding) + `policy:` das capabilities |
| `validation/` | `runner/tests/test_<d>_pipeline.py` |
| `tools/` (opcional) | declarativo nas capabilities. Hoje o worker não tem tools (`tools_allowed` é declarativo) |
| `agents/` (OPCIONAIS) | `agents/<d>/*.agent.md` + entrada em `areas.yaml`. Só se a identidade for estável |

Uma capability pode ser **skill-only** (conhecimento + prompt), uma **composição** (combina skills existentes) ou um **agente** (só se precisar de identidade, grounding e budget estáveis).

### 2.3 As 4 categorias de repos (canónicas)
＋ NOVO: **esta pesquisa já tinha sido feita** (e verificada contra CVEs reais na `AUDIT-INGESTION.md`, que **prevalece** sobre a FASE3 por ser posterior, §15.1) em `NAS:docs/architecture/agents-audit/FASE3-AGENTES.md` (2026-09-18) e `NAS:docs/architecture/ingestion-audit/AUDIT-INGESTION.md`. A adopção está registada como itens de conectores de ingestão (`NAS:docs/initiatives/OPEN-ITEMS.md:20`). Este plano **reaproveita** essas decisões e não as refaz.

**Categoria 1 — Infrastructure primitives (ADOPTAR)**
Componentes reutilizáveis da plataforma:

| Repo | Função | Estado | Decisão anterior |
|---|---|---|---|
| MarkItDown | PDF/DOCX/XLSX/PPTX → Markdown | A adoptar (F1) | ADOPT, 1.ª escolha (`FASE3-AGENTES.md:40`), **com mitigação obrigatória**: `markitdown>=0.1.4` (CVE-2025-64512), limite de descompressão antes de ZIP/EPUB, limite de memória do processo (`ingestion-audit/AUDIT-INGESTION.md:140-156`) |
| Docling | PDF complexo, tabelas, OCR | Condicional (F1b) | Condicional (`FASE3-AGENTES.md:59`); `docling-core>=2.48.4` (CVE-2026-24009, `AUDIT-INGESTION.md:189`) |
| Crawl4AI | Web fetch + crawl com limites | A adoptar (F2) | **ADOPT condicional** (`AUDIT-INGESTION.md:304`): `crawl4ai>=0.9.3` (3 CVEs SSRF/escrita de ficheiros), só como biblioteca local, `check_robots_txt=True`, nunca expor o servidor Docker; ＋ partir do `ANM:.github/workflows/scrape.yml`, que já existe |
| OSV-Scanner | Vulnerabilidades em dependências | A adoptar | — (supply_chain está `partial`) |
| Gitleaks | Segredos no git | ✅ em uso (#59) | — |
| Semgrep | SAST | ✅ em uso (#59, #61) | — |
| Instructor | Extracção estruturada com LLM | A avaliar | — |
| ＋ gitingest | Repo → texto (só código) | ⚠ **ADAPT com reservas** | Revisto de ADOPT para ADAPT: projecto órfão há mais de 13 meses, com issue de segurança aberta; pin `0.3.1`, só repos públicos (`AUDIT-INGESTION.md:249,309`). A FASE3 (`:31`) dizia ADOPT |
| ＋ yt-dlp + faster-whisper | Áudio/vídeo → texto | **Já em uso** (ANM), por ligar ao RAG (AU-44) | ADOPT (manter) (`FASE3-AGENTES.md:24,50`) |
| ＋ Unstructured | 60+ formatos | DEFER (dependências pesadas) | `FASE3-AGENTES.md:42` |

**Categoria 2 — Knowledge architecture patterns (EXTRAIR, não instalar)**

| Repo | O que extrair |
|---|---|
| LightRAG | GraphRAG leve, nativo em Postgres. **Só depois** de: pgvector a funcionar → retrieval comprovado → provenance → metadata → temporalidade → avaliação de retrieval → só então a camada de grafo/entidades |
| Graphiti | Modelo bi-temporal: `valid_from`, `valid_until`, `observed_at`, `source`, `confidence`, `supersedes`. A L4 já tem `supersedes` e `expires_at` (`NAS:scripts/create_memory_l4_table.sql:42,47`); absorver o resto no próximo ADR de memória |
| mem0 | Padrões ADD/UPDATE/DELETE. **Spike J11 (L4-2) = extrair padrões, não substituir a L4** (D3) |

**Categoria 3 — Domain packs (CONSTRUIR)**

| Pack | Estado |
|---|---|
| security-pack | O mais avançado (agents + capabilities + plans + testes) |
| marketing-pack | Agentes e skills fortes; sem `capabilities.yaml` (candidato do F4) |
| legal / medicine / trading / manufacturing / gamedev / imobiliário | Knowledge fino ou área vazia (§5) |

**Categoria 4 — Agent runtimes (REJEITAR como núcleo)**

| Repo | Porquê |
|---|---|
| CrewAI | Substitui o plan_runner |
| AutoGen | Em manutenção |
| GraphRAG (Microsoft) | Pesado |
| Letta | Runtime paralelo |

⚠ CORRIGIDO: o **LangGraph não é rejeitado**. É um engine opcional *dentro* do plan_runner (`engine: langgraph`), com checkpoints.
**Regra:** só o `plan_runner` é execution runtime.

## 3. Os 3 ajustes de precisão (baseline)
Antes de implementar qualquer coisa, estes três ajustes:

**Ajuste 1 — `ingest_document(source, options)` não fica preso a `path`**
```
ingest_document(source, options) → { content, source_meta, artifacts?, warnings? }
source = path | url | bytes | connector_ref
```
O MarkItDown é um **adapter**, não o contrato.

**Ajuste 2 — `web_research` separa descoberta de aquisição**
```
discover(query) → candidate URLs
fetch/crawl(url, limits) → normalize → provenance → research artifact
```
O Crawl4AI é **uma implementação** da aquisição, não "o agente de pesquisa". **RESEARCH ≠ WEB SCRAPING.**
Formato de saída:
```json
{ "content": "...", "sources": [{"uri": "...", "title": "...", "retrieved_at": "...", "content_hash": "..."}],
  "limitations": [], "artifacts": [] }
```
Com este contrato, podem entrar fornecedores novos sem mudar a capability: Crawl4AI, GitHub, Crossref, fontes legislativas, médicas ou financeiras, connectors.

**Ajuste 3 — Provenance em TODAS as camadas**
```
SOURCE → DOCUMENT → CONTENT → CHUNK → EMBEDDING → RETRIEVAL → ARTIFACT
```
Cada camada aponta para a anterior, para se poder responder a "de onde veio esta afirmação?" sem depender da memória do agente.

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
  # ＋ NOVO (§15.8):
  status: active | superseded | revoked | expired | deleted
  supersedes: ref?
  superseded_by: ref?
```
**Regra:** nenhum conhecimento externo entra no L5 sem provenance mínima.
＋ **Ponto de partida real:** a `knowledge_chunks` já tem `source`, `content_hash`, `chunk_index`, `kb`, `project`, `updated_at` (`NAS:docs/ops/RAG-CANONICAL.md:19-25`). O retrieve devolve só `source` (`ANM:memory/schema.sql:50`). O contrato L5 existente é `NAS:docs/architecture/memory/rag-l5.md` e `contracts.md`; o F3 **estende-o**, não cria outro.

---

# PARTE 2 — MATRIZES, DOMÍNIOS, ROADMAP

## 4. Matriz P0 — capacidades universais

**Critério "pronto":** knowledge útil + skill (ou equivalente) + agente/composição no registo + caminho de execução (plan/worker) + validação mínima.
**Legenda:** `ready` | `partial` | `gap` (+ `UNVERIFIED` quando falta prova)

### 4.1 Tabela

| Capacidade | Knowledge | Skills | Tools / wiring | Agente / composição | Área | Policy | Pronto? | Evidência / lacuna |
|---|---|---|---|---|---|---|---|---|
| Planning | playbooks de orquestração | planejador + skills claude de planning | `plan_runner` native/langgraph | `meta.planejador` | horizontal | read/prepare | **ready** | Motor + HITL + budget; plano YAML |
| Workflow / execution | WORKER-EXTERNAL, ops | — (runtime) | executor, external_worker, resume | composição de steps | — | conforme o plan | **ready** | Stub + external + ledger |
| Human approval (HITL) | docs HITL / councils | — | `human_gate`, resume, gate do conselho | gates nos plans + councils | áreas de risco `required` | approve/reject/edit | **ready** | Security/finance/legal com `hitl: required` (`areas.yaml:99,128,169`) |
| Security (defensive) | `SECURITY.md`, `security-agents-stack.md` | triage, security-audit, reporter | `repo_files`, CI gitleaks/semgrep | triage → auditor → reporter | security | read/prepare; act forbidden | **partial** ⚠ | 3/8 implemented; L5 **não ingerido** (`ingest_delta.py:32-71`); run real UNVERIFIED; red-team deferred |
| Audit / observability (runs) | BUDGET, ledger de tokens | — | `token_usage.jsonl`, events, status | runtime | — | — | **partial** | Tokens + status; ledger Supabase sem `council_*` (C-2). ⚠ O `MetricsDashboard` é TS arquivado e INCOMPLETO (`AUDIT-4-modulos.md:143`), irrelevante para o runtime |
| Memory (L4) | contracts, MEMORY-L4 | wiring no worker | Supabase `memory_l4`, recall/remember | opt-in por plan | — | candidate → promoção HITL | **partial** | Código + SQL; L4-1b pendente; L4-2/L4-3 abertos |
| Knowledge retrieval (L5) | dezenas de packs | wiring S9 (`knowledge:`) / MCP | pgvector, ingest T6 | step com bloco `knowledge:` | — | — | **partial + UNVERIFIED** ⚠ | Quadro L5 da §1.2: J3 passos 3/5 abertos; 31 ficheiros fora da lista; security não ingerido nem consumido |
| Knowledge engineering (entidades, vigência, jurisdição, conflitos) | packs ad hoc | `cheap-entity-extraction` (`skills/meta`) | chunk/embed | — | — | — | **gap** | Chunking básico ≠ modelo de entidades/autoridade |
| Research / intelligence | research-marketing, radar | research de marketing; radar | web **limitado** no worker; ＋ `ANM:.github/workflows/scrape.yml` existe mas está desligado | `marketing.research`, `meta.radar-ferramentas` | research, marketing | read | **partial** | Sem research web/GitHub/legislação com provenance unificada |
| Document intelligence (PDF/Office/OCR) | pouco genérico | — | `repo_files` (só texto do repo) | — | docs (vazia) | — | **gap** | Área `docs` sem agentes; MarkItDown decidido mas não adoptado |
| Communication (email/atendimento) | comunicações importadas | skill de atendimento | — | `atendimento.comunicacoes-atendimento` | ops | read/prepare | **partial** | Um agente; não é omnichannel |
| Identity / permissions | GOVERNANCE, grounding | — | não há IAM no runtime | — | — | docs de policy | **gap** | ⚠ "packages/core security MOCK" é TS **arquivado** (D1); no runtime, a policy está só nas capabilities e no HITL |
| Tool discovery / registry | skills-map, using-agent-skills | `meta.using_agent_skills` | resolução skill/agente por action | `meta.using_agent_skills` | horizontal | — | **partial** | Resolução A8 + inventário E7; sem registry dinâmico |
| Source / provenance / verification | grounding "não inventar" | — | `knowledge_refs` declarativo (AU-22); `repo_files` com paths | — | — | — | **partial** | O chunk tem `source`/`content_hash`; o retrieve devolve só `source` (`ANM:memory/schema.sql:50`); `metadata`/`locator` = None (`mcp_knowledge.py:23-29`) |
| Data analysis | qualidade-dados | engenharia.qualidade-dados | — | `engenharia.qualidade-dados` | software | read | **partial** | Focado em produto/código, não em BI |
| Software engineering | TDD, revisor, imported | guia-tdd, revisor (+ pack Claude) | git/CI no repo | desenvolvimento, tdd, revisor, arquitectura | software | read/prepare | **partial** | Forte em agentes; skills longas = custo (por medir) |

Todos os IDs de agentes citados existem em `NAS:config/areas.yaml` (verificado: 0 em falta).

### 4.2 Áreas P0 profissionais (cobertura)

| Domínio | Área yaml | Agents | Capabilities yaml | Knowledge | Pronto? |
|---|---|---|---|---|---|
| Marketing | marketing | 18 | não | forte | **ready só na cadeia SEO** ⚠; o resto é partial (stub) |
| Software / coding | software | 10 | não | médio | partial |
| Security / cyber | security | 3 | **sim** | médio (docs); RAG **não ingerido** ⚠ | partial |
| Research | research | 1 (radar) | não | fino | partial |
| Ops / administração | ops | 2 | não | fino | partial |
| Finance | finance | 1 (contabilidade) | não | fino | partial (trading = gap) |
| Legal | legal | 0 | não | `legal/direito-br-pt.md` (ingerido) | gap (hitl reservado) |
| Docs | docs | 0 | não | — | gap |
| Gamedev | gamedev | 0 | não | — | gap |
| ＋ Imobiliário | — (não há área) | 0 | não | `imobiliario/fipezap.md` (ingerido) | gap de execução; knowledge partial |
| Medicine / HR / Sales-CRM… | — | — | — | packs isolados de saúde | fora / gap |

(Contagens: `NAS:config/areas.yaml`, verificadas.)

### 4.3 Scorecard P0 ⚠ CORRIGIDO
O rascunho original dava **~40–50% ready, ~35% partial, ~15–20% gap**, com as listas: ready = Planning, Workflow, HITL, Marketing (vertical composta); partial = Security, Memory L4, Knowledge L5, Research, Communication, Tool registry, Provenance, Data analysis, Software eng., Ops, Finance; gap = Document intelligence, Knowledge engineering, Identity/permissions, Legal agents, Docs agents, Trading execution. Isso **não bate com a própria tabela**, que tem 16 linhas com 3 ready, 10 partial e 3 gap. Além disso, o scorecard misturava itens da P1 (Marketing, Ops, Finance, Legal agents, Docs agents, Trading execution) e omitia Audit/observability.

| Estado | Capacidades (16) | % |
|---|---|---|
| ready | Planning, Workflow, HITL | ~19% |
| partial | Security, Audit/observability, Memory L4, Knowledge L5, Research, Communication, Tool registry, Provenance, Data analysis, Software eng. | ~62% |
| gap | Document intelligence, Knowledge engineering, Identity/permissions runtime | ~19% |

Leitura: **o núcleo de orquestração está pronto; a cognição transversal e a profundidade de knowledge são desiguais.** A percentagem é uma ordem de grandeza, **não um KPI formal**. O KPI formal é o da §15.9.

### 4.4 O que a matriz P0 implica (prioridade de ingestão / build)
Não abrir 20 agentes novos. Fechar os partials do núcleo:
1. **L5:** ingerir e provar retrieval de `SECURITY.md` + `security-agents-stack.md` (+ marketing, que já está forte) → **F0**.
2. **Capability registry genérico** (padrão security), só quando uma área tiver ≥2 capabilities estáveis. Marketing pode ser o 2.º ficheiro → **F4**.
3. **Research:** uma capability + skill curta + tool de fetch com provenance (antes de Legal/Medicina) → **F2**.
4. **Document intelligence:** capacidade de plataforma (tool), não um `docs.agent` vazio → **F1**.
5. **Legal:** knowledge com jurisdição/data **antes** de agente → gate §6.3.
6. **Identity:** não priorizar enquanto não houver policy no runtime. ⚠ O `packages/core` está arquivado (D1) e não volta a ser opção.

### 4.5 Como ler esta matriz
- **Agente no `areas.yaml` ≠ capacidade pronta.**
- **Só security tem `*-capabilities.yaml` validado no E7.**
- **Knowledge no git ≠ knowledge no vector store ≠ knowledge consumido por um passo.** Assinalar sempre UNVERIFIED quando não houver query de retrieval.
- HITL, budget e router são o que mais se aproxima do "nível 0 universal" já utilizável.

## 5. Matriz P1 — domínios profissionais

**Nota:** P1 = domínios profissionais. Muitos reutilizam P0 (planning, HITL, knowledge, security). Quando a área declara keywords sem agentes, o estado é **gap de execução**, não de intenção.

### 5.1 Cybersecurity
| Capacidade | Knowledge | Skills | Tools | Agente / composição | Pronto? | Nota |
|---|---|---|---|---|---|---|
| Triage | pack security | `security/triage` | — | `security.triage` | **ready** (testes; run real UNVERIFIED) | |
| Defensive audit | `SECURITY.md` | `meta/security-audit` | `repo_files`, scanners orientados | `meta.security-auditor` | **partial–ready** | L5 não ingerido e não consumido (sem bloco `knowledge:`) |
| Security report | pack | `security/reporter` | — | `security.reporter` | **ready** (testes) | |
| Secrets hygiene | SECURITY.md | via audit | gitleaks no CI | composição | **partial** | Histórico ignorado com justificação (`.gitleaksignore`, SEC-2b) |
| Supply chain / deps | SECURITY.md | via audit | orientação OSV/Trivy | auditor | **partial** | Sem job OSV dedicado |
| MCP surface | SECURITY.md | audit | — | auditor | **partial** | |
| Hardening recommend | — | `next_steps` do report | — | reporter → engenharia | **partial** | Só PREPARE |
| Threat model / conselho | councils | — | council_session | conselho security | **partial** | Deliberação, não pipeline diário; custo por medir no 1.º uso |
| Agent red-team lab | pack §B | — | PyRIT/DeepTeam | — | **gap** | deferred, fora de produção (SEC-3) |
| SOC / SIEM / IR | — | — | — | — | **gap** | Fora do âmbito de custo zero |
| Compliance formal (ISO/SOC2) | GOVERNANCE parcial | — | — | — | **gap** | |

Área `security` · capabilities.yaml: sim · hitl: required · act: forbidden.

### 5.2 Software engineering
| Capacidade | Knowledge | Skills | Tools | Agente | Pronto? | Nota |
|---|---|---|---|---|---|---|
| Implementation | TDD/prod importados | desenvolvimento | — | `engenharia.desenvolvimento` | partial | |
| TDD / tests | knowledge guia-tdd | guia-tdd (+ pack Claude) | — | `engenharia.guia-tdd` | partial | Custo em tokens (pack Claude por medir) |
| Code review | revisor + security/DB | revisor (+ pack Claude) | — | `engenharia.revisor-codigo` | partial | Idem |
| Data quality | — | qualidade-dados | — | `engenharia.qualidade-dados` | partial | |
| Agent architecture | ADRs | — | — | `meta.arquitetura-agentes` | partial | Conselho architecture |
| Product/tech transversal | a11y/SEO importados | — | — | `produto.produto-tech-transversal` | partial | |
| CI/CD / deploy | skills meta de deploy, GHA | skills ci-cd (claude) | GHA | composição | partial | Não é capability formal |
| Repo understanding | — | — | `repo_files` | passos que o declaram | partial | Opt-in por passo; ＋ gitingest (F1/E) |
| Refactor / migration | pack claude | skills longas | — | via desenvolvimento | gap | Só se a skill for carregada |
| Observability de produto | — | — | ledger de tokens | — | partial | Runs, não APM |

Área `software` · capabilities.yaml: não · hitl: null.

### 5.3 Design & media
| Capacidade | Knowledge | Skills | Agente | Pronto? |
|---|---|---|---|---|
| UI spec | ui.md, design/* | ui_spec | `design.ui` | partial–ready |
| UX flow | ux.md | ux_flow | `design.ux` | partial–ready |
| UX writing | packs de ux-writing | ux_writing | `design.ux_writer` | partial–ready |
| Design critic | — | design_critic | `design.design_critic` | partial |
| Identidade visual | diretor-arte | — | `design.identidade-visual` | partial |
| Video edit | editor-video | — | `marketing.editor_video` | partial |

⚠ Nota: `docs/knowledge/design/*` **não está na lista de ingestão** (`ingest_delta.py:32-71`).

### 5.4 Marketing ⚠ CORRIGIDO
| Capacidade | Knowledge | Skills | Agente | Pronto? |
|---|---|---|---|---|
| Orchestration / brief | orquestrador, playbook | internal_brief | `marketing.marketing`, `marketing.internal_brief` | ready-stub (run real UNVERIFIED) |
| Research | research-marketing | research | `marketing.research` | **ready** (Gemini real, SEO) |
| SEO brief | seo-specialist, geo | seo_brief | `marketing.seo_brief` | **ready** (Gemini real) |
| Copy answer-first | copywriter | copy_answer_first | `marketing.copy_answer_first` | **ready** (Gemini real) |
| Critic / item-13 | item-13, findability | critic, critic_item13 | `marketing.critic`, `marketing.critic_item13` | **ready** no critic_item13 (Gemini real); critic: stub |
| Copy social | — | copy_social | `marketing.copy_social` | partial (stub) |
| Storytelling | storytelling | storytelling | `marketing.storytelling` | partial (stub) |
| Creative / ads | — | ad_creative, creative_review | ad_creative, creative_review | partial (stub) |
| Trends | trend-hunter | trend_hunter | `marketing.trend_hunter` | partial–ready |
| Content analysis | content-strategist | — | `marketing.content_analyst` | partial |
| Media buy | media-buyer | — | `marketing.media_buyer` | partial |
| Influencer / UGC | packs | — | influencer, ugc | partial |
| Analytics / conversion | performance-analyst | — | — | gap (sem wiring de API) |
| Brand guard | brand-guard-cliente | — | — | partial (só knowledge) |

Área `marketing` · capabilities.yaml: não (candidato do F4) · grounding: slim · planos SEO medidos em tokens (B1-bis-R2).

### 5.5 Administration / operations
| Capacidade | Knowledge | Agente | Pronto? |
|---|---|---|---|
| Gestão empresarial | — | `gestao.gestao-empresarial` | partial |
| Atendimento / comunicações | comunicações importadas | `atendimento.comunicacoes-atendimento` | partial |
| Tasks / projects / calendar | — | — | gap |
| Approvals workflows (negócio) | HITL do runner | runtime | partial (só plans, não BPM) |
| KPIs / reporting ops | — | — | gap |
| RH / recrutamento | keywords em ops (`areas.yaml:103`: "recursos humanos", "recrutamento") ✓ | — | gap |
| Procurement | keyword "fornecedor" (`areas.yaml:103`) ✓ | — | gap |

### 5.6 Finance & accounting
| Capacidade | Agente | Pronto? |
|---|---|---|
| Contabilidade PT/BR | `gestao.contabilidade` | partial |
| Orçamento / fluxo de caixa | keywords (`areas.yaml:123`) | gap |
| Faturação / impostos | keywords | gap |
| Análise financeira | — | gap |
| Trading / markets (research) | — (keywords trading/bolsa/cripto, `areas.yaml:123`) | gap |
| Trading execution | — | gap + **act forbidden** |
| Risk / portfolio | — | gap |

Área `finance` · hitl: required · capabilities.yaml: não.

### 5.7 Sales & CRM ⚠ CORRIGIDO
Todas as capacidades estão em gap (leads/pipeline, propostas/follow-up, integração CRM). **Não existe área dedicada, e ⚠ não há keywords em ops:** vend/crm/lead aparecem 0 vezes em `areas.yaml`. O original dizia "keywords em ops".

### 5.8 Legal
| Capacidade | Knowledge | Agente | Pronto? |
|---|---|---|---|
| Direito PT/BR base | `legal/direito-br-pt.md` (ingerido) | — | partial (só knowledge fino) |
| Contratos / cláusulas | keywords (`areas.yaml:95`) | — | gap |
| Jurisprudência / pesquisa | — | — | gap |
| RGPD / compliance | keywords rgpd/gdpr | — | gap |
| Metadata de jurisdição + vigência | — | — | gap (**bloqueia o "ready"**, gate §6.3) |

Área `legal` · agents: [] · hitl: required.

### 5.9–5.14 Outros domínios ⚠ CORRIGIDO
- **Medicine:** knowledge isolado (`saude/*`: cardio, derma, oftalmo, ingerido). ⚠ **Não há área nem keywords** (saude/medic/clinic aparecem 0 vezes em `areas.yaml`). Gap; o gate está em §6.3.
- **HR:** keywords em ops ✓. Gap.
- **Manufacturing / supply chain:** ⚠ **sem keywords** (fabric/industr aparecem 0 vezes); ops só tem "encomenda" e "fornecedor". Gap.
- **Engineering & science (não-software):** gap.
- **Education:** gap.
- **Game development:** área `gamedev` vazia (0 agentes; keywords em `areas.yaml:132`). Gap.
- **＋ Imobiliário:** knowledge `imobiliario/fipezap.md` (ingerido). Sem área. Gap de execução.

### 5.15 Scorecard P1 ⚠ CORRIGIDO
| Ready (utilizável em plans) | Partial | Gap |
|---|---|---|
| Marketing: **cadeia SEO** (research, seo_brief, copy_answer_first, critic_item13) | Security (testes ok, L5/run real por provar), Software, Design, Ops, Finance (contabilidade), Research (radar), restantes capacidades de marketing (stub) | Legal (execução), Sales/CRM, Medicine, HR, Manufacturing, Supply chain, Education, Science/Eng. de campo, Games, Trading, Imobiliário (execução), SOC/IR, red-team lab, compliance formal |

**Resumo:** em P1, **marketing está à frente** (na cadeia SEO), **security é o modelo de capabilities**, e software, design, ops e finance estão partial.

### 5.16 Ordem P1 recomendada (da matriz P1, mapeada para F0–F6)
1. Fechar Security: prova L5 + merges SEC (feitos) → **F0**.
2. `marketing-capabilities.yaml` (espelhar security) → **F4**.
3. Capabilities curtas de software (impl, review, tdd) **e medir o pack Claude** → depois do F4 (pendente §9.2).
4. Finance: alargar knowledge e skills **sem** execução de trading → F6 candidato.
5. Legal: metadata de fonte/jurisdição no knowledge **antes** do 1.º agente → F3 + gate §6.3.
6. Gamedev, Sales, Medicine, Manufacturing: só depois de Research (F2) e Documents (F1).

### 5.17 Regra de ouro P1
| Evitar | Fazer |
|---|---|
| Um agente por subárea da tabela | Capability + skill curta + plan; agente só se a identidade for estável |
| Trading com `act` de execução | Research/risco partial; execução forbidden até haver permissões |
| Medicina "pronta" por ter `saude/*.md` | Policy + provenance + HITL clínico explícito |
| Duplicar marketing num "Sales agent" | Capability CRM quando houver tool real |

### ＋ 5.18 Matriz P2 — verticais (adendo do Maestro)
| Vertical | Estado | Nota |
|---|---|---|
| Imobiliário | partial (só knowledge) | `fipezap.md` ingerido; sem área nem agentes |
| Saúde | partial (só knowledge) | `saude/*` ingerido; sem área |
| Ficha de cliente | partial | Memória de cliente só de leitura (`PLANO-DE-ACAO.md:93`) |
| Restantes (HVAC, construção, etc.) | gap | |

**Regra:** **nenhum vertical está ready.** Um vertical só avança **com uso real** (cliente ou necessidade concreta). Packs P2 em massa: proibido (§10).

## 6. Matriz estendida — Domínio → Capability → …

### 6.1 Formato para cada domínio novo (com a coluna "Reutiliza P0")
| Domínio | Capability | Knowledge | Skill | Tool | Policy | Execução | Validação | Reutiliza P0 |
|---|---|---|---|---|---|---|---|---|
| Legal | pesquisa jurídica | legislação/jurisprudência | legal-research | web/docs | jurisdição | plan | source check + HITL | Research, Documents, L5, HITL |
| Trading | análise de mercado | market data | market-analysis | market API | financial | plan | backtest/risk | Research, Data, Planning; Risk ← Finance |
| Manufacturing | manutenção | manuais/SOP | maintenance | CMMS/sensores | industrial | plan | KPI | Documents, Data, Planning |
| Games | implementação | docs de engine | game-dev | Git/engine | software | worker | tests/build | Software (coding, QA), Design |
| Medicine | guideline research | literatura | clinical-research | fontes médicas | clinical | plan | provenance + HITL | Research, L5, Provenance |

A coluna "Reutiliza P0" mostra que, quanto mais madura estiver a plataforma, menos código novo é preciso para um domínio novo. A métrica está em §15.9.

### ＋ 6.2 Porque estes 5 domínios (cada um testa uma dimensão diferente do núcleo)
- **Legal:** testa knowledge engineering (jurisdição, vigência, autoridade, versão, hierarquia). Não é "mais um agente", é um **teste de maturidade do L5**.
- **Medicine:** testa provenance + temporalidade (distinguir as guidelines de 2024, 2025 e 2026) + policy + HITL.
- **Trading:** testa dados, tempo, risco e permissões. A pipeline é `RESEARCH → ANALYSIS → STRATEGY → BACKTEST → RISK → HUMAN APPROVAL → EXECUTION`, e a **execução é uma capability explicitamente privilegiada (RESTRICTED)**, nunca uma consequência de ter acesso a uma API. Sub-capabilities: market research, market data, fundamental, technical, news/event, strategy research, backtesting, portfolio, risk; execution restrita.
- **Manufacturing:** testa o mundo fora do digital (manual.pdf, maintenance_history.csv, sensor_data, SOP.pdf, parts_catalog). Combina Documents + Knowledge + Data + Research + Planning + Operations. Sub-áreas: planning, scheduling, inventory, procurement, quality, maintenance, energy, safety.
- **Game development:** testa **composição de domínios** (Software + Design + Project mgmt + Documents + QA + Research + Marketing). Capabilities específicas só quando faltarem: game design, level design, gameplay, balancing, conhecimento da engine, asset pipeline, build/release.

**Decisão do Maestro (fechada):** os 5 servem de **critério de desenho**, mas no F6 entra **UM** domínio de cada vez, com uso real. Cinco em paralelo diluem o esforço.

### ＋ 6.3 Readiness gates por domínio (nenhum pode passar a `ready` sem isto)
- **Legal:** jurisdição, autoridade da fonte, datas de vigência, versão, provenance, HITL.
- **Medicine:** fonte, versão da guideline, data de publicação, provenance clínica, âmbito, HITL.
- **Trading (para `act`):** provenance dos dados de mercado, controlos de risco, backtesting, limites de posição, autorização, HITL, audit.
- **Geral:** o validador actual força `act_in_production: forbidden` (`NAS:runner/plan_runner/capabilities.py:37,112`). O F4/F6 testa se esta regra serve para domínios sem produção (marketing) e para trading. Alterá-la é decisão do maestro.

### ＋ 6.4 Ingestão como multiplicador (análise "repos → primitives")
```
Legal:         PDF de legislação → ingest → metadata → chunks → provenance → L5 → capability legal
Medicine:      guideline PDF → ingest → versão/data → provenance → L5 → medical research
Manufacturing: manual PDF / SOP / relatório / CSV → ingest → knowledge → capability de produção
Games:         docs Unity/Unreal / design docs / repo Git → ingest/research → knowledge → capabilities gamedev
```
Um investimento em ingestão alimenta dezenas de domínios. Research (fetch + crawl + normalize + URL + timestamp + cache + evidência) é **P0**, não marketing. Usos: legislação (Legal), literatura (Medicine), notícias e dados (Trading), advisories e CVEs (Security), docs técnicas (Games), concorrentes e tendências (Marketing), normas (Engineering).

## 7. Roadmap de execução (F0–F6)

> Ordem obrigatória. Não avançar para F1-código sem F0 verde (sobre o contrato do F1 em paralelo, ver a decisão D-EP4).

### F0 — REVALIDAR o L5 existente (não construir) ⚠ CORRIGIDO
**Porquê primeiro:** para não construir uma pipeline de ingestão excelente e descobrir depois que o problema estava no retrieval existente.

**Checklist executável.** Tipos de passo:
- `R` = leitura/observação (sem commit);
- `W-repo` = alteração versionada no Git, sem efeito em produção (commit + PR);
- `W-prod` = alteração com efeito externo/produção (obriga a PARAR para decisão).

| # | Passo | Tipo | Quem | Evidência / referência |
|---|---|---|---|---|
| F0.1 | Confirmar a tabela canónica: `count(*)` por `project`, `count(*)` total, e `pg_proc` com 1 só `match_knowledge` (repetir o passo 2 do RAG-CANONICAL) | R | DEV ou Claude Code via SELECT (se autorizado) | `RAG-CANONICAL.md:33-42` (base: 121 / 322 / 1) |
| F0.2 | Query em `knowledge_chunks` com `source ILIKE '%security%'` (`security-agents-stack`, `SECURITY`) | R | idem | Esperado: **0** (o pack não está em `ingest_delta.py:32-71`) |
| F0.3 | J3 passo 3: confirmar que o último ingest escreveu na `knowledge_chunks` e que a t6 não mudou | R | DEV | `RAG-CANONICAL.md:44-57` |
| F0.4 | Pôr o pack de security na lista de ingestão (agent_id/kb a alinhar com quem consome) → PR. **O push para main dispara o workflow, que escreve em produção** | **W-prod** (potencial, no merge) | Claude Code prepara o PR; **o maestro decide** (D-EP2 = A: só o pack de security) | `.github/workflows/ingest-knowledge.yml`; D-EP2 |
| F0.5 | Dar um consumidor ao pack: bloco `knowledge:` (kb + query) no passo `audit` do plano demo de security | **W-repo** | Claude Code | `knowledge_wiring.py:20-29`; `security-audit-demo.plan.yaml` |
| F0.6 | J3 passo 5: teste real no MCP (conector) que cite `[Fonte: …]` | R | DEV | `RAG-CANONICAL.md:69-70` |
| F0.7a | **Definir** o golden set security: 10–20 perguntas, versionado no repo, com `expected chunks` (id/`chunk_index`) **e** `expected_sources` por pergunta (as fontes são estáveis entre re-ingestões; os ids podem não ser). Inclui o script de avaliação em Python puro (o DeepEval/Ragas está bloqueado por S19) | **W-repo** | Claude Code | `NAS:docs/initiatives/STATUS.md:41` |
| F0.7b | **Medir** o golden set: `hit@k` (k = `match_count`, por omissão 4), relevância e "provenance presente?" | R + embeddings de query (Gemini; credenciais autorizadas) | DEV ou CI com segredos | `ANM:memory/schema.sql:48` (`match_count default 4`) |
| F0.8 | Registar a provenance que existe hoje: só `source` no retrieve; `metadata`/`locator` a `None`; `filters` sem efeito | R | Claude Code | `mcp_knowledge.py:23-29`; `ANM:memory/schema.sql:50` |
| F0.9 | Comparar com o histórico: C8 (110, t6) → J3 (121/322 canónica) → hoje | R | Claude Code | §1.2 quadro L5 |
| F0.10 | Merges SEC em main | R | — | ✅ já verificado (`969d3ce`) |
| F0.11 | Cobertura dos outros ~31 ficheiros fora da lista: **decidido** pack a pack, não em bloco (no F3) | decisão ✅ | maestro | D-EP2 = A |
| F0.12 | (Opcional, não bloqueia) J3 passo 6: apagar a t6. **Irreversível**, com backup | **W-prod** (irreversível) | DEV | `RAG-CANONICAL.md:72-75` |

**Critério de done:**
- o retrieve devolve chunks reais do pack de security;
- golden set **definido** e versionado (estado do artefacto, F0.7a) **e** golden set **medido** com `hit@k` registado (estado da avaliação, F0.7b). Os dois estados são registados em separado: uma limitação operacional (sem credenciais) não invalida o artefacto, mas o F0 só fica verde com a medição;
- estado da provenance documentado;
- J3 passos 3 e 5 fechados;
- decisão de cobertura tomada (✅ D-EP2 = A).

**Se não houver ingestão, resolve-se antes de F1.**

### F1 — Ingestão universal (spike pequeno)
1. **Contrato** (ADR curto *Universal Ingestion & Research Primitives*):
   - `ingest_document(source, options) → {content, source_meta, artifacts?, warnings?}`, com `source = path | url | bytes | connector_ref`;
   - `web_research(...)` já com a separação discover/fetch (§3);
   - **proibido** substituir o plan_runner; **obrigatórios** os campos de provenance (§3);
   - o ADR fica com os 10 itens do contract-first (§15.4).
2. **Spike MarkItDown** (adapter; **fronteira de segurança obrigatória**: pin `>=0.1.4`, limite de descompressão, limite de memória, segundo `AUDIT-INGESTION.md:140-156`): PDF textual, DOCX, XLSX (+ PPTX se for barato) → Markdown → metadata/provenance → **pipeline T6 existente** → pgvector.
3. **Zero alteração do worker de steps.** Script ou CLI em `scripts/`.
4. **＋ Regra T6 (§15.12):** o MarkItDown **alimenta** o T6 e **não cria uma pipeline paralela**. Antes de escrever código, decidir a relação com a 2.ª pipeline (`ANM:.github/workflows/ingest.yml`) (D-EP9).
5. **＋ Ligar o que existe** (candidato, decisão do maestro): AU-44, transcrições (`ANM:transcripts`) → T6.

**Done:** 3 formatos processados; ingestão E2E pela pipeline existente; path de knowledge estável.

### F1b — Docling (condicional)
Só se o MarkItDown perder estrutura que é precisa (tabelas, layout, colunas, figuras, PDF complexo, documentos técnicos). Exige um benchmark escrito, não adopção por moda. **Se não houver perda relevante, não entra.**

### F2 — Web research universal
1. Contrato: `discover(query) → candidate URLs`; `fetch/crawl(url, limits) → normalized + provenance`.
2. **＋ Partir do que existe:** o `ANM:.github/workflows/scrape.yml` (requests + BS4, Playwright de fallback) é a implementação actual. O Crawl4AI entra como implementação **se** superar essa, com evidência.
3. Limites: allowlist, timeout, N páginas, cache, URL + timestamp + `content_hash`. Crawl4AI só com pin `>=0.9.3`, como biblioteca local, com `check_robots_txt=True` e sem servidor Docker exposto (`AUDIT-INGESTION.md:66-73,304`).
4. Não é "o agente de pesquisa": é a implementação da aquisição.

**Done:** 1 capability + 1 tool de fetch com provenance no artefacto.

### F3 — Provenance formal + L5 medido
1. Schema de provenance em **todas** as camadas (SOURCE → … → ARTIFACT), **estendendo** `docs/architecture/memory/contracts.md` e `rag-l5.md`.
2. Metadata mínima e quando aplicável (§3), mais `status` (active/superseded/revoked/expired/deleted).
3. **＋ Knowledge validity / conflict resolution** (§15.8): precedência de fontes, versão, vigência, supersedes, jurisdição, autoridade. **"Retrieval relevante ≠ retrieval válido."** Desenho no F3; implementação só quando um domínio o exigir.
4. **＋ Source Authority** como dimensão própria do L5: quem publicou ≠ que autoridade tem a fonte.
5. Golden set + métricas (hit@k, relevância), alargados para além de security.

**Done:** provenance em todos os artefactos; métricas do golden set registadas.

### F4 — Capability registry (2.º domínio)
1. Security = padrão (feito).
2. `config/marketing-capabilities.yaml` como 2.º caso, espelhando security e validado no E7.
3. **Não generalizar o registry ainda.** Primeiro provar o 2.º caso.
4. ＋ Testar a regra `act_in_production: forbidden` num domínio sem produção (§6.3).
5. ＋ Maturidade por capability (§15.7): marcar DECLARED/WIRED/EXECUTABLE/VALIDATED/PROVEN.

**Done:** `marketing-capabilities.yaml` validado no E7.

### F5 — Validation E2E de capability
Provar a cadeia `discover → select → authorize → execute → validate → audit`. **"YAML válido ≠ capability válida."**

**Done:** teste E2E de uma capability real (security ou marketing), com **run real** (não só com Gemini falso).

### F6 — UM domínio de prova
Escolher **um** domínio com cliente ou necessidade real e adicioná-lo como Domain Pack: knowledge + skills + capabilities + plans + policies + validation (+ tools). **O core não é alterado**; se for preciso mexer nele, há uma abstracção incompleta, e a alteração segue a evolução explícita do core (§11: ADR, impacto, regressão, DOC).

**Done:** um domínio novo funcional, com o Domain Onboarding Cost medido (core changes = 0). **NÃO fazer 5 domínios em paralelo.**

### ＋ 7.1 Backlog imediato (baseline)
- **AGORA:** F0 (prova L5 security, ingest → embedding → retrieval, provenance actual, merges SEC). Contrato do F1 só em documento (D-EP4).
- **DEPOIS:** F1 spike MarkItDown → F1b (se o benchmark justificar) → F2 → F3 → F4 → F5 → F6.

---

# PARTE 3 — META-AGENTES, PENDENTES, ANTI-PADRÕES, INSTRUÇÕES

## 8. Meta-agentes — Fase 2 (Execution Broker + Lease)
Contexto: as 3 IAs (Claude Code, Grok, GPT) têm acesso ao repo e executam.
⚠ CORRIGIDO: "o caso real foi Grok e Claude a executarem em paralelo o security pipeline" é **um relato do maestro, não registado no repo**. O `META-AGENTS-PHASE-2.md` regista o caso Grok + Claude em paralelo como **teste de validação**, sem dizer que foi o security pipeline. Não é um anti-padrão: é a descoberta empírica de que esta camada é precisa.

### 8.1 Separação de responsabilidades
```
COUNCIL          → "O que devemos fazer?"                              (JÁ EXISTE — CouncilSession, Fase 1)
EXECUTION BROKER → "Quem pode fazer agora, dentro das restrições?"     (NOVO)
EXECUTOR         → "Vou executar."                                     (1 só, com lease)
PLAN RUNNER      → "Vou controlar o workflow."                         (JÁ EXISTE)
```

### 8.2 O que o CouncilSession já faz (Fase 1)
- Delibera em três estágios: independent → peer_rank (Borda, anónimo; o par nunca ordena a própria posição) → synthesize (chairman `kind: meta`).
- Produz um veredicto estruturado: decision, confidence, conditions, kill_criteria, next_actions (`council_session.py:369`).
- Passa por um gate determinístico (tau, veto, quorum) e por HITL (approve/reject/edit; o approve só promove, `:853-858`).
- Escreve na L4 (candidate → active).
- **O que NÃO faz:** não escolhe o executor, não considera custo na escolha, não tem lease.

### 8.3 Execution Broker (Fase 2) — responsabilidades
Provider discovery; quota, budget, capability, authorization, availability e cost; fallback, queue, lease, retry e resume.
＋ Fluxo-norte: `TASK → CAPABILITY → eligible workers → policy/authorization → dispatch → execution → validation`. Se nenhum worker estiver disponível: `WAIT/QUEUE` sem perder estado, e retoma depois.
**Não abrir** o scheduler multi-IA na mesma sprint que o MarkItDown (decisão do Maestro).

### 8.4 As 5 decisões de execução ⚠ CORRIGIDO (nomes canónicos de `META-AGENTS-PHASE-2.md:28-29`)
(No original: "Os 5 estados de execução", com DEFERRED/BLOCKED.)
| Decisão | Significado | Exemplo |
|---|---|---|
| EXECUTE | Tudo elegível | Claude: capability ✓, tokens ✓, budget ✓ |
| REDIRECT | O executor escolhido está bloqueado e há outro elegível | Claude sem tokens → Grok com 25k e capability compatível |
| WAIT | Ninguém está elegível agora, mas espera-se recuperação | Quota do Claude repõe às 14:00; Grok sem capability; GPT sem quota |
| **DEFER** | Adiado de forma consciente (não vale o custo agora) | Análise de 300 ficheiros = $8; budget = $2; não urgente |
| **BLOCK** | Nenhum executor válido → HITL se for preciso | A tarefa exige capability + escrita no GitHub + produção, e nenhum provider cumpre |

Nota já registada (`META-AGENTS-PHASE-2.md:80`): "4 estados" vs "5 decisões". Os 4 (READY → EXECUTABLE → BLOCKED → WAITING) parecem ser do ciclo da tarefa, não decisões do broker. Fica por fixar no desenho detalhado.

### 8.5 Orçamento em camadas — **MODELO PRELIMINAR, não é contrato v1** ⚠ CORRIGIDO
```yaml
budget:
  session:   { tokens_remaining: 12000 }
  plan:      { tokens_remaining: 30000 }
  task:      { max_tokens: 10000 }
  providers:
    claude:     { available_tokens: 0 }
    grok:       { available_tokens: 8000 }
    gpt:        { available_tokens: 15000 }
    free_model: { available_tokens: 5000 }
```
⚠ O rascunho chamava-lhe "5 budgets", mas o YAML tem 4 níveis (session/plan/task/providers). **Falta `cost`.**
＋ Distinções obrigatórias antes do contrato: **availability ≠ quota ≠ budget ≠ cost; authorization ≠ capability ≠ quality**, e rate limit é outro conceito ainda.
A decisão não é "o Claude acabou", é: *"Que executor elegível consegue cumprir esta tarefa dentro das restrições actuais?"*

### 8.6 Fallback hierárquico (configurável)
```
1. Executor deliberado   2. Mesmo provider / outra sessão   3. Provider equivalente
4. Provider gratuito compatível   5. Modelo mais barato compatível   6. WAIT   7. HITL   8. BLOCK
```
**REGRA CRÍTICA — nada de downgrade silencioso.** Se o conselho deliberou "Claude Sonnet necessário", não mandar para um modelo gratuito sem validar:
```yaml
fallback: { allowed: true, minimum_capability_match: 0.85, minimum_quality: medium }
```
Se não atingir o mínimo: WAIT.

### 8.7 Execution Lease (contrato temporário) ＋ campos e invariantes
```yaml
execution_lease:
  lease_id: ...
  task_id: task_7842
  holder: { provider: claude, agent: security_specialist }   # = `executor:` no original
  capabilities: [application_security, vulnerability_management]
  permissions: { repository_read: true, repository_write: true, production_write: false }
  budget: { max_tokens: 30000, max_cost: 0.80, max_execution_time: 15m }
  issued_at: ...
  expires_at: ...
  status: active | expired | revoked | released
  revoked_at: ...?
  revoked_reason: ...?
  approval: { status: approved }
```
**Invariantes:**
- uma lease expirada ou revogada **não pode executar**;
- **1 task → 1 lease activa**;
- enquanto a lease está activa, 1 executa e os outros observam.

A lease resolve a concorrência e a auditabilidade, e é a **fronteira de autorização operacional**.

### 8.8 Execution Package (contexto para redirect)
Num redirect não se recomeça do zero:
```yaml
execution_package: { task, objective, decision, constraints, relevant_context, artifacts,
                     prior_findings, required_capabilities, policies, acceptance_criteria, budget }
```

### 8.9 Plano persistente
```
PLAN ├── Task A → DONE ├── Task B → WAITING (reason: quota) ├── Task C → EXECUTING └── Task D → BLOCKED
```
Um provider sem quota **não mata o plano**: `WAITING → RESUME → select provider → execute`. Melhor do que "erro → reiniciar tudo". Base que já existe: `waiting_external`, `paused_human_gate` e `paused_budget` são retomáveis (`engine.py:72`, `_RESUMABLE`; `META-AGENTS-PHASE-2.md:56`).

### 8.10 As duas "Fase 2" (não confundir) ⚠ CORRIGIDO
- **ADR-META-AGENTS §2.2:** Fase 2a, deliberação entre várias IAs.
- **Análise do Execution Broker:** Fase 2b, execução depois do conselho.
- ⚠ O original dizia "Ordem decidida: 2b primeiro". **A ordem NÃO foi decidida** (`META-AGENTS-PHASE-2.md:81`: "sem ordem decidida entre elas").
- **Pré-requisitos (ADR §4):** o ledger obrigatório, com a **C-2** corrida (`META-AGENTS-PHASE-2.md:82`), mais F0–F6 (§12).

### 8.11 Learning (estimado vs real)
```
Task → Estimate → Select → Execute → Actual usage → Compare → Ledger → Learning
```
Exemplo real: o C-1 foi estimado com `countTokens` entre 5 860 (floor) e 22 756 (ceiling) e gastou 11 760. Por estágio: independent 45%, peer 28%, synthesize 27% (`NAS:docs/ops/COUNCIL.md`). O par estimado/real é o início do Learning. O ledger regista `selected_executor`, `selection_reason`, `estimated_cost`, `selection_confidence` e `alternatives` (`META-AGENTS-PHASE-2.md:76`).

## 9. Pendentes e decisões (todas com recomendação)

### 9.1 Pista security (fechada)
| # | Item | Estado |
|---|---|---|
| SEC-1 | `repo_files` | ✅ merged (#58) |
| SEC-2 | gitleaks + semgrep | ✅ merged (#59) |
| SEC-2b | chave confirmada revogada (`rotated-2026-09-19`) | ✅ registado (#61; `OPEN-ITEMS.md:266`) |
| SEC-2c | actions fixadas por SHA | ✅ merged (#60) |
| SEC-2d | falsos positivos + triagem | ✅ merged (#61) |
| SEC-3 | red-team lab | `deferred` (`OPEN-ITEMS.md:260`) |

### 9.2 Pendentes operacionais ⚠ CORRIGIDO + ＋ NOVO
| # | Item | Repo | Tipo | Recomendada |
|---|---|---|---|---|
| **C-2** ⚠ | Correr `NAS:scripts/alter_token_usage_council_kinds.sql` no Supabase e depois actualizar `ANM:memory/token_usage.sql:12` (CHECK do `call_kind`) | ambos | **W prod** | **A:** o DEV corre antes de qualquer trabalho da Fase 2 (pré-requisito do ADR §4) |
| **J3 passos 3/5/6** ＋ | Verificação do ingest canónico, teste MCP real, apagar a t6 | NAS + Supabase | R / W (6) | Dentro do F0 (F0.3, F0.6, F0.12) |
| **L4-1b** | Teste real mínimo da L4 pela CLI | NAS | R/W L4 | **A:** o DEV faz |
| **R1** | `router eval` com Gemini real | NAS | R | **A:** o DEV faz |
| **B1-bis-C** | Encurtar skills/prompt-base | NAS | código | **A:** só depois de F0–F3 (§14.2) e com ordem |
| **Pack Claude** | Medir o custo em `revisor-codigo` e `guia-tdd` | NAS | R | **A:** medir antes de cortar |
| **Estado L4 no C-1** | Confirmar se o veredicto ficou `active` ou se correu com `--no-memory` | NAS | R | **A:** o DEV confirma |
| **Conselho security** | Medir no 1.º uso real | NAS | R | **A:** medir quando for usado |
| **L4-2** ＋ | Spike comparativo do mem0 (J11), só padrões | NAS | spike | **A:** depois do F3 (`OPEN-ITEMS.md:197`) |
| **L4-3** ＋ | Ligar o MCP de produção à L4 (ADR-M7) | ANM | código | **A:** depois do F5 (`OPEN-ITEMS.md:198`) |
| **AU-22** ＋ | O `knowledge_refs` dos planos não é lido; há campos mortos no plano | NAS | código | **A:** resolver no F0.5/F3 com o bloco `knowledge:` (S9), sem generalizar o `knowledge_refs` |
| **AU-44** ＋ | Reels/transcrições sem template nem ponte para o RAG | ambos | código | **A:** candidato do F1 (ligar o que existe) |
| **B7** ＋ | Expor `engine: langgraph` + `decision: edit` no MCP | NAS (tools_impl) | código | **A:** depois do F5; verificar o impacto no conector Claude.ai |
| **S20** ＋ | O bridge-worker na VM Oracle ainda usa a chave antiga e falha com 401 | VM | ops | **A:** o DEV faz (SSH, fora do âmbito do Claude) (`OPEN-ITEMS.md:32`) |
| **S27 / S19** ＋ | Oracle A1 reduzida para 2 OCPU/12 GB (**não verificado**; o S19 ainda diz 24 GB) | VM | ops | **A:** o DEV confirma na consola (`STATUS.md:41,46`) |
| **Ligação ingest MCP vs T6** ＋ | 2 pipelines de ingestão | ambos | decisão | ✅ D-EP9 = A (T6 canónico) |
| **Schema do plano do runner** ＋ | O `Plan.schema.json` (`docs/architecture/plan-execute/schemas/`) é de outro formato (exige `plan_id`/`goal`/`verify`…, :7) e só é usado em testes (`runner/tests/test_plan_schema_json.py`). Declara o bloco `knowledge` (:83), mas **não** declara `repo_files` nem `context` por passo, que os planos do runner já usam (`security-audit-demo.plan.yaml:56,73`). Os planos YAML do runner não têm schema validado | NAS | contrato | **A:** tratar no contract-first (§15.4) quando um passo do F0–F1 tocar no formato do plano; não bloqueia o F0 |
| **C-3** ＋ | Regra: não escalar `hitl: required` para o conselho | NAS | regra | Manter registado |
| **Ressalva B1-bis-R2** ＋ | −22% medido; **~−16% atribuível ao `opt`** (o copy escreveu −523 tokens, que contam 2×) | NAS | registo | Citar sempre as duas |
| **Dependabot** ＋ | `github-actions` mantido (`NAS:.github/dependabot.yml:76`); 0 PRs abertos (2026-10-03) | NAS | — | Não reabrir o pin por SHA |

### 9.3 Pendentes da Fase 2 (meta-agentes) ⚠ CORRIGIDO
| # | Item | Ordem |
|---|---|---|
| Execution Broker | Implementar | Depois de F0–F6 + C-2 |
| Execution Lease | Implementar | ⚠ O original dizia "Primeiro", o que contradiz a §12. **Por decidir** (D-EP5), sempre depois de F0–F6 + C-2 |
| Execution Package | Implementar | Junto da Lease |
| Learning | Implementar | Depois do Broker. O registo estimado/real pode começar já no ledger (custo zero) |

### 9.4 Pendentes da análise (P0/P1)
| # | Item | Fase |
|---|---|---|
| L5 revalidação (J3 3/5) + cobertura + consumidor | ⚠ antes "prova real", agora **revalidação** | **F0** |
| Golden set security | 10–20 perguntas, hit@k | **F0** |
| Contrato Universal Ingestion & Research | `ingest_document(source, options)` + discover/fetch | **F1** (documento; ver D-EP4) |
| MarkItDown spike | PDF, DOCX, XLSX → T6 | **F1** |
| Docling | Condicional | **F1b** |
| Crawl4AI vs `scrape.yml` | Web research | **F2** |
| Provenance formal + validity/conflicts + authority | Schema em camadas | **F3** |
| `marketing-capabilities.yaml` | 2.º domínio | **F4** |
| Validation E2E | Cadeia completa, run real | **F5** |
| Domínio de prova | Um só | **F6** |

### ＋ 9.5 Decisões do maestro sobre este plano (A/B/C, com recomendação)
**D-EP1..D-EP9: FECHADAS pelo maestro em 2026-10-03, todas na opção A** (`execution-plan-sources/11-maestro-decisao-v2.md`). A tabela fica com as opções para registo.

| ID | Decisão | A | B | C | Recomendada → **Decidida** |
|---|---|---|---|---|---|
| **D-EP1** | Gravar este documento | Gravar depois desta revisão, + arquivar as fontes tal como estão (§17) + OPEN-ITEMS F0–F6 | Gravar sem arquivar as fontes | Não gravar; manter os documentos soltos | **A** → ✅ A |
| **D-EP2** | Cobertura da lista de ingestão (escrita em produção através do workflow) | Só o pack de security agora (F0); os ~31 restantes decididos pack a pack no F3 | Os ~31 todos agora | Não mexer; ingestão manual | **A** (o F0 só precisa de security; os `imported-from-production/*` podem não ser conhecimento consumível) → ✅ A |
| **D-EP3** | Quando corre a C-2 | Já, pelo DEV (independente do F0) | Antes da Fase 2 | Nunca (manter o ledger local) | **A** (objectivo nº 1, tokens; custo baixo) → ✅ A: o DEV corre já |
| **D-EP4** | O contrato do F1 em paralelo com o F0? | Contrato (ADR, só documentação) em paralelo; spike de código só com o F0 verde | Tudo depois do F0 | Spike em paralelo também | **A** (concilia "em paralelo" com "F0 antes do MarkItDown") → ✅ A |
| **D-EP5** | Ordem 2a/2b da Fase 2 | Decidir só depois do F5 | 2b (Lease) primeiro: era a "ordem decidida" do original, com o argumento de que a Execution Lease resolve o caso real Grok + Claude em paralelo | 2a primeiro | **A** → ✅ A: nada de Broker/Lease antes de F0–F6 + C-2 |
| **D-EP6** | Colisão de nomes "E" (E1–E7 conectores de ingestão em `OPEN-ITEMS.md:20` vs E1–E11 decisões em `PLANO-DE-ACAO.md` §13.2, onde **E7 = validador areas.py**) | Neste plano, os conectores passam a ING-1..7, com nota; o histórico não se reescreve | Renomear em todos os documentos | Deixar | **A** → ✅ A: ING-1..7; E7 continua a ser o validador `areas.py` |
| **D-EP7** | `MASTER-PLAN.md` (2026-09-18, anterior à D1) | Marcar como histórico, a apontar para o EXECUTION-PLAN | Fundir no EXECUTION-PLAN | Deixar | **A** (padrão do `BOOTSTRAP.md:17-20`) → ✅ A |
| **D-EP8** | Domínio do F6 | Escolher só depois do F5, com uso real | Escolher já | Os 5 em paralelo | **A** → ✅ A |
| **D-EP9** | Duas pipelines de ingestão (T6 runner vs `ANM:.github/workflows/ingest.yml`) | O T6 é canónico; o `ingest.yml` fica para JSON do MCP e é documentado como legado/adaptador | Fundir já | Deixar sem regra | **A** (fundir fica para depois do F1) → ✅ A: T6 canónico; `ANM:.github/workflows/ingest.yml` = JSON MCP / legado documentado |

**Decisões em aberto (propostas da revisão pré-gravação, `execution-plan-sources/12-outra-ia-7-pontos-pre-gravacao.md`; mexem em regras permanentes do maestro, por isso não foram aplicadas):**

| ID | Decisão | A | B | C | Recomendada |
|---|---|---|---|---|---|
| **D-EP10** | Refinar as regras "commit + push no fim de cada passo" e "uma só verificação de CI por PR" | Passos `R` não geram commit; alterações relacionadas podem ir num commit lógico; uma verificação consolidada de CI por push (sem polling), e nova verificação só quando uma alteração posterior o exigir | Manter as regras literais | Só a parte dos commits | **A**: não muda a intenção (sem polling, sem commits vazios) e evita a ambiguidade quando um PR recebe uma correcção |
| **D-EP11** | Os passos `W-repo` do F0 (F0.5 bloco `knowledge:`, F0.7a golden set) entram na Etapa 2 ("F0 só passos R")? | Sim: são reversíveis e não tocam em produção; vão no mesmo PR da Etapa 2 | Não: Etapa 2 só `R`; os `W-repo` num PR seguinte, com ordem | Só o F0.7a | **A**: sem eles o F0 não pode ficar verde e não há risco de produção |

## 10. O que não fazer (anti-padrões)

### 10.1 Não fazer agora
- Implementar os 5 repos "porque estão no top".
- LightRAG ou Graphiti como serviço.
- Novos agentes de Legal, Medicine ou Trading.
- Segundo runtime (CrewAI/AutoGen como motor).
- Packs P2 em massa.
- Tectos do conselho abaixo de 80k no architecture (o tecto do conselho é o `budget.max_tokens` da área; `councils.yaml:12`).
- Downgrade silencioso de modelo.
- Migrar SQLite → Postgres só porque o conselho falou nisso.
- ＋ Disparar o conselho por omissão ("1 conselho ≈ 1 SEO"; só para decisões estruturais ou quando o router escala; `COUNCIL.md`/`BUDGET.md`).
- ＋ Escalar `hitl: required` para o conselho (C-3).
- ＋ Abrir o scheduler multi-IA na mesma sprint que o MarkItDown.
- ＋ Generalizar o `knowledge_refs` (opção B rejeitada no SEC-1).
- ＋ Propor Neo4j, GraphRAG MS ou SaaS pago "porque a pesquisa citou" (§14.3).
- ＋ Usar `packages/core` (TS arquivado, D1) como base de qualquer fase.

### 10.2 Não repetir
- **Agente por subárea:** usar capability + skill curta + plan.
- **Trading com `act` de execução:** research/risco partial; execução forbidden.
- **Medicina "pronta" por ter knowledge:** precisa de policy + provenance + HITL clínico.
- **Duplicar marketing num "Sales agent":** capability CRM quando houver tool.
- **Registos de conversa:** o que não está em processo perde-se.
- ＋ **Confiar no inventário sem revalidar:** o C8 "fechado" escrevia na tabela errada; o `CORE-MAPPING` classificou mal o `Orchestrator.ts` (§15.2).
- ＋ **Projectar tokens por caracteres:** medir com `usageMetadata`/`countTokens`; verificar o modo de cada braço antes de comparar; separar entrada de saída antes de atribuir causas.

### 10.3 Regra de ouro
| Evitar | Fazer |
|---|---|
| Um agente por subárea | Capability + skill curta + plan |
| Importar framework completo | Extrair o padrão |
| Novo runtime | Só o `plan_runner` |
| Agentes "wrappers" | Capacidades compostas |
| Packs P2 em massa | Um domínio de prova primeiro |
| ＋ Construir de novo | Ligar o que já existe (scrape, transcribe, knowledge_wiring) |

## 11. O teste definitivo
**Pergunta:** "Quanto custa adicionar um domínio novo?"
**Resposta correcta:**
```
domain-pack/
  knowledge/  skills/  capabilities/  plans/  policies/  validation/  tools?
```
(nos paths reais da §2.2).
**Resposta errada:** criar um novo agent, orchestrator, runtime, memória, RAG ou executor.
**Indicador:** Domain Onboarding Cost e Reuse Ratio (§15.9). **Se for preciso mexer no core, há uma abstracção incompleta.**

**Evolução explícita do core:** quando um domínio novo exige alterar o core, isso é evidência de que uma abstracção universal pode estar incompleta, e não uma proibição de a corrigir. A alteração é tratada como evolução do Universal Core:
1. ADR aprovado pelo maestro;
2. análise de impacto;
3. teste de regressão;
4. actualização do DOC (a alteração conta para o KPI).

O Claude Code não altera o core por iniciativa própria.

## 12. Instruções ao Claude Code ⚠ CORRIGIDO (em etapas)
Este documento é o baseline arquitectural consolidado.
1. **Etapa 0:** ✅ consolidado apresentado e aprovado (D-EP1..9 = A).
2. **Etapa 1 (este PR):** sem reinterpretar a arquitectura nem tomar decisões;
   - gravar em `NAS:docs/architecture/EXECUTION-PLAN.md`;
   - arquivar as fontes tal como foram escritas em `NAS:docs/architecture/execution-plan-sources/` (§17);
   - registar em `NAS:docs/initiatives/OPEN-ITEMS.md` os itens F0–F6 (§9.4), com dono e fase, e as decisões D-EP;
   - acrescentar o EXECUTION-PLAN ao `NAS:docs/architecture/BOOTSTRAP.md`;
   - marcar `MASTER-PLAN.md` como histórico (D-EP7);
   - commit + push no branch + PR; sem merge, sem `--force`, sem código do F1, sem escrita em produção.
3. **Etapa 2 (só depois do merge da Etapa 1, ou com ordem explícita):** F0, passos `R` (F0.1–F0.3 se houver autorização de SELECT, F0.8, F0.9; F0.6 e F0.7b pelo DEV). Os `W-repo` (F0.5, F0.7a) entram aqui se D-EP11 = A. PR, verificação de CI conforme as regras permanentes. **Não:** MarkItDown, Broker, agentes novos.
4. **Etapa 3:** os passos `W-prod` do F0. O F0.4 (ingest do pack de security) segue D-EP2 = A, já decidida; o efeito em produção só acontece no merge. O F0.12 é irreversível e cabe ao DEV.
5. **Não avançar** para o código do F1 sem o F0 verde (o contrato/ADR do F1 pode avançar em paralelo, D-EP4). **Não alterar** o core para adicionar domínios, salvo pela evolução explícita do core (§11).

**Ordem operacional imediata (maestro, 2026-10-03):**

| Quem | O quê |
|---|---|
| Claude Code | Etapa 1 (gravar o plano) |
| DEV | C-2 (SQL dos `council_*`) quando puder (D-EP3) |
| DEV | Confirmar Oracle S27 (12 vs 24 GB) e S20 (bridge 401) |
| Depois | F0 passos `R` → PR → só então F0.4 (ingest security, D-EP2 = A) |

**NÃO fazer:**
- reabrir decisões fechadas (D1/D2/D3, SEC, Dependabot);
- criar agentes sem capability;
- implementar a Fase 2 antes de F0–F6;
- escrever em produção sem decisão (no original: "não tocar em produção sem HITL");
- tocar no repo errado (§14.6).

**Regras permanentes:**
- Autonomia para APRIMORAR, nunca para CORTAR. Para cortar algo, propor em A/B/C com recomendada e esperar decisão.
- Toda a apresentação de opções vem com recomendação explícita.
- Sem merge, sem `--force`, sem polling; uma só verificação de CI por PR (refinamento proposto: D-EP10, em aberto).
- Evidência (ficheiro:linha) em cada afirmação.
- Commit + push no fim de cada passo (refinamento proposto: D-EP10, em aberto).
- **Regras de paragem:** decisão fora de D1–D3/ADR/PLANO; teste que não fica verde; escrita em produção (o SQL fica versionado, não executado); custo do conselho acima do tecto.
- Não expor dados sensíveis; nunca imprimir valores de segredos.

## 13. O que este documento cobre
- O que existe (Blocos A/B/C, L4, L5 com histórico C8→J3, security, CouncilSession, peças desligadas).
- A arquitectura (Universal Core → Domain Packs) e o mapa para os paths reais.
- As 4 categorias de repos e a ligação à FASE3/AUDIT-INGESTION.
- Os 3 ajustes de precisão.
- As matrizes P0, P1 e P2, corrigidas e com evidência.
- A matriz estendida, os 5 domínios como critério, os readiness gates e a ingestão como multiplicador.
- O roadmap F0–F6, com o F0 em checklist executável R/W.
- A Fase 2 (Broker, Lease, 5 decisões, orçamento preliminar, fallback, package, plano persistente, Learning).
- Os pendentes (operacionais, Fase 2, análise) e as decisões D-EP1..9.
- Os anti-padrões, o teste definitivo e as instruções em etapas.
- O adendo do Maestro (§14), a governança do próprio plano (§15), o registo de verificação (§16) e as fontes (§17).

### 13.1 Checklist de inclusão (o "Revisão — o que ficou incluído" do original, verificado)
- Matriz P0: as 16 capacidades com estado ✓ (§4.1); scorecard ✓ (§4.3, corrigido); lacunas ✓.
- Matriz P1: os 14 domínios (security, software, design, marketing, ops, finance, sales, legal, medicine, HR, manufacturing, engineering, education, games) ✓ (§5), + imobiliário (＋); scorecard ✓ (§5.15).
- Universal Core: arquitectura ✓, padrão do Domain Pack ✓, 4 categorias ✓, 3 ajustes ✓, teste definitivo ✓.
- Roadmap: F0–F6 com critérios de done ✓, a ordem ✓, o não-fazer ✓.
- Meta-agentes: CouncilSession Fase 1 ✓; Broker + Lease ✓; 5 estados/decisões, "5 budgets" (corrigido para 4 níveis + cost), fallback, Execution Package, plano persistente ✓; Learning ✓.
- Decisões: pendentes operacionais ✓, da Fase 2 ✓, da análise ✓.
- Anti-padrões, regra de ouro, instruções ao Claude Code ✓.

---

# PARTE 4 — ADENDO, GOVERNANÇA, VERIFICAÇÃO, FONTES

> Numeração: o Maestro chamou §14 ao seu adendo, e a outra IA chamou "14. GOVERNANÇA" à sua Parte 4. Para não colidir: **§14 = adendo do Maestro; §15 = governança** (os 14.1–14.11 da outra IA correspondem a 15.1–15.11).

## 14. Adendo do Maestro

### 14.1 Matriz P2
Ver §5.18.

### 14.2 Objectivo nº 1: tokens (métrica operacional)
- **Ledger obrigatório** em planos externos: `token_usage.jsonl` por run e Supabase `token_usage` (C-2 para os conselhos).
- **Tectos por área** (`NAS:config/areas.yaml`, B5-bis fase 1, "rever depois do B1-bis-C"): software 80k (:63), marketing 80k (:89), legal 40k (:98), ops 30k (:108), research 80k (:117), finance 40k (:127), gamedev 30k (:135), security 40k (:168), docs 80k (:176), horizontal 20k (:187).
- **Conselho:** o tecto é o da área (`config/councils.yaml:12`). Custo medido: 11 760 tokens por ronda (14,7% de 80k).
- **B1-bis-C** (optimizar skills e prompt-base): **depois de F0–F3**, nunca em paralelo com o MarkItDown.
- **Método de medição:** `usageMetadata`/`countTokens`; nunca projecções por caracteres.

### 14.3 Restrições de infra
- **Oracle:** ~12 GB RAM segundo o S27 (2 OCPU/12 GB, **não verificado**; o S19 ainda diz 24 GB). A VM tem S20 aberto.
- **Custos:** zero SaaS pago; zero custo recorrente; Supabase free tier.
- **Arquitectura:** local-first; o MCP é da casa (`agent-network-mcp`).
- **Licenças:** só MIT ou Apache.
- Repo público, por isso os minutos de GitHub Actions são grátis. Mesmo assim, não reactivar workflows pagos sem decisão explícita.
- **Consequência:** não propor Neo4j, GraphRAG MS, Unstructured com dependências de sistema pesadas, nem serviços pagos.

### 14.4 Paths canónicos (NAS, salvo indicação)
- `docs/architecture/adr/ADR-META-AGENTS.md`, `docs/architecture/META-AGENTS-PHASE-2.md`
- `docs/architecture/memory/contracts.md`, `docs/architecture/memory/rag-l5.md`, `docs/ops/MEMORY-L4.md`, `docs/ops/RAG-CANONICAL.md`, `docs/T6-INGEST-PIPELINE.md`
- `config/areas.yaml`, `config/security-capabilities.yaml`, `config/councils.yaml`
- `docs/audit/PLANO-DE-ACAO.md`, `docs/initiatives/OPEN-ITEMS.md`, `docs/initiatives/STATUS.md`, `docs/architecture/BOOTSTRAP.md`
- `docs/architecture/SECURITY-AGENTS.md`, `docs/ops/COUNCIL.md`, `docs/ops/BUDGET.md`, `docs/ops/WORKER-EXTERNAL.md`, `docs/ops/ROUTER.md`
- `docs/architecture/agents-audit/FASE3-AGENTES.md`, `docs/architecture/ingestion-audit/AUDIT-INGESTION.md`
- `scripts/ingest_delta.py`, `scripts/ingest_apply.py`, `.github/workflows/ingest-knowledge.yml`
- ANM: `memory/token_usage.sql`, `memory/schema.sql`, `lib/knowledge.js`, `lib/agents.js`, `.github/workflows/{ingest,scrape,transcribe}.yml`

### 14.5 Detalhe do SEC-1 (`repo_files`)
- Opt-in por passo e só de leitura.
- Paths explícitos (sem globs, sem `..`, sem absolutos; symlinks verificados).
- Denylist fixa (`.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa*`/`id_ecdsa*`/`id_ed25519*`/`id_dsa*`, `.npmrc`, `.pypirc`, `.netrc`, `credentials*`; dirs `secrets/`, `.git/`, `node_modules/`).
- Limite total de 50 KB; os binários ficam de fora (`NAS:runner/plan_runner/repo_files.py:34-41`).
- **Não generalizar o `knowledge_refs`** (opção B rejeitada).

### 14.6 Dual-repo
| Trabalho | Repo |
|---|---|
| Ledger C-2 (CHECK do `call_kind`), schema do `knowledge_chunks`/`match_knowledge`, `lib/knowledge.js`, workflows ingest/scrape/transcribe, conector Claude.ai | **agent-network-mcp** (alterações ao router e às tools MCP: verificar o impacto no conector Claude.ai, segundo o `ANM:CLAUDE.md`) |
| Todo o resto deste plano (runner, areas, capabilities, knowledge, planos, testes, docs) | **network-agents-setup** |

### 14.7 J11 / mem0
Spike J11 = **extrair padrões, não substituir a L4** (D3). A L4 própria permanece.

### 14.8 Dependabot
Manter `github-actions` no Dependabot (`NAS:.github/dependabot.yml:76`). Não reabrir o pin por SHA (SEC-2c).

## 15. Governança do próprio Execution Plan

### 15.1 Fonte de verdade e hierarquia documental
```
ARCHITECTURE   EXECUTION-PLAN.md         → o que deve acontecer e porquê
    ↓
DECISIONS      ADRs (docs/architecture/adr/, docs/audit/DECISAO-*.md)
    ↓
WORK           docs/initiatives/OPEN-ITEMS.md (+ docs/audit/PLANO-DE-ACAO.md para os itens da auditoria)
    ↓
EVIDENCE       commits / testes / CI / relatórios / queries
    ↓
CURRENT STATUS docs/initiatives/STATUS.md
```
- **O EXECUTION-PLAN não é uma segunda fonte de verdade do estado operacional.** Os estados citados aqui são uma fotografia datada, e o estado vivo está no STATUS/OPEN-ITEMS.
- **Índice:** o `NAS:docs/architecture/BOOTSTRAP.md` ("onde está cada fonte de verdade") passa a listar o EXECUTION-PLAN. Não se cria outro índice.
- **Histórico:** `docs/STATUS.md`, `STATUS-PROJETOS.md` e `STATUS-ECOSSISTEMA.md` são históricos (`BOOTSTRAP.md:9`). `MASTER-PLAN.md` passa a histórico se D-EP7 = A.
- **Overrides de auditoria:** quando uma auditoria posterior contradiz um mapa anterior, **prevalece a posterior** (ex.: `AUDIT-4-modulos.md:24` sobre `CORE-MAPPING.md`). Ainda assim, revalida-se (§15.2).

### 15.2 Regra de evidência
**DOCUMENTAÇÃO ≠ EVIDÊNCIA.** Uma afirmação REAL/READY/IMPLEMENTED/WORKING só vale com evidência verificável: ficheiro + linha, teste, execução real, CI, query, commit ou artefacto. **Sem evidência, o estado é `unverified`.**
Casos que fundamentam a regra: o C8 "fechado" escrevia na tabela errada (AU-19); o `CORE-MAPPING` classificou mal o `Orchestrator.ts`; o scorecard P0 do rascunho não batia com a própria tabela (§4.3).

### 15.3 Estados
| Estado | Significado |
|---|---|
| `verified` | A afirmação está comprovada **no âmbito e nas condições indicados pela evidência** (§15.2). Uma prova com stub/fake não comprova a execução real com provider externo. Exemplo: security pipeline = `verified` com Gemini falso, run real = `unverified`; a capability fica VALIDATED e só depois PROVEN (§15.7) |
| `partial` | Funciona em parte; o que falta está identificado |
| `unverified` | Existe, mas não há evidência actual (≠ gap) |
| `gap` | Não existe |
| `blocked` | Não pode avançar; o bloqueio e o dono estão identificados |
| `deferred` | Adiado de forma consciente, com motivo |

Exemplo: L5 = `partial + unverified`, não `gap`.

### 15.4 Contract-first
Toda a primitive, capability ou tool nova tem, antes de código: 1) contrato; 2) input schema; 3) output schema; 4) policy; 5) provenance; 6) estados de erro; 7) validação; 8) observabilidade; 9) comportamento de custo/budget; 10) fronteira de segurança.
Aplica-se a MarkItDown, Crawl4AI/scrape, OSV, Instructor, tools futuras e Execution Broker.

### 15.5 READ / PREPARE / ACT (universal)
| Nível | Política |
|---|---|
| READ | Pode ser automático |
| PREPARE | Policy/HITL conforme o domínio |
| ACT | Capability privilegiada + autorização + policy explícita + audit + HITL quando exigido |

Já existe no validador: os LEVELS read/prepare/act/lab; nenhuma capability `act` hoje; `lab` só em `deferred` (`NAS:runner/plan_runner/capabilities.py`).

### 15.6 Idempotência e retry
Toda a capability **mutável** declara: idempotency key, retry policy, side effects, e rollback/compensação quando for possível.
Caso típico: o executor respondeu, a rede caiu, não houve ACK e o retry executa duas vezes.
Base que já existe: os estágios do conselho são idempotentes (`council.json`, mapas por membro; `COUNCIL.md:38`); o ingest é por hash e incremental (T6).
Obrigatório antes de: escrita no GitHub, produção, financeiro, trading, CRM, manufacturing.

### 15.7 Maturidade de capability
`DRAFT → DECLARED → WIRED → EXECUTABLE → VALIDATED → PROVEN`
- **PROVEN** = evidência E2E com run real.
- Exemplo: `security.defensive_audit` hoje = **VALIDATED** (testes com Gemini falso); PROVEN depois do F5.
- `marketing.analytics` = DECLARED/GAP.
- O status do YAML (`implemented/partial/deferred/planned`) **não** é maturidade. O F4 decide se a maturidade entra no schema validado pelo E7.

### 15.8 Validade do conhecimento, conflitos e revogação
- Estados de uma fonte: `active | superseded | revoked | expired | deleted`. Corresponde aos `supersedes`/`expires_at` da L4.
- Precedência: versão, `effective_from`/`effective_until`, `supersedes`/`superseded_by`, jurisdição, autoridade.
- **Retrieval relevante ≠ retrieval válido.** O L5 não devolve três versões em conflito para o LLM decidir.
- Purge: uma fonte apagada do git sai do índice (T6 com purge; §15.12).
- Desenho no F3; implementação quando um domínio o exigir.

### 15.9 Domain Onboarding Cost (KPI) + Reuse Ratio
```
DOC = core files modified + core code changes + new infrastructure + new runtime
      + new persistence + new orchestration logic
Objectivo: DOC(core) = 0 para um Domain Pack normal.

Reuse Ratio = capabilities universais reutilizadas / total de capabilities necessárias
```
Também se regista o que o pack acrescenta (ex.: Legal = 5 knowledge packs, 3 skills, 2 tools, 1 capability file, 2 plans, 1 validation suite).
Medido no F4 (marketing) e obrigatório no F6.

### 15.10 Deprecação / sunset
Tudo o que deixa de existir (skills duplicadas, agentes antigos, adapters, frameworks experimentais, conhecimento obsoleto) regista `deprecated_at`, `replacement`, `reason` e `migration`.
Casos já existentes: o TS arquivado (D1); a `knowledge_chunks_t6` (J3 passo 6).

### 15.11 Regra de actualização do próprio plano
- O plano muda **só** por decisão registada (ADR ou D-EP) ou por correcção com evidência (§16 ganha uma linha).
- Cada fase concluída actualiza o estado no OPEN-ITEMS/STATUS, **não** aqui. Aqui muda só o que deve acontecer.
- Revisão obrigatória no fim de cada fase F0–F6: "o que este plano diz ainda bate com a evidência?"
- Toda a análise externa usada como fundamento de uma decisão é arquivada tal como foi escrita (§17), **quando o conteúdo integral estiver disponível**. Quando não estiver, regista-se a referência e a limitação, sem reconstruir nem inventar o conteúdo.

### 15.12 ＋ Evaluation & Quality (secção permanente) e regra T6
**Evaluation & Quality:** cada capability passa por: teste funcional → teste de qualidade → teste de custo → teste de segurança → regressão → evidência.
Ferramentas: o golden set em Python puro, por agora. O DeepEval (D3) e o Ragas (D4) estão bloqueados pelo S19 (`STATUS.md:41`). A comparação estimado/real vem do ledger (§8.11).

**Regra T6:** o Git é a fonte de verdade e o RAG/L5 é um índice derivado (`NAS:docs/T6-INGEST-PIPELINE.md`). Toda a ingestão é idempotente, incremental, baseada em hash, capaz de purge, auditável e reproduzível. **O F1 não cria uma pipeline paralela:** o MarkItDown alimenta o T6. A 2.ª pipeline (`ANM:.github/workflows/ingest.yml`) fica sob a decisão D-EP9.

## 16. Registo de verificação (correcções aplicadas ao original)
| # | Afirmação original | Correcção | Evidência |
|---|---|---|---|
| V1 | "A pista security está 100% fechada" | Pista SEC-1/SEC-2 fechada; o pack tem 4 partial e 1 deferred | `config/security-capabilities.yaml:45-78` |
| V2 | "Ledger `token_usage` no Supabase (com `council_*`)" | O CHECK recusa `council_*`; C-2 por correr | `ANM:memory/token_usage.sql:12`; `COUNCIL.md:42` |
| V3 | "Knowledge L5 — pgvector + ingest (prova incompleta)" / "C8 fechado" | O C8 escrevia na t6 (AU-19); o J3 reparou; os passos 3/5/6 estão abertos; o security não está na lista; não há consumidor | §1.2 quadro L5 |
| V4 | F0 = "provar o L5" | F0 = **revalidar** (J3 + cobertura + consumidor + golden set) | idem |
| V5 | Scorecard P0 "40–50% ready" | 3/10/3 em 16 linhas, ~19% ready; o scorecard misturava a P1 e omitia Audit | §4.3 |
| V6 | "Sales: keywords em ops" | 0 keywords de vendas, CRM ou lead | `config/areas.yaml` (contagem 0) |
| V7 | "Manufacturing: keywords" | 0 keywords (fabric/industr) | idem |
| V8 | Medicine sem nota de área | Sem área e sem keywords | idem |
| V9 | P1/P2 sem imobiliário | Acrescentado (fipezap ingerido) | `scripts/ingest_delta.py` (MANIFEST) |
| V10 | Marketing "ready" em quase todas as subcapacidades | Ready só na cadeia SEO (Gemini real); o resto em stub | B1-bis-R2; `seo-article-demo` |
| V11 | "Ordem decidida: 2b primeiro"; §9.3 "Lease: Primeiro" | Ordem por decidir; contradizia a §12 | `META-AGENTS-PHASE-2.md:81` |
| V12 | Estados DEFERRED/BLOCKED | Nomes canónicos DEFER/BLOCK | `META-AGENTS-PHASE-2.md:28-29` |
| V13 | "5 budgets" | 4 níveis no YAML (falta cost); modelo preliminar | §8.5 |
| V14 | "Caso real = security pipeline" | Relato do maestro, não registado no repo | `META-AGENTS-PHASE-2.md` |
| V15 | Layout `domain-pack/` | Não existe; mapa para os paths reais | §2.2 |
| V16 | Categoria 4 sem o LangGraph | O LangGraph é um engine opcional dentro do plan_runner | `engine: langgraph` |
| V17 | Packages/core "security MOCK" e "MetricsDashboard MOCK" como lacunas | TS arquivado (D1); MetricsDashboard = INCOMPLETO | `AUDIT-4-modulos.md:10,24,143` |
| V18 | Pesquisa de repos tratada como nova | Já feita (FASE3-AGENTES, AUDIT-INGESTION; itens de ingestão em OPEN-ITEMS:20) | §2.3 |
| V19 | F2 a partir do zero | `ANM:.github/workflows/scrape.yml` já existe | §1.2 |
| V20 | Ingestão única | 2 pipelines (T6 + `ANM:.github/workflows/ingest.yml`); transcrições fora do RAG (AU-44) | `AUDIT-6-lacunas.md:28`; `PLANO-DE-ACAO.md:329` |
| V21 | "Oracle ~12GB" sem ressalva | S27 não verificado; S19 diz 24 GB | `STATUS.md:41,46` |
| V22 | Pendentes em falta | Acrescentados: L4-2, L4-3, AU-22, AU-44, B7, S20, S27, J3 3/5/6, C-3, ressalva −16%/−22%, Dependabot (0 PRs abertos) | §9.2 |
| V23 | Colisão "E7" | E7 = validador; os conectores de ingestão também usam "E" | D-EP6 |
| V24 | Duas numerações §14 (Maestro vs outra IA) | §14 adendo; §15 governança | Parte 4 |
| V25 | C-2 = "Migração do ledger no `agent-network-mcp` (versionar `token_usage.sql`)" | Correr `scripts/alter_token_usage_council_kinds.sql` no Supabase **e depois** actualizar o CHECK em `ANM:memory/token_usage.sql:12` (escrita em produção) | `COUNCIL.md:31,42` |
| V27 | gitingest "ADOPT" (FASE3) e primitives sem fronteira de segurança | gitingest = ADAPT com reservas; pins e mitigações obrigatórios para MarkItDown, Crawl4AI e Docling | `ingestion-audit/AUDIT-INGESTION.md:69,148,189,249,304,309` |
| V28 | (omissão) contrato do plano do runner | O `Plan.schema.json` não é o contrato dos YAML do runner; `repo_files`/`context` não estão declarados | `Plan.schema.json:7,83`; `security-audit-demo.plan.yaml:56,73` |
| V26 | §12 "Gravar + OPEN-ITEMS + começar F0" de uma vez | Em etapas (revisão → gravar → F0 só leitura → passos W com decisão) | Regras de paragem; análise da outra IA |

### 16.2 Refinamentos pré-gravação (fonte 12, 7 pontos)
| # | Ponto | Aplicado? | Onde |
|---|---|---|---|
| R1 | Arquivar as fontes só quando o conteúdo integral existir | ✅ | §15.11, §17 |
| R2 | Taxonomia `R` / `W-repo` / `W-prod` no F0 | ✅ | §7 F0 |
| R3 | Commit só em unidades com alterações; commits lógicos | ⏸ regra permanente do maestro | D-EP10 |
| R4 | Verificação de CI sem polling, repetida só quando necessária | ⏸ regra permanente do maestro | D-EP10 |
| R5 | Golden set definido ≠ golden set medido (F0.7a/F0.7b) | ✅ | §7 F0 |
| R6 | `verified` com âmbito da prova (fake ≠ real) | ✅ | §15.3 |
| R7 | Alterar o core = evolução explícita com ADR (não é proibição absoluta) | ✅ (o Claude Code continua sem alterar o core por iniciativa própria) | §1.3, §11, §12, F6 |
| — | "Operacional ≠ completo" na §1.2 | ✅ (nota) | §1.2 |

### 16.1 Rastreabilidade: secção do original → secção deste documento
| Original (3 partes) | Aqui |
|---|---|
| Cabeçalho (natureza, base, destino, regra) | Cabeçalho + §17 |
| 1.1 / 1.2 / 1.3 | 1.1 / 1.2 (corrigido + quadro L5 + peças desligadas) / 1.3 |
| 2.1 diagrama | 2.1 (+ OCR/etc., scrape, yt-dlp) |
| 2.2 domain-pack | 2.2 (árvore original + mapa de paths) |
| 2.3 as 4 categorias | 2.3 (+ decisões FASE3) |
| 3 ajustes 1–3 + schema | 3 (+ status/supersedes) |
| 4 Matriz P0 + scorecard | 4.1–4.3 (+ 4.2 áreas, 4.4 implicações, 4.5 como ler) |
| 5.1–5.15 Matriz P1 | 5.1–5.15 (+ 5.16 ordem, 5.17 regra de ouro, 5.18 P2) |
| 6 Matriz estendida | 6.1 (+ 6.2 domínios, 6.3 gates, 6.4 ingestão) |
| 7 F0–F6 | 7 (F0 em checklist R/W; + 7.1 backlog) |
| 8.1–8.11 | 8.1–8.11 (8.4/8.5/8.7/8.10 corrigidos) |
| 9.1–9.4 | 9.1–9.4 (+ 9.5 decisões D-EP1..9) |
| 10.1–10.3 | 10.1–10.3 (+ itens novos) |
| 11 teste definitivo | 11 |
| 12 instruções | 12 (em etapas, V26) |
| 13 o que cobre + "Revisão — o que ficou incluído" | 13 + 13.1 |

## 17. Fontes (arquivadas tal como foram escritas)
Pasta: `NAS:docs/architecture/execution-plan-sources/`, um ficheiro por documento, sem edição de conteúdo (índice no `README.md` da pasta):
1. `01-processo-de-execucao-3-partes.md`: PROCESSO DE EXECUÇÃO — Universal Core (Partes 1–3).
2. `02-maestro-revisao-adendo-14.md`: revisão do Maestro (adendo §14).
3. `03-outra-ia-20-pontos-governanca.md`: análise da outra IA (20 pontos + Parte 4).
4. `04-matriz-p0.md`: Matriz P0 — `network-agents-setup`.
5. `05-matriz-p1.md`: Matriz P1 — capacidades profissionais.
6. `06-analise-dominios-de-prova.md`: "Com essas duas matrizes…" (domínios de prova, DOC, Reuse).
7. `07-analise-repos-primitives.md`: "Essa pesquisa está bem alinhada…" (4 categorias, primitives, ingestão).
8. `08-maestro-alinhamento-e-decisoes.md`: Maestro — alinhamento e decisões.
9. `09-baseline-3-ajustes.md`: baseline ("Eu trataria este documento como o baseline…").
10. **Não fornecido:** as análises Grok/GPT originais (os "7 documentos"). Não estão no repo nem foram fornecidas em forma completa. Fica registada a referência, sem reconstrução (§15.11).
11. `11-maestro-decisao-v2.md`: decisão do maestro (D-EP1..9 = A, instrução da Etapa 1).
12. `12-outra-ia-7-pontos-pre-gravacao.md`: revisão pré-gravação (7 pontos; §16.2).
13. O registo de verificação está neste documento (§16), não é um ficheiro à parte.

---
**FIM.** O estado vivo está em `docs/initiatives/STATUS.md` e `docs/initiatives/OPEN-ITEMS.md` (§15.1).
