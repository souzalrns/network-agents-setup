"""L4 em SQLite (perfil de pouca capacidade, plano setup-estrutura-2, passo s2).

Mesmo contrato e mesmas regras que a L4 em Postgres (`memory_l4.py`), num único ficheiro, sem servidor e sem
pgvector. As regras que o Postgres impõe por trigger impõem-se aqui também:
  - statement, subject, âmbito, created_at e created_by são imutáveis (corrigir = facto novo com `supersedes`);
  - DELETE é proibido (esquecer = tombstone `archived`).

Diferenças honestas face ao Postgres:
  - o embedding fica em JSON e a similaridade (cosseno) calcula-se em Python: serve para milhares de memórias,
    não para milhões;
  - sem embedding (ou sem GEMINI_API_KEY), o recall ordena por recência, como no Postgres.

Quem chama usa `memory_l4.remember/recall/...` como sempre: `connect()` devolve esta ligação quando
`DATABASE_URL=sqlite:///caminho.db` ou `L4_SQLITE=caminho.db`.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

COLUMNS = ("id, scope_kind, scope_id, subject, statement, status, confidence, source_run_id, tags, metadata, "
           "supersedes, superseded_by, created_by, created_at, updated_at, expires_at, promoted_at, promoted_by, "
           "archived_at, archived_by, archived_reason")

SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_l4 (
  id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL CHECK (scope_kind IN ('global','org','project','user','agent')),
  scope_id TEXT NOT NULL CHECK (length(trim(scope_id)) > 0),
  subject TEXT,
  statement TEXT NOT NULL CHECK (length(trim(statement)) > 0 AND length(statement) <= 2000),
  status TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','active','archived','superseded')),
  confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  source_run_id TEXT,
  tags TEXT NOT NULL DEFAULT '[]',
  metadata TEXT NOT NULL DEFAULT '{}',
  embedding TEXT,
  supersedes TEXT REFERENCES memory_l4(id),
  superseded_by TEXT REFERENCES memory_l4(id),
  created_by TEXT NOT NULL DEFAULT 'agent',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expires_at TEXT,
  promoted_at TEXT,
  promoted_by TEXT,
  archived_at TEXT,
  archived_by TEXT,
  archived_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_memory_l4_scope_status ON memory_l4 (scope_kind, scope_id, status);
CREATE TRIGGER IF NOT EXISTS memory_l4_guard_update BEFORE UPDATE ON memory_l4
BEGIN
  SELECT RAISE(ABORT, 'memory_l4: statement/subject/ambito sao imutaveis (escreve um facto novo com supersedes)')
  WHERE NEW.statement IS NOT OLD.statement OR NEW.subject IS NOT OLD.subject
     OR NEW.scope_kind IS NOT OLD.scope_kind OR NEW.scope_id IS NOT OLD.scope_id
     OR NEW.created_at IS NOT OLD.created_at OR NEW.created_by IS NOT OLD.created_by;
END;
CREATE TRIGGER IF NOT EXISTS memory_l4_guard_delete BEFORE DELETE ON memory_l4
BEGIN
  SELECT RAISE(ABORT, 'memory_l4: DELETE proibido -- usa forget (status archived)');
END;
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return (value if value.tzinfo else value.replace(tzinfo=UTC)).astimezone(UTC).isoformat()


def path_from_url(url: str) -> str:
    """`sqlite:///rel.db` -> `rel.db`; `sqlite:////abs/x.db` -> `/abs/x.db`; `sqlite://` -> memória."""
    rest = url[len("sqlite:"):]
    if rest.startswith("///"):
        rest = rest[3:]
    elif rest.startswith("//"):
        rest = rest[2:]
    return rest or ":memory:"


def open_db(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(Path(path).expanduser()) if path != ":memory:" else path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def _row(r: sqlite3.Row | None) -> dict[str, Any] | None:
    if r is None:
        return None
    d = dict(r)
    d.pop("embedding", None)
    if "tags" in d:
        d["tags"] = json.loads(d["tags"] or "[]")
    if "metadata" in d:
        d["metadata"] = json.loads(d["metadata"] or "{}")
    return d


def get(conn: sqlite3.Connection, memory_id: str) -> dict[str, Any] | None:
    return _row(conn.execute(f"SELECT {COLUMNS} FROM memory_l4 WHERE id = ?", (memory_id,)).fetchone())  # noqa: S608


def insert(conn: sqlite3.Connection, *, scope_kind: str, scope_id: str, subject: str | None, statement: str,
           status: str, confidence: float | None, source_run_id: str | None, tags: list[str],
           metadata: dict[str, Any], vector: list[float] | None, supersedes: str | None, actor: str,
           expires_at: datetime | None) -> dict[str, Any]:
    now = _now()
    new_id = str(uuid4())
    conn.execute(
        """INSERT INTO memory_l4 (id, scope_kind, scope_id, subject, statement, status, confidence, source_run_id,
               tags, metadata, embedding, supersedes, created_by, created_at, updated_at, expires_at,
               promoted_at, promoted_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (new_id, scope_kind, scope_id, subject, statement, status, confidence, source_run_id,
         json.dumps(list(tags)), json.dumps(metadata, default=str),
         None if vector is None else json.dumps(vector), supersedes, actor, now, now, _iso(expires_at),
         now if status == "active" else None, actor if status == "active" else None),
    )
    return get(conn, new_id)  # type: ignore[return-value]


def supersede(conn: sqlite3.Connection, old_id: str, new_id: str) -> None:
    conn.execute("UPDATE memory_l4 SET status = 'superseded', superseded_by = ?, updated_at = ? "
                 "WHERE id = ? AND status IN ('candidate','active')", (new_id, _now(), old_id))


def promote_row(conn: sqlite3.Connection, memory_id: str, actor: str) -> dict[str, Any]:
    now = _now()
    conn.execute("UPDATE memory_l4 SET status = 'active', promoted_at = ?, promoted_by = ?, updated_at = ? WHERE id = ?",
                 (now, actor, now, memory_id))
    row = get(conn, memory_id)
    if row and row["supersedes"]:
        supersede(conn, row["supersedes"], row["id"])
    return row  # type: ignore[return-value]


def forget_row(conn: sqlite3.Connection, memory_id: str, actor: str, reason: str | None) -> None:
    now = _now()
    conn.execute("UPDATE memory_l4 SET status = 'archived', archived_at = ?, archived_by = ?, archived_reason = ?, "
                 "updated_at = ? WHERE id = ? AND status <> 'archived'", (now, actor, reason, now, memory_id))


def candidates(conn: sqlite3.Connection, scopes: list[tuple[str, str]] | None, limit: int) -> list[dict[str, Any]]:
    sql = f"SELECT {COLUMNS} FROM memory_l4 WHERE status = 'candidate'"  # noqa: S608
    params: list[Any] = []
    if scopes:
        sql += " AND (" + " OR ".join("(scope_kind = ? AND scope_id = ?)" for _ in scopes) + ")"
        for kind, sid in scopes:
            params += [kind, sid]
    sql += " ORDER BY created_at LIMIT ?"
    params.append(limit)
    return [_row(r) for r in conn.execute(sql, params).fetchall()]  # type: ignore[misc]


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0 or nb == 0 else sum(x * y for x, y in zip(a, b, strict=True)) / (na * nb)


def recall(conn: sqlite3.Connection, *, chain: list[tuple[str, str]], vector: list[float] | None, limit: int,
           tags: list[str] | None, include_candidates: bool) -> list[dict[str, Any]]:
    """Mesma semântica da RPC `recall_l4`: só a cadeia declarada, nunca archived/superseded/expiradas."""
    statuses = ("active", "candidate") if include_candidates else ("active",)
    marks = ",".join("?" for _ in statuses)
    now = _now()
    out: list[dict[str, Any]] = []
    for kind, sid in chain:
        rows = conn.execute(
            f"SELECT {COLUMNS}, embedding FROM memory_l4 WHERE scope_kind = ? AND scope_id = ? "  # noqa: S608
            f"AND status IN ({marks}) AND (expires_at IS NULL OR expires_at > ?)", (kind, sid, *statuses, now)).fetchall()
        for r in rows:
            row = _row(r)
            if row is None or (tags and not set(tags) <= set(row["tags"])):
                continue
            emb = json.loads(r["embedding"]) if r["embedding"] else None
            row["similarity"] = _cosine(vector, emb) if vector is not None and emb is not None else None
            out.append({k: row[k] for k in ("id", "scope_kind", "scope_id", "subject", "statement", "status", "confidence",
                                            "tags", "source_run_id", "created_at", "updated_at", "similarity")})
    out.sort(key=lambda m: m["updated_at"], reverse=True)
    out.sort(key=lambda m: (m["similarity"] is None, -(m["similarity"] or 0.0)))
    return out[:max(1, min(limit, 50))]
