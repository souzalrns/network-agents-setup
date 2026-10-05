"""F1 / T6f: medições do S5 do ADR-INGESTION-PRIMITIVES §9 sobre as fixtures sintéticas.

Por formato: bytes de entrada, chars de saída, estrutura preservada (título como heading,
itens de lista, linhas de tabela, folhas do XLSX), tempo de parede (mediana de N corridas,
com o processo filho do T6d) e memória residente máxima dos processos filhos.

A estrutura esperada vem das constantes dos geradores das fixtures (o mesmo golden set dos
testes). Serve de base objectiva ao F1b (Docling só se houver perda material de estrutura),
com uma ressalva: são documentos sintéticos, não documentos reais do domínio.

Uso (a partir da raiz do repo, com `pip install -r runner/requirements-ingest.txt`):

    python scripts/ingest_benchmark.py [--repeats 3] [--json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "runner" / "tests" / "fixtures" / "ingest"
FORMATS = ("pdf", "docx", "xlsx")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # o @dataclass do ingest_document precisa do módulo registado
    spec.loader.exec_module(module)
    return module


def _table_rows(markdown: str) -> list[list[str]]:
    rows = []
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                rows.append(cells)
    return rows


def _cell_ok(expected: Any, actual: str) -> bool:
    if expected is None or (isinstance(expected, str) and expected.startswith("=")):
        return actual == "NaN"  # célula vazia / fórmula sem cache (comportamento conhecido)
    if isinstance(expected, int | float):
        try:
            return float(actual) == float(expected)
        except ValueError:
            return False
    return actual == expected


def structure(fmt: str, markdown: str, gen) -> dict[str, Any]:
    """Estrutura preservada face ao golden set do gerador."""
    rows = _table_rows(markdown)
    lines = markdown.splitlines()
    if fmt == "xlsx":
        expected = [row for sheet in gen.SHEETS.values() for row in sheet]
        found = sum(
            any(
                len(a) == len(e) and all(_cell_ok(x, y) for x, y in zip(e, a, strict=True))
                for a in rows
            )
            for e in expected
        )
        sheets = sum(f"## {name}" in lines for name in gen.SHEETS)
        return {
            "heading": f"{sheets}/{len(gen.SHEETS)} folhas como ##",
            "list": "n/a",
            "table_rows": f"{found}/{len(expected)}",
        }
    title_heading = any(re.fullmatch(rf"#+ {re.escape(gen.TITLE)}", ln) for ln in lines)
    items = sum(any(re.fullmatch(rf"[*-] {re.escape(i)}", ln) for ln in lines) for i in gen.ITEMS)
    table_ok = sum(list(r) in rows for r in gen.TABLE)
    return {
        "heading": "sim" if title_heading else "não (texto simples)",
        "list": f"{items}/{len(gen.ITEMS)}",
        "table_rows": f"{table_ok}/{len(gen.TABLE)}",
    }


def _peak_child_rss_mib() -> int | str:
    """RSS máximo dos processos filhos terminados até aqui; "n/d" sem `resource` (Windows)."""
    try:
        import resource
    except ImportError:
        return "n/d"
    kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss  # KiB em Linux
    return round(kib / 1024) if sys.platform.startswith("linux") else "n/d"


def run(repeats: int = 3) -> list[dict[str, Any]]:
    # Reutiliza o módulo já carregado: recarregá-lo trocaria a classe IngestError a quem já
    # o tem (achado no F2: o `fetch` deixava de reconhecer o erro do conversor).
    ing = sys.modules.get("ingest_document") or _load(
        "ingest_document", REPO_ROOT / "scripts" / "ingest_document.py"
    )
    results = []
    for fmt in FORMATS:
        gen = _load(f"bench_gen_{fmt}", FIXTURES / fmt / "generate_simple_synthetic.py")
        path = FIXTURES / fmt / f"simple_synthetic.{fmt}"
        durations, out = [], None
        for _ in range(repeats):
            start = time.perf_counter()
            out = ing.ingest_document(path)
            durations.append(time.perf_counter() - start)
        peak = _peak_child_rss_mib()
        results.append(
            {
                "format": fmt,
                "bytes_in": path.stat().st_size,
                "chars_out": len(out["content"]),
                **structure(fmt, out["content"], gen),
                "seconds_median": round(statistics.median(durations), 2),
                "peak_child_rss_mib": peak,
                "warnings": out["warnings"],
            }
        )
    return results


def _mib(value: int | str) -> str:
    return f"{value} MiB" if isinstance(value, int) else value


def _row(r: dict[str, Any]) -> str:
    cells = [
        r["format"].upper(),
        r["bytes_in"],
        r["chars_out"],
        r["heading"],
        r["list"],
        r["table_rows"],
        f"{r['seconds_median']} s",
        _mib(r["peak_child_rss_mib"]),
        ", ".join(r["warnings"]) or "—",
    ]
    return "| " + " | ".join(str(c) for c in cells) + " |"


def to_markdown(results: list[dict[str, Any]]) -> str:
    head = (
        "| Formato | Bytes | Chars | Título como heading | Lista | Linhas de tabela "
        "| Tempo (mediana) | RSS máx. filhos | Avisos |\n|---|---|---|---|---|---|---|---|---|"
    )
    body = [_row(r) for r in results]
    return "\n".join([head, *body])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    opts = parser.parse_args(argv)
    results = run(opts.repeats)
    print(json.dumps(results, ensure_ascii=False, indent=2) if opts.json else to_markdown(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
