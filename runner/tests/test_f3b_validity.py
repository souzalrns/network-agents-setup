"""F3b, validade, ponta a ponta contra Postgres + pgvector descartável (nunca o Supabase).

- uma página web do F2 ganha `effective_until` = `retrieved_at` + 90 dias na
  `knowledge_sources`, e a `match_knowledge_v2` deixa-a de fora depois disso (fica na BD:
  com `valid_at` antigo volta a aparecer; P-29 = A);
- uma lei com sidecar sem `effective_from` é INVALID_META, sem escrita nenhuma;
- um .md de classe datada sem sidecar entra como antes, com um aviso (zero breaking change).
"""

from __future__ import annotations

import pytest

from tests import test_f3_provenance as f3
from tests.test_f3_provenance import DB_URL, _ingest_apply, _v2, _write_doc

pytestmark = pytest.mark.skipif(not DB_URL, reason="RAG_TEST_DATABASE_URL nao definida")


@pytest.fixture
def f3b_db():
    """Schema descartável com a migração F3a (a mesma do test_f3_provenance)."""
    schema, opener = f3._schema(apply_migration=True)
    try:
        yield opener
    finally:
        f3._drop(schema)


WEB = {
    "uri": "https://exemplo.pt/politica",
    "final_url": "https://exemplo.pt/politica",
    "document_type": "html",
    "retrieved_at": "2026-01-10T09:00:00+00:00",
}


def test_web_ganha_ttl_e_sai_do_retrieve_depois_de_expirar(f3b_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3b_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/pagina.md", meta=WEB)
    out = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK" and "warnings" not in out

    with f3b_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT effective_until, meta->>'effective_until_source' FROM knowledge_sources "
            "WHERE source_path = %s",
            (rel,),
        )
        until, origem = cur.fetchone()
    assert until.isoformat() == "2026-04-10T09:00:00+00:00"  # 10 de Janeiro + 90 dias
    assert origem == "ttl:90d"

    pergunta = "Nunca ataque activo"
    assert _v2(f3b_db, "security", pergunta, {"valid_at": "2026-10-06T00:00:00Z"}) == []
    antes = _v2(f3b_db, "security", pergunta, {"valid_at": "2026-02-01T00:00:00Z"})
    assert {r["source"] for r in antes} == {rel}  # continua na BD


def test_lei_com_sidecar_sem_vigencia_nao_entra(f3b_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3b_db)
    rel = _write_doc(tmp_path, "docs/knowledge/legal/lei.md", meta={})
    out = ia.apply_one(rel, "legal", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "INVALID_META" and "effective_from" in out["note"]
    assert ia.embedded == []
    with f3b_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks")
        assert cur.fetchone()[0] == 0


def test_lei_com_vigencia_entra_com_a_data(f3b_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3b_db)
    rel = _write_doc(
        tmp_path, "docs/knowledge/legal/lei.md", meta={"effective_from": "2024-01-01T00:00:00+00:00"}
    )
    out = ia.apply_one(rel, "legal", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK"
    assert _v2(f3b_db, "legal", "Nunca ataque activo", {"valid_at": "2023-06-01T00:00:00Z"}) == []
    assert len(_v2(f3b_db, "legal", "Nunca ataque activo")) == 1


def test_classe_datada_sem_sidecar_entra_como_antes_com_aviso(f3b_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3b_db)
    rel = _write_doc(tmp_path, "docs/knowledge/imobiliario/indice.md")  # sem sidecar
    out = ia.apply_one(rel, "imobiliario", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK"
    assert len(out["warnings"]) == 1 and out["warnings"][0].startswith("VALIDITY_MISSING")
    rows = _v2(f3b_db, "imobiliario", "Nunca ataque activo")
    assert len(rows) == 1 and rows[0]["status"] == "active"

    again = ia.apply_one(rel, "imobiliario", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert again["action"] == "UNCHANGED" and again["warnings"] == out["warnings"]
