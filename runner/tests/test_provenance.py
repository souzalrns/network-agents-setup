"""F3a: plan_runner.provenance (sidecar `.meta.yaml` → colunas da knowledge_sources), sem BD."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml

from plan_runner import provenance as pv

REPO_ROOT = Path(__file__).resolve().parents[2]
BODY = "# Política\n\nTexto.\n"
HASH = hashlib.sha256(BODY.encode("utf-8")).hexdigest()


def _write(tmp_path: Path, **meta) -> Path:
    md = tmp_path / "politica.md"
    md.write_text(BODY, encoding="utf-8", newline="")
    base = {
        "uri": "external:politica.pdf",
        "title": "Política",
        "document_type": "pdf",
        "retrieved_at": "2026-10-05T10:00:00+00:00",
        "content_hash": HASH,
        "status": "active",
        "warnings": ["title_from_filename"],
    }
    base.update(meta)
    (tmp_path / "politica.meta.yaml").write_text(
        yaml.safe_dump({k: v for k, v in base.items() if v is not None}, allow_unicode=True),
        encoding="utf-8",
    )
    return md


def test_sem_sidecar_devolve_none_e_o_default_vem_do_git(tmp_path: Path) -> None:
    md = tmp_path / "solto.md"
    md.write_text(BODY, encoding="utf-8")
    assert pv.load_meta(md, HASH) is None
    assert pv.default_meta("docs/knowledge/solto.md") == {
        "uri": "docs/knowledge/solto.md",
        "document_type": "md",
        "status": "active",
    }


def test_sidecar_valido_vira_colunas(tmp_path: Path) -> None:
    md = _write(tmp_path, jurisdiction="PT", effective_from="2026-01-01", final_url="https://x/y")
    meta = pv.load_meta(md, HASH)
    cols = pv.to_source_columns(meta)
    assert cols["uri"] == "external:politica.pdf"
    assert cols["final_url"] == "https://x/y"
    assert cols["document_type"] == "pdf"
    assert cols["status"] == "active"
    assert cols["jurisdiction"] == "PT"
    assert cols["retrieved_at"] == datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    assert cols["effective_from"] in (date(2026, 1, 1), datetime(2026, 1, 1))
    assert cols["effective_until"] is None
    # o resto do sidecar vai para o jsonb `meta` (sem o content_hash, que já tem coluna)
    assert cols["meta"] == {"warnings": ["title_from_filename"]}


@pytest.mark.parametrize(
    ("meta", "erro"),
    [
        ({"title": None}, "faltam campos"),
        ({"content_hash": "0" * 64}, "content_hash"),
        ({"status": "apagado"}, "status"),
        ({"effective_from": "ontem"}, "ISO 8601"),
        ({"effective_from": "2026-06-01", "effective_until": "2026-01-01"}, "depois de"),
    ],
)
def test_sidecar_invalido(tmp_path: Path, meta: dict, erro: str) -> None:
    md = _write(tmp_path, **meta)
    with pytest.raises(pv.ProvenanceError, match=erro):
        pv.load_meta(md, HASH)


def test_yaml_invalido_e_nao_mapa(tmp_path: Path) -> None:
    md = tmp_path / "x.md"
    md.write_text(BODY, encoding="utf-8")
    side = tmp_path / "x.meta.yaml"
    side.write_text("uri: [aberto", encoding="utf-8")
    with pytest.raises(pv.ProvenanceError, match="YAML"):
        pv.load_meta(md, HASH)
    side.write_text("- só uma lista", encoding="utf-8")
    with pytest.raises(pv.ProvenanceError, match="mapa"):
        pv.load_meta(md, HASH)


def test_datas_com_e_sem_fuso_comparam_sem_erro(tmp_path: Path) -> None:
    md = _write(tmp_path, effective_from="2026-01-01", effective_until="2026-06-01T00:00:00+00:00")
    assert pv.load_meta(md, HASH)["effective_until"] == datetime(2026, 6, 1, tzinfo=UTC)


def test_required_meta_igual_ao_do_f1() -> None:
    spec = importlib.util.spec_from_file_location(
        "ingest_document", REPO_ROOT / "scripts" / "ingest_document.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("ingest_document", mod)
    spec.loader.exec_module(mod)
    assert pv.REQUIRED_META == mod.REQUIRED_META
