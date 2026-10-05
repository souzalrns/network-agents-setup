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
- **Não escreve nada.** A ligação ao T6 (ficheiro em `docs/knowledge/…` → MANIFEST → ingest) é o T6e.

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
