"""hitlwright: a typed, versioned, auditable human-in-the-loop approval contract.

When an agent or a workflow must pause for a human decision, hitlwright writes a
**typed request** and reads back a **typed decision** — both following a versioned
JSON Schema (``hitl-request-v1``), stored as append-only JSONL so the whole
approval trail is auditable and nothing is overwritten.

    from pathlib import Path
    from hitlwright import write_request, read_decision, write_decision

    run = Path("runs/42")
    req_id = write_request(run, step_id="publish", action="publish",
                           allow=["approve", "reject"], title="Approve publish")
    # ... the run pauses; a human (or another process) responds ...
    write_decision(run, req_id, response="approve", responder_id="user:ana")
    decision = read_decision(run)      # {"response": "approve", ...} or None

The contract is **storage-light and language-agnostic**: two files of JSON lines
(``hitl-requests.jsonl`` + ``hitl-decisions.jsonl``) that any producer and any
responder — Python, Node, a CLI, a web UI — can read and write. The shape is the
shipped JSON Schema (``schema_path()``), so both sides validate the same thing.

Design: zero runtime dependencies (pure stdlib). ``build_*`` functions construct
and validate the shape without touching disk; ``write_*``/``read_*`` do the
append-only IO. Nothing is interpreted by an LLM.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any
from uuid import uuid4

__version__ = "0.1.0"

__all__ = [
    "DECISIONS_FILE",
    "REQUESTS_FILE",
    "SCHEMA_ID",
    "VALID_DECISIONS",
    "__version__",
    "build_decision",
    "build_request",
    "latest_request",
    "pending_request",
    "read_decision",
    "schema_path",
    "write_decision",
    "write_request",
]

REQUESTS_FILE = "hitl-requests.jsonl"
DECISIONS_FILE = "hitl-decisions.jsonl"
SCHEMA_ID = "hitl-request-v1"
VALID_DECISIONS = frozenset({"approve", "reject", "edit"})
_VALID_PRIORITIES = frozenset({"low", "medium", "high", "critical"})


def schema_path() -> Path:
    """Filesystem path to the shipped ``hitl-request-v1`` JSON Schema."""
    return Path(str(resources.files("hitlwright") / "hitl-request-v1.json"))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file, tolerating blank and malformed lines (one bad line
    never invalidates the whole file)."""
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_request(
    *,
    step_id: str | None,
    action: str | None = None,
    run_id: str | None = None,
    plan_id: str | None = None,
    completed: list[str] | None = None,
    allow: list[str] | None = None,
    title: str | None = None,
    description: str | None = None,
    priority: str = "medium",
    source: str = "hitlwright",
    agent_id: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    mode: str | None = None,
    context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a ``hitl-request-v1`` record (does not touch disk).

    ``allow`` filters to the valid decisions (``approve``/``reject``/``edit``),
    falling back to ``["approve", "reject"]``. ``context`` defaults to
    ``{paused_at_step, completed[, mode]}``.
    """
    if priority not in _VALID_PRIORITIES:
        raise ValueError(f"priority must be one of {sorted(_VALID_PRIORITIES)}, got {priority!r}")
    allow = [a for a in (allow or ["approve", "reject"]) if a in VALID_DECISIONS] or ["approve", "reject"]
    ctx: dict[str, Any] = {"paused_at_step": step_id, "completed": sorted(completed or [])}
    if mode is not None:
        ctx["mode"] = mode
    if context:
        ctx.update(context)
    return {
        "schema": SCHEMA_ID,
        "id": f"hitl_{uuid4()}",
        "source": source,
        "run_id": run_id,
        "plan_id": plan_id,
        "step_id": step_id,
        "agent_id": agent_id,
        "domain": domain,
        "category": category,
        "priority": priority,
        "status": "pending",
        "title": title or _title(step_id, action),
        "description": description,
        "proposed_action": action,
        "allow": allow,
        "context": ctx,
        "alternatives": [],
        "risks": [],
        "impacts": [],
        "requested_at": _now(),
        "expires_at": None,
        "responded_at": None,
        "response": None,
        "response_comment": None,
        "responder_id": None,
        "metadata": metadata or {},
    }


def _title(step_id: str | None, action: str | None) -> str:
    if step_id and action:
        return f"Approve step '{step_id}' ({action})"
    if step_id:
        return f"Approve step '{step_id}'"
    return "Approve HITL gate"


def write_request(run_dir: str | Path, **kwargs: Any) -> str:
    """Append a request to ``hitl-requests.jsonl``; return its ``hitl_`` id."""
    record = build_request(**kwargs)
    _append_jsonl(Path(run_dir) / REQUESTS_FILE, record)
    return record["id"]


def build_decision(
    request_id: str,
    *,
    response: str,
    responder_id: str = "cli",
    comment: str | None = None,
) -> dict[str, Any]:
    """Build a decision record (does not touch disk)."""
    if response not in VALID_DECISIONS:
        raise ValueError(f"response must be one of {sorted(VALID_DECISIONS)}, got {response!r}")
    return {
        "id": request_id,
        "response": response,
        "responded_at": _now(),
        "responder_id": responder_id,
        "response_comment": comment,
    }


def write_decision(
    run_dir: str | Path,
    request_id: str,
    *,
    response: str,
    responder_id: str = "cli",
    comment: str | None = None,
) -> dict[str, Any]:
    """Append a decision to ``hitl-decisions.jsonl``; return the record."""
    record = build_decision(request_id, response=response, responder_id=responder_id, comment=comment)
    _append_jsonl(Path(run_dir) / DECISIONS_FILE, record)
    return record


def read_decision(run_dir: str | Path) -> dict[str, Any] | None:
    """Return the most recent valid decision, or ``None``. The last one wins."""
    for record in reversed(_read_jsonl(Path(run_dir) / DECISIONS_FILE)):
        if record.get("response") in VALID_DECISIONS:
            return record
    return None


def latest_request(run_dir: str | Path) -> dict[str, Any] | None:
    """Return the most recent request, or ``None``."""
    records = _read_jsonl(Path(run_dir) / REQUESTS_FILE)
    return records[-1] if records else None


def pending_request(run_dir: str | Path) -> dict[str, Any] | None:
    """Return the latest request that has no matching decision yet, or ``None``.

    "Matching" is by id. Useful to know whether a run is still waiting on a human.
    """
    decided = {d.get("id") for d in _read_jsonl(Path(run_dir) / DECISIONS_FILE) if d.get("response") in VALID_DECISIONS}
    for record in reversed(_read_jsonl(Path(run_dir) / REQUESTS_FILE)):
        if record.get("id") not in decided:
            return record
    return None
