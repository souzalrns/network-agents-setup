"""F3b: match_knowledge_v3 (autoridade e supersessão) contra Postgres + pgvector descartável.

Prova as P-31 = D, P-32 = B e P-33 = B sobre a migração
`scripts/migrations/f3b_authority_v3.sql`:
- aditiva e idempotente: corre 2 vezes sobre o schema com a F3a e dados já gravados;
  a `match_knowledge` e a `match_knowledge_v2` não mudam;
- sem autoridade gravada = `curado` (as fontes de hoje e as linhas do MCP);
- devolve tudo por omissão, com a autoridade e o `superseded_by`; `min_authority` filtra;
  valor desconhecido = erro (nunca um RAG vazio em silêncio);
- a BD recusa um nível desconhecido e um `superseded_by` sem `status = 'superseded'`.

Reutiliza a BD e o `ingest_apply` real do test_f3_provenance.py. Com RAG_TEST_REQUIRED=1
(CI), a falta da BD é erro.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from tests.test_f3_provenance import (  # noqa: E402
    BASE_SQL,
    DB_URL,
    MIGRATION_SQL,
    _drop,
    _fake_embed,
    _ingest_apply,
    _v2,
    _write_doc,
)

pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida (Postgres descartavel com pgvector; "
    "nunca o Supabase de producao)",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_SQL = (REPO_ROOT / "scripts" / "migrations" / "f3b_authority_v3.sql").read_text(
    encoding="utf-8"
)
Q = "ataque activo autorização"


@pytest.fixture
def v3_db():
    schema = f"f3b_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        admin.execute(f"CREATE SCHEMA {schema}")

    def _open():
        return psycopg.connect(DB_URL, autocommit=False, options=f"-c search_path={schema},public")

    for sql in (BASE_SQL, MIGRATION_SQL, V3_SQL):
        with _open() as c:
            c.execute(sql)
    try:
        yield _open
    finally:
        _drop(schema)


def _v3(opener, agent: str, question: str, filters: dict | None = None, k: int = 10):
    with opener() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT source, status, authority, superseded_by, uri, title FROM match_knowledge_v3("
            "query_embedding => %s::vector, match_agent_id => %s, match_count => %s, "
            "filters => %s::jsonb)",
            (_fake_embed(question), agent, k, json.dumps(filters or {})),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


def _ingest(ia, *rels: str) -> None:
    for rel in rels:
        out = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
        assert out["action"] == "OK", out


def test_migracao_v3_idempotente_e_nao_mexe_na_v2(v3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, v3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/manual.md")
    _ingest(ia, rel)
    before = _v2(v3_db, "security", Q)
    with v3_db() as conn:  # 2.ª vez: idempotente
        conn.execute(V3_SQL)
    assert _v2(v3_db, "security", Q) == before
    with v3_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM pg_constraint WHERE conname IN "
            "('knowledge_sources_authority_check', 'knowledge_sources_superseded_by_check')"
        )
        assert cur.fetchone()[0] == 2
        cur.execute("SELECT * FROM match_knowledge(%s::vector, 'security', 4)", (_fake_embed(Q),))
        assert [d.name for d in cur.description] == ["id", "content", "source", "similarity"]


def test_fonte_de_hoje_e_linha_do_mcp_ficam_curado(v3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, v3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/manual.md")
    _ingest(ia, rel)
    with v3_db() as conn:
        conn.execute(
            "INSERT INTO knowledge_chunks (agent_id, source, content, embedding) "
            "VALUES ('security', 'mcp-nota', 'nota do MCP: ataque activo', %s::vector)",
            (_fake_embed("nota do MCP ataque activo"),),
        )
        conn.commit()
        meta = conn.execute("SELECT meta FROM knowledge_sources").fetchone()[0]
    assert meta == {}  # nada gravado: o default vem do SQL
    hits = _v3(v3_db, "security", Q)
    assert {h["source"] for h in hits} == {rel, "mcp-nota"}
    assert all(h["authority"] == "curado" and h["superseded_by"] is None for h in hits)


def test_v3_devolve_tudo_e_min_authority_filtra(v3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, v3_db)
    oficial = _write_doc(
        tmp_path, "docs/knowledge/ingested/lei.md", body="# Lei\n\nAtaque activo: crime.\n",
        meta={"authority": "oficial"},
    )
    curado = _write_doc(tmp_path, "docs/knowledge/manual.md")
    exp = _write_doc(
        tmp_path, "docs/knowledge/ingested/blog.md", body="# Blog\n\nAtaque activo é ok.\n",
        meta={"authority": "experimental"},
    )
    _ingest(ia, oficial, curado, exp)

    def by_source(filters=None):
        return {h["source"]: h["authority"] for h in _v3(v3_db, "security", Q, filters)}

    assert by_source() == {oficial: "oficial", curado: "curado", exp: "experimental"}
    assert by_source({"min_authority": "experimental"}) == by_source()
    assert by_source({"min_authority": "curado"}) == {oficial: "oficial", curado: "curado"}
    assert by_source({"min_authority": "oficial"}) == {oficial: "oficial"}
    assert set(by_source({"min_authority": "oficial", "document_type": "md"})) == set()
    with pytest.raises(psycopg.errors.InvalidParameterValue, match="min_authority"):
        _v3(v3_db, "security", Q, {"min_authority": "maxima"})


def test_supersessao_explicita(v3_db, monkeypatch, tmp_path) -> None:
    """P-31 = D: a antiga sai por omissão (status) e, pedida, traz o superseded_by."""
    ia = _ingest_apply(monkeypatch, tmp_path, v3_db)
    nova = _write_doc(tmp_path, "docs/knowledge/ingested/v2.md", body="# V2\n\nAtaque activo: 2.\n",
                      meta={})
    velha = _write_doc(
        tmp_path, "docs/knowledge/ingested/v1.md",
        meta={"status": "superseded", "superseded_by": "docs/knowledge/ingested/v2.md"},
    )
    _ingest(ia, nova, velha)
    assert {h["source"] for h in _v3(v3_db, "security", Q)} == {nova}
    ambas = {h["source"]: h for h in _v3(v3_db, "security", Q, {"status": "any"})}
    assert ambas[velha]["superseded_by"] == "docs/knowledge/ingested/v2.md"
    assert ambas[velha]["status"] == "superseded" and ambas[nova]["superseded_by"] is None


def test_autoridade_mudada_no_sidecar_e_so_meta_updated(v3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, v3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={})
    _ingest(ia, rel)
    n_embeds = len(ia.embedded)
    _write_doc(tmp_path, rel, meta={"authority": "oficial"})  # o .md é o mesmo
    again = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert again == {"action": "META_UPDATED", "chunks": 0, "deleted": 0}
    assert len(ia.embedded) == n_embeds
    assert [h["authority"] for h in _v3(v3_db, "security", Q)] and all(
        h["authority"] == "oficial" for h in _v3(v3_db, "security", Q)
    )


def test_bd_recusa_autoridade_e_supersessao_invalidas(v3_db) -> None:
    with v3_db() as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "INSERT INTO knowledge_sources (source_path, content_hash, agent_id, meta) "
                "VALUES ('x.md', 'h', 'global', '{\"authority\": \"maxima\"}')"
            )
    with v3_db() as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "INSERT INTO knowledge_sources (source_path, content_hash, agent_id, meta) "
                "VALUES ('y.md', 'h', 'global', '{\"superseded_by\": \"z.md\"}')"
            )
