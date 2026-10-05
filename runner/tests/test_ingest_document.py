"""F1 / T6a: primitiva `ingest_document` (scripts/ingest_document.py), contrato do ADR-INGESTION-PRIMITIVES.

2 camadas:
- contrato (correm sempre, sem o pacote `markitdown`): erros do ADR §3 item 6, tectos do §5
  (mitigação 2: ZIP que descomprime acima do tecto, sem chegar ao adapter), normalização,
  `source_meta` do §4, pin em `runner/requirements-ingest.txt` e CLI;
- smoke com o MarkItDown real (documentos sintéticos gerados em `tmp_path`, nada versionado).
  O `markitdown` está fora do `requirements.txt` (puxa o onnxruntime, entre outros):
  `tests/optional_deps.py` dá skip em local sem ele e erro no job `test-ingest` do CI (T6b).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from tests.optional_deps import require

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    name = "ingest_document"
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts/ingest_document.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # o @dataclass precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


ing = _load()


def _nunca_chamar(path: Path, document_type: str):
    raise AssertionError(f"o adapter não devia ser chamado para {path}")


def _fake(markdown: str, title: str | None = None):
    return lambda path, document_type: ing.Converted(markdown=markdown, title=title)


def _file(tmp_path: Path, name: str, data: bytes = b"%PDF-1.4 sintetico") -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


def _zip(tmp_path: Path, name: str, entries: dict[str, bytes]) -> Path:
    p = tmp_path / name
    with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry, data in entries.items():
            zf.writestr(entry, data)
    return p


# --- contrato: recusas antes do adapter -------------------------------------------------


@pytest.mark.parametrize("name", ["notas.txt", "slides.pptx", "pagina.html", "sem_extensao"])
def test_formato_fora_do_spike_da_unsupported_format(tmp_path: Path, name: str) -> None:
    p = _file(tmp_path, name)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_nunca_chamar)
    assert exc.value.code == "unsupported_format"


def test_extensao_em_maiusculas_e_aceite(tmp_path: Path) -> None:
    p = _file(tmp_path, "RELATORIO.PDF")
    out = ing.ingest_document(p, converter=_fake("texto"))
    assert out["source_meta"]["document_type"] == "pdf"


def test_ficheiro_inexistente_da_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ing.ingest_document(tmp_path / "nao-existe.pdf", converter=_nunca_chamar)


def test_acima_do_max_bytes_da_too_large(tmp_path: Path) -> None:
    p = _file(tmp_path, "grande.pdf", b"x" * 100)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, max_bytes=10, converter=_nunca_chamar)
    assert exc.value.code == "too_large"


def test_zip_bomb_numa_entrada_da_decompression_limit(tmp_path: Path) -> None:
    # 2 MB de zeros comprimem para poucos KB: o ficheiro é pequeno, a descompressão não.
    p = _zip(tmp_path, "bomba.docx", {"word/document.xml": b"\0" * (2 * 1024 * 1024)})
    assert p.stat().st_size < 64 * 1024
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, max_uncompressed=1024 * 1024, converter=_nunca_chamar)
    assert exc.value.code == "decompression_limit"
    assert "word/document.xml" in str(exc.value)


def test_zip_bomb_no_total_da_decompression_limit(tmp_path: Path) -> None:
    entries = {f"xl/worksheets/sheet{i}.xml": b"\0" * (400 * 1024) for i in range(3)}
    p = _zip(tmp_path, "bomba.xlsx", entries)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, max_uncompressed=1024 * 1024, converter=_nunca_chamar)
    assert exc.value.code == "decompression_limit"
    assert "total" in str(exc.value)


def test_zip_abaixo_do_tecto_chega_ao_adapter(tmp_path: Path) -> None:
    p = _zip(tmp_path, "ok.docx", {"word/document.xml": b"<w/>"})
    out = ing.ingest_document(p, converter=_fake("# Ok"))
    assert out["source_meta"]["document_type"] == "docx"


@pytest.mark.parametrize(
    ("name", "data"),
    [("falso.pdf", b"nao e um pdf"), ("falso.docx", b"nao e um zip"), ("falso.xlsx", b"%PDF-1.4")],
)
def test_conteudo_que_nao_bate_com_a_extensao_da_unsupported_format(
    tmp_path: Path, name: str, data: bytes
) -> None:
    # O MarkItDown 0.1.8 converteria o falso.pdf como texto, sem erro (smoke abaixo).
    p = _file(tmp_path, name, data)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_nunca_chamar)
    assert exc.value.code == "unsupported_format"


def test_pdf_com_lixo_antes_da_assinatura_e_aceite(tmp_path: Path) -> None:
    p = _file(tmp_path, "doc.pdf", b"\n\n%PDF-1.7 resto")
    assert ing.ingest_document(p, converter=_fake("ok"))["content"] == "ok\n"


def test_zip_estragado_da_conversion_failed(tmp_path: Path, monkeypatch) -> None:
    # Passa na assinatura, mas o directório central não se lê.
    p = _file(tmp_path, "estragado.xlsx", b"PK")
    monkeypatch.setattr(ing.zipfile, "is_zipfile", lambda path: True)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_nunca_chamar)
    assert exc.value.code == "conversion_failed"


def test_pdf_nao_passa_pelo_controlo_de_zip(tmp_path: Path) -> None:
    # O PDF não é ZIP: o tecto de descompressão não se aplica (o limite de memória é o T6b).
    p = _file(tmp_path, "doc.pdf")
    out = ing.ingest_document(p, max_uncompressed=1, converter=_fake("texto"))
    assert out["content"] == "texto\n"


# --- contrato: saída ---------------------------------------------------------------------


def test_saida_tem_o_contrato_e_o_source_meta_minimo(tmp_path: Path) -> None:
    p = _file(tmp_path, "politica.pdf")
    out = ing.ingest_document(
        p, converter=_fake("# Política\r\n\nlinha com espaços   \n\n\n", None)
    )

    assert set(out) == {"content", "source_meta", "warnings"}
    assert out["content"] == "# Política\n\nlinha com espaços\n"
    meta = out["source_meta"]
    assert set(meta) == {"uri", "title", "document_type", "retrieved_at", "content_hash", "status"}
    assert meta["uri"] == p.as_posix()
    assert meta["document_type"] == "pdf"
    assert meta["status"] == "active"
    assert meta["content_hash"] == hashlib.sha256(out["content"].encode("utf-8")).hexdigest()
    assert datetime.fromisoformat(meta["retrieved_at"]).utcoffset().total_seconds() == 0
    # sem título do adapter: usa o nome do ficheiro e avisa (nunca em silêncio)
    assert meta["title"] == "politica"
    assert out["warnings"] == ["title_from_filename"]


def test_titulo_do_adapter_nao_gera_aviso(tmp_path: Path) -> None:
    p = _file(tmp_path, "x.pdf")
    out = ing.ingest_document(p, converter=_fake("corpo", "  Título real  "))
    assert out["source_meta"]["title"] == "Título real"
    assert out["warnings"] == []


def test_content_hash_e_o_mesmo_do_t6_para_o_ficheiro_gravado(tmp_path: Path) -> None:
    # S4 grava o `content` tal como está; o T6 faz o hash dos bytes do ficheiro (sha256_file).
    p = _file(tmp_path, "x.pdf")
    out = ing.ingest_document(p, converter=_fake("á\r\nb"))
    gravado = tmp_path / "x.md"
    gravado.write_text(out["content"], encoding="utf-8", newline="")
    assert hashlib.sha256(gravado.read_bytes()).hexdigest() == out["source_meta"]["content_hash"]


@pytest.mark.parametrize("markdown", ["", "   \n\n\t\n"])
def test_conversao_vazia_da_empty_content(tmp_path: Path, markdown: str) -> None:
    p = _file(tmp_path, "vazio.pdf")
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_fake(markdown))
    assert exc.value.code == "empty_content"


def test_codigo_fora_do_contrato_e_recusado() -> None:
    with pytest.raises(ValueError):
        ing.IngestError("inventado", "x")
    assert set(ing.ERROR_CODES) == {
        "unsupported_format",
        "too_large",
        "decompression_limit",
        "conversion_failed",
        "empty_content",
        "missing_provenance",
    }


def test_sem_markitdown_da_conversion_failed_com_o_comando(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "markitdown", None)  # o import passa a falhar
    p = _file(tmp_path, "doc.pdf")
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p)
    assert exc.value.code == "conversion_failed"
    assert "requirements-ingest.txt" in str(exc.value)


# --- pin e CLI ---------------------------------------------------------------------------


def test_pin_do_markitdown_fica_a_parte_e_com_o_minimo_do_adr() -> None:
    ingest_reqs = (REPO_ROOT / "runner/requirements-ingest.txt").read_text(encoding="utf-8")
    pins = [ln for ln in ingest_reqs.splitlines() if ln.startswith("markitdown")]
    assert len(pins) == 1
    m = re.fullmatch(r"markitdown(\[[a-z,]+\])?>=(\d+)\.(\d+)\.(\d+)", pins[0])
    assert m, pins[0]
    assert tuple(int(x) for x in m.groups()[1:]) >= (0, 1, 4)  # CVE-2025-64512 (ADR §5)
    assert set(m.group(1).strip("[]").split(",")) >= {"docx", "pdf", "xlsx"}
    # O runner base e o CI continuam sem o markitdown.
    base = (REPO_ROOT / "runner/requirements.txt").read_text(encoding="utf-8")
    assert "markitdown" not in base


def test_cli_uso_errado_da_2(capsys) -> None:
    assert ing.main([]) == 2
    assert "uso:" in capsys.readouterr().err


def test_cli_erro_tipado_sai_em_json(tmp_path: Path, capsys) -> None:
    p = _file(tmp_path, "notas.txt")
    assert ing.main([str(p)]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "unsupported_format"


# --- smoke com o MarkItDown real ---------------------------------------------------------


def _markitdown():
    return require("markitdown")


def test_smoke_versao_instalada_cumpre_o_pin() -> None:
    _markitdown()
    from importlib.metadata import version

    major, minor, patch = (int(x) for x in version("markitdown").split(".")[:3])
    assert (major, minor, patch) >= (0, 1, 4)


def test_smoke_xlsx_real_preserva_a_tabela(tmp_path: Path) -> None:
    _markitdown()
    openpyxl = require("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Custos"
    ws.append(["Fornecedor", "Mensal"])
    ws.append(["Vercel", 0])
    ws.append(["Supabase", 0])
    p = tmp_path / "custos.xlsx"
    wb.save(p)

    out = ing.ingest_document(p)
    assert out["source_meta"]["document_type"] == "xlsx"
    assert "Custos" in out["content"]
    linhas = [ln for ln in out["content"].splitlines() if ln.startswith("|")]
    assert any("Fornecedor" in ln and "Mensal" in ln for ln in linhas)
    assert any("Supabase" in ln for ln in linhas)


def test_smoke_docx_real_mantem_o_titulo_e_o_texto(tmp_path: Path) -> None:
    _markitdown()
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    document = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {w}><w:body>'
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Politica de acesso</w:t></w:r></w:p>'
        "<w:p><w:r><w:t>Nunca ataque activo sem autorizacao escrita.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    ct = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    p = _zip(
        tmp_path,
        "politica.docx",
        {
            "[Content_Types].xml": ct.encode(),
            "_rels/.rels": rels.encode(),
            "word/document.xml": document.encode(),
        },
    )

    out = ing.ingest_document(p)
    assert out["source_meta"]["document_type"] == "docx"
    assert "Nunca ataque activo sem autorizacao escrita." in out["content"]
    assert "Politica de acesso" in out["content"]


def _pdf_minimo(texto: str) -> bytes:
    """PDF 1.4 de 1 página com 1 linha de texto (Helvetica), com a tabela xref certa."""
    stream = f"BT /F1 12 Tf 72 720 Td ({texto}) Tj ET".encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def test_smoke_pdf_real_extrai_o_texto(tmp_path: Path) -> None:
    _markitdown()
    p = _file(tmp_path, "politica.pdf", _pdf_minimo("Nunca ataque activo sem autorizacao."))
    out = ing.ingest_document(p)
    assert out["source_meta"]["document_type"] == "pdf"
    assert "Nunca ataque activo sem autorizacao." in out["content"]


def test_smoke_markitdown_sozinho_converte_um_pdf_falso_como_texto(tmp_path: Path) -> None:
    # Porque existe o check_signature: sem ele, o `document_type` seria "pdf" para um texto.
    _markitdown()
    from markitdown import MarkItDown

    p = _file(tmp_path, "falso.pdf", b"nao e um pdf")
    assert "nao e um pdf" in MarkItDown(enable_plugins=False).convert_local(p).markdown
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p)
    assert exc.value.code == "unsupported_format"


def test_smoke_pdf_real_estragado_da_conversion_failed_ou_empty_content(tmp_path: Path) -> None:
    _markitdown()
    p = _file(tmp_path, "estragado.pdf", b"%PDF-1.4\n1 0 obj << /Type /Catalog >>")
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p)
    assert exc.value.code in {"conversion_failed", "empty_content"}
