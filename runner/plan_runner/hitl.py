"""HITL request/decision side (Python) for the shared contract v1.

Contract: docs/architecture/hitl/hitl-request-v1.json
Alignment: docs/architecture/hitl/README.md (Phase A.2)

This module is *additive*. It does not replace the existing writes in
engine.py / langgraph_engine.py (status.json, events.jsonl, HITL.md).
It writes the shared contract files that the Node platform (HitlManager)
can read, and reads the decision that the Node platform writes back.

Storage (Option A, per README):
    <run_dir>/hitl-requests.jsonl   -- append-only, written by plan_runner
    <run_dir>/hitl-decisions.jsonl  -- append-only, written by the responder

API (per README Phase A.2):
    write_request(run_dir, *, step, run_id, plan_id, completed) -> str
    read_decision(run_dir) -> dict | None

Design notes:
- No new dependency. The JSON Schema is validated in the test suite
  (runner/tests/test_hitl_contract.py), not at runtime.
- Python never sets expires_at (always null) and always uses
  priority="medium" and category=None. See README "What stays
  Python-specific".
- Fields follow the schema exactly; additionalProperties is false.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


REQUESTS_FILE = "hitl-requests.jsonl"
DECISIONS_FILE = "hitl-decisions.jsonl"

SCHEMA_ID = "hitl-request-v1"
SOURCE = "plan_runner"

_VALID_DECISIONS = frozenset({"approve", "reject", "edit"})


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _requests_path(run_dir: Path) -> Path:
    return run_dir / REQUESTS_FILE


def _decisions_path(run_dir: Path) -> Path:
    return run_dir / DECISIONS_FILE


def _ensure_file(path: Path) -> None:
    """Cria o ficheiro (e a pasta pai) vazio se nao existir.

    Append-only: nunca trunca um ficheiro existente.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Le um ficheiro JSONL, tolerando linhas em branco e linhas invalidas.

    Mesma robustez que EventLog.has_event: uma linha corrompida nao
    invalida o ficheiro todo.
    """
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    _ensure_file(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_request(
    *,
    step: Any,
    run_id: str | None,
    plan_id: str | None,
    completed: list[str] | None,
    mode: str | None = None,
    agent_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Constroi o dict do pedido HITL conforme o contrato v1.

    Nao escreve nada. Separado de write_request para ser testavel
    isoladamente (validar o shape antes de tocar no disco).
    """
    step_id = getattr(step, "id", None)
    action = getattr(step, "action", None)
    gate = getattr(step, "human_gate", None)

    allow = list(getattr(gate, "allow", None) or ["approve", "reject"])
    # 'edit' so e valido se o plano o permitir (schema: allow enum).
    allow = [a for a in allow if a in _VALID_DECISIONS]
    if not allow:
        allow = ["approve", "reject"]

    context: dict[str, Any] = {
        "paused_at_step": step_id,
        "completed": sorted(completed or []),
    }
    if mode is not None:
        context["mode"] = mode

    record: dict[str, Any] = {
        "schema": SCHEMA_ID,
        "id": f"hitl_{uuid4()}",
        "source": SOURCE,
        "run_id": run_id,
        "plan_id": plan_id,
        "step_id": step_id,
        "agent_id": agent_id,
        "domain": domain,
        "category": None,
        "priority": "medium",
        "status": "pending",
        "title": _title(step_id, action),
        "description": None,
        "proposed_action": action,
        "allow": allow,
        "context": context,
        "alternatives": [],
        "risks": [],
        "impacts": [],
        "requested_at": _now(),
        "expires_at": None,
        "responded_at": None,
        "response": None,
        "response_comment": None,
        "responder_id": None,
        "metadata": {},
    }
    return record


def _title(step_id: str | None, action: str | None) -> str:
    """Titulo humano curto, sem depender de LLM."""
    if step_id and action:
        return f"Approve step '{step_id}' ({action})"
    if step_id:
        return f"Approve step '{step_id}'"
    return "Approve HITL gate"


def write_request(
    run_dir: Path,
    *,
    step: Any,
    run_id: str | None,
    plan_id: str | None,
    completed: list[str] | None,
    mode: str | None = None,
    agent_id: str | None = None,
    domain: str | None = None,
) -> str:
    """Append de um pedido HITL a hitl-requests.jsonl. Devolve o hitl_id.

    Assinatura alinhada com o README (Phase A.2), com kwargs extra
    opcionais (mode, agent_id, domain) que o contrato permite e que o
    engine pode passar sem breaking change.
    """
    record = build_request(
        step=step,
        run_id=run_id,
        plan_id=plan_id,
        completed=completed,
        mode=mode,
        agent_id=agent_id,
        domain=domain,
    )
    _append_jsonl(_requests_path(run_dir), record)
    return record["id"]


def read_decision(run_dir: Path) -> dict[str, Any] | None:
    """Le a decisao mais recente de hitl-decisions.jsonl.

    Devolve None se o ficheiro nao existir ou nao tiver decisoes.
    Devolve o ultimo registo valido (ha varios, o ultimo manda).

    Um registo de decisao tem, no minimo:
        {"id": "hitl_...", "response": "approve|reject|edit", ...}

    O contrato completo e o mesmo do pedido, com status/response/
    responded_at/responder_id preenchidos. Aceitamos qualquer dict que
    tenha 'response' valido -- o schema completo e validado no teste.
    """
    records = _read_jsonl(_decisions_path(run_dir))
    for record in reversed(records):
        response = record.get("response")
        if response in _VALID_DECISIONS:
            return record
    return None


def build_decision(
    request_id: str,
    *,
    response: str,
    responder_id: str = "cli",
    comment: str | None = None,
) -> dict[str, Any]:
    """Constroi o dict da decisao conforme o contrato v1.

    Espelha build_request: nao escreve, so constroi. Usado pelo lado
    Python (CLI/engine) para escrever uma decisao que o Node le, e
    pelos testes para validar o shape.
    """
    if response not in _VALID_DECISIONS:
        raise ValueError(
            f"response must be one of {sorted(_VALID_DECISIONS)}, got {response!r}"
        )
    return {
        "id": request_id,
        "response": response,
        "responded_at": _now(),
        "responder_id": responder_id,
        "response_comment": comment,
    }


def write_decision(
    run_dir: Path,
    request_id: str,
    *,
    response: str,
    responder_id: str = "cli",
    comment: str | None = None,
) -> dict[str, Any]:
    """Append de uma decisao a hitl-decisions.jsonl. Devolve o registo.

    Usado pelo lado Python quando o CLI resolve um gate (S6b liga isto
    ao cli.py). Nesta fase (S6a) e usado pelos testes para simular o
    lado Node a responder.
    """
    record = build_decision(
        request_id,
        response=response,
        responder_id=responder_id,
        comment=comment,
    )
    _append_jsonl(_decisions_path(run_dir), record)
    return record


def latest_request(run_dir: Path) -> dict[str, Any] | None:
    """Devolve o pedido HITL mais recente, ou None.

    Util para o engine saber se ja escreveu um pedido para a pausa atual
    (idempotencia) e para o Node API listar o pedido pendente.
    """
    records = _read_jsonl(_requests_path(run_dir))
    return records[-1] if records else None