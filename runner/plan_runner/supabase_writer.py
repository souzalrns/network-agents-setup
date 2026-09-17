"""Escrita de chunks no Supabase (Postgres + pgvector) para o T6.

Design: docs/T6-INGEST-PIPELINE.md (secao 4: knowledge_sources + knowledge_chunks).

Este modulo e ADITIVO e escreve numa tabela EXCLUSIVA:
    - knowledge_sources: source_path (PK), content_hash, agent_id, priority,
      last_ingested_at, chunk_count, git_sha, size_bytes, updated_at
    - knowledge_chunks_t6: id, source_path (FK), content_hash, chunk_index,
      content, agent_id, kb, embedding vector(768), created_at, updated_at

NAO usa a tabela `knowledge_chunks` do agent-network-mcp (schema diferente,
projeto diferente). A separacao evita colisoes de schema e de dados.

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
        cur.execute(
            "DELETE FROM knowledge_chunks_t6 WHERE source_path = %s",
            (source_path,),
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
    """Insere chunks com embeddings. Devolve o numero inserido.

    Cada chunk (dict) deve ter:
        - content: str
        - content_hash: str
        - chunk_index: int
        - embedding: list[float] (768 dims)
    """
    if not chunks:
        return 0

    sql = """
        INSERT INTO knowledge_chunks_t6 (
            id, source_path, content_hash, chunk_index, content,
            agent_id, kb, embedding, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s::vector, NOW(), NOW()
        )
    """
    n = 0
    with conn.cursor() as cur:
        for c in chunks:
            emb = c.get("embedding") or []
            if len(emb) != 768:
                raise SupabaseWriterError(
                    f"chunk_index={c.get('chunk_index')} tem {len(emb)} dims "
                    "(esperado 768)"
                )
            cur.execute(
                sql,
                (
                    str(uuid.uuid4()),
                    source_path,
                    c["content_hash"],
                    c["chunk_index"],
                    c["content"],
                    agent_id,
                    kb,
                    emb,
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
            cur.execute(
                "SELECT COUNT(*) FROM knowledge_chunks_t6 WHERE source_path = %s",
                (source_path,),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM knowledge_chunks_t6")
        row = cur.fetchone()
        return int(row[0]) if row else 0
