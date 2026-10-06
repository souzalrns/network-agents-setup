"""F3a: proveniência no retrieve, contra Postgres + pgvector descartável (nunca o Supabase).

Prova a opção A da P-26 (docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md):
- a migração `scripts/migrations/f3_provenance_retrieve.sql` é aditiva e idempotente:
  corre sobre o schema actual (`scripts/rag_schema.sql`) com dados já gravados, 2 vezes;
- o `match_knowledge` antigo não muda (o MCP continua a funcionar durante a transição);
- o `match_knowledge_v2` devolve a proveniência e filtra por status, jurisdição, tipo e
  validade; as linhas do MCP (project NULL) não herdam proveniência de uma fonte do T6;
- o writer **detecta** a migração: sem ela escreve como antes (o merge pode vir antes do SQL);
- o `ingest_apply` lê o sidecar: inválido = INVALID_META sem escrita; o .md igual com o
  sidecar mudado = META_UPDATED sem embeddings.

Reutiliza o embedder falso e o padrão do `test_rag_canonical.py`. Com RAG_TEST_REQUIRED=1
(CI), a falta da BD é erro.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

psycopg = pytest.importorskip("psycopg")

from plan_runner import supabase_writer as sw  # noqa: E402
from tests.test_rag_canonical import _fake_embed  # noqa: E402

DB_URL = os.environ.get("RAG_TEST_DATABASE_URL", "").strip()
if os.environ.get("RAG_TEST_REQUIRED") == "1" and not DB_URL:
    raise RuntimeError("RAG_TEST_REQUIRED=1 mas RAG_TEST_DATABASE_URL nao esta definida")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida (Postgres descartavel com pgvector; "
    "nunca o Supabase de producao)",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SQL = (REPO_ROOT / "scripts" / "rag_schema.sql").read_text(encoding="utf-8")
MIGRATION_SQL = (REPO_ROOT / "scripts" / "migrations" / "f3_provenance_retrieve.sql").read_text(
    encoding="utf-8"
)


def _schema(apply_migration: bool):
    schema = f"f3_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        admin.execute(f"CREATE SCHEMA {schema}")

    def _open():
        return psycopg.connect(DB_URL, autocommit=False, options=f"-c search_path={schema},public")

    with _open() as c:
        c.execute(BASE_SQL)
    if apply_migration:
        with _open() as c:
            c.execute(MIGRATION_SQL)
    return schema, _open


def _drop(schema: str) -> None:
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def base_db():
    """O schema de produção de hoje (sem a migração F3a)."""
    schema, opener = _schema(apply_migration=False)
    try:
        yield opener
    finally:
        _drop(schema)


@pytest.fixture
def f3_db():
    schema, opener = _schema(apply_migration=True)
    try:
        yield opener
    finally:
        _drop(schema)


def _ingest_apply(monkeypatch, tmp_path: Path, opener):
    """O apply_one real, com o embedder falso e o connect() desta BD."""
    monkeypatch.setattr(os, "environ", dict(os.environ))
    spec = importlib.util.spec_from_file_location(
        "ingest_apply_f3", REPO_ROOT / "scripts" / "ingest_apply.py"
    )
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)

    @contextmanager
    def test_connect():
        with opener() as conn:
            yield conn

    embedded: list[str] = []
    monkeypatch.setattr(ia, "connect", test_connect)
    monkeypatch.setattr(ia, "embed_text", lambda t: embedded.append(t) or _fake_embed(t))
    monkeypatch.setattr(ia, "ROOT", tmp_path)
    ia.embedded = embedded
    return ia


DOC = """# Política de acesso

## Regra

Nunca ataque activo sem autorização escrita do cliente.
"""


def _write_doc(root: Path, rel: str, body: str = DOC, meta: dict | None = None) -> str:
    md = root / rel
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(body, encoding="utf-8", newline="")
    if meta is not None:
        full = {
            "uri": f"external:{md.stem}.pdf",
            "title": "Política de acesso",
            "document_type": "pdf",
            "retrieved_at": "2026-10-05T10:00:00+00:00",
            "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "status": "active",
            **meta,
        }
        md.with_suffix(".meta.yaml").write_text(
            yaml.safe_dump(full, allow_unicode=True), encoding="utf-8"
        )
    return rel


def _v2(opener, agent: str, question: str, filters: dict | None = None, k: int = 10):
    with opener() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT source, uri, title, document_type, status, jurisdiction, locator, "
            "content_hash, retrieved_at FROM match_knowledge_v2("
            "query_embedding => %s::vector, match_agent_id => %s, match_count => %s, "
            "filters => %s::jsonb)",
            (_fake_embed(question), agent, k, json.dumps(filters or {})),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


# --- migração --------------------------------------------------------------------------------


def test_migracao_sobre_dados_antigos_e_idempotente(base_db) -> None:
    with base_db() as conn:
        conn.execute(
            "INSERT INTO knowledge_sources (source_path, content_hash, agent_id) "
            "VALUES ('docs/a.md', 'h', 'global')"
        )
        conn.commit()
    for _ in range(2):  # 2 vezes: idempotente
        with base_db() as conn:
            conn.execute(MIGRATION_SQL)
    with base_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT status, meta, uri FROM knowledge_sources")
        assert cur.fetchall() == [("active", {}, None)]
        cur.execute(
            "SELECT count(*) FROM pg_constraint WHERE conname = 'knowledge_sources_status_check'"
        )
        assert cur.fetchone()[0] == 1
        assert sw.has_f3_columns(conn) is True


def test_status_fora_do_conjunto_e_recusado_pela_bd(f3_db) -> None:
    with f3_db() as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "INSERT INTO knowledge_sources (source_path, content_hash, agent_id, status) "
                "VALUES ('x.md', 'h', 'global', 'apagado')"
            )


# --- writer: compatível antes e depois do SQL ---------------------------------------------------


def test_writer_sem_migracao_escreve_como_antes(base_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, base_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={})
    out = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK" and out["chunks"] >= 1
    with base_db() as conn:
        assert sw.has_f3_columns(conn) is False
        cur = conn.execute(
            "SELECT * FROM match_knowledge(%s::vector, 'security', 4)",
            (_fake_embed("ataque activo"),),
        )
        assert [d.name for d in cur.description] == ["id", "content", "source", "similarity"]
        assert cur.fetchall()


def test_writer_com_migracao_grava_proveniencia_e_locator(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={"jurisdiction": "PT"})
    out = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK"
    with f3_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT uri, title, document_type, status, jurisdiction, retrieved_at, meta "
            "FROM knowledge_sources WHERE source_path = %s",
            (rel,),
        )
        uri, title, dtype, status, jur, retrieved, meta = cur.fetchone()
        assert (uri, title, dtype, status, jur) == (
            "external:politica.pdf",
            "Política de acesso",
            "pdf",
            "active",
            "PT",
        )
        assert retrieved == datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
        assert meta == {}
        cur.execute("SELECT locator FROM knowledge_chunks WHERE source = %s", (rel,))
        assert all(row[0] and row[0].startswith("l.") for row in cur.fetchall())


def test_md_sem_sidecar_fica_com_a_proveniencia_do_git(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/manual.md")
    ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    hits = _v2(f3_db, "security", "ataque activo autorização")
    assert hits and hits[0]["uri"] == rel
    assert hits[0]["document_type"] == "md" and hits[0]["status"] == "active"


# --- retrieve v2 ----------------------------------------------------------------------------


def test_v2_devolve_proveniencia(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={"jurisdiction": "PT"})
    ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    hit = _v2(f3_db, "security", "ataque activo autorização")[0]
    assert hit["source"] == rel
    assert hit["uri"] == "external:politica.pdf"
    assert hit["title"] == "Política de acesso"
    assert hit["document_type"] == "pdf"
    assert hit["jurisdiction"] == "PT"
    assert hit["locator"].startswith("l.")
    assert hit["content_hash"] == hashlib.sha256(DOC.encode("utf-8")).hexdigest()


def test_v2_filtros(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    pt = _write_doc(tmp_path, "docs/knowledge/ingested/pt.md", meta={"jurisdiction": "PT"})
    br = _write_doc(
        tmp_path,
        "docs/knowledge/ingested/br.md",
        body=DOC + "\nVersão BR.\n",
        meta={"jurisdiction": "BR"},
    )
    velho = _write_doc(
        tmp_path,
        "docs/knowledge/ingested/velho.md",
        body=DOC + "\nVersão antiga.\n",
        meta={"status": "superseded"},
    )
    expirado = _write_doc(
        tmp_path,
        "docs/knowledge/ingested/expirado.md",
        body=DOC + "\nExpirou.\n",
        meta={"effective_from": "2025-01-01", "effective_until": "2026-01-01"},
    )
    for rel in (pt, br, velho, expirado):
        ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    q = "ataque activo autorização"

    def sources(filters=None):
        return {h["source"] for h in _v2(f3_db, "security", q, filters)}

    assert sources() == {pt, br}  # por omissão: só active e em vigor
    assert sources({"jurisdiction": "BR"}) == {br}
    assert sources({"status": "superseded"}) == {velho}
    assert sources({"status": "any", "valid_at": "2025-06-01T00:00:00Z"}) == {
        pt,
        br,
        velho,
        expirado,
    }
    assert sources({"valid_at": "2025-06-01T00:00:00Z"}) == {pt, br, expirado}
    assert sources({"document_type": "md"}) == set()
    assert sources({"document_type": "pdf"}) == {pt, br}


def test_match_knowledge_antigo_nao_muda(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    velho = _write_doc(tmp_path, "docs/knowledge/ingested/velho.md", meta={"status": "superseded"})
    ia.apply_one(velho, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    with f3_db() as conn:
        cur = conn.execute(
            "SELECT * FROM match_knowledge(%s::vector, 'security', 4)",
            (_fake_embed("ataque activo"),),
        )
        assert [d.name for d in cur.description] == ["id", "content", "source", "similarity"]
        assert {row[2] for row in cur.fetchall()} == {velho}  # sem filtros, como antes


def test_linha_do_mcp_nao_herda_proveniencia_do_t6(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={"status": "superseded"})
    ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    with f3_db() as conn:  # linha do MCP (project NULL) com o MESMO source
        conn.execute(
            "INSERT INTO knowledge_chunks (agent_id, source, content, embedding) "
            "VALUES ('security', %s, 'nota do MCP: ataque activo', %s::vector)",
            (rel, _fake_embed("nota do MCP ataque activo")),
        )
        conn.commit()
    # Por omissão a v2 exclui o T6 'superseded'; o que volta é a linha do MCP, que tem o
    # mesmo `source` mas não herda o status nem o título da fonte do T6.
    hits = _v2(f3_db, "security", "nota do MCP ataque activo")
    assert hits and all(h["source"] == rel for h in hits)
    assert all(h["status"] == "active" and h["title"] is None for h in hits)


# --- ingest_apply: sidecar inválido e proveniência mudada ----------------------------------------


def test_sidecar_invalido_nao_escreve_nada(f3_db, monkeypatch, tmp_path) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/mau.md", meta={"content_hash": "0" * 64})
    out = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "INVALID_META" and "content_hash" in out["note"]
    assert ia.embedded == []
    with f3_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_sources WHERE source_path = %s", (rel,))
        assert cur.fetchone()[0] == 0


def test_md_igual_com_status_mudado_actualiza_so_a_proveniencia(
    f3_db, monkeypatch, tmp_path
) -> None:
    ia = _ingest_apply(monkeypatch, tmp_path, f3_db)
    rel = _write_doc(tmp_path, "docs/knowledge/ingested/politica.md", meta={})
    first = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    n_embeds = len(ia.embedded)
    assert first["action"] == "OK"
    assert _v2(f3_db, "security", "ataque activo autorização")

    _write_doc(tmp_path, rel, meta={"status": "revoked"})  # o .md é o mesmo; só o sidecar muda
    again = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert again == {"action": "META_UPDATED", "chunks": 0, "deleted": 0}
    assert len(ia.embedded) == n_embeds  # nenhum embedding novo
    assert _v2(f3_db, "security", "ataque activo autorização") == []  # revogado: fora por omissão
    assert _v2(f3_db, "security", "ataque activo autorização", {"status": "revoked"})

    third = ia.apply_one(rel, "security", "P1", dry_run=False, budget=ia.ChunkBudget(100))
    assert third == {"action": "UNCHANGED", "chunks": 0, "deleted": 0}  # nada mais mudou
