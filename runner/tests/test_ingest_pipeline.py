"""F1 / T6e: a saída do `ingest_document` encaixa no T6 sem pipeline paralela (ADR §2, regra 2).

Sem base de dados (o ingest real contra Postgres está em `test_ingest_pipeline_rag.py`):
- `write_ingested` grava o `.md` byte a byte como o `content`: o `sha256_file` do T6
  (`scripts/ingest_delta.py`) dá o `source_meta.content_hash`;
- `validate_ingested` aplica a regra 3 do ADR (nada entra no L5 sem `source_meta` válido), e
  o MANIFEST é verificado com ela: qualquer entrada futura em `docs/knowledge/ingested/`
  precisa do `.meta.yaml` certo;
- o Markdown convertido passa pelo chunker real do T6 (`plan_runner.chunking.chunk_markdown`).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

from plan_runner.chunking import chunk_markdown
from tests.optional_deps import require

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # o @dataclass precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


ing = _load("ingest_document", "scripts/ingest_document.py")
delta = _load("ingest_delta_t6e", "scripts/ingest_delta.py")


def _result(content: str = "# Título\n\nCorpo.\n", **meta) -> dict:
    source_meta = {
        "uri": "runner/tests/fixtures/ingest/pdf/simple_synthetic.pdf",
        "title": "Título",
        "document_type": "pdf",
        "retrieved_at": "2026-10-05T00:00:00+00:00",
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "active",
        **meta,
    }
    return {"content": content, "source_meta": source_meta, "warnings": ["title_from_filename"]}


# --- write_ingested ----------------------------------------------------------------------


def test_md_gravado_tem_o_hash_do_t6(tmp_path: Path) -> None:
    result = _result("# Relatório\n\nLinha com acentos: ação, índice.\n")
    md, meta = ing.write_ingested(result, tmp_path, "relatorio")
    digest, size = delta.sha256_file(md)  # a função que o T6 usa
    assert digest == result["source_meta"]["content_hash"]
    assert size == len(result["content"].encode("utf-8"))
    saved = yaml.safe_load(meta.read_text(encoding="utf-8"))
    assert saved == {**result["source_meta"], "warnings": ["title_from_filename"]}


def test_nao_sobrepoe_sem_overwrite(tmp_path: Path) -> None:
    ing.write_ingested(_result(), tmp_path, "doc")
    with pytest.raises(FileExistsError):
        ing.write_ingested(_result("# Outro\n"), tmp_path, "doc")
    md, _ = ing.write_ingested(_result("# Outro\n"), tmp_path, "doc", overwrite=True)
    assert md.read_text(encoding="utf-8") == "# Outro\n"


@pytest.mark.parametrize(
    ("stem", "slug"),
    [("Relatório Anual 2026", "relatorio-anual-2026"), ("  ", "documento"), ("a__b", "a-b")],
)
def test_slugify(stem: str, slug: str) -> None:
    assert ing.slugify(stem) == slug


def test_uri_relativo_ao_repo_e_sem_caminho_local_fora_dele(tmp_path: Path) -> None:
    dentro = FIXTURES / "pdf" / "simple_synthetic.pdf"
    assert ing.source_uri(dentro) == ("runner/tests/fixtures/ingest/pdf/simple_synthetic.pdf", None)
    fora = tmp_path / "Relatorio.pdf"
    assert ing.source_uri(fora) == ("external:Relatorio.pdf", "uri_outside_repo")


# --- validate_ingested (regra 3 do ADR) -----------------------------------------------------


def test_validador_aceita_a_saida_do_write(tmp_path: Path) -> None:
    md, _ = ing.write_ingested(_result(), tmp_path, "doc")
    assert ing.validate_ingested(md) == []


def test_validador_sem_sidecar(tmp_path: Path) -> None:
    md = tmp_path / "solto.md"
    md.write_text("# Solto\n", encoding="utf-8")
    assert "falta o solto.meta.yaml" in ing.validate_ingested(md)[0]


def test_validador_hash_errado_e_campos_em_falta(tmp_path: Path) -> None:
    md, meta = ing.write_ingested(_result(), tmp_path, "doc")
    md.write_text("# Editado à mão depois da conversão\n", encoding="utf-8")
    data = yaml.safe_load(meta.read_text(encoding="utf-8"))
    del data["status"]
    meta.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    problems = ing.validate_ingested(md)
    assert any("content_hash" in p for p in problems)
    assert any("falta o campo status" in p for p in problems)


def test_manifest_so_tem_convertidos_com_source_meta_valido() -> None:
    """Guarda do S4: hoje não há entradas em docs/knowledge/ingested/ (pôr uma no MANIFEST
    escreve em produção no merge e é decisão do maestro). Quando houver, cada uma tem de
    passar no validador."""
    ingested = [e for e in delta.MANIFEST if e[0].startswith(f"{ing.INGESTED_DIR}/")]
    for entry in ingested:
        assert ing.validate_ingested(REPO_ROOT / entry[0]) == [], entry[0]


# --- conversão real → chunker do T6 --------------------------------------------------------


@pytest.mark.parametrize("fmt", ["pdf", "docx", "xlsx"])
def test_convertido_passa_pelo_chunker_do_t6(tmp_path: Path, fmt: str) -> None:
    require("markitdown")
    result = ing.ingest_document(FIXTURES / fmt / f"simple_synthetic.{fmt}")
    md, _ = ing.write_ingested(result, tmp_path, f"simple-{fmt}")
    rel = f"{ing.INGESTED_DIR}/simple-{fmt}.md"
    chunks = chunk_markdown(
        md.read_text(encoding="utf-8"), source_path=rel, agent_id="global", kb="global"
    )
    assert chunks, "o chunker do T6 não produziu chunks"
    joined = "\n".join(c["content"] for c in chunks)
    # nada se perde entre o conversor e o chunker: as linhas de tabela chegam inteiras
    for line in result["content"].splitlines():
        if line.startswith("|") and "---" not in line:
            assert line in joined, line
    assert all(c["citation"]["source"] == rel for c in chunks)  # a citação aponta para o .md
    assert ing.validate_ingested(md) == []


def test_cli_out_dir_grava_e_resume(tmp_path: Path, capsys) -> None:
    require("markitdown")
    pdf = FIXTURES / "pdf" / "simple_synthetic.pdf"
    assert ing.main([str(pdf), "--out-dir", str(tmp_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    md = Path(summary["md"])
    assert md.name == "simple-synthetic.md"
    assert ing.validate_ingested(md) == []
    assert "MANIFEST" in summary["next"]
    assert ing.main([str(pdf), "--out-dir", str(tmp_path)]) == 1  # não sobrepõe
    assert ing.main([str(pdf), "--out-dir", str(tmp_path), "--overwrite"]) == 0
