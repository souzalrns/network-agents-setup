"""J3: ingest -> retrieve na tabela canonica (knowledge_chunks).

Escreve 1 documento com supabase_writer.replace_chunks (o caminho real do
ingest) e le-o com match_knowledge chamado como o agent-network-mcp o chama
(lib/knowledge.js:54: 3 argumentos com nome). Embeddings sinteticos de 768
dims, sem Gemini.

Corre so contra um Postgres DESCARTAVEL com pgvector, indicado em
RAG_TEST_DATABASE_URL (ex.: o servico pgvector/pgvector do ci.yml). Nunca usa
DATABASE_URL: esse e o Supabase de producao. Cria e apaga um schema proprio.
"""
from __future__ import annotations

import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

from plan_runner import supabase_writer as sw  # noqa: E402

DB_URL = os.environ.get("RAG_TEST_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida (Postgres descartavel com pgvector; "
    "nunca o Supabase de producao)",
)

# Esquema minimo igual ao de producao (verificado em 2026-09-30) e o
# match_knowledge versionado em agent-network-mcp/memory/schema.sql:45-58.
SCHEMA_SQL = """
CREATE TABLE knowledge_sources (
  source_path text PRIMARY KEY, content_hash text NOT NULL, agent_id text NOT NULL,
  priority text NOT NULL DEFAULT 'P1', last_ingested_at timestamptz NOT NULL DEFAULT now(),
  chunk_count int NOT NULL DEFAULT 0, git_sha text, size_bytes int,
  updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE knowledge_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), agent_id text NOT NULL, source text NOT NULL,
  content text NOT NULL, embedding vector(768), created_at timestamptz DEFAULT now(),
  project text, content_hash text, chunk_index integer, kb text DEFAULT 'marketing',
  updated_at timestamptz DEFAULT now());
CREATE FUNCTION match_knowledge(query_embedding vector(768), match_agent_id text,
  match_count int DEFAULT 4)
RETURNS TABLE (id uuid, content text, source text, similarity float)
LANGUAGE sql STABLE AS $$
  SELECT id, content, source, 1 - (embedding <=> query_embedding) AS similarity
  FROM knowledge_chunks WHERE agent_id = match_agent_id OR agent_id = 'global'
  ORDER BY embedding <=> query_embedding LIMIT match_count; $$;
"""


def _vec(i: int) -> list[float]:
    return [1.0 if d == i else 0.001 for d in range(768)]


@pytest.fixture
def connect():
    """Devolve uma fabrica de ligacoes ao schema de teste. Uma ligacao por
    operacao, como o ingest real (scripts/ingest_apply.py:183): no psycopg 3,
    `with conn:` (usado em replace_chunks) faz commit E fecha a ligacao."""
    schema = f"rag_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        admin.execute(f"CREATE SCHEMA {schema}")

    def _open():
        return psycopg.connect(DB_URL, autocommit=False, options=f"-c search_path={schema},public")

    try:
        with _open() as c:
            c.execute(SCHEMA_SQL)
        yield _open
    finally:
        with psycopg.connect(DB_URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA {schema} CASCADE")


def _retrieve(connect, agent_id: str, query: list[float], k: int = 3) -> list[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT source FROM match_knowledge("
            "query_embedding => %s::vector, match_agent_id => %s, match_count => %s)",
            (query, agent_id, k),
        )
        return [r[0] for r in cur.fetchall()]


def _ingest(connect, source: str, agent_id: str, dim: int) -> dict[str, int]:
    return sw.replace_chunks(
        connect(),
        source_path=source,
        content_hash="h",
        agent_id=agent_id,
        kb="marketing",
        chunks=[{"content": f"conteudo {source}", "content_hash": "c0",
                 "chunk_index": 0, "embedding": _vec(dim)}],
    )


def test_ingested_doc_is_retrieved(connect):
    assert _ingest(connect, "docs/knowledge/geo-agent.md", "marketing", 7)["inserted"] == 1
    assert _retrieve(connect, "marketing", _vec(7))[0] == "docs/knowledge/geo-agent.md"


def test_composite_agent_retrieved_by_each_agent(connect):
    _ingest(connect, "docs/item-13-ai-findability.md", "marketing+produto-tech-transversal", 9)
    for agent in ("marketing", "produto-tech-transversal"):
        assert _retrieve(connect, agent, _vec(9))[0] == "docs/item-13-ai-findability.md"


def test_reingest_does_not_touch_mcp_rows_with_same_source(connect):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO knowledge_chunks (agent_id, source, content, embedding) "
            "VALUES ('marketing', 'docs/x.md', 'linha do MCP', %s::vector)",
            (_vec(3),),
        )
    _ingest(connect, "docs/x.md", "marketing", 3)
    out = _ingest(connect, "docs/x.md", "marketing", 3)
    assert out == {"deleted": 1, "inserted": 1}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks WHERE project IS NULL")
        assert cur.fetchone()[0] == 1
