"""F1 / T6a-T6d: primitiva `ingest_document` com o adapter MarkItDown (spike).

Contrato (docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md §2-§4), só com `kind = path`:

    ingest_document(path) -> {"content": str, "source_meta": dict, "warnings": [str]}

O que este esqueleto faz:
- recusa antes de converter (excepção `IngestError` com o código do ADR §3, item 6):
  formato fora do spike, ou conteúdo que não bate com a extensão (`unsupported_format`),
  ficheiro acima do tecto (`too_large`), ZIP corrompido (`conversion_failed`),
  ZIP (DOCX/XLSX) que descomprime acima do tecto (`decompression_limit`, mitigação 2 do §5);
- converte num **processo filho** (mitigação 3 do §5, T6d), com timeout (`timeout`) e, em
  Linux, limite de memória do SO (`RLIMIT_DATA`; `memory_limit`). Fora de Linux não há
  limite de memória, e isso fica no aviso `memory_limit_unavailable`, nunca em silêncio;
- converte com o MarkItDown só por `convert_local` (sem URL), sem plugins (§5, item 5) e só com
  o conversor do formato validado: sem os conversores por omissão, uma falha do conversor de
  PDF não cai no de texto simples (que devolveria o PDF em bruto como "Markdown");
- devolve `content` normalizado e `source_meta` com o schema mínimo do §4;
- nunca devolve conteúdo parcial em silêncio: falha da conversão = `conversion_failed`,
  conteúdo vazio = `empty_content`;
- avisa (`warnings`) sem alterar o conteúdo: título tirado do nome do ficheiro
  (`title_from_filename`) e células `NaN` num XLSX (`xlsx_nan_cells=<n>`: célula vazia ou
  fórmula sem valor em cache).

Limites por omissão (todos ajustáveis por parâmetro e pela CLI):

| Limite | Valor | Porquê |
|---|---|---|
| Tamanho do ficheiro | 25 MiB | Spike; ajusta-se com o benchmark (S5) |
| Total descomprimido (ZIP) | 200 MiB | Proposta do ADR §5, mitigação 2 |
| Memória do processo filho | 1 GiB (`RLIMIT_DATA`) | Medido no T6d: o MarkItDown 0.1.8 precisa de ≥ 384 MiB (o onnxruntime do magika rebenta abaixo); o `RLIMIT_AS` foi recusado por ser instável com o onnxruntime (768 MiB falhava sempre e 512 MiB só às vezes) |
| Tempo da conversão | 60 s | O filho é morto ao fim do tempo |

Encaixe no T6 (T6e, ADR §9 S4): `write_ingested` grava `<nome>.md` (o `content` tal como
está, por isso o hash do T6 é o `content_hash`) e `<nome>.meta.yaml` (proveniência). Para o
L5, o `.md` entra no MANIFEST de `scripts/ingest_delta.py`, e o merge corre o T6 real
(`ingest_apply.apply_one`). Esse passo escreve em produção e é decisão do maestro.
`validate_ingested` verifica a regra 3 do ADR (nada entra no L5 sem `source_meta` válido).

O `uri` é relativo à raiz do repo. Um ficheiro de fora do repo fica só com o nome
(`external:<nome>`) e o aviso `uri_outside_repo`, para não gravar caminhos da máquina local.

O que ainda NÃO faz:
- não emite o evento de observabilidade do ADR §3, item 8;
- só aceita ficheiros do repo ou entregues pelo DEV (§5, item 5).

O `content_hash` é o SHA-256 do `content` em UTF-8: é o mesmo hash que o T6 calcula
(`scripts/ingest_delta.py`, `sha256_file`) se o S4 gravar este `content` tal como está.

Dependência à parte do runner: `pip install -r runner/requirements-ingest.txt`.
Uso (só lê e imprime JSON, não escreve nada):

    python scripts/ingest_document.py caminho/do/documento.pdf [--timeout-s 60] [--memory-limit-mb 1024]
    python scripts/ingest_document.py caminho/do/documento.pdf --out-dir docs/knowledge/ingested
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
INGESTED_DIR = "docs/knowledge/ingested"
# Campos do source_meta que o `.meta.yaml` tem de ter (ADR §4, mínimo deste spike).
REQUIRED_META = ("uri", "title", "document_type", "retrieved_at", "content_hash", "status")

# Formatos do spike (ADR §9, S2). Os outros dão `unsupported_format` até haver golden set.
DOCUMENT_TYPES = {".pdf": "pdf", ".docx": "docx", ".xlsx": "xlsx"}
ZIP_TYPES = {"docx", "xlsx"}

# Tectos por omissão. 200 MB descomprimidos é a proposta do ADR §5 (mitigação 2);
# os 25 MB de entrada são do spike e ajustam-se com o benchmark (S5).
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_UNCOMPRESSED = 200 * 1024 * 1024
# Mitigação 3 do ADR §5 (T6d): ver a tabela de limites no docstring.
DEFAULT_TIMEOUT_S = 60.0
DEFAULT_MEMORY_LIMIT = 1024 * 1024 * 1024

ERROR_CODES = (
    "unsupported_format",
    "too_large",
    "decompression_limit",
    "conversion_failed",
    "empty_content",
    "missing_provenance",
    # T6d (mitigação 3): extensão do contrato, registada no ADR §9.
    "timeout",
    "memory_limit",
)

REQUIREMENTS_HINT = "pip install -r runner/requirements-ingest.txt"


class IngestError(Exception):
    """Erro tipado da primitiva; `code` é um dos ERROR_CODES (ADR §3, item 6)."""

    def __init__(self, code: str, message: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"código de erro fora do contrato: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = message


@dataclass(frozen=True)
class Converted:
    """O que um adapter devolve: Markdown, o título se o souber, e avisos do adapter."""

    markdown: str
    title: str | None = None
    warnings: tuple[str, ...] = ()


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
    except ModuleNotFoundError as exc:
        if (exc.name or "").split(".")[0] != "markitdown":
            raise IngestError(
                "conversion_failed", f"falta uma dependência do markitdown: {exc}"
            ) from exc
        raise IngestError(
            "conversion_failed", f"o pacote markitdown não está instalado ({REQUIREMENTS_HINT})"
        ) from exc
    except ImportError as exc:
        # Ex.: sem memória para carregar o onnxruntime do magika. Não é "não instalado".
        raise IngestError(
            "conversion_failed", f"o markitdown não carregou: {type(exc).__name__}: {exc}"
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
    with path.open("rb") as fh:
        head = fh.read(1024)
    if document_type == "pdf":
        ok = b"%PDF-" in head  # a assinatura pode vir depois de lixo inicial
    else:
        ok = zipfile.is_zipfile(path)
        if not ok and head.startswith(b"PK\x03\x04"):
            # Começa como ZIP mas não tem directório central: truncado ou estragado.
            raise IngestError(
                "conversion_failed", f"{path.name} é um ZIP corrompido (sem directório central)"
            )
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


def memory_limit_supported(platform: str = sys.platform) -> bool:
    """O `RLIMIT_DATA` só é aplicado em Linux.

    No Windows não há `resource`; no macOS o `RLIMIT_DATA` não trava as alocações por mmap.
    """
    return platform.startswith("linux")


def apply_memory_limit(limit: int | None) -> list[str]:
    """Aplica o limite ao processo **actual** (só no filho). Devolve os avisos."""
    if limit is None:
        return []
    if not memory_limit_supported():
        return ["memory_limit_unavailable"]
    import resource

    resource.setrlimit(resource.RLIMIT_DATA, (limit, limit))
    return []


# Alvo do processo filho por omissão (o adapter MarkItDown deste ficheiro).
DEFAULT_TARGET = "markitdown_converter"


def isolated_converter(
    path: Path,
    document_type: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    memory_limit: int | None = DEFAULT_MEMORY_LIMIT,
    target: str | None = None,
) -> Converted:
    """Mitigação 3 do ADR §5: converte num processo filho com timeout e limite de memória.

    O filho aplica o limite a si próprio antes de carregar o MarkItDown e escreve o
    resultado num ficheiro JSON (o stdout das bibliotecas não interfere). `target`
    (`ficheiro.py:função`) existe para os testes; por omissão é o `markitdown_converter`.
    """
    target = target or DEFAULT_TARGET
    with tempfile.TemporaryDirectory(prefix="ingest-") as tmp:
        out = Path(tmp) / "result.json"
        limit = "none" if memory_limit is None else str(memory_limit)
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            target,
            document_type,
            str(Path(path).resolve()),
            str(out),
            limit,
        ]
        try:
            # Falso positivo (auditoria): lista sem shell; os elementos são o interpretador,
            # este ficheiro e caminhos resolvidos por nós, nada vem de input externo.
            # nosemgrep: dangerous-subprocess-use-audit
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
        except subprocess.TimeoutExpired as exc:
            raise IngestError(
                "timeout", f"a conversão de {Path(path).name} passou de {timeout_s} s"
            ) from exc
        if not out.is_file():
            stderr = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
            if proc.returncode < 0:
                raise IngestError(
                    "conversion_failed",
                    f"o processo filho terminou com o sinal {-proc.returncode} "
                    f"(limite de memória: {limit} bytes): {' / '.join(stderr)}",
                )
            raise IngestError(
                "conversion_failed",
                f"o processo filho saiu com {proc.returncode} sem resultado "
                f"(limite de memória: {limit} bytes): {' / '.join(stderr)}",
            )
        data = json.loads(out.read_text(encoding="utf-8"))
    if "error" in data:
        raise IngestError(data["error"], data["message"])
    return Converted(
        markdown=data["markdown"], title=data.get("title"), warnings=tuple(data["warnings"])
    )


def _load_target(target: str) -> Callable[[Path, str], Any]:
    """`DEFAULT_TARGET` é o adapter deste ficheiro; outro alvo (`ficheiro.py:função`) é dos
    testes, que simulam abusos no filho. O pai só passa alvos que ele próprio escolheu."""
    if target == DEFAULT_TARGET:
        return markitdown_converter  # a mesma classe IngestError, sem reimportar o script
    file_name, _, func = target.rpartition(":")
    spec = importlib.util.spec_from_file_location("ingest_child_target", file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func)


def _child_main(target: str, document_type: str, path: str, out: str, limit: str) -> int:
    """Corre no processo filho: limite de memória primeiro, conversão depois."""
    warnings = apply_memory_limit(None if limit == "none" else int(limit))
    try:
        converted = _load_target(target)(Path(path), document_type)
        result = {
            "markdown": converted.markdown,
            "title": getattr(converted, "title", None),
            "warnings": warnings + list(getattr(converted, "warnings", ())),
        }
    except MemoryError:
        result = {"error": "memory_limit", "message": f"o limite de {limit} bytes foi atingido"}
    except Exception as exc:  # o resultado tem de chegar ao pai, com o código certo
        code = getattr(exc, "code", None)
        if code in ERROR_CODES:
            result = {"error": code, "message": getattr(exc, "detail", str(exc))}
        else:
            result = {"error": "conversion_failed", "message": f"{type(exc).__name__}: {exc}"}
    Path(out).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 0


def source_uri(path: Path, repo_root: Path = REPO_ROOT) -> tuple[str, str | None]:
    """`uri` relativo à raiz do repo; de fora do repo, só o nome e um aviso.

    Evita gravar no `.meta.yaml` (que vai para o git) um caminho da máquina local.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix(), None
    except ValueError:
        return f"external:{path.name}", "uri_outside_repo"


def slugify(text: str) -> str:
    """Nome de ficheiro estável: minúsculas ASCII, dígitos e hífens."""
    import re
    import unicodedata

    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "documento"


def write_ingested(
    result: dict[str, Any],
    out_dir: str | Path,
    name: str,
    *,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """S4 do ADR §9: grava `<name>.md` (o `content` tal e qual) e `<name>.meta.yaml`.

    O `.md` é gravado byte a byte como o `content` (UTF-8, LF), por isso o
    `sha256_file` do T6 dá o `source_meta.content_hash`. Não sobrepõe ficheiros
    existentes sem `overwrite=True`. Não toca no MANIFEST.
    """
    import yaml  # PyYAML está no runner/requirements.txt

    out = Path(out_dir)
    md_path, meta_path = out / f"{name}.md", out / f"{name}.meta.yaml"
    for target in (md_path, meta_path):
        if target.exists() and not overwrite:
            raise FileExistsError(f"{target} já existe (usar overwrite=True / --overwrite)")
    out.mkdir(parents=True, exist_ok=True)
    md_path.write_bytes(result["content"].encode("utf-8"))
    meta = {**result["source_meta"], "warnings": list(result["warnings"])}
    meta_path.write_text(
        yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
    )
    return md_path, meta_path


def validate_ingested(md_path: str | Path) -> list[str]:
    """Regra 3 do ADR §2: um `.md` convertido só entra no L5 com `source_meta` válido.

    Devolve a lista de problemas (vazia = válido): sidecar `.meta.yaml` em falta, campos
    mínimos em falta, ou `content_hash` diferente do SHA-256 do `.md`.
    """
    import yaml

    md = Path(md_path)
    meta_path = md.with_suffix(".meta.yaml")
    if not md.is_file():
        return [f"{md}: o ficheiro não existe"]
    if not meta_path.is_file():
        return [f"{md}: falta o {meta_path.name} (source_meta obrigatório, ADR §2 regra 3)"]
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    problems = [f"{meta_path.name}: falta o campo {k}" for k in REQUIRED_META if not meta.get(k)]
    digest = hashlib.sha256(md.read_bytes()).hexdigest()
    if meta.get("content_hash") and meta["content_hash"] != digest:
        problems.append(
            f"{meta_path.name}: content_hash {meta['content_hash'][:12]}… ≠ sha256 do .md {digest[:12]}…"
        )
    return problems


def count_nan_cells(markdown: str) -> int:
    """Células `NaN` nas tabelas Markdown do XLSX.

    O conversor do MarkItDown lê os valores pelo pandas: uma célula vazia e uma fórmula sem
    valor em cache (ficheiro gerado por programa e nunca aberto no Excel) saem as 2 como
    `NaN`. O conteúdo não é alterado (um `NaN` pode ser um valor que falta); fica o aviso.
    """
    total = 0
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            total += sum(cell.strip() == "NaN" for cell in line.strip("|").split("|"))
    return total


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
    timeout_s: float = DEFAULT_TIMEOUT_S,
    memory_limit: int | None = DEFAULT_MEMORY_LIMIT,
    converter: Converter | None = None,
) -> dict[str, Any]:
    """Converte um documento local em Markdown com `source_meta` (ADR §2-§4).

    Por omissão, a conversão corre num processo filho (`isolated_converter`) com
    `timeout_s` e `memory_limit`. Levanta `IngestError` em vez de devolver conteúdo
    parcial, e `FileNotFoundError` se o caminho não for um ficheiro.
    """
    if converter is None:
        converter = partial(isolated_converter, timeout_s=timeout_s, memory_limit=memory_limit)
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

    warnings: list[str] = list(converted.warnings)
    title = (converted.title or "").strip()
    if not title:
        title = p.stem
        warnings.append("title_from_filename")
    if document_type == "xlsx":
        nan_cells = count_nan_cells(content)
        if nan_cells:
            warnings.append(f"xlsx_nan_cells={nan_cells}")

    uri, uri_warning = source_uri(p)
    if uri_warning:
        warnings.append(uri_warning)
    source_meta = {
        "uri": uri,
        "title": title,
        "document_type": document_type,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "active",
    }
    return {"content": content, "source_meta": source_meta, "warnings": warnings}


def _parse_args(args: list[str]) -> argparse.Namespace | None:
    parser = argparse.ArgumentParser(
        prog="python scripts/ingest_document.py",
        description="Converte 1 documento (PDF, DOCX, XLSX) e imprime o JSON. Não escreve nada.",
    )
    parser.add_argument("caminho")
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument(
        "--memory-limit-mb", type=int, default=DEFAULT_MEMORY_LIMIT // (1024 * 1024)
    )
    parser.add_argument(
        "--out-dir",
        help=f"grava <nome>.md e <nome>.meta.yaml nesta pasta (S4; ex.: {INGESTED_DIR}). "
        "Não toca no MANIFEST.",
    )
    parser.add_argument("--name", help="nome dos ficheiros de saída (por omissão, o do documento)")
    parser.add_argument("--overwrite", action="store_true")
    try:
        return parser.parse_args(args)
    except SystemExit:
        return None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["--child"] and len(args) == 6:
        return _child_main(*args[1:])
    opts = _parse_args(args)
    if opts is None:
        return 2
    try:
        result = ingest_document(
            opts.caminho,
            timeout_s=opts.timeout_s,
            memory_limit=opts.memory_limit_mb * 1024 * 1024,
        )
    except IngestError as exc:
        print(json.dumps({"error": exc.code, "message": exc.detail}, ensure_ascii=False))
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if opts.out_dir:
        try:
            md_path, meta_path = write_ingested(
                result,
                opts.out_dir,
                opts.name or slugify(Path(opts.caminho).stem),
                overwrite=opts.overwrite,
            )
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        summary = {
            "md": md_path.as_posix(),
            "meta": meta_path.as_posix(),
            "content_hash": result["source_meta"]["content_hash"],
            "warnings": result["warnings"],
            "next": "para o L5: entrada no MANIFEST de scripts/ingest_delta.py (decisão do maestro)",
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
