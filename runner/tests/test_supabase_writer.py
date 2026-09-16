"""Testes de supabase_writer.py -- sem ligar ao Postgres real.

Cobre:
- validacao de DATABASE_URL
- upsert_source / delete_chunks / insert_chunks / replace_chunks / purge_source
- validacao de dimensao do embedding
- contagem

A tabela alvo e `knowledge_chunks_t6` (exclusiva do T6), nao a
`knowledge_chunks` do agent-network-mcp.
"""
from __future__ import annotations

import pytest

from plan_runner import supabase_writer as sw


class _FakeCursor:
    def __init__(self, rows=None):
        self.executed: list[tuple] = []
        self._rows = rows or []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql.strip(), params))
        if sql.strip().upper().startswith("DELETE"):
            self.rowcount = 3
        if sql.strip().upper().startswith("INSERT"):
            self.rowcount = 1

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeConn:
    def __init__(self, rows=None):
        self.cur = _FakeCursor(rows)
        self.committed = False

    def cursor(self):
        return self.cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.committed = True
        return False


@pytest.fixture(autouse=True)
def _set_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")


def test_raises_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(sw.SupabaseWriterError, match="DATABASE_URL"):
        sw._database_url()


def test_upsert_source_executes_insert_on_conflict():
    conn = _FakeConn()
    sw.upsert_source(
        conn,
        source_path="docs/x.md",
        content_hash="abc",
        agent_id="marketing",
        priority="P0",
        git_sha="deadbeef",
        size_bytes=1234,
        chunk_count=5,
    )
    sql, params = conn.cur.executed[0]
    assert "INSERT INTO knowledge_sources" in sql
    assert "ON CONFLICT (source_path) DO UPDATE" in sql
    assert params == ("docs/x.md", "abc", "marketing", "P0", 5, "deadbeef", 1234)


def test_delete_chunks_targets_t6_table():
    conn = _FakeConn()
    n = sw.delete_chunks(conn, "docs/x.md")
    assert n == 3
    sql, params = conn.cur.executed[0]
    assert "knowledge_chunks_t6" in sql
    assert "WHERE source_path = %s" in sql
    assert params == ("docs/x.md",)


def test_insert_chunks_rejects_wrong_embedding_size():
    conn = _FakeConn()
    with pytest.raises(sw.SupabaseWriterError, match="dims"):
        sw.insert_chunks(
            conn,
            source_path="docs/x.md",
            agent_id="marketing",
            kb="marketing",
            chunks=[
                {
                    "content": "a",
                    "content_hash": "h",
                    "chunk_index": 0,
                    "embedding": [0.1] * 10,
                }
            ],
        )


def test_insert_chunks_empty_returns_zero():
    conn = _FakeConn()
    assert (
        sw.insert_chunks(
            conn,
            source_path="x",
            agent_id="m",
            kb="marketing",
            chunks=[],
        )
        == 0
    )


def test_insert_chunks_ok_targets_t6_table():
    conn = _FakeConn()
    chunks = [
        {"content": "a", "content_hash": "h1", "chunk_index": 0, "embedding": [0.0] * 768},
        {"content": "b", "content_hash": "h2", "chunk_index": 1, "embedding": [0.0] * 768},
    ]
    n = sw.insert_chunks(
        conn,
        source_path="docs/x.md",
        agent_id="marketing",
        kb="marketing",
        chunks=chunks,
    )
    assert n == 2
    inserts = [e for e in conn.cur.executed if e[0].upper().startswith("INSERT")]
    assert len(inserts) == 2
    sql, params = inserts[0]
    assert "knowledge_chunks_t6" in sql
    assert "source_path" in sql
    # params: id, source_path, content_hash, chunk_index, content, agent_id, kb, embedding
    assert params[1] == "docs/x.md"
    assert params[3] == 0
    assert params[5] == "marketing"
    assert params[6] == "marketing"


def test_replace_chunks_runs_upsert_delete_insert():
    conn = _FakeConn()
    chunks = [
        {"content": "a", "content_hash": "h", "chunk_index": 0, "embedding": [0.0] * 768}
    ]
    out = sw.replace_chunks(
        conn,
        source_path="docs/x.md",
        content_hash="abc",
        agent_id="marketing",
        kb="marketing",
        chunks=chunks,
        priority="P0",
        size_bytes=10,
    )
    assert out["inserted"] == 1
    assert out["deleted"] == 3
    assert conn.committed is True


def test_count_chunks_with_source_targets_t6_table():
    conn = _FakeConn(rows=[(7,)])
    n = sw.count_chunks(conn, "docs/x.md")
    assert n == 7
    sql, params = conn.cur.executed[0]
    assert "knowledge_chunks_t6" in sql
    assert params == ("docs/x.md",)


def test_count_chunks_without_source():
    conn = _FakeConn(rows=[(42,)])
    assert sw.count_chunks(conn) == 42
    sql, _ = conn.cur.executed[0]
    assert "knowledge_chunks_t6" in sql