"""Escrita de chunks no Supabase (Postgres + pgvector) para o T6.

Design: docs/T6-INGEST-PIPELINE.md (secao 4: knowledge_sources + knowledge_chunks).

Escreve em:
    - knowledge_sources: source_path (PK), content_hash, agent_id, priority,
      last_ingested_at, chunk_count, git_sha, size_bytes, updated_at
    - knowledge_chunks (J3, tabela canonica -- a que o match_knowledge do
      agent-network-mcp le): agent_id, source, content, embedding vector(768),
      project, content_hash, chunk_index, kb, created_at, updated_at

F3a (ADR-F3-PROVENANCE-RETRIEVE, P-26 = A): com a migracao
scripts/migrations/f3_provenance_retrieve.sql aplicada, grava tambem a proveniencia
(uri, title, document_type, retrieved_at, status, jurisdiction, validade, meta) na
knowledge_sources e o `locator` de cada chunk. Sem a migracao (producao antes de o DEV a
correr), `has_f3_columns` da False e a escrita e exactamente a de antes: o ingest nunca
parte por causa da ordem merge -> SQL.

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
from psycopg.types.json import Jsonb

CHUNKS_TABLE = "knowledge_chunks"
PROJECT = "network-agents-setup"


class SupabaseWriterError(RuntimeError):
    """Erro ao escrever no Supabase (connection, query, etc.)."""


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SupabaseWriterError(
            "DATABASE_URL nao definida no ambiente. Adiciona ao .env e exporta antes de correr."
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


def has_f3_columns(conn: psycopg.Connection) -> bool:
    """A migracao F3a esta aplicada neste schema? (knowledge_sources.uri e
    knowledge_chunks.locator existem). Detecta, em vez de assumir, para o merge do codigo
    poder vir antes do SQL sem partir o ingest de producao."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND ((table_name = 'knowledge_sources' AND column_name = 'uri')
                OR (table_name = 'knowledge_chunks' AND column_name = 'locator'))
            """
        )
        row = cur.fetchone()
        return bool(row) and row[0] == 2


# Colunas de proveniencia da knowledge_sources (F3a), pela ordem dos parametros.
PROVENANCE_COLUMNS = (
    "uri",
    "final_url",
    "title",
    "document_type",
    "retrieved_at",
    "status",
    "jurisdiction",
    "effective_from",
    "effective_until",
    "meta",
)


def _provenance_values(provenance: dict[str, Any]) -> list[Any]:
    values = [provenance.get(col) for col in PROVENANCE_COLUMNS]
    values[PROVENANCE_COLUMNS.index("status")] = provenance.get("status") or "active"
    values[PROVENANCE_COLUMNS.index("meta")] = Jsonb(provenance.get("meta") or {})
    return values


def update_source_provenance(
    conn: psycopg.Connection, source_path: str, provenance: dict[str, Any]
) -> bool:
    """So a proveniencia de uma fonte ja gravada (o .md nao mudou, o sidecar sim: ex. o
    documento passou a 'superseded'). Sem embeddings. Devolve True se alguma coisa mudou."""
    cols = ", ".join(PROVENANCE_COLUMNS)
    marks = ", ".join(["%s"] * len(PROVENANCE_COLUMNS))
    sets = ", ".join(f"{c} = %s" for c in PROVENANCE_COLUMNS)
    # Falso positivo (SEC-2d): a f-string so interpola nomes de colunas constantes
    # (PROVENANCE_COLUMNS); os valores vao como parametros %s.
    # nosemgrep: sqlalchemy-execute-raw-query
    sql = f"""
        UPDATE knowledge_sources SET {sets}, updated_at = NOW()
        WHERE source_path = %s AND ({cols}) IS DISTINCT FROM ({marks})
    """
    values = _provenance_values(provenance)
    with conn.cursor() as cur:
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(sql, [*values, source_path, *values])
        return cur.rowcount == 1


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
    provenance: dict[str, Any] | None = None,
) -> None:
    """INSERT ... ON CONFLICT (source_path) DO UPDATE em knowledge_sources.

    Com `provenance` (so quando has_f3_columns), grava tambem as colunas do F3a."""
    if provenance is not None:
        _upsert_source_with_provenance(
            conn,
            (source_path, content_hash, agent_id, priority, chunk_count, git_sha, size_bytes),
            provenance,
        )
        return
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


def _upsert_source_with_provenance(
    conn: psycopg.Connection, base: tuple[Any, ...], provenance: dict[str, Any]
) -> None:
    cols = ", ".join(PROVENANCE_COLUMNS)
    marks = ", ".join(["%s"] * len(PROVENANCE_COLUMNS))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in PROVENANCE_COLUMNS)
    # Falso positivo (SEC-2d): a f-string so interpola nomes de colunas constantes.
    sql = f"""
        INSERT INTO knowledge_sources (
            source_path, content_hash, agent_id, priority,
            last_ingested_at, chunk_count, git_sha, size_bytes, updated_at, {cols}
        ) VALUES (
            %s, %s, %s, %s, NOW(), %s, %s, %s, NOW(), {marks}
        )
        ON CONFLICT (source_path) DO UPDATE SET
            content_hash = EXCLUDED.content_hash,
            agent_id = EXCLUDED.agent_id,
            priority = EXCLUDED.priority,
            last_ingested_at = NOW(),
            chunk_count = EXCLUDED.chunk_count,
            git_sha = EXCLUDED.git_sha,
            size_bytes = EXCLUDED.size_bytes,
            updated_at = NOW(),
            {updates}
    """
    with conn.cursor() as cur:
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(sql, [*base, *_provenance_values(provenance)])


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
    with_locator: bool = False,
) -> int:
    """Insere chunks com embeddings. Devolve o numero de linhas inseridas.

    Com `with_locator` (migracao F3a aplicada), grava tambem `citation.locator`.

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

    locator_col = ", locator" if with_locator else ""
    locator_mark = ", %s" if with_locator else ""
    sql = f"""
        INSERT INTO {CHUNKS_TABLE} (
            id, source, content_hash, chunk_index, content,
            agent_id, kb, embedding, project, created_at, updated_at{locator_col}
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s::vector, %s, NOW(), NOW(){locator_mark}
        )
    """
    agents = [a for a in agent_id.split("+") if a] or [agent_id]
    n = 0
    with conn.cursor() as cur:
        for c in chunks:
            emb = c.get("embedding") or []
            if len(emb) != 768:
                raise SupabaseWriterError(
                    f"chunk_index={c.get('chunk_index')} tem {len(emb)} dims (esperado 768)"
                )
            for agent in agents:
                params = [
                    str(uuid.uuid4()),
                    source_path,
                    c["content_hash"],
                    c["chunk_index"],
                    c["content"],
                    agent,
                    kb,
                    emb,
                    PROJECT,
                ]
                if with_locator:
                    params.append((c.get("citation") or {}).get("locator"))
                # SEC-2d falso positivo: `sql` so interpola CHUNKS_TABLE e o nome da coluna
                # `locator` (constantes); os valores vao como parametros %s.
                # nosemgrep: sqlalchemy-execute-raw-query
                cur.execute(sql, params)
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
    provenance: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Operacao idempotente: upsert source + delete chunks antigos + insert novos.

    Com a migracao F3a aplicada, grava a `provenance` (colunas de
    plan_runner.provenance.to_source_columns) e os locators; sem ela, ignora-as.
    Devolve {"deleted": N, "inserted": M} (o contrato de antes do F3a).
    """
    with conn:
        f3 = has_f3_columns(conn)
        upsert_source(
            conn,
            source_path=source_path,
            content_hash=content_hash,
            agent_id=agent_id,
            priority=priority,
            git_sha=git_sha,
            size_bytes=size_bytes,
            chunk_count=len(chunks),
            provenance=provenance if f3 else None,
        )
        deleted = delete_chunks(conn, source_path)
        inserted = insert_chunks(
            conn,
            source_path=source_path,
            agent_id=agent_id,
            kb=kb,
            chunks=chunks,
            with_locator=f3,
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
