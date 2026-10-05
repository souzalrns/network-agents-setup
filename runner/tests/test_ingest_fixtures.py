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
import io
import re
import sys
import zipfile
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
docx_gen = _load("fixture_docx_generator", FIXTURES / "docx" / "generate_simple_synthetic.py")
xlsx_gen = _load("fixture_xlsx_generator", FIXTURES / "xlsx" / "generate_simple_synthetic.py")
PDF = FIXTURES / "pdf" / "simple_synthetic.pdf"
DOCX = FIXTURES / "docx" / "simple_synthetic.docx"
XLSX = FIXTURES / "xlsx" / "simple_synthetic.xlsx"
GENERATOR_TAG = b"network-agents-setup fixture generator"


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
    assert GENERATOR_TAG in data  # gerada pelo script, não à mão


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


# --- T6c: DOCX e XLSX ------------------------------------------------------------------


def _zip_entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def _assert_reproducible_zip(package: str, module: str, gen, fixture: Path) -> None:
    """Compara o conteúdo de cada entrada do ZIP, não os bytes comprimidos.

    A saída do deflate pode variar com a versão da zlib (local vs CI); o conteúdo não.
    """
    require(module)
    from importlib.metadata import version

    installed, pinned = version(package), _pinned(package)
    if installed != pinned:
        pytest.skip(f"{package} {installed} instalado; o conteúdo só é estável com o pin {pinned}")
    assert _zip_entries(gen.build()) == _zip_entries(fixture.read_bytes()), (
        f"a fixture {fixture.name} não é a saída do gerador: correr "
        f"`python runner/tests/fixtures/ingest/{fixture.suffix[1:]}/generate_simple_synthetic.py`"
        " e commitar"
    )


@pytest.mark.parametrize("fixture", [DOCX, XLSX], ids=["docx", "xlsx"])
def test_fixtures_ooxml_cumprem_as_regras(fixture: Path) -> None:
    data = fixture.read_bytes()
    assert len(data) <= MAX_FIXTURE_BYTES
    assert zipfile.is_zipfile(fixture)
    entries = _zip_entries(data)
    assert GENERATOR_TAG in entries["docProps/core.xml"]  # gerada pelo script, não à mão
    # ZIP normalizado: datas fixas em todas as entradas
    with zipfile.ZipFile(fixture) as zf:
        assert {i.date_time for i in zf.infolist()} == {(2026, 1, 1, 0, 0, 0)}


def test_golden_docx_e_xlsx_tem_a_estrutura_pedida() -> None:
    assert len(docx_gen.ITEMS) == 3
    assert len(docx_gen.TABLE) == 3 and all(len(row) == 3 for row in docx_gen.TABLE)
    assert set(xlsx_gen.SHEETS) == {"Custos", "Notas"}
    sheet, cell = xlsx_gen.FORMULA_CELL
    col, row = ord(cell[0]) - ord("A"), int(cell[1:]) - 1
    assert str(xlsx_gen.SHEETS[sheet][row][col]).startswith("=")


def test_fixture_docx_e_reprodutivel() -> None:
    _assert_reproducible_zip("python-docx", "docx", docx_gen, DOCX)


def test_fixture_xlsx_e_reprodutivel() -> None:
    _assert_reproducible_zip("openpyxl", "openpyxl", xlsx_gen, XLSX)


def _assert_docx_golden(markdown: str) -> None:
    assert markdown.strip(), "conversão vazia"
    # Ao contrário do PDF, o DOCX tem headings semânticos: o título sai como `#`.
    assert f"# {docx_gen.TITLE}" in markdown.splitlines()
    assert docx_gen.PARAGRAPH in markdown
    for item in docx_gen.ITEMS:
        assert re.search(rf"^[*-] {re.escape(item)}$", markdown, re.MULTILINE), item
    # Com o w:tblHeader, a 1.ª linha é o cabeçalho da tabela Markdown.
    assert _table_rows(markdown) == [list(row) for row in docx_gen.TABLE]


def test_docx_simple_synthetic_conversion() -> None:
    """API pública do MarkItDown, com os conversores por omissão."""
    require("markitdown")
    from markitdown import MarkItDown

    _assert_docx_golden(MarkItDown().convert(str(DOCX)).markdown)


def test_docx_simple_synthetic_via_ingest_document() -> None:
    require("markitdown")
    out = ing.ingest_document(DOCX)
    _assert_docx_golden(out["content"])
    assert out["source_meta"]["document_type"] == "docx"


def _cell_matches(expected, actual: str) -> bool:
    """Texto igual; número igual em valor (o pandas mostra 300 como `300.0` numa coluna com
    `NaN`); fórmula sem cache e célula vazia = `NaN`."""
    if expected is None or (isinstance(expected, str) and expected.startswith("=")):
        return actual == "NaN"
    if isinstance(expected, int | float):
        return float(actual) == float(expected)
    return actual == expected


def _assert_xlsx_golden(markdown: str) -> None:
    assert markdown.strip(), "conversão vazia"
    rows = _table_rows(markdown)
    for name, sheet_rows in xlsx_gen.SHEETS.items():
        assert f"## {name}" in markdown.splitlines()  # cada folha é uma secção
        for expected in sheet_rows:
            assert any(
                len(actual) == len(expected)
                and all(_cell_matches(e, a) for e, a in zip(expected, actual, strict=True))
                for actual in rows
            ), f"linha {expected} da folha {name} não está no Markdown"
    assert markdown.index("## Custos") < markdown.index("## Notas")  # ordem das folhas


def test_xlsx_simple_synthetic_conversion() -> None:
    """API pública do MarkItDown: 2 folhas, texto, números, 1 fórmula e 1 célula vazia."""
    require("markitdown")
    from markitdown import MarkItDown

    _assert_xlsx_golden(MarkItDown().convert(str(XLSX)).markdown)


def test_xlsx_simple_synthetic_via_ingest_document() -> None:
    """O mesmo golden set, e o aviso das 2 células `NaN` (fórmula sem cache + célula vazia)."""
    require("markitdown")
    out = ing.ingest_document(XLSX)
    _assert_xlsx_golden(out["content"])
    assert out["source_meta"]["document_type"] == "xlsx"
    assert "xlsx_nan_cells=2" in out["warnings"]


def test_geradores_nao_mexem_no_sys_path() -> None:
    # Com `fixtures/ingest` no sys.path, a pasta `docx/` passava a importar como `docx`,
    # a fazer-se passar pelo python-docx (achado no T6c).
    ingest_dir = str(FIXTURES)
    assert all(Path(p).resolve() != FIXTURES for p in sys.path if p), ingest_dir
