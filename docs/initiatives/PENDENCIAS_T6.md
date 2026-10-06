# PENDENCIAS — Cadeia F1 → F6

Última atualização: 2026-10-06 07:00 UTC

> Ficheiro de estado da cadeia F1 → F6 (prompt do maestro de 2026-10-05). É lido no início de cada sessão e actualizado no fim de cada fase.
> **Não substitui** o `docs/initiatives/PENDENCIAS.md`, que continua a ser o documento único de estado do repo (tabela de 10 colunas, regra permanente). A linha do F1 no canónico aponta para este ficheiro.
> **Estados:** 🔒 Bloqueado · ⏳ Em curso · ✅ Concluído (critério de saída cumprido: PR aberto e CI verde; **o merge é do maestro**) · ❌ Bloqueado permanentemente.
> No canónico, um item só passa a FECHADO depois do merge (providência 2). Por isso o F1 lá continua EM CURSO enquanto os PRs desta cadeia estiverem abertos.

## Tabela de estado
| ID   | Descrição                                      | Estado     | Artefactos / Links                  | Critério de saída cumprido? |
|------|------------------------------------------------|------------|-------------------------------------|-----------------------------|
| T6a  | (pré-existente)                                | ✅ Merged  | PR #105 (merge `99b2cee`)           | Sim                         |
| T6b  | PDF funcional (fixture + teste + PR)           | ✅ Merged  | PR #106 (CI verde, 11 checks, incl. `test-ingest`); branch `feat/t6b-pdf-functional-fixture-and-test`; fixture `runner/tests/fixtures/ingest/pdf/` | Sim (merge pendente)        |
| T6c  | DOCX + XLSX                                    | ✅ Merged  | PR #107 (CI verde, 11 checks); branch `feat/t6c-docx-xlsx-fixtures-and-tests` (empilhado no #106); fixtures `runner/tests/fixtures/ingest/docx/` e `xlsx/` | Sim (merge pendente)        |
| T6d  | Segurança de entrada                           | ✅ Merged  | PR #108 (CI verde, 11 checks, depois da correcção do semgrep); branch `feat/t6d-input-security-guards` (empilhado no #107); `docs/ops/INGEST-DOCUMENT.md` | Sim (merge pendente)        |
| T6e  | Encaixe na pipeline T6                         | ✅ Merged  | PR #109 (CI verde, 11 checks, `test-ingest` com Postgres + pgvector); branch `feat/t6e-pipeline-integration` (empilhado no #108) | Sim (merge pendente)        |
| T6f  | Fecho F1 no PENDENCIAS                         | ✅ Merged  | PR #110 (CI verde, 11 checks); S5 em `scripts/ingest_benchmark.py`; decisões P-21 a P-23 no canónico | Sim        |
| F1b  | Docling (só se perda de estrutura)             | ✅ Não necessário | S5 (#110): listas e tabelas a 100%; só os headings do PDF se perdem; sem documentos reais do domínio no repo → regra do prompt: não necessário por agora. Reabre com PDFs reais (P-21 B) | Sim (saltada, regra do prompt) |
| F2   | Research web (Crawl4AI / scrape + provenance)  | ✅ Merged  | PR #111 (CI verde, 11 checks); `scripts/web_fetch.py`, `docs/ops/WEB-FETCH.md`; corrida real no pypi.org. No canónico, o F2 continua EM CURSO (`discover`, fallback JS, P-24, P-25) | Sim (critério do prompt) |
| F3   | Provenance no retrieve                         | ✅         | NAS #113 (migração aditiva, `match_knowledge_v2`, writer, 21 testes; CI verde em código, jobs de infra cancelados por falta de runner — ver comentário no #113) + MCP `agent-network-mcp` #19 (flag `KNOWLEDGE_RPC_V2`, 26 testes + 13 e2e). No canónico, o F3 continua EM CURSO (F3b, F3c) | Sim (critério do prompt; merge pendente) |
| F4   | marketing-capabilities.yaml                    | ✅         | PR #114: `config/marketing-capabilities.yaml` (18 capabilities), maturidade medida pelo E7, 32 testes. CI: test, test-rag, test-ingest, test-slow e gitleaks verdes; semgrep/CodeQL sem runner do GitHub (semgrep local: 0 achados) | Sim (merge pendente) |
| F5   | Validação E2E real (1 run Gemini)              | 🔒 aguarda run do DEV | Preparado: `docs/ops/F5-E2E-RUN.md` (comando único PowerShell, critérios), `scripts/f5_evidence.py` + 11 testes; branch `feat/f5-e2e-evidence` | Não (só o DEV tem as credenciais) |
| F6   | Hardening final + portfolio package            | 🔒         |                                     | Não                         |

## Histórico de fases
- 2026-10-05 · T6a · ✅ merged no #105 (`99b2cee`): esqueleto do `ingest_document` + adapter MarkItDown + 32 testes.
- 2026-10-05 · T6b · ✅ PR #106 aberto, CI verde: fixture PDF + gerador reprodutível + testes + job `test-ingest`.
- 2026-10-05 · T6c · ✅ PR #107 aberto, CI verde: fixtures DOCX e XLSX + geradores reprodutíveis + aviso `xlsx_nan_cells`.
- 2026-10-05 · T6d · ✅ PR #108 aberto, CI verde: processo filho com timeout e `RLIMIT_DATA` (medido), 22 testes de segurança, limites documentados.
- 2026-10-05 · T6e · ✅ PR #109 aberto, CI verde: `write_ingested` + `validate_ingested` (regra 3), `uri` relativo ao repo, caminho completo até ao `match_knowledge` provado contra Postgres + pgvector.
- 2026-10-06 · T6f · ✅ PR #110 aberto, CI verde: S5 (benchmark), balanço do "Done do F1", decisões P-21 a P-23. **F1 tecnicamente concluído**; no canónico fecha com o merge de #106 a #110.
- 2026-10-06 · F1b · ✅ não necessário por agora (regra do prompt: sem benchmark de perda material em documentos reais). Reabre com a P-21 B.
- 2026-10-06 · F2 · ✅ PR #111 aberto, CI verde: `fetch` com allowlist por redirect, robots.txt (RFC 9309), SSRF, tectos de bytes e de tempo, proveniência e saída pelo T6; 42 testes com servidor local; corrida real no pypi.org.
- 2026-10-06 · F4 · ✅ PR #114 aberto: marketing-capabilities.yaml (15 implemented, 1 partial, 2 planned) e maturidade medida pelo E7.
- 2026-10-06 · F5 · preparado (runbook + recolhedor + testes); 🔒 à espera do run real do DEV.
- 2026-10-06 · F3 (F3a) · ✅ NAS #113 + MCP #19 abertos: migração aditiva, `match_knowledge_v2` com filtros, writer com detecção da migração, MCP atrás de flag com fallback. Merge e SQL pelo DEV.
- 2026-10-05 19:09–19:22 UTC · **merge do maestro: #110, #111 e #112** (`main` `e10f772`). **F1 FECHADO** no canónico (§7). P-26 = A (2026-10-06): o F3 arranca.
- 2026-10-05 17:39–17:40 UTC · **merge do maestro: #106, #107, #108 e #109** (`main` `cd8aeb3`). CI da `main` verde (incluindo o `test-ingest`); `ingest-knowledge` com sucesso na última corrida (`cd8aeb3`; as 3 anteriores canceladas pela concorrência do workflow). Falta o #110 para o F1 fechar no canónico.

## Riscos / bloqueios abertos
- **F5 à espera do run real do DEV** (regra 9: as credenciais Gemini, MCP e bypass da Vercel são só do DEV). Tudo preparado em `docs/ops/F5-E2E-RUN.md`; a evidência cola-se na §4 desse ficheiro. Sem o F5, o F6 não arranca (e o F6 depende também da P-23).
- **CI do GitHub sem runners (2026-10-05, 19:50 UTC em diante):** jobs "not acquired by Runner" nos PRs #113 e #114; 1 re-execução feita em cada; o resto do CI e a validação local estão verdes.
- ~~**F3 bloqueado pela decisão P-26**~~ — **resolvido: P-26 = A (maestro, 2026-10-06)**; F3a em curso. O F3 muda o schema e a RPC `match_knowledge` de produção, que o MCP chama; o ADR propõe a via aditiva (`match_knowledge_v2`, a antiga intacta), com o SQL corrido pelo DEV. Sem a P-26 não há código do F3, e por isso também não há F4, F5 e F6 (cada fase exige a anterior concluída).
- **PR upstream no `microsoft/markitdown` (T6b, passo 6 do prompt): decisão do maestro.** Esta sessão só tem acesso aos repos `souzalrns/*`, e um PR num repo da Microsoft é uma acção pública em nome do DEV (fork, CLA da Microsoft, contacto com maintainers). Os PRs desta cadeia vão para a `main` da plataforma. As fixtures e os testes ficam prontos para servir de base a uma contribuição upstream, se o maestro a quiser.
- **F5 precisa de credenciais** (run real com Gemini): só o DEV o pode correr. O Claude prepara o comando e o molde de evidência.
- **F2, rede da sessão cloud:** a política de rede deste ambiente recusa (403 no proxy) `example.com`, `python.org` e `wikipedia.org`. A corrida real do F2 foi feita no `pypi.org`, que é acessível. Para outros hosts: acrescentá-los em Network access nas definições do ambiente (https://code.claude.com/docs/en/cloud-environments#network-access), ou correr na máquina do DEV.
- **F2, Crawl4AI:** o prompt diz "Crawl4AI preferencial"; a decisão canónica do F2 é "a partir do `scrape.yml`; Crawl4AI só se o superar". Seguiu-se a canónica: o F2a não instala o Crawl4AI.
- **F6 do prompt ≠ F6 do canónico.** No `PENDENCIAS.md`, o F6 é "UM domínio de prova, com o Domain Onboarding Cost medido; escolhido só depois do F5" (D-EP8). Neste ficheiro, F6 é "hardening final + portfolio package". Não se redefine um ID decidido: quando se chegar lá, o maestro escolhe (A/B/C) entre fazer os 2, renomear o do prompt ou fundi-los.
- **F4 do prompt ≈ F4 do canónico**, que também pede validação no E7 e maturidade de capability; e **F3 do canónico é mais largo** (validade/conflitos, source authority, golden set alargado, 33 ficheiros fora do MANIFEST). Cada fase cumpre o critério do prompt **e** regista o que falta do canónico, sem o cortar.
- **Escrita em produção:** pôr ficheiros convertidos no MANIFEST (`scripts/ingest_delta.py`) faz o merge escrever no Supabase. É decisão do maestro e fica fora do T6e (o T6e prova o encaixe contra Postgres local).

## Decisões de interpretação (registadas para revisão do maestro)
| Ponto do prompt | Conflito | Como foi feito |
|---|---|---|
| "criar PENDENCIAS.md com esta estrutura exacta" | Já existe o `PENDENCIAS.md` canónico, com 10 colunas fixas por regra permanente | Usada a alternativa que o próprio prompt prevê: `PENDENCIAS_T6.md` |
| "Abrir PR contra upstream/main" (T6b) | Sem acesso ao `microsoft/markitdown`; acção pública em nome do DEV | PR para a `main` da plataforma; o upstream fica como decisão (riscos, acima) |
| "Parar no fim de cada fase e esperar instrução" | O maestro, na mesma mensagem: "tens autonomia para prosseguir com tudo" | Fases em sequência, cada uma só com o critério da anterior cumprido; PRs empilhados, sem merge |
| "fixture em `tests/fixtures/pdf/`" | Os testes do repo vivem em `runner/tests/` | Caminho canónico: `runner/tests/fixtures/ingest/<formato>/` |
| "commits em inglês" | Os commits anteriores do repo estão em português | Commits desta cadeia em inglês (Conventional Commits); documentação em português, como o resto do repo |

## Mini-relatórios

```
FASE: T6b
DATA: 2026-10-05
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → ✅ (merge pendente, do maestro)
ARTEFACTOS:
- runner/tests/fixtures/ingest/pdf/simple_synthetic.pdf (1748 bytes, 1 página) + generate_simple_synthetic.py
- runner/requirements-fixtures.txt (fpdf2==2.8.9), runner/tests/optional_deps.py
- runner/tests/test_ingest_fixtures.py (5 testes); test_ingest_document.py passa a exigir as deps no CI
- .github/workflows/runner-tests.yml: job test-ingest + scripts/ingest_document.py no filtro paths
- docs/initiatives/PENDENCIAS_T6.md (novo), PENDENCIAS.md (linha F1), PROGRESS-SESSAO.md
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/106
- Branch: feat/t6b-pdf-functional-fixture-and-test
- Commits: 4598d9b, e256934, c84684e, 069aeb5
TESTES: pytest 602 passed, 10 skipped (sem extras); 37 passed com extras e INGEST_TEST_REQUIRED=1; CI 11/11 verde
PENDENCIAS.md: atualizado (sim: PENDENCIAS_T6.md e a linha F1 do canónico)
PRÓXIMO PASSO RECOMENDADO: T6c (DOCX + XLSX)
BLOQUEIOS: nenhum para a plataforma; o PR upstream no microsoft/markitdown fica como decisão do maestro
```

```
FASE: T6c
DATA: 2026-10-05
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → ✅ (merge pendente, do maestro; empilhado no #106)
ARTEFACTOS:
- runner/tests/fixtures/ingest/docx/simple_synthetic.docx (34652 bytes) + generate_simple_synthetic.py
- runner/tests/fixtures/ingest/xlsx/simple_synthetic.xlsx (5491 bytes) + generate_simple_synthetic.py
- runner/tests/fixtures/ingest/reproducible_zip.py; requirements-fixtures.txt (python-docx==1.2.0, openpyxl==3.1.5)
- scripts/ingest_document.py: aviso xlsx_nan_cells=<n> (conteúdo inalterado)
- runner/tests/test_ingest_fixtures.py (+10 testes), test_ingest_document.py (+3 de contrato)
- ADR §9 (achados), PENDENCIAS.md (linha F1), PROGRESS-SESSAO.md
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/107
- Branch: feat/t6c-docx-xlsx-fixtures-and-tests
- Commits: 4c93618, a76c525, 69f837b
TESTES: pytest 608 passed, 16 skipped (sem extras); 49 passed com extras e INGEST_TEST_REQUIRED=1; CI 11/11 verde
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: T6d (segurança de entrada: processo filho com limite de memória e timeout, testes negativos)
BLOQUEIOS: nenhum
```

```
FASE: T6d
DATA: 2026-10-05
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → ✅ (merge pendente, do maestro; empilhado no #107)
ARTEFACTOS:
- scripts/ingest_document.py: isolated_converter (processo filho, timeout 60 s, RLIMIT_DATA 1 GiB em Linux),
  códigos timeout e memory_limit, aviso memory_limit_unavailable, ZIP corrompido ≠ formato errado,
  mensagem certa quando o markitdown não carrega, CLI --timeout-s / --memory-limit-mb
- runner/tests/test_ingest_security.py (22 testes; alvos de abuso injectados no filho)
- docs/ops/INGEST-DOCUMENT.md (limites, medição, códigos, avisos, comportamento por formato)
- ADR §9 (extensão do contrato), job test-ingest inclui os testes de segurança
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/108
- Branch: feat/t6d-input-security-guards
- Commits: 3c8bdba, ecfdefc, 052b096, eced32a (semgrep), fb0a49e
TESTES: pytest 629 passed, 18 skipped (sem extras); 72 passed com extras e INGEST_TEST_REQUIRED=1; CI 11/11 verde
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: T6e (encaixe na pipeline T6)
BLOQUEIOS: nenhum. Nota: o 1.º push teve o semgrep vermelho (4 achados, 2 deles anteriores ao T6d);
corrigido na raiz e verificado localmente com a versão e as regras do CI antes do 2.º push.
```

```
FASE: T6e
DATA: 2026-10-05
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → ✅ (merge pendente, do maestro; empilhado no #108)
ARTEFACTOS:
- scripts/ingest_document.py: write_ingested (.md byte a byte + .meta.yaml), validate_ingested (regra 3 do ADR),
  source_uri (relativo ao repo; external:<nome> + uri_outside_repo), slugify, CLI --out-dir/--name/--overwrite
- runner/tests/test_ingest_pipeline.py (14), runner/tests/test_ingest_pipeline_rag.py (4, Postgres + pgvector)
- job test-ingest com o serviço pgvector/pgvector:pg16 e RAG_TEST_REQUIRED=1
- docs/ops/INGEST-DOCUMENT.md §7, ADR §9, PENDENCIAS.md (linha F1), PROGRESS-SESSAO.md
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/109
- Branch: feat/t6e-pipeline-integration
- Commits: bb8ae7a, 36dc64e, 67f326b, fe4cc11
TESTES: pytest 639 passed, 26 skipped (sem extras); 90 passed com MarkItDown + Postgres (modo obrigatório); semgrep 0; CI 11/11 verde
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: T6f (fecho do F1, com as medições do S5)
BLOQUEIOS: nenhum. A entrada no MANIFEST (escrita em produção) fica para o maestro, como manda o ADR.
```

```
FASE: T6f (fecho do F1) + F1b
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: T6f ⏳ → ✅; F1b 🔒 → ✅ não necessário (regra do prompt)
ARTEFACTOS:
- scripts/ingest_benchmark.py (S5) + teste no CI; docs/ops/INGEST-DOCUMENT.md §8
- ADR §9: balanço do "Done do F1"; PENDENCIAS.md: P-21 (F1b), P-22 (upstream), P-23 (F6), F1 e F1b actualizados
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/110
- Branch: docs/t6f-close-f1
- Commits: b25211d, 9b8d986
TESTES: pytest 639 passed, 27 skipped (sem extras); 91 passed com MarkItDown + Postgres; semgrep 0; CI 11/11 verde
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: F2 (research web: fetch com provenance)
BLOQUEIOS: nenhum para o código. Para produção: merge de #106→#110 e a entrada no MANIFEST (maestro).
```

## Fecho do F1: PRs, fixtures e riscos

**PRs da cadeia** (todos abertos com CI verde, empilhados; ordem de merge #106 → #107 → #108 → #109 → #110):

| PR | Fase | O quê |
|---|---|---|
| #105 (merged) | T6a | Esqueleto do `ingest_document` + adapter MarkItDown |
| #106 | T6b | Fixture PDF + gerador reprodutível + job `test-ingest` |
| #107 | T6c | Fixtures DOCX e XLSX + aviso `xlsx_nan_cells` |
| #108 | T6d | Processo filho com timeout e `RLIMIT_DATA` (medido) + 22 testes de segurança |
| #109 | T6e | Saída para o T6 com proveniência + E2E contra Postgres + pgvector |
| #110 | T6f | Benchmark S5, fecho do F1, P-21 a P-23 |

**Fixtures** (`runner/tests/fixtures/ingest/`, sintéticas, reprodutíveis): `pdf/simple_synthetic.pdf` (1748 B), `docx/simple_synthetic.docx` (34 652 B) e `xlsx/simple_synthetic.xlsx` (5491 B), cada uma com o gerador ao lado; os pins estão em `runner/requirements-fixtures.txt`.

**Riscos que restam:**
- A 1.ª ingestão real de um documento convertido escreve em produção no merge (entrada no MANIFEST): é decisão do maestro.
- O título dos metadados de PDF e DOCX não é lido (aviso `title_from_filename`). O F3 pode ler os metadados à parte.
- Os PDFs longos são cortados por tamanho, e não por secções, porque o PDF não tem headings. Isto reabre o F1b com documentos reais (P-21 B).
- Fora de Linux não há limite de memória (aviso `memory_limit_unavailable`); o timeout vale na mesma.
- Antes de subir a versão do MarkItDown, ver `github.com/microsoft/markitdown/security` (ADR §5, mitigação 4).

**Relatório executivo (portfólio, 10 linhas):**
1. Construí a ingestão de documentos (PDF, DOCX, XLSX) de uma plataforma multi-agente com RAG, por cima do MarkItDown, sem pipeline paralela.
2. O contrato vem de um ADR: `ingest_document(path) → {content, source_meta, warnings}`, com proveniência obrigatória e erros tipados.
3. Encontrei e corrigi 2 falhas silenciosas do MarkItDown: PDFs ilegíveis ou com a extensão errada voltavam como "Markdown" em bruto.
4. Segurança: recusa de bombas ZIP sem descomprimir, e conversão num processo filho com timeout e limite de memória do SO.
5. O limite de memória foi medido: o `RLIMIT_AS` não é monótono com o onnxruntime, por isso escolhi o `RLIMIT_DATA` com 1 GiB.
6. As fixtures sintéticas são reprodutíveis byte a byte (PDF) ou entrada a entrada (DOCX/XLSX), com o gerador versionado.
7. O caminho completo, documento → T6 real → pgvector → retrieve, está provado no CI, e o hash do T6 é o da proveniência.
8. O CI tem um job dedicado que falha (em vez de dar skip) se faltar o conversor ou a base de dados.
9. As medições (S5) mostram listas e tabelas a 100%, e só os headings de PDF perdidos; isso orientou a decisão de não adoptar já o Docling.
10. 6 PRs pequenos e empilhados, cada um com CI verde e relatório, sem tocar em produção.

```
FASE: F2 (F2a: fetch)
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: 🔒 → ⏳ → ✅ (critério do prompt; merge pendente, do maestro; empilhado no #110)
ARTEFACTOS:
- scripts/web_fetch.py (fetch + CLI), runner/tests/test_web_fetch.py (42, servidor HTTP local)
- scripts/ingest_document.py: HtmlConverter com strict=True; scripts/ingest_benchmark.py: reutiliza o módulo carregado
- docs/ops/WEB-FETCH.md (protecções, códigos, corrida real, fora do âmbito); ADR §9; P-24 e P-25 no canónico
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/111
- Branch: feat/f2-web-fetch-provenance
- Commits: aea5fe6, e5c2601, 17c1144, 2989a48, 65a1c6c
TESTES: pytest 679 passed, 29 skipped (sem extras); 133 passed com MarkItDown + Postgres; semgrep 0; CI 11/11 verde
CORRIDA REAL: pypi.org (3 páginas 200; robots.txt real proíbe /simple/ → recusado; domínio fora da allowlist → recusado).
  example.com, python.org e wikipedia.org: 403 no proxy da sessão (política de rede do ambiente).
PENDENCIAS.md: atualizado (sim; F2 → EM CURSO no canónico)
PRÓXIMO PASSO RECOMENDADO: F3 (provenance no retrieve)
BLOQUEIOS: nenhum para o F2a. Decisões P-24 e P-25 pendentes (não bloqueiam).
```

```
FASE: F3 (proveniência no retrieve)
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → 🔒 aguarda P-26
ARTEFACTOS:
- docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md (proposta: opções A/B/C, contrato do F3a, F3b/F3c)
- PENDENCIAS.md: P-26 no §10 (26 decisões), linha do F3 com o bloqueio
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/112 (só o ADR, sem código)
- Branch: docs/f3-provenance-adr
TESTES: n/a (só documentação)
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: o maestro decide a P-26 (recomendada A). Com A: F3a em 2 PRs (NAS: SQL versionado + v2 + ingest_apply lê o .meta.yaml + testes Postgres; MCP: retrieve_knowledge na v2, depois do DEV correr o SQL)
BLOQUEIOS: P-26 (schema e RPC de produção). Regra 9 do prompt: documentado e parado.
```

```
FASE: F3 (F3a: proveniência no retrieve)
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: 🔒 aguarda P-26 → ⏳ → ✅ (P-26 = A; merge e SQL pendentes, do maestro/DEV)
ARTEFACTOS:
- NAS: scripts/migrations/f3_provenance_retrieve.sql (aditiva, idempotente), runner/plan_runner/provenance.py,
  supabase_writer (has_f3_columns, proveniência, locator, update_source_provenance), ingest_apply (INVALID_META, META_UPDATED),
  runner/tests/test_f3_provenance.py (11, Postgres) + test_provenance.py (10), passo no job test-rag, runbook RAG-CANONICAL.md § F3a
- MCP: lib/knowledge.js (KNOWLEDGE_RPC_V2, sanitizeKnowledgeFilters, hits com proveniência, fallback PGRST202),
  tests/knowledgeV2.test.mjs (7), docs/RAG_GROUNDING.md, .env.example
LINKS:
- PR NAS: https://github.com/souzalrns/network-agents-setup/pull/113
- PR MCP: https://github.com/souzalrns/agent-network-mcp/pull/19
- Branches: feat/f3-provenance-retrieve; claude/reels-analysis-tools-access-hwudk9
TESTES: NAS pytest 700 passed (sem extras), 144 passed (com extras + Postgres); MCP npm test 26/26, e2e 13/13;
  CI #113: todos os checks verdes em pelo menos 1 das 2 cabeças (delta = só docs); a última teve jobs sem runner do GitHub
PENDENCIAS.md: atualizado (sim)
PRÓXIMO PASSO RECOMENDADO: F4 (marketing-capabilities.yaml)
BLOQUEIOS: nenhum no código. Produção: merge #113 → o DEV corre o SQL → merge MCP #19 → KNOWLEDGE_RPC_V2=1.
```

```
FASE: F4 (marketing-capabilities.yaml)
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: 🔒 → ⏳ → ✅ (merge pendente; empilhado no #113)
ARTEFACTOS:
- config/marketing-capabilities.yaml (18: 15 implemented, 1 partial, 2 planned; policy prepare + HITL)
- runner/plan_runner/capabilities.py: maturidade medida (implemented exige plano do runner com a action)
- runner/tests/test_capabilities.py (32)
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/114
- Branch: feat/f4-marketing-capabilities
- Commits: 475dc52, 1a4ee6d
TESTES: pytest 704 passed; planos reais em stub 21 passed; E7 "2 ficheiro(s) de capabilities válido(s)"; semgrep 0
PENDENCIAS.md: atualizado (sim; F4 EM CURSO no canónico)
PRÓXIMO PASSO RECOMENDADO: F5 (run real E2E, do DEV)
BLOQUEIOS: nenhum no código; CI parcialmente sem runners do GitHub (infraestrutura)
```

```
FASE: F5 (validação E2E real)
DATA: 2026-10-06
ESTADO ANTERIOR → NOVO ESTADO: 🔒 → 🔒 aguarda run do DEV (preparado)
ARTEFACTOS:
- docs/ops/F5-E2E-RUN.md (o que prova, comando único PowerShell, critérios, molde de evidência, se falhar)
- scripts/f5_evidence.py (veredicto PASSOU/INCOMPLETO sem segredos nem conteúdo) + runner/tests/test_f5_evidence.py (11)
- .gitignore: pilots/f5-run/ e pilots/test-f5-*/
LINKS:
- Branch: feat/f5-e2e-evidence (PR a abrir, empilhado no #114)
TESTES: test_f5_evidence 11 passed (inclui: um run stub real dá INCOMPLETO; segredos plantados não aparecem)
PENDENCIAS.md: atualizado (sim; F5 BLOQUEADO com o bloqueio exacto)
PRÓXIMO PASSO RECOMENDADO: o DEV corre os comandos da §2 do F5-E2E-RUN.md e cola a saída na §4
BLOQUEIOS: credenciais (só o DEV) — regra 9: documentado e parado
```
