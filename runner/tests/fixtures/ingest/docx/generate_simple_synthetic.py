"""Gera a fixture `simple_synthetic.docx` (F1 / T6c), de forma reprodutível.

Conteúdo sintético, sem dados pessoais nem texto de terceiros:
- heading de nível 1;
- 1 parágrafo;
- 1 lista com 3 itens (estilo "List Bullet");
- 1 tabela com 3 colunas: cabeçalho e 2 linhas. A 1.ª linha está marcada como cabeçalho
  (`w:tblHeader`); sem isso, o conversor do MarkItDown põe um cabeçalho vazio e trata a
  1.ª linha como dados.

Os estilos e o tema vêm do template por omissão do python-docx (licença MIT); o texto é todo
deste gerador.

Reprodutível: propriedades do documento fixas e ZIP normalizado (`reproducible_zip.py`).

Uso (a partir da raiz do repo, com `pip install -r runner/requirements-fixtures.txt`):

    python runner/tests/fixtures/ingest/docx/generate_simple_synthetic.py
"""

from __future__ import annotations

import io
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

OUT = Path(__file__).with_name("simple_synthetic.docx")

TITLE = "Relatório sintético de ingestão"
PARAGRAPH = "Este documento é sintético e serve só para testar a conversão de DOCX para Markdown."
ITEMS = ("Primeiro item da lista", "Segundo item da lista", "Terceiro item da lista")
TABLE = (
    ("Formato", "Conversor", "Estado"),
    ("DOCX", "DocxConverter", "testado"),
    ("XLSX", "XlsxConverter", "testado"),
)
FIXED_DATE = datetime(2026, 1, 1)
TAG = "network-agents-setup fixture generator"


def build() -> bytes:
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    doc = Document()
    props = doc.core_properties
    props.author = TAG
    props.last_modified_by = TAG
    props.title = TITLE
    props.created = FIXED_DATE
    props.modified = FIXED_DATE
    props.revision = 1

    doc.add_heading(TITLE, level=1)
    doc.add_paragraph(PARAGRAPH)
    for item in ITEMS:
        doc.add_paragraph(item, style="List Bullet")
    table = doc.add_table(rows=len(TABLE), cols=len(TABLE[0]))
    for r, row in enumerate(TABLE):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    header_props = table.rows[0]._tr.get_or_add_trPr()
    header_props.append(OxmlElement("w:tblHeader"))
    header_props[-1].set(qn("w:val"), "true")

    buf = io.BytesIO()
    doc.save(buf)
    return normalize_zip(buf.getvalue())


def main() -> int:
    data = build()
    OUT.write_bytes(data)
    print(f"{OUT} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
