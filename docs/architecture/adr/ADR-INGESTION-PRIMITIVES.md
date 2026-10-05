# ADR-INGESTION-PRIMITIVES — Universal Ingestion & Research Primitives (F1)

| Campo | Valor |
|---|---|
| **ID** | ADR-INGESTION-PRIMITIVES |
| **Estado** | **Aceite** (`PENDENCIAS.md` §10 P-13 = A, maestro, 2026-10-03, com consulta cruzada a uma 2.ª IA). Só contrato: nenhum código (D-EP4). O spike (§9) só arranca com o F0 verde |
| **Data** | 2026-10-03 |
| **Decisores** | Maestro (aceita ou rejeita); redigido pelo Claude |
| **Item** | F1 em `docs/initiatives/PENDENCIAS.md` (alias ING-2) |
| **Fontes** | EXECUTION-PLAN §3 (ajustes 1–3), §7 F1/F1b/F2, §15.4 (contract-first), §15.12 (regra T6); `docs/architecture/ingestion-audit/AUDIT-INGESTION.md:140-156` (MarkItDown); D-EP4, D-EP9 |

## 1. Contexto

- O L5 já tem uma pipeline canónica: o T6. O Git é a fonte de verdade e o RAG é um índice derivado.
  - Escreve na `knowledge_chunks` (`scripts/ingest_apply.py`, `runner/plan_runner/supabase_writer.py`).
  - É incremental por `content_hash`; foi provado em produção na corrida #163 do `ingest-knowledge` (`unchanged=39`).
  - O DDL canónico está em `scripts/rag_schema.sql` (AU-11).
- Hoje só entra **Markdown versionado no MANIFEST** (`scripts/ingest_delta.py`). PDF, DOCX, XLSX e conteúdo web não têm caminho.
- A 2.ª pipeline (`ANM:.github/workflows/ingest.yml`) é legado/adaptador (D-EP9 = A, documentado no PR MCP #13).
- A provenance actual perde-se no retrieve: só chega o `source` (L5F0 §1, F0.8).

## 2. Decisão

Definir 2 primitivas com contrato estável e tratar cada ferramenta (MarkItDown, Docling, Crawl4AI, `scrape.yml`) como **adapter**, nunca como o contrato:

```
ingest_document(source, options) -> {content, source_meta, artifacts?, warnings?}
    source = path | url | bytes | connector_ref

discover(query, options) -> [candidate {uri, title?, snippet?, score?}]
fetch(uri, limits)       -> {content, source_meta, artifacts?, warnings?}
```

**Regras que este ADR fixa:**
1. **Não substitui o `plan_runner`** nem o worker de passos: as primitivas são chamadas por scripts/CLI (`scripts/`) ou por uma tool, e alimentam o T6 (EXECUTION-PLAN §7 F1.3).
2. **Regra T6 (§15.12):** o `content` de `ingest_document`/`fetch` entra no L5 **pelo T6** (chunker, `content_hash`, `knowledge_sources`, `replace_chunks`). Não há pipeline paralela.
3. **Provenance mínima obrigatória** (§3, ajuste 3): nenhum conteúdo entra no L5 sem `source_meta` válido (§4).
4. **RESEARCH ≠ WEB SCRAPING** (§3, ajuste 2): `discover` e `fetch` são separados; o Crawl4AI ou o `scrape.yml` são implementações do `fetch`.

## 3. Contrato (os 10 itens do contract-first, §15.4)

| # | Item | `ingest_document` | `discover` / `fetch` |
|---|---|---|---|
| 1 | **Contrato** | §2 acima | §2 acima |
| 2 | **Input schema** | `source`: `{kind: path\|url\|bytes\|connector_ref, value}`; `options`: `{agent_id, kb, priority, mime?, max_bytes, title?, document_type?}` | `discover`: `{query, max_results ≤ 20, allowlist?}`; `fetch`: `{uri, limits: {timeout_s, max_bytes, max_pages, robots: true}}` |
| 3 | **Output schema** | `{content: markdown, source_meta (§4), artifacts: [{path, kind}], warnings: [str]}` | `discover`: lista de candidatos; `fetch`: igual ao `ingest_document` |
| 4 | **Policy** | Nível **PREPARE** (§15.5): escreve no L5 só pelo T6, e o T6 só escreve no merge/CI (como hoje) | `discover`: READ. `fetch`: PREPARE, com allowlist por área |
| 5 | **Provenance** | `source_meta` obrigatório (§4); a cadeia SOURCE→DOCUMENT→CONTENT→CHUNK mantém-se no T6 | Igual, com `retrieved_at` e `content_hash` do conteúdo normalizado |
| 6 | **Estados de erro** | `unsupported_format`, `too_large`, `decompression_limit`, `conversion_failed`, `empty_content`, `missing_provenance` (cada um em `warnings` ou como excepção tipada; nunca conteúdo parcial silencioso) | `blocked_by_allowlist`, `robots_disallowed`, `timeout`, `http_error`, `too_large`, `empty_content` |
| 7 | **Validação** | Golden set por formato (PDF textual, DOCX, XLSX): texto esperado presente, tabelas preservadas, `source_meta` completo; mesmo padrão do `config/l5-golden-security.yaml` | Fixtures HTML locais (sem rede no CI) |
| 8 | **Observabilidade** | Evento por documento: `{source.uri, mime, bytes_in, chars_out, warnings, duration_ms, adapter, adapter_version}` | Igual + `status_code`, `final_url` |
| 9 | **Custo / budget** | A conversão é local e grátis; os embeddings passam pelo orçamento do T6 (`--max-chunks`, hoje 50 por corrida) | `max_pages` e `max_bytes` por pedido; sem serviços pagos (custo zero, EXECUTION-PLAN:39) |
| 10 | **Fronteira de segurança** | §5 | Allowlist, timeout, `robots: true`, sem servidor exposto; Crawl4AI só com pin `>=0.9.3` e como biblioteca local (EXECUTION-PLAN §7 F2.3) |

## 4. `source_meta` (schema mínimo, §3 ajuste 3)

```yaml
uri: str                 # path no git, URL ou connector_ref
title: str
document_type: str       # pdf | docx | xlsx | pptx | html | md
retrieved_at: datetime
content_hash: str        # sha256 do content normalizado (o mesmo que o T6 usa)
publisher: str?
author: str?
jurisdiction: str?
published_at: datetime?
effective_from: datetime?
effective_until: datetime?
version: str?
authority: str?
status: active | superseded | revoked | expired | deleted   # §15.8
supersedes: ref?
superseded_by: ref?
```

**Onde fica:**
- Hoje, a `knowledge_sources` guarda `source_path`, `content_hash`, `git_sha`, `last_ingested_at` e `size_bytes` (`scripts/rag_schema.sql`).
- Os campos novos (`title`, `document_type`, `status`, …) ficam para o **F3**, que estende o contrato L5 (EXECUTION-PLAN §3: "o F3 **estende-o**, não cria outro").
- No spike, o `source_meta` é escrito num ficheiro lado a lado (`<doc>.meta.yaml`). **Não se altera schema de produção.**

## 5. Fronteira de segurança do adapter MarkItDown (`AUDIT-INGESTION.md:140-156`)

Classificação de risco: **MÉDIO** (zip bomb sem fix a caminho). Mitigações **obrigatórias**:
1. Pin `markitdown>=0.1.4` (CVE-2025-64512 explorável abaixo disso).
2. Antes de invocar o MarkItDown em ZIP/DOCX/XLSX/PPTX/EPUB (são todos ZIP): verificar o `ZipInfo.file_size` de cada entrada e o total descomprimido, e **recusar acima de um tecto** (proposta: 200 MB; `decompression_limit`).
3. Converter num **processo filho com limite de memória do SO** (`resource.setrlimit` / `ulimit`), independente do código do MarkItDown.
4. Antes de cada subida de versão, ver `github.com/microsoft/markitdown/security`.
5. Só ficheiros do repo ou entregues pelo DEV; `url` e `connector_ref` ficam fora do spike.

## 6. Relação com o que existe

| Peça | Relação |
|---|---|
| T6 (`ingest_apply.py`, MANIFEST) | **Destino** do `content`. O spike acrescenta um passo antes: documento → Markdown + `source_meta` → ficheiro em `docs/knowledge/…` → MANIFEST → T6 |
| `ANM:.github/workflows/ingest.yml` | Legado (D-EP9 = A). Não recebe estas primitivas |
| `ANM:.github/workflows/scrape.yml` | Implementação actual do `fetch` (F2). O Crawl4AI só entra se a superar, com evidência |
| AU-44 (reels), `ANM:transcripts` | Candidatos a `connector_ref` (decisão do maestro, EXECUTION-PLAN §7 F1.5); fora do spike |
| Docling (F1b) | Só se o MarkItDown perder estrutura que faz falta, com benchmark escrito |

## 7. Alternativas consideradas

| | Alternativa | Porque não |
|---|---|---|
| A | MarkItDown como contrato (sem primitiva) | Acopla o L5 a uma ferramenta; trocar por Docling obrigaria a mudar os consumidores (§3, ajuste 1) |
| B | Pipeline nova MarkItDown → pgvector | Viola a regra T6 (§15.12): perde hash, purge e reprodutibilidade |
| C | Docling desde o início | Mais pesado; o F1b só o aceita com benchmark |

## 8. Consequências

- **Positivas:** os formatos novos entram sem tocar no retrieve nem no worker; a provenance passa a ter um schema; os adapters são trocáveis.
- **Negativas/custos:** dependência nova (`markitdown`) com risco MÉDIO controlado por §5; os campos novos de `source_meta` só são persistidos no F3.

## 9. Plano do spike (NÃO executado; só com o F0 verde e este ADR aceite)

| Passo | O quê | Tipo |
|---|---|---|
| S1 | `scripts/ingest_document.py`: `ingest_document(path)` com o adapter MarkItDown e as 5 mitigações do §5 (pin em `runner/requirements.txt` ou num `requirements-ingest.txt` à parte) | W-repo |
| S2 | 3 documentos de teste **sintéticos** versionados (PDF textual, DOCX, XLSX) + golden por formato (texto e tabela esperados) | W-repo |
| S3 | Testes: zip bomb sintético → `decompression_limit`; ficheiro acima do `max_bytes` → `too_large`; formato desconhecido → `unsupported_format` | W-repo |
| S4 | Saída → `docs/knowledge/ingested/<nome>.md` + `<nome>.meta.yaml` → entrada no MANIFEST → T6 (o merge dispara o ingest: **W-prod, decisão do maestro**) | W-repo → W-prod no merge |
| S5 | Medir: chars por formato, tabelas preservadas (sim/não), tempo, memória máxima | R |

**Estado do spike (2026-10-05, T6a, branch `feat/F1-markitdown-spike`):** o gate M1 fechou (decisão do maestro). O S1 está feito em esqueleto: `scripts/ingest_document.py`, pin em `runner/requirements-ingest.txt` e `runner/tests/test_ingest_document.py`. Ficam para o T6b: a mitigação 3 (processo filho com limite de memória), o evento de observabilidade (§3, item 8) e o S2 a S5.

**T6d (2026-10-05): mitigação 3 feita.**
- A conversão corre num processo filho, com timeout e, em Linux, `RLIMIT_DATA` (1 GiB por omissão).
- O `RLIMIT_AS` foi medido e recusado: não é monótono com o onnxruntime do magika (768 MiB falhava sempre e 512 MiB só às vezes).
- **Extensão do contrato (§3, item 6):** 2 códigos novos no `ingest_document`, `timeout` (o mesmo nome do `fetch`) e `memory_limit`.
- Fora de Linux não há limite de memória, e isso fica no aviso `memory_limit_unavailable`.
- Os limites, os códigos e os avisos estão em `docs/ops/INGEST-DOCUMENT.md`.

**T6e (2026-10-05): S4 feito, sem a entrada no MANIFEST.**
- `write_ingested` grava `<nome>.md` (o `content` byte a byte) e `<nome>.meta.yaml`.
- `validate_ingested` aplica a regra 3 a qualquer entrada do MANIFEST em `docs/knowledge/ingested/`.
- O caminho completo (conversão → `apply_one` real → `match_knowledge`) está provado contra Postgres com pgvector no CI. O `content_hash` do T6 é o do `source_meta`.
- Pôr ficheiros no MANIFEST continua a ser decisão do maestro (W-prod).

Achados do T6a com o MarkItDown 0.1.8. Os 2 estão cobertos por testes:
- com os conversores por omissão, um `.pdf` que é texto sai como texto, sem erro;
- com os conversores por omissão, um PDF que o pdfminer não lê também cai no conversor de texto e volta em bruto como "Markdown". O adapter regista só o conversor do formato (`enable_builtins=False` + `register_converter`) e verifica a assinatura do ficheiro antes de converter.

Achados do T6b e do T6c, com as fixtures sintéticas de `runner/tests/fixtures/ingest/`:
- PDF: o título sai como texto simples, sem `#`, e o `/Title` dos metadados não é lido. A tabela com bordas é reconstruída em Markdown;
- DOCX: os headings saem como `#`. Uma tabela sem `w:tblHeader` na 1.ª linha sai com um cabeçalho vazio;
- XLSX: as células vazias e as fórmulas sem valor em cache saem como `NaN`. O `ingest_document` avisa com `xlsx_nan_cells=<n>`, sem alterar o conteúdo.

**Done do F1** (EXECUTION-PLAN §7): 3 formatos processados; ingestão E2E pela pipeline existente; path de knowledge estável.

## 10. Decisão pedida ao maestro

| | Opção |
|---|---|
| **A (recomendada)** | Aceitar o contrato (§2–§5) e o plano do spike (§9), a executar depois do F0 verde |
| B | Aceitar o contrato e adiar o spike para depois do F3 (provenance persistida primeiro) |
| C | Rever o contrato (ex.: incluir já `url` no spike) |
