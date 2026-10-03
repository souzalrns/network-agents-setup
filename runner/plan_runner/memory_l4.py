"""L4 -- memoria semantica persistente (D3, VIA A: propria, sobre o Supabase).

Contrato: docs/architecture/memory/contracts.md (remember/recall/forget) e
scopes.md (ambitos). SQL: scripts/create_memory_l4_table.sql e
scripts/create_recall_l4_rpc.sql. Operacao: docs/ops/MEMORY-L4.md.

Regras (as criticas tambem impostas na BD):
- `remember` exige ambito explicito; sem ele, recusa (scopes.md:26).
- Ambitos: global | org | project | user | agent. O `run` e L2 (events.jsonl).
- Ninguem eleva o ambito: um agente so escreve em project/user/agent E so nos
  ids da cadeia do proprio passo (`allowed`); org e global so por humano
  (scopes.md:23-24).
- Escrita de agente fica `candidate`; `active` so por humano -- promocao por
  HITL (contracts.md:34). Um agente que peca `active` e recusado, nao rebaixado.
- Nao editar em silencio: corrigir = facto novo com `supersedes`; quando o novo
  fica active, o antigo passa a `superseded` (layers.md:44). A BD recusa
  UPDATE de statement/ambito.
- `forget` = tombstone (`archived`), nunca DELETE (contracts.md:68).
- Escrita EXPLICITA: nada aqui extrai factos sozinho (D3; auto-extraccao so
  apos spike + flag).

Promocao por HITL (formato hitl-request-v1, o mesmo do HITL duravel) em
`<run>/memory-requests.jsonl` / `memory-decisions.jsonl` -- ficheiros a parte
para nunca colidirem com a decisao de um gate do run, que o `resume` le de
hitl-decisions.jsonl. O estado de verdade e a BD.

CLI: python -m plan_runner.memory_l4 --help
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from . import hitl

SCOPE_KINDS = ("global", "org", "project", "user", "agent")
AGENT_WRITABLE = ("project", "user", "agent")  # nunca org/global (scopes.md:23-24)
WRITE_STATUSES = ("candidate", "active")
MAX_STATEMENT = 2000
REQUESTS_FILE = "memory-requests.jsonl"
DECISIONS_FILE = "memory-decisions.jsonl"
COLUMNS = ("id, scope_kind, scope_id, subject, statement, status, confidence, source_run_id, tags, metadata, "
           "supersedes, superseded_by, created_by, created_at, updated_at, expires_at, promoted_at, promoted_by, "
           "archived_at, archived_by, archived_reason")

Embed = Callable[[str], list[float]]


class L4Error(ValueError):
    """Pedido L4 invalido (contrato)."""


class ScopeError(L4Error):
    """Ambito em falta, desconhecido ou acima do permitido (elevacao)."""


@dataclass(frozen=True)
class Scope:
    kind: str
    id: str

    @classmethod
    def parse(cls, text: str) -> Scope:
        kind, sep, sid = text.partition(":")
        if not sep or not sid.strip():
            raise ScopeError(f"ambito tem de ser kind:id (got {text!r})")
        return cls(kind.strip(), sid.strip())

    def __str__(self) -> str:
        return f"{self.kind}:{self.id}"


def _is_human(actor: str) -> bool:
    return actor.startswith("human")


def _validate_scope(scope: Scope | None) -> Scope:
    if scope is None:
        raise ScopeError("remember exige um ambito explicito (scopes.md:26): sem ambito, recusado")
    if scope.kind not in SCOPE_KINDS:
        raise ScopeError(f"ambito desconhecido {scope.kind!r} (validos: {', '.join(SCOPE_KINDS)}; o `run` e L2)")
    if not str(scope.id).strip():
        raise ScopeError(f"ambito {scope.kind!r} sem id")
    return scope


@contextmanager
def connect(database_url: str | None = None) -> Iterator[Any]:
    """Ligacao ao Postgres da L4: o mesmo DATABASE_URL do J3/RAG (D3)."""
    import psycopg
    from psycopg.rows import dict_row

    url = (database_url or os.environ.get("DATABASE_URL", "")).strip()
    if not url:
        raise L4Error("DATABASE_URL nao definida (a L4 vive no Supabase do projecto agent-network-memory)")
    conn = psycopg.connect(url, autocommit=False, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def _embed(embed: Embed | None, text: str) -> tuple[list[float] | None, str | None]:
    if embed is None or not text:
        return None, None
    try:
        return embed(text), None
    except Exception as e:  # noqa: BLE001 -- sem embedding a memoria vale na mesma (recall por recencia)
        return None, f"{type(e).__name__}: {str(e)[:200]}"


def _vec(v: list[float] | None) -> str | None:
    return None if v is None else "[" + ",".join(f"{x:.7g}" for x in v) + "]"


def _row(cur) -> dict[str, Any] | None:
    r = cur.fetchone()
    return dict(r) if r else None


def get(conn, memory_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        # SEC-2d falso positivo: a f-string so interpola a constante COLUMNS (linha 51); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(f"SELECT {COLUMNS} FROM memory_l4 WHERE id = %s", (memory_id,))
        return _row(cur)


def remember(
    conn,
    *,
    scope: Scope | None,
    statement: str,
    actor: str,
    subject: str | None = None,
    confidence: float | None = None,
    source_run_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    status: str = "candidate",
    supersedes: str | None = None,
    expires_at: datetime | None = None,
    allowed: list[Scope] | None = None,
    embed: Embed | None = None,
) -> dict[str, Any]:
    """Escreve um facto (contracts.md:7-34). Devolve a linha gravada."""
    scope = _validate_scope(scope)
    human = _is_human(actor)
    if not human and scope.kind not in AGENT_WRITABLE:
        raise ScopeError(f"um agente nao escreve em {scope.kind!r}: so humano (scopes.md:23-24)")
    if allowed is not None and scope not in allowed:
        raise ScopeError(f"ambito {scope} fora da cadeia do passo ({', '.join(map(str, allowed))}): elevacao recusada")
    if status not in WRITE_STATUSES:
        raise L4Error(f"status de escrita tem de ser candidate ou active (got {status!r})")
    if status == "active" and not human:
        raise L4Error("um agente escreve `candidate`; `active` so por gate humano (contracts.md:34)")
    text = (statement or "").strip()
    if not text or len(text) > MAX_STATEMENT:
        raise L4Error(f"statement vazio ou com mais de {MAX_STATEMENT} caracteres")
    if confidence is not None and not 0 <= confidence <= 1:
        raise L4Error("confidence tem de estar em [0, 1]")

    old = None
    if supersedes:
        old = get(conn, supersedes)
        if old is None:
            raise L4Error(f"supersedes: memoria {supersedes} nao existe")
        if (old["scope_kind"], old["scope_id"]) != (scope.kind, scope.id):
            raise ScopeError("supersedes so dentro do mesmo ambito")
        if old["status"] not in ("candidate", "active"):
            raise L4Error(f"supersedes: memoria {supersedes} ja esta {old['status']}")

    vector, embed_error = _embed(embed, text)
    meta = dict(metadata or {})
    if embed_error:
        meta["embedding_error"] = embed_error
    with conn.cursor() as cur:
        # SEC-2d falso positivo: a f-string so interpola a constante COLUMNS (linha 51); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(
            f"""INSERT INTO memory_l4 (scope_kind, scope_id, subject, statement, status, confidence,
                    source_run_id, tags, metadata, embedding, supersedes, created_by, expires_at,
                    promoted_at, promoted_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector, %s, %s, %s,
                        CASE WHEN %s = 'active' THEN now() END, CASE WHEN %s = 'active' THEN %s END)
                RETURNING {COLUMNS}""",
            (scope.kind, scope.id, subject, text, status, confidence, source_run_id, list(tags or []),
             json.dumps(meta), _vec(vector), supersedes, actor, expires_at, status, status, actor),
        )
        row = _row(cur)
        if old is not None and status == "active":
            _supersede(cur, old["id"], row["id"])
    conn.commit()
    return row


def _supersede(cur, old_id: str, new_id: str) -> None:
    cur.execute(
        "UPDATE memory_l4 SET status = 'superseded', superseded_by = %s WHERE id = %s AND status IN ('candidate', 'active')",
        (new_id, old_id),
    )


def recall(
    conn,
    *,
    scopes: list[Scope],
    query: str | None = None,
    limit: int = 10,
    tags: list[str] | None = None,
    include_candidates: bool = False,
    embed: Embed | None = None,
) -> list[dict[str, Any]]:
    """Memorias da cadeia de ambitos (contracts.md:36-52), via a RPC recall_l4."""
    if not scopes:
        raise ScopeError("recall exige ambito (contracts.md:42)")
    for s in scopes:
        _validate_scope(s)
    if not 1 <= int(limit) <= 50:
        raise L4Error("limit tem de estar em 1..50 (contracts.md:46)")
    vector, _ = _embed(embed, query or "")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM recall_l4(%s::vector, %s::text[], %s::text[], %s, %s::text[], %s)",
            (_vec(vector), [s.kind for s in scopes], [s.id for s in scopes], int(limit),
             list(tags) if tags else None, include_candidates),
        )
        rows = [dict(r) for r in cur.fetchall()]
    conn.commit()
    return rows


def forget(conn, memory_id: str, *, actor: str, reason: str | None = None) -> dict[str, Any]:
    """Tombstone (contracts.md:54-68): status archived. Nunca apaga. Idempotente."""
    with conn.cursor() as cur:
        # SEC-2d falso positivo: a f-string so interpola a constante COLUMNS (linha 51); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(
            f"""UPDATE memory_l4 SET status = 'archived', archived_at = now(), archived_by = %s, archived_reason = %s
                WHERE id = %s AND status <> 'archived' RETURNING {COLUMNS}""",
            (actor, reason, memory_id),
        )
        row = _row(cur)
    conn.commit()
    if row is None:
        row = get(conn, memory_id)
        if row is None:
            raise L4Error(f"memoria {memory_id} nao existe")
    return row


def promote(conn, memory_id: str, *, actor: str) -> dict[str, Any]:
    """candidate -> active. So humano (gate HITL). Aplica o supersedes pendente."""
    if not _is_human(actor):
        raise L4Error("promote e um gate humano: actor tem de ser human:<id>")
    row = get(conn, memory_id)
    if row is None:
        raise L4Error(f"memoria {memory_id} nao existe")
    if row["status"] == "active":
        return row
    if row["status"] != "candidate":
        raise L4Error(f"so candidate pode ser promovida (esta {row['status']})")
    with conn.cursor() as cur:
        # SEC-2d falso positivo: a f-string so interpola a constante COLUMNS (linha 51); os valores vao como parametros %s.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(
            f"UPDATE memory_l4 SET status = 'active', promoted_at = now(), promoted_by = %s WHERE id = %s RETURNING {COLUMNS}",
            (actor, memory_id),
        )
        row = _row(cur)
        if row["supersedes"]:
            _supersede(cur, row["supersedes"], row["id"])
    conn.commit()
    return row


def candidates(conn, *, scopes: list[Scope] | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Fila de revisao: candidates (todas ou de uma cadeia de ambitos)."""
    sql = f"SELECT {COLUMNS} FROM memory_l4 WHERE status = 'candidate'"
    params: list[Any] = []
    if scopes:
        sql += " AND (" + " OR ".join("(scope_kind = %s AND scope_id = %s)" for _ in scopes) + ")"
        for s in scopes:
            params += [s.kind, s.id]
    sql += " ORDER BY created_at LIMIT %s"
    params.append(limit)
    with conn.cursor() as cur:
        # SEC-2d falso positivo: `sql` so junta COLUMNS e placeholders %s; os valores vao em `params`.
        # nosemgrep: sqlalchemy-execute-raw-query
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    conn.commit()
    return rows


# --------------------------------------------------------------------------
# Promocao por HITL (formato hitl-request-v1, ficheiros proprios)
# --------------------------------------------------------------------------

def request_promotion(
    run_dir: Path,
    memories: list[dict[str, Any]],
    *,
    run_id: str | None,
    plan_id: str | None,
    step_id: str | None,
    agent_id: str | None,
) -> dict[str, Any] | None:
    """Pedido HITL duravel (nao bloqueia o run) para promover as candidates de um passo."""
    if not memories:
        return None
    from uuid import uuid4

    lines = [f"- [{m['scope_kind']}:{m['scope_id']}] {m['statement']}" for m in memories]
    record = {
        "schema": hitl.SCHEMA_ID,
        "id": f"hitl_{uuid4()}",
        "source": hitl.SOURCE,
        "run_id": run_id,
        "plan_id": plan_id,
        "step_id": step_id,
        "agent_id": agent_id,
        "domain": None,
        "category": "approval",
        "priority": "medium",
        "status": "pending",
        "title": f"Promover {len(memories)} memoria(s) L4 do passo '{step_id}'",
        "description": "Factos propostos pelo agente (candidate). Aprovar = active; rejeitar = archived.\n" + "\n".join(lines),
        "proposed_action": "memory_promote",
        "allow": ["approve", "reject"],
        "context": {"paused_at_step": None, "completed": []},
        "alternatives": [],
        "risks": [],
        "impacts": [],
        "requested_at": hitl._now(),
        "expires_at": None,
        "responded_at": None,
        "response": None,
        "response_comment": None,
        "responder_id": None,
        "metadata": {"kind": "memory_l4_promotion", "memory_ids": [str(m["id"]) for m in memories]},
    }
    hitl._append_jsonl(run_dir / REQUESTS_FILE, record)
    return record


def pending_requests(run_dir: Path) -> list[dict[str, Any]]:
    decided = {d.get("id") for d in hitl._read_jsonl(run_dir / DECISIONS_FILE)}
    return [r for r in hitl._read_jsonl(run_dir / REQUESTS_FILE) if r.get("id") not in decided]


def decide(conn, run_dir: Path, request_id: str, *, response: str, actor: str,
           comment: str | None = None) -> dict[str, Any]:
    """approve -> promote de cada memoria; reject -> forget (tombstone). Grava a decisao."""
    if not _is_human(actor):
        raise L4Error("a decisao de promocao e humana: actor tem de ser human:<id>")
    if response not in ("approve", "reject"):
        raise L4Error("response tem de ser approve ou reject")
    req = next((r for r in hitl._read_jsonl(run_dir / REQUESTS_FILE) if r.get("id") == request_id), None)
    if req is None:
        raise L4Error(f"pedido {request_id} nao existe em {run_dir / REQUESTS_FILE}")
    if request_id not in {r["id"] for r in pending_requests(run_dir)}:
        raise L4Error(f"pedido {request_id} ja foi decidido")
    results = []
    for mid in req["metadata"]["memory_ids"]:
        if response == "approve":
            row = promote(conn, mid, actor=actor)
        else:
            row = forget(conn, mid, actor=actor, reason=f"rejeitada no HITL {request_id}" + (f": {comment}" if comment else ""))
        results.append({"id": mid, "status": row["status"]})
    decision = hitl.build_decision(request_id, response=response, responder_id=actor, comment=comment)
    hitl._append_jsonl(run_dir / DECISIONS_FILE, {**decision, "results": results})
    return {"request_id": request_id, "response": response, "results": results}


# --------------------------------------------------------------------------
# CLI (humano)
# --------------------------------------------------------------------------

def _gemini_embed() -> Embed | None:
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    from .embedder import embed_text

    return embed_text


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plan_runner.memory_l4", description="Memoria L4 (D3): operacoes humanas")
    ap.add_argument("--by", default=None, help="Quem decide (omissao: utilizador do sistema)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("remember", help="Escreve um facto (humano)")
    r.add_argument("statement")
    r.add_argument("--scope", required=True, help="kind:id, ex.: project:site-x")
    r.add_argument("--subject")
    r.add_argument("--tags", default="")
    r.add_argument("--active", action="store_true", help="Escrita humana ja confirmada (salta a fila)")
    r.add_argument("--supersedes")
    q = sub.add_parser("recall", help="Le a cadeia de ambitos")
    q.add_argument("--scope", action="append", required=True)
    q.add_argument("--query")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--candidates", action="store_true", help="Inclui candidates")
    f = sub.add_parser("forget", help="Tombstone (archived)")
    f.add_argument("id")
    f.add_argument("--reason")
    p = sub.add_parser("promote", help="candidate -> active (gate humano)")
    p.add_argument("id")
    c = sub.add_parser("candidates", help="Fila de revisao na BD")
    c.add_argument("--scope", action="append")
    pe = sub.add_parser("pending", help="Pedidos HITL de promocao de um run")
    pe.add_argument("run_dir", type=Path)
    d = sub.add_parser("decide", help="Decide um pedido HITL de promocao")
    d.add_argument("run_dir", type=Path)
    d.add_argument("request_id")
    d.add_argument("response", choices=["approve", "reject"])
    d.add_argument("--comment")
    args = ap.parse_args(argv)
    actor = f"human:{args.by or getpass.getuser()}"
    try:
        if args.cmd == "pending":
            _print(pending_requests(args.run_dir))
            return 0
        with connect() as conn:
            if args.cmd == "remember":
                _print(remember(conn, scope=Scope.parse(args.scope), statement=args.statement, actor=actor,
                                subject=args.subject, tags=[t for t in args.tags.split(",") if t],
                                status="active" if args.active else "candidate", supersedes=args.supersedes,
                                embed=_gemini_embed()))
            elif args.cmd == "recall":
                _print(recall(conn, scopes=[Scope.parse(s) for s in args.scope], query=args.query, limit=args.limit,
                              include_candidates=args.candidates, embed=_gemini_embed()))
            elif args.cmd == "forget":
                _print(forget(conn, args.id, actor=actor, reason=args.reason))
            elif args.cmd == "promote":
                _print(promote(conn, args.id, actor=actor))
            elif args.cmd == "candidates":
                _print(candidates(conn, scopes=[Scope.parse(s) for s in args.scope] if args.scope else None))
            elif args.cmd == "decide":
                _print(decide(conn, args.run_dir, args.request_id, response=args.response, actor=actor,
                              comment=args.comment))
    except L4Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
