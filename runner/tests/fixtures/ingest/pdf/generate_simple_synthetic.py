"""Gera a fixture `simple_synthetic.pdf` (F1 / T6b), de forma reprodutível.

Conteúdo sintético, sem dados pessoais nem texto de terceiros:
- título (o que seria um H1; o PDF não tem headings semânticos);
- 1 parágrafo;
- 1 lista com 3 itens;
- 1 tabela com cabeçalho e 3 colunas por 2 linhas de dados, com bordas (é pelas linhas
  que o conversor do MarkItDown reconhece a tabela).

Reprodutível: data de criação, producer e creator fixos, e fontes base do PDF (Helvetica,
sem embutir). Com a mesma versão do fpdf2, os bytes são iguais em cada corrida
(`test_fixture_pdf_e_reprodutivel`).

Uso (a partir da raiz do repo, com o fpdf2 instalado: `pip install -r runner/requirements-fixtures.txt`):

    python runner/tests/fixtures/ingest/pdf/generate_simple_synthetic.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

OUT = Path(__file__).with_name("simple_synthetic.pdf")

TITLE = "Relatório sintético de ingestão"
PARAGRAPH = (
    "Este documento é sintético e serve só para testar a conversão de PDF para Markdown "
    "na pipeline de ingestão."
)
ITEMS = ("Primeiro item da lista", "Segundo item da lista", "Terceiro item da lista")
TABLE = (
    ("Formato", "Conversor", "Estado"),
    ("PDF", "PdfConverter", "testado"),
    ("DOCX", "DocxConverter", "planeado"),
)
FIXED_DATE = datetime(2026, 1, 1, tzinfo=UTC)
TAG = "network-agents-setup fixture generator"


def build() -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_creation_date(FIXED_DATE)
    pdf.set_producer(TAG)
    pdf.set_creator(TAG)
    pdf.set_title(TITLE)
    pdf.set_lang("pt-PT")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, TITLE, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, PARAGRAPH, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for item in ITEMS:
        pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    with pdf.table(col_widths=(50, 50, 50)) as table:
        for row in TABLE:
            cells = table.row()
            for value in row:
                cells.cell(value)
    return bytes(pdf.output())


def main() -> int:
    data = build()
    OUT.write_bytes(data)
    print(f"{OUT} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
