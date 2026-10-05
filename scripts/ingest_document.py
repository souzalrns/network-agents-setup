"""F1 / T6a: primitiva `ingest_document` com o adapter MarkItDown (esqueleto do spike).

Contrato (docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md §2-§4), só com `kind = path`:

    ingest_document(path) -> {"content": str, "source_meta": dict, "warnings": [str]}

O que este esqueleto faz:
- recusa antes de converter (excepção `IngestError` com o código do ADR §3, item 6):
  formato fora do spike, ou conteúdo que não bate com a extensão (`unsupported_format`),
  ficheiro acima do tecto (`too_large`),
  ZIP (DOCX/XLSX) que descomprime acima do tecto (`decompression_limit`, mitigação 2 do §5);
- converte com o MarkItDown só por `convert_local` (sem URL), sem plugins (§5, item 5) e só com
  o conversor do formato validado: sem os conversores por omissão, uma falha do conversor de
  PDF não cai no de texto simples (que devolveria o PDF em bruto como "Markdown");
- devolve `content` normalizado e `source_meta` com o schema mínimo do §4;
- nunca devolve conteúdo parcial em silêncio: falha da conversão = `conversion_failed`,
  conteúdo vazio = `empty_content`.

O que ainda NÃO faz (passos seguintes do §9 do ADR):
- não está ligado ao worker, ao `plan_runner` nem ao T6, e não escreve ficheiros (S4);
- a conversão ainda corre neste processo: o processo filho com limite de memória do SO
  (mitigação 3 do §5) fica para o T6b. Até lá, usar só com ficheiros do repo ou entregues
  pelo DEV (§5, item 5);
- não emite o evento de observabilidade do ADR §3, item 8.

O `content_hash` é o SHA-256 do `content` em UTF-8: é o mesmo hash que o T6 calcula
(`scripts/ingest_delta.py`, `sha256_file`) se o S4 gravar este `content` tal como está.

Dependência à parte do runner: `pip install -r runner/requirements-ingest.txt`.
Uso (só lê e imprime JSON, não escreve nada):

    python scripts/ingest_document.py caminho/do/documento.pdf
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Formatos do spike (ADR §9, S2). Os outros dão `unsupported_format` até haver golden set.
DOCUMENT_TYPES = {".pdf": "pdf", ".docx": "docx", ".xlsx": "xlsx"}
ZIP_TYPES = {"docx", "xlsx"}

# Tectos por omissão. 200 MB descomprimidos é a proposta do ADR §5 (mitigação 2);
# os 25 MB de entrada são do spike e ajustam-se com o benchmark (S5).
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_UNCOMPRESSED = 200 * 1024 * 1024

ERROR_CODES = (
    "unsupported_format",
    "too_large",
    "decompression_limit",
    "conversion_failed",
    "empty_content",
    "missing_provenance",
)

REQUIREMENTS_HINT = "pip install -r runner/requirements-ingest.txt"


class IngestError(Exception):
    """Erro tipado da primitiva; `code` é um dos ERROR_CODES (ADR §3, item 6)."""

    def __init__(self, code: str, message: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"código de erro fora do contrato: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class Converted:
    """O que um adapter devolve: Markdown e, se o souber, o título."""

    markdown: str
    title: str | None = None


Converter = Callable[[Path, str], Converted]

# O conversor do MarkItDown para cada `document_type` do spike.
MARKITDOWN_CONVERTERS = {"pdf": "PdfConverter", "docx": "DocxConverter", "xlsx": "XlsxConverter"}


def markitdown_converter(path: Path, document_type: str) -> Converted:
    """Adapter MarkItDown: só ficheiros locais, sem plugins e só com o conversor do formato.

    Com os conversores por omissão (verificado no 0.1.8), um PDF que o pdfminer não lê cai
    no conversor de texto simples e volta como "Markdown" sem erro.
    """
    try:
        from markitdown import MarkItDown
        from markitdown import converters as md_converters
    except ImportError as exc:
        raise IngestError(
            "conversion_failed", f"o pacote markitdown não está instalado ({REQUIREMENTS_HINT})"
        ) from exc
    md = MarkItDown(enable_builtins=False, enable_plugins=False)
    md.register_converter(getattr(md_converters, MARKITDOWN_CONVERTERS[document_type])())
    try:
        result = md.convert_local(path)
    except Exception as exc:  # o MarkItDown e as bibliotecas por baixo têm excepções próprias
        raise IngestError("conversion_failed", f"{type(exc).__name__}: {exc}") from exc
    return Converted(markdown=result.markdown or "", title=result.title)


def check_signature(path: Path, document_type: str) -> None:
    """O conteúdo tem de ser do formato que a extensão diz.

    Com os conversores por omissão, o MarkItDown converte um `.pdf` que é texto pelo
    conversor de texto, sem erro, e o `source_meta` ficaria com um `document_type` falso
    (verificado com o 0.1.8). Com o conversor fixo daria `conversion_failed` com o erro do
    pdfminer; esta verificação dá o código certo antes de o ficheiro chegar ao adapter.
    """
    if document_type == "pdf":
        with path.open("rb") as fh:
            ok = b"%PDF-" in fh.read(1024)  # a assinatura pode vir depois de lixo inicial
    else:
        ok = zipfile.is_zipfile(path)
    if not ok:
        raise IngestError(
            "unsupported_format", f"o conteúdo de {path.name} não é {document_type.upper()}"
        )


def check_zip_limits(path: Path, max_uncompressed: int) -> None:
    """Mitigação 2 do ADR §5: recusar um ZIP que descomprime acima do tecto, sem o extrair.

    Lê só o directório central (`ZipInfo.file_size`), por entrada e no total.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as exc:
        raise IngestError("conversion_failed", f"ZIP inválido: {exc}") from exc
    total = 0
    for info in infos:
        if info.file_size > max_uncompressed:
            raise IngestError(
                "decompression_limit",
                f"a entrada {info.filename!r} descomprime para {info.file_size} bytes "
                f"(tecto {max_uncompressed})",
            )
        total += info.file_size
        if total > max_uncompressed:
            raise IngestError(
                "decompression_limit",
                f"o total descomprimido passa de {max_uncompressed} bytes",
            )


def normalize(markdown: str) -> str:
    """Fins de linha LF, sem espaços no fim das linhas, um único `\\n` no fim do texto."""
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    text = "\n".join(line.rstrip() for line in lines).strip()
    return f"{text}\n" if text else ""


def ingest_document(
    path: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_uncompressed: int = DEFAULT_MAX_UNCOMPRESSED,
    converter: Converter = markitdown_converter,
) -> dict[str, Any]:
    """Converte um documento local em Markdown com `source_meta` (ADR §2-§4).

    Levanta `IngestError` em vez de devolver conteúdo parcial, e `FileNotFoundError`
    se o caminho não for um ficheiro.
    """
    p = Path(path)
    document_type = DOCUMENT_TYPES.get(p.suffix.lower())
    if document_type is None:
        raise IngestError(
            "unsupported_format",
            f"{p.suffix or '(sem extensão)'} não está no spike ({', '.join(sorted(DOCUMENT_TYPES))})",
        )
    if not p.is_file():
        raise FileNotFoundError(f"o ficheiro não existe: {p}")
    size = p.stat().st_size
    if size > max_bytes:
        raise IngestError("too_large", f"{size} bytes (tecto {max_bytes})")
    check_signature(p, document_type)
    if document_type in ZIP_TYPES:
        check_zip_limits(p, max_uncompressed)

    converted = converter(p, document_type)
    content = normalize(converted.markdown)
    if not content:
        raise IngestError("empty_content", f"a conversão de {p.name} não deu texto")

    warnings: list[str] = []
    title = (converted.title or "").strip()
    if not title:
        title = p.stem
        warnings.append("title_from_filename")

    source_meta = {
        "uri": p.as_posix(),
        "title": title,
        "document_type": document_type,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "active",
    }
    return {"content": content, "source_meta": source_meta, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("uso: python scripts/ingest_document.py <caminho>", file=sys.stderr)
        return 2
    try:
        result = ingest_document(args[0])
    except IngestError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}, ensure_ascii=False))
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
