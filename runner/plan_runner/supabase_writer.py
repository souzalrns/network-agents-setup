"""Escrita de chunks no Supabase (Postgres + pgvector) para o T6.

Design: docs/T6-INGEST-PIPELINE.md (secao 4: knowledge_sources + knowledge_chunks).

Escreve em:
    - knowledge_sources: source_path (PK), content_hash, agent_id, priority,
      last_ingested_at, chunk_count, git_sha, size_bytes, updated_at
    - knowledge_chunks (J3, tabela canonica -- a que o match_knowledge do
      agent-network-mcp le): agent_id, source, content, embedding vector(768),
      project, content_hash, chunk_index, kb, created_at, updated_at

A knowledge_chunks e partilhada com o agent-network-mcp: as linhas deste
ingest ficam marcadas com project='network-agents-setup' e o DELETE so apaga
essas (nunca as do MCP com a mesma `source`). A knowledge_chunks_t6 foi
abandonada (scripts/migrate_t6_to_knowledge_chunks.sql).

Le DATABASE_URL do ambiente (mesma que o Prisma usa).
Sem ORM: usa psycopg directo (mais leve, sem migrations).
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg

CHUNKS_TABLE = "knowledge_chunks"
PROJECT = "network-agents-setup"


class SupabaseWriterError(RuntimeError):
    """Erro ao escrever no Supabase (connection, query, etc.)."""


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SupabaseWriterError(
            "DATABASE_URL nao definida no ambiente. "
            "Adiciona ao .env e exporta antes de correr."
        )
    return url


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Context manager: abre e fecha a ligacao ao Postgres (Supabase)."""
    try:
        conn = psycopg.connect(_database_url(), autocommit=False)
    except psycopg.Error as e:
        raise SupabaseWriterError(f"Falha ao ligar ao Postgres: {e}") from e
    try:
        yield conn
    finally:
        conn.close()


def upsert_source(
    conn: psycopg.Connection,
    *,
    source_path: str,
    content_hash: str,
    agent_id: str,
    priority: str = "P1",
    git_sha: str | None = None,
    size_bytes: int | None = None,
    chunk_count: int = 0,
) -> None:
    """INSERT ... ON CONFLICT (source_path) DO UPDATE em knowledge_sources."""
    sql = """
        INSERT INTO knowledge_sources (
            source_path, content_hash, agent_id, priority,
            last_ingested_at, chunk_count, git_sha, size_bytes, updated_at
        ) VALUES (
            %s, %s, %s, %s, NOW(), %s, %s, %s, NOW()
        )
        ON CONFLICT (source_path) DO UPDATE SET
            content_hash = EXCLUDED.content_hash,
            agent_id = EXCLUDED.agent_id,
            priority = EXCLUDED.priority,
            last_ingested_at = NOW(),
            chunk_count = EXCLUDED.chunk_count,
            git_sha = EXCLUDED.git_sha,
            size_bytes = EXCLUDED.size_bytes,
            updated_at = NOW()
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                source_path,
                content_hash,
                agent_id,
                priority,
                chunk_count,
                git_sha,
                size_bytes,
            ),
        )


def delete_chunks(conn: psycopg.Connection, source_path: str) -> int:
    """Apaga todos os chunks de um source_path. Devolve o numero apagado."""
    with conn.cursor() as cur:
        # SEC-2d falso positivo: a f-string so interpola a constante CHUNKS_TABLE (linha 30); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(
            f"DELETE FROM {CHUNKS_TABLE} WHERE source = %s AND project = %s",
            (source_path, PROJECT),
        )
        return cur.rowcount


def insert_chunks(
    conn: psycopg.Connection,
    *,
    source_path: str,
    agent_id: str,
    kb: str,
    chunks: list[dict[str, Any]],
) -> int:
    """Insere chunks com embeddings. Devolve o numero de linhas inseridas.

    agent_id composto ('a+b') gera uma linha por agente: o match_knowledge
    filtra por igualdade de agent_id, por isso 'a+b' nunca seria encontrado.

    Cada chunk (dict) deve ter:
        - content: str
        - content_hash: str
        - chunk_index: int
        - embedding: list[float] (768 dims)
    """
    if not chunks:
        return 0

    sql = f"""
        INSERT INTO {CHUNKS_TABLE} (
            id, source, content_hash, chunk_index, content,
            agent_id, kb, embedding, project, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s::vector, %s, NOW(), NOW()
        )
    """
    agents = [a for a in agent_id.split("+") if a] or [agent_id]
    n = 0
    with conn.cursor() as cur:
        for c in chunks:
            emb = c.get("embedding") or []
            if len(emb) != 768:
                raise SupabaseWriterError(
                    f"chunk_index={c.get('chunk_index')} tem {len(emb)} dims "
                    "(esperado 768)"
                )
            for agent in agents:
                # SEC-2d falso positivo: `sql` so interpola CHUNKS_TABLE (linha 30); os valores vao como parametros %s.
                # nosemgrep: sqlalchemy-execute-raw-query
                cur.execute(
                    sql,
                    (
                        str(uuid.uuid4()),
                        source_path,
                        c["content_hash"],
                        c["chunk_index"],
                        c["content"],
                        agent,
                        kb,
                        emb,
                        PROJECT,
                    ),
                )
                n += 1
    return n


def replace_chunks(
    conn: psycopg.Connection,
    *,
    source_path: str,
    content_hash: str,
    agent_id: str,
    kb: str,
    chunks: list[dict[str, Any]],
    priority: str = "P1",
    git_sha: str | None = None,
    size_bytes: int | None = None,
) -> dict[str, int]:
    """Operacao idempotente: upsert source + delete chunks antigos + insert novos.

    Devolve {"deleted": N, "inserted": M}.
    """
    with conn:
        upsert_source(
            conn,
            source_path=source_path,
            content_hash=content_hash,
            agent_id=agent_id,
            priority=priority,
            git_sha=git_sha,
            size_bytes=size_bytes,
            chunk_count=len(chunks),
        )
        deleted = delete_chunks(conn, source_path)
        inserted = insert_chunks(
            conn,
            source_path=source_path,
            agent_id=agent_id,
            kb=kb,
            chunks=chunks,
        )
    return {"deleted": deleted, "inserted": inserted}


def source_state(conn: psycopg.Connection, source_path: str) -> dict[str, Any] | None:
    """Estado gravado de uma fonte (F0.4, ingest incremental): hash, agent_id e
    chunk_count de knowledge_sources + linhas reais deste projecto em knowledge_chunks.
    None se a fonte nunca foi registada."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content_hash, agent_id, chunk_count FROM knowledge_sources WHERE source_path = %s",
            (source_path,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        # SEC-2d falso positivo: a f-string so interpola a constante CHUNKS_TABLE (linha 30); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(
            f"SELECT count(*) FROM {CHUNKS_TABLE} WHERE source = %s AND project = %s",
            (source_path, PROJECT),
        )
        rows = cur.fetchone()[0]
    return {"content_hash": row[0], "agent_id": row[1], "chunk_count": row[2], "rows": rows}


def purge_source(conn: psycopg.Connection, source_path: str) -> int:
    """Apaga um source e os seus chunks. Devolve chunks apagados."""
    with conn:
        n = delete_chunks(conn, source_path)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM knowledge_sources WHERE source_path = %s",
                (source_path,),
            )
    return n


def count_chunks(conn: psycopg.Connection, source_path: str | None = None) -> int:
    """Conta chunks (total ou por source_path). Util para verificacao."""
    with conn.cursor() as cur:
        if source_path:
            # SEC-2d falso positivo: a f-string so interpola a constante CHUNKS_TABLE (linha 30); os valores vao como parametros %s.
            # nosemgrep: sqlalchemy-execute-raw-query
            cur.execute(
                f"SELECT COUNT(*) FROM {CHUNKS_TABLE} WHERE source = %s AND project = %s",
                (source_path, PROJECT),
            )
        else:
            # SEC-2d falso positivo: a f-string so interpola a constante CHUNKS_TABLE (linha 30); os valores vao como parametros %s.
            # nosemgrep: sqlalchemy-execute-raw-query
            cur.execute(f"SELECT COUNT(*) FROM {CHUNKS_TABLE} WHERE project = %s", (PROJECT,))
        row = cur.fetchone()
        return int(row[0]) if row else 0
