"""F1 / T6d: segurança de entrada do `ingest_document` (ADR-INGESTION-PRIMITIVES §5).

Casos negativos, cada um com a rejeição e uma mensagem útil, sem derrubar o processo pai:
- ficheiro excessivamente grande → `too_large` (antes de abrir o conteúdo);
- bomba de descompressão (ZIP) → `decompression_limit` (antes do processo filho);
- ficheiro corrompido / assinatura inválida → `unsupported_format` ou `conversion_failed`;
- tempo esgotado → `timeout` (o filho é morto);
- memória esgotada → `memory_limit` (o filho bate no `RLIMIT_DATA`; só Linux);
- o filho morre com um sinal → `conversion_failed` com o sinal na mensagem.

Os alvos do processo filho que simulam o abuso são escritos em `tmp_path` (`target=`), por
isso estes testes não precisam do `markitdown`. Os 2 testes no fim usam o MarkItDown real.
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
import time
import zipfile
from pathlib import Path

import pytest

from tests.optional_deps import require

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"
MIB = 1024 * 1024
LINUX = sys.platform.startswith("linux")


def _load():
    name = "ingest_document"
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts/ingest_document.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ing = _load()


def _target(tmp_path: Path, body: str) -> str:
    """Escreve um alvo `convert(path, document_type)` para o processo filho."""
    f = tmp_path / "alvo_filho.py"
    f.write_text(
        "from types import SimpleNamespace\n"
        "def convert(path, document_type):\n" + textwrap.indent(textwrap.dedent(body), "    "),
        encoding="utf-8",
    )
    return f"{f}:convert"


def _pdf(tmp_path: Path, name: str = "doc.pdf", data: bytes = b"%PDF-1.4 sintetico") -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


# --- processo filho: o caminho feliz e o protocolo -------------------------------------


def test_filho_devolve_o_resultado_e_os_avisos(tmp_path: Path) -> None:
    target = _target(
        tmp_path,
        "return SimpleNamespace(markdown='# Ok', title='T', warnings=('aviso_do_adapter',))",
    )
    out = ing.isolated_converter(_pdf(tmp_path), "pdf", target=target)
    assert out.markdown == "# Ok" and out.title == "T"
    assert "aviso_do_adapter" in out.warnings


def test_stdout_das_bibliotecas_nao_interfere(tmp_path: Path) -> None:
    # O resultado vai por ficheiro: lixo no stdout (avisos de bibliotecas) não estraga o JSON.
    target = _target(tmp_path, "print('{lixo'); return SimpleNamespace(markdown='texto')")
    assert ing.isolated_converter(_pdf(tmp_path), "pdf", target=target).markdown == "texto"


def test_erro_tipado_do_filho_chega_ao_pai_com_o_codigo(tmp_path: Path) -> None:
    target = _target(
        tmp_path,
        """
        class E(Exception):
            code = "empty_content"
            detail = "nada para converter"
        raise E()
        """,
    )
    with pytest.raises(ing.IngestError) as exc:
        ing.isolated_converter(_pdf(tmp_path), "pdf", target=target)
    assert exc.value.code == "empty_content"
    assert "nada para converter" in str(exc.value)


def test_excepcao_qualquer_do_filho_da_conversion_failed(tmp_path: Path) -> None:
    target = _target(tmp_path, "raise ValueError('rebentou')")
    with pytest.raises(ing.IngestError) as exc:
        ing.isolated_converter(_pdf(tmp_path), "pdf", target=target)
    assert exc.value.code == "conversion_failed"
    assert "ValueError: rebentou" in str(exc.value)


def test_ingest_document_usa_o_processo_filho_por_omissao(tmp_path: Path, monkeypatch) -> None:
    chamadas = []

    def espiao(path, document_type, *, timeout_s, memory_limit):
        chamadas.append((document_type, timeout_s, memory_limit))
        return ing.Converted(markdown="ok", title="T")

    monkeypatch.setattr(ing, "isolated_converter", espiao)
    ing.ingest_document(_pdf(tmp_path), timeout_s=7, memory_limit=512 * MIB)
    assert chamadas == [("pdf", 7, 512 * MIB)]


# --- recusas antes de converter ---------------------------------------------------------


def test_ficheiro_grande_e_recusado_antes_do_filho(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ing, "isolated_converter", _nunca)
    p = _pdf(tmp_path, data=b"%PDF-1.4" + b"\0" * 4096)
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, max_bytes=1024)
    assert exc.value.code == "too_large"
    assert "tecto 1024" in str(exc.value)


def test_bomba_zip_e_recusada_antes_do_filho(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ing, "isolated_converter", _nunca)
    p = tmp_path / "bomba.docx"
    with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", b"\0" * (8 * MIB))  # 8 MiB → poucos KB
    assert p.stat().st_size < 64 * 1024
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, max_uncompressed=4 * MIB)
    assert exc.value.code == "decompression_limit"


@pytest.mark.parametrize("fmt", ["docx", "xlsx"])
def test_zip_truncado_da_conversion_failed_e_nao_formato_errado(tmp_path: Path, fmt) -> None:
    # Começa como ZIP (PK\x03\x04) mas perdeu o directório central: é corrupção, não outro
    # formato. Antes do T6d dava `unsupported_format` ("não é DOCX"), o que enganava.
    data = (FIXTURES / fmt / f"simple_synthetic.{fmt}").read_bytes()
    p = tmp_path / f"truncado.{fmt}"
    p.write_bytes(data[: len(data) // 2])
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_nunca)
    assert exc.value.code == "conversion_failed"
    assert "ZIP corrompido" in str(exc.value)


def test_assinatura_invalida_continua_unsupported_format(tmp_path: Path) -> None:
    p = tmp_path / "texto.docx"
    p.write_bytes(b"isto e texto, nao um zip")
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(p, converter=_nunca)
    assert exc.value.code == "unsupported_format"


def _nunca(*args, **kwargs):
    raise AssertionError("o conversor não devia ser chamado")


# --- recursos: tempo, memória, sinais ---------------------------------------------------


def test_timeout_mata_o_filho_e_da_timeout(tmp_path: Path) -> None:
    target = _target(tmp_path, "import time; time.sleep(30)")
    inicio = time.monotonic()
    with pytest.raises(ing.IngestError) as exc:
        ing.isolated_converter(_pdf(tmp_path), "pdf", timeout_s=1, target=target)
    assert exc.value.code == "timeout"
    assert "1 s" in str(exc.value)
    assert time.monotonic() - inicio < 15  # não esperou pelos 30 s


@pytest.mark.skipif(not LINUX, reason="o RLIMIT_DATA só é aplicado em Linux")
def test_memoria_acima_do_limite_da_memory_limit(tmp_path: Path) -> None:
    # Pede 512 MiB com um limite de 128 MiB: o filho apanha o MemoryError e reporta-o.
    target = _target(tmp_path, "buf = bytearray(512 * 1024 * 1024)\nreturn None")
    with pytest.raises(ing.IngestError) as exc:
        ing.isolated_converter(_pdf(tmp_path), "pdf", memory_limit=128 * MIB, target=target)
    assert exc.value.code == "memory_limit"
    assert str(128 * MIB) in str(exc.value)


@pytest.mark.skipif(not LINUX, reason="o RLIMIT_DATA só é aplicado em Linux")
def test_memoria_abaixo_do_limite_passa(tmp_path: Path) -> None:
    target = _target(
        tmp_path, "buf = bytearray(32 * 1024 * 1024)\nreturn SimpleNamespace(markdown='ok')"
    )
    out = ing.isolated_converter(_pdf(tmp_path), "pdf", memory_limit=256 * MIB, target=target)
    assert out.markdown == "ok"
    assert out.warnings == ()


@pytest.mark.skipif(not LINUX, reason="sinais POSIX")
def test_filho_que_morre_com_sinal_da_conversion_failed(tmp_path: Path) -> None:
    target = _target(tmp_path, "import os; os.abort()")
    with pytest.raises(ing.IngestError) as exc:
        ing.isolated_converter(_pdf(tmp_path), "pdf", target=target)
    assert exc.value.code == "conversion_failed"
    assert "sinal 6" in str(exc.value)  # SIGABRT


@pytest.mark.parametrize(
    ("platform", "esperado"),
    [("linux", True), ("win32", False), ("darwin", False), ("cygwin", False)],
)
def test_limite_de_memoria_so_em_linux(platform: str, esperado: bool) -> None:
    assert ing.memory_limit_supported(platform) is esperado


def test_sem_limite_de_memoria_fora_de_linux_avisa(tmp_path: Path, monkeypatch) -> None:
    # Só a decisão (no processo de teste não se aplica nenhum limite): fora de Linux, o aviso.
    monkeypatch.setattr(ing, "memory_limit_supported", lambda platform=None: False)
    assert ing.apply_memory_limit(512 * MIB) == ["memory_limit_unavailable"]
    assert ing.apply_memory_limit(None) == []


# --- CLI -----------------------------------------------------------------------------------


def test_cli_passa_os_limites(tmp_path: Path, monkeypatch, capsys) -> None:
    recebido = {}

    def falso(path, **kwargs):
        recebido.update(kwargs)
        raise ing.IngestError("timeout", "simulado")

    monkeypatch.setattr(ing, "ingest_document", falso)
    assert ing.main([str(tmp_path / "x.pdf"), "--timeout-s", "5", "--memory-limit-mb", "256"]) == 1
    assert recebido == {"timeout_s": 5.0, "memory_limit": 256 * MIB}
    assert '"error": "timeout"' in capsys.readouterr().out


# --- MarkItDown real ---------------------------------------------------------------------


def test_fixtures_reais_convertem_dentro_dos_limites_por_omissao() -> None:
    require("markitdown")
    for fmt in ("pdf", "docx", "xlsx"):
        out = ing.ingest_document(FIXTURES / fmt / f"simple_synthetic.{fmt}")
        assert out["content"].strip()
        assert "memory_limit_unavailable" not in out["warnings"] or not LINUX


@pytest.mark.skipif(not LINUX, reason="o RLIMIT_DATA só é aplicado em Linux")
def test_markitdown_com_memoria_insuficiente_falha_limpo(tmp_path: Path) -> None:
    # Abaixo do mínimo medido (384 MiB), o MarkItDown rebenta ao carregar o onnxruntime.
    # O pai recebe um erro tipado e nenhum conteúdo parcial.
    require("markitdown")
    with pytest.raises(ing.IngestError) as exc:
        ing.ingest_document(FIXTURES / "pdf" / "simple_synthetic.pdf", memory_limit=64 * MIB)
    assert exc.value.code in {"memory_limit", "conversion_failed"}
