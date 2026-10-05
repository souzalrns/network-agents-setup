"""F1 / T6b+: fixtures sintéticas versionadas da ingestão, convertidas pelo MarkItDown real.

Cada formato tem uma fixture pequena em `tests/fixtures/ingest/<formato>/`, gerada por um
script reprodutível ao lado dela. Os testes verificam 3 coisas:
- a fixture cumpre as regras (tamanho, assinatura, sem dados de terceiros: o texto vem todo
  das constantes do gerador, que são o golden set);
- a API pública do MarkItDown (`MarkItDown().convert`) extrai o golden set;
- a primitiva `ingest_document` (scripts/ingest_document.py) dá o mesmo conteúdo, com o
  `source_meta` certo.

Dependências opcionais (`tests/optional_deps.py`): skip em local sem elas, erro no job
`test-ingest` do CI.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from tests.optional_deps import require

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"
REQS_FIXTURES = REPO_ROOT / "runner" / "requirements-fixtures.txt"
MAX_FIXTURE_BYTES = 50 * 1024


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # o @dataclass do ingest_document precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


ing = _load("ingest_document", REPO_ROOT / "scripts" / "ingest_document.py")
pdf_gen = _load("fixture_pdf_generator", FIXTURES / "pdf" / "generate_simple_synthetic.py")
PDF = FIXTURES / "pdf" / "simple_synthetic.pdf"


def _flat(text: str) -> str:
    """Espaços e quebras de linha colapsados (o PDF parte o parágrafo em linhas)."""
    return re.sub(r"\s+", " ", text).strip()


def _table_rows(markdown: str) -> list[list[str]]:
    """Linhas de tabela Markdown, sem a linha separadora (`| --- |`)."""
    rows = []
    for line in markdown.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def _pinned(package: str) -> str:
    for line in REQS_FIXTURES.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{package}=="):
            return line.split("==", 1)[1].strip()
    raise AssertionError(f"{package} sem pin exacto em {REQS_FIXTURES.name}")


def _assert_pdf_golden(markdown: str) -> None:
    flat = _flat(markdown)
    assert markdown.strip(), "conversão vazia"
    assert pdf_gen.TITLE in flat
    assert _flat(pdf_gen.PARAGRAPH) in flat
    for item in pdf_gen.ITEMS:
        assert f"- {item}" in markdown
    assert _table_rows(markdown) == [list(row) for row in pdf_gen.TABLE]


# --- regras da fixture (sem dependências opcionais) ---------------------------------------


def test_fixture_pdf_cumpre_as_regras() -> None:
    data = PDF.read_bytes()
    assert data.startswith(b"%PDF-")
    assert len(data) <= MAX_FIXTURE_BYTES
    pages = len(re.findall(rb"/Type\s*/Page(?!s)", data))
    assert 1 <= pages <= 2
    assert b"network-agents-setup fixture generator" in data  # gerada pelo script, não à mão


def test_golden_pdf_tem_a_estrutura_pedida() -> None:
    assert pdf_gen.TITLE and pdf_gen.PARAGRAPH
    assert len(pdf_gen.ITEMS) == 3
    assert len(pdf_gen.TABLE) == 3 and all(len(row) == 3 for row in pdf_gen.TABLE)


# --- reprodutibilidade (fpdf2 com o pin exacto) -------------------------------------------


def test_fixture_pdf_e_reprodutivel() -> None:
    require("fpdf")
    from importlib.metadata import version

    installed, pinned = version("fpdf2"), _pinned("fpdf2")
    if installed != pinned:
        pytest.skip(f"fpdf2 {installed} instalado; os bytes só são estáveis com o pin {pinned}")
    assert pdf_gen.build() == PDF.read_bytes(), (
        "a fixture versionada não é a saída do gerador: correr "
        "`python runner/tests/fixtures/ingest/pdf/generate_simple_synthetic.py` e commitar"
    )


# --- conversão real ------------------------------------------------------------------------


def test_pdf_simple_synthetic_conversion() -> None:
    """API pública do MarkItDown, com os conversores por omissão."""
    require("markitdown")
    from markitdown import MarkItDown

    result = MarkItDown().convert(str(PDF))
    _assert_pdf_golden(result.markdown)


def test_pdf_simple_synthetic_via_ingest_document() -> None:
    """A primitiva da plataforma: o mesmo golden set, com o `source_meta` do ADR §4."""
    require("markitdown")
    out = ing.ingest_document(PDF)
    _assert_pdf_golden(out["content"])
    meta = out["source_meta"]
    assert meta["document_type"] == "pdf"
    assert meta["uri"] == PDF.as_posix()
    # O PdfConverter (0.1.8) não lê o /Title dos metadados: o título vem do nome do ficheiro,
    # com aviso. Se um dia o ler, este assert falha e o golden passa a ser o TITLE.
    assert meta["title"] == PDF.stem
    assert out["warnings"] == ["title_from_filename"]
