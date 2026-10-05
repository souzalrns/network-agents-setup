"""Gera a fixture `simple_synthetic.xlsx` (F1 / T6c), de forma reprodutível.

Conteúdo sintético, sem dados pessoais nem texto de terceiros:
- folha "Custos": cabeçalho, texto, números, 1 célula vazia e 1 fórmula simples (`=B2*12`);
- folha "Notas": pares chave/valor em texto.

O openpyxl grava a fórmula **sem valor em cache** (só o Excel ou o LibreOffice a calculam).
O conversor do MarkItDown lê os valores em cache (pandas), por isso a fórmula e a célula
vazia saem como `NaN`. A fixture inclui as 2 de propósito, para o teste fixar esse
comportamento e o aviso que o `ingest_document` emite.

Reprodutível: propriedades do livro fixas (o `dcterms:modified` é corrigido depois de
guardar, porque o openpyxl o reescreve) e ZIP normalizado (`reproducible_zip.py`).

Uso (a partir da raiz do repo, com `pip install -r runner/requirements-fixtures.txt`):

    python runner/tests/fixtures/ingest/xlsx/generate_simple_synthetic.py
"""

from __future__ import annotations

import io
import re
import sys
from datetime import datetime
from pathlib import Path


def _load_reproducible_zip():
    """Carrega o helper pelo caminho, sem mexer no `sys.path`.

    Pôr `fixtures/ingest/` no `sys.path` tornava a pasta `docx/` importável como `docx`, a
    fazer-se passar pelo python-docx quando este não está instalado.
    """
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "reproducible_zip.py"
    spec = importlib.util.spec_from_file_location("fixtures_reproducible_zip", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalize_zip = _load_reproducible_zip().normalize_zip

OUT = Path(__file__).with_name("simple_synthetic.xlsx")

SHEETS = {
    "Custos": (
        ("Fornecedor", "Mensal", "Anual", "Nota"),
        ("Vercel", 0, "=B2*12", "plano gratuito"),
        ("Supabase", 25, 300, None),
    ),
    "Notas": (
        ("Chave", "Valor"),
        ("origem", "sintético"),
        ("versão", "1"),
    ),
}
FORMULA_CELL = ("Custos", "C2")
EMPTY_CELL = ("Custos", "D3")
FIXED_DATE = datetime(2026, 1, 1)
FIXED_W3CDTF = b"2026-01-01T00:00:00Z"
TAG = "network-agents-setup fixture generator"


def build() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.properties.creator = TAG
    wb.properties.lastModifiedBy = TAG
    wb.properties.created = FIXED_DATE
    wb.properties.modified = FIXED_DATE
    wb.remove(wb.active)
    for name, rows in SHEETS.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(list(row))

    buf = io.BytesIO()
    wb.save(buf)
    return normalize_zip(buf.getvalue(), {"docProps/core.xml": _fix_modified})


def _fix_modified(core_xml: bytes) -> bytes:
    """O openpyxl grava a hora actual no `dcterms:modified` ao guardar, por cima da fixada."""
    fixed, n = re.subn(
        rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
        rb"\g<1>" + FIXED_W3CDTF + rb"\g<2>",
        core_xml,
    )
    if n != 1:
        raise RuntimeError("docProps/core.xml sem dcterms:modified: rever o gerador")
    return fixed


def main() -> int:
    data = build()
    OUT.write_bytes(data)
    print(f"{OUT} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
