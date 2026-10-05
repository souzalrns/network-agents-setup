# `ingest_document`: conversão de documentos (F1)

> Primitiva do contrato `docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md` (§2–§5), com o adapter MarkItDown.
> Código: `scripts/ingest_document.py`. Testes: `runner/tests/test_ingest_document.py`, `test_ingest_fixtures.py` e `test_ingest_security.py`.
> Estado da cadeia: `docs/initiatives/PENDENCIAS_T6.md`.

## 1. O que faz

```
ingest_document(path) -> {"content": str, "source_meta": dict, "warnings": [str]}
```

- **Entrada:** 1 ficheiro local PDF, DOCX ou XLSX (os formatos do spike). Só ficheiros do repo ou entregues pelo DEV (ADR §5, item 5); `url` e `connector_ref` ficam fora.
- **Saída:**
  - `content`: Markdown normalizado (LF, sem espaços no fim das linhas, um `\n` no fim);
  - `source_meta`: o schema mínimo do ADR §4 (`uri`, `title`, `document_type`, `retrieved_at`, `content_hash`, `status`). O `content_hash` é o SHA-256 do `content` em UTF-8, o mesmo que o T6 calcula sobre o ficheiro gravado;
  - `warnings`: avisos que não alteram o conteúdo (§4).
- **Só escreve com `--out-dir`** (T6e): ver a §7. O `uri` é relativo à raiz do repo; um ficheiro de fora do repo fica `external:<nome>`, com o aviso `uri_outside_repo`, para não gravar caminhos da máquina local no git.

Uso:

```bash
pip install -r runner/requirements-ingest.txt
python scripts/ingest_document.py caminho/do/documento.pdf [--timeout-s 60] [--memory-limit-mb 1024]
```

A CLI imprime o JSON do resultado, ou `{"error": <código>, "message": …}` com código de saída 1.

## 2. Limites (T6d)

| Limite | Valor por omissão | Parâmetro / flag | Código quando passa |
|---|---|---|---|
| Tamanho do ficheiro | 25 MiB | `max_bytes` | `too_large` |
| Total descomprimido de um ZIP (DOCX/XLSX) | 200 MiB, por entrada e no total | `max_uncompressed` | `decompression_limit` |
| Tempo da conversão | 60 s | `timeout_s` / `--timeout-s` | `timeout` |
| Memória do processo filho | 1 GiB (`RLIMIT_DATA`, só em Linux) | `memory_limit` / `--memory-limit-mb` | `memory_limit`, ou `conversion_failed` com a causa |

**Como se aplicam:**
1. As recusas de tamanho, formato e ZIP acontecem **antes** de abrir o conteúdo. A verificação do ZIP lê só o directório central (`ZipInfo.file_size`), sem descomprimir nada.
2. A conversão corre num **processo filho** (`isolated_converter`, mitigação 3 do ADR §5):
   - o filho aplica o `RLIMIT_DATA` a si próprio antes de carregar o MarkItDown;
   - o resultado volta por um ficheiro JSON temporário, por isso o stdout das bibliotecas não interfere;
   - ao fim do `timeout_s`, o filho é morto.
3. Se o filho morrer sem resultado (sinal, ou `exit(1)` de uma biblioteca nativa), o erro é `conversion_failed`, com o sinal ou o código de saída, o limite de memória e as últimas linhas do stderr. O processo pai não cai.

**Porque `RLIMIT_DATA` e 1 GiB** (medido no T6d, MarkItDown 0.1.8, Linux 6.18, 4 CPUs; 3 a 5 corridas por valor):

| Limite | `RLIMIT_AS` | `RLIMIT_DATA` |
|---|---|---|
| 128 MiB | — | falha (OpenBLAS) |
| 256 MiB | falha | falha (onnxruntime: "Resource temporarily unavailable") |
| 384 MiB | — | ok |
| 512 MiB | ok 4 em 5 | ok |
| 768 MiB | **falha 5 em 5** | ok |
| 1 GiB e acima | ok | ok |

- O `RLIMIT_AS` não é monótono com o onnxruntime (o magika, que o MarkItDown carrega sempre): não serve como limite fiável.
- O `RLIMIT_DATA` trava uma alocação de 2 GiB e também muitas pequenas acumuladas (verificado com `bytearray`).
- 1 GiB dá cerca de 2,7× de margem sobre o mínimo de 384 MiB; o pico de memória residente nas 3 fixtures foi ~165 MiB.

**Fora de Linux** (Windows, macOS) não há limite de memória: no Windows não existe `resource`, e no macOS o `RLIMIT_DATA` não trava as alocações por mmap. O timeout continua a valer, e o resultado traz o aviso `memory_limit_unavailable`, nunca em silêncio.

## 3. Códigos de erro (`IngestError.code`)

| Código | Quando |
|---|---|
| `unsupported_format` | Extensão fora do spike, ou conteúdo que não bate com a extensão (sem `%PDF-` num `.pdf`; um `.docx`/`.xlsx` que não é ZIP) |
| `too_large` | Ficheiro acima do `max_bytes` |
| `decompression_limit` | Uma entrada ou o total do ZIP acima do `max_uncompressed` |
| `conversion_failed` | O conversor falhou; ZIP corrompido (começa por `PK\x03\x04` mas não tem directório central); o filho morreu sem resultado; o `markitdown` não está instalado ou não carregou (mensagens diferentes para cada caso) |
| `empty_content` | A conversão não deu texto |
| `timeout` | A conversão passou do `timeout_s` (extensão do contrato no T6d) |
| `memory_limit` | O filho apanhou um `MemoryError` sob o `RLIMIT_DATA` (extensão do contrato no T6d) |
| `missing_provenance` | Reservado pelo ADR (sem `source_meta` válido); ainda não é emitido |

Um caminho que não é ficheiro dá `FileNotFoundError` (não é um erro do contrato).

## 4. Avisos (`warnings`)

| Aviso | Quando | O conteúdo muda? |
|---|---|---|
| `title_from_filename` | O conversor não deu título (o `PdfConverter` nunca dá; ver §5) | Não |
| `xlsx_nan_cells=<n>` | Células `NaN` nas tabelas de um XLSX: célula vazia ou fórmula sem valor em cache | Não |
| `memory_limit_unavailable` | Conversão fora de Linux, sem limite de memória | Não |
| `uri_outside_repo` | O documento está fora do repo: o `uri` fica só com o nome | Não |

## 5. Comportamento do MarkItDown 0.1.8 (fixado por testes)

| Formato | Observado | Teste |
|---|---|---|
| Todos | Com os conversores por omissão, um ficheiro ilegível ou com a extensão errada cai no conversor de texto e volta em bruto como "Markdown". O adapter regista só o conversor do formato | `test_smoke_markitdown_sozinho_converte_um_pdf_falso_como_texto` |
| PDF | O título sai como texto simples, sem `#` (o PDF não tem headings semânticos); o `/Title` dos metadados não é lido; uma tabela com bordas é reconstruída em Markdown | `test_pdf_simple_synthetic_*` |
| DOCX | Os headings saem como `#`. Uma tabela sem `w:tblHeader` na 1.ª linha sai com um cabeçalho vazio | `test_docx_simple_synthetic_*` |
| XLSX | Uma folha por secção `##`. As células vazias e as fórmulas sem cache saem como `NaN`; uma coluna com `NaN` passa a float (`300.0`) | `test_xlsx_simple_synthetic_*` |
| DOCX/XLSX truncados | Detectados antes do conversor (`conversion_failed`, "ZIP corrompido") | `test_zip_truncado_*` |
| PDF truncado | O pdfminer falha (`PSEOF` ou "No /Root object"), por isso dá `conversion_failed` | `test_smoke_pdf_real_estragado_*` |

## 6. Fixtures e CI

- As fixtures sintéticas estão em `runner/tests/fixtures/ingest/<formato>/`, cada uma com o gerador reprodutível ao lado. Os pins dos geradores estão em `runner/requirements-fixtures.txt`.
- O job `test-ingest` (`.github/workflows/runner-tests.yml`) instala o MarkItDown e os geradores, com `INGEST_TEST_REQUIRED=1`: a falta de uma dependência opcional é erro, não skip.
- Sem os extras (jobs `test`/`test-slow` e em local), os testes que precisam deles dão skip com o motivo.

## 7. Encaixe no T6 (T6e, ADR §9 S4)

Não há pipeline paralela (ADR §2, regra 2). O documento convertido entra no L5 pelo T6 que já existe:

```
documento → ingest_document (processo filho, MarkItDown)
  → write_ingested: docs/knowledge/ingested/<nome>.md + <nome>.meta.yaml
  → entrada no MANIFEST de scripts/ingest_delta.py          ← decisão do maestro (escreve em produção no merge)
  → merge → workflow ingest-knowledge → ingest_apply.apply_one
       (chunk_markdown → embed com orçamento --max-chunks → replace_chunks)
  → match_knowledge (MCP retrieve_knowledge)
```

```bash
python scripts/ingest_document.py caminho/doc.pdf --out-dir docs/knowledge/ingested [--name nome] [--overwrite]
```

- **O `.md` é o `content` byte a byte.** O `sha256_file` do T6 dá o `source_meta.content_hash`, e o `knowledge_sources.content_hash` gravado pelo T6 é esse mesmo valor (provado contra Postgres em `test_ingest_pipeline_rag.py`).
- **O `.meta.yaml`** guarda o `source_meta` e os avisos. Até ao F3, os campos novos do ADR §4 vivem só neste ficheiro; o F3 é que estende a `knowledge_sources`.
- **Regra 3 do ADR no CI:** o `validate_ingested` exige o `.meta.yaml`, os campos mínimos e o hash certo. `test_manifest_so_tem_convertidos_com_source_meta_valido` aplica-o a qualquer entrada do MANIFEST em `docs/knowledge/ingested/`. Um `.md` editado à mão depois da conversão falha o CI.
- **Sem sobreposição:** `write_ingested` recusa ficheiros existentes sem `overwrite=True` / `--overwrite`.
- **Orçamento e incremental:** os do T6, sem mudanças. Sem orçamento, o ficheiro fica `SKIPPED_QUOTA`, sem escrita parcial; a 2.ª corrida igual é `UNCHANGED`, sem embeddings. Os 2 casos estão testados com o documento convertido.
- **Gate humano:** o T6 não tem HITL próprio. O gate é o PR que põe o `.md` no MANIFEST, cujo merge é do maestro.

## 8. Medições do S5 (T6f)

`python scripts/ingest_benchmark.py --repeats 5` (MarkItDown 0.1.8, Linux, 4 CPUs, processo filho do T6d). A estrutura esperada vem das constantes dos geradores das fixtures, que são o golden set dos testes:

| Formato | Bytes | Chars | Título como heading | Lista | Linhas de tabela | Tempo (mediana) | RSS máx. filhos | Avisos |
|---|---|---|---|---|---|---|---|---|
| PDF | 1748 | 370 | não (texto simples) | 3/3 | 3/3 | 0.85 s | 141 MiB | title_from_filename |
| DOCX | 34652 | 319 | sim | 3/3 | 3/3 | 1.03 s | 156 MiB | title_from_filename |
| XLSX | 5491 | 225 | 2/2 folhas como ## | n/a | 6/6 | 0.87 s | 156 MiB | title_from_filename, xlsx_nan_cells=2 |

- **Estrutura:** listas e tabelas a 100% nos 3 formatos. A única perda é o título do PDF, que sai como texto simples. Consequência para o T6: o `chunk_markdown` corta por H2/H3, por isso um PDF longo é cortado por tamanho e não por secções.
- **Título:** nem o `PdfConverter` nem o `DocxConverter` devolvem o título dos metadados (o DOCX tem-no), e o `source_meta.title` vem do nome do ficheiro, com aviso.
- **Custo:** cerca de 1 s e 150 MiB por documento, quase tudo do arranque do processo filho e do MarkItDown/magika. Os documentos são pequenos; documentos grandes medem-se no benchmark real do P-21 B.
- **Ressalva:** são fixtures sintéticas e pequenas, e não documentos reais do domínio. A decisão do F1b (Docling) está na P-21 do `PENDENCIAS.md`.
- Em Windows, a coluna de memória sai `n/d` (sem `resource`).
- O teste `test_benchmark_s5_mede_os_3_formatos_e_fixa_a_estrutura` corre o script no CI e fixa a estrutura medida.
