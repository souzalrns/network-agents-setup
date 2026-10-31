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
- O contrato (build/write/read de pedidos e decisoes) vem do pacote publicado
  `hitlwright` (PyPI, extraido de oss/hitlwright; zero dependencias). Devolvido
  em 2026-10-13 (flywheel, docs/initiatives/REPO-EVAL-PLAYBOOK.md). Este modulo
  fica como a cola do runner: `build_request`/`write_request` recebem o objecto
  `step` do plano e fixam `source="plan_runner"` (o enum do schema partilhado com
  o Node); `_read_jsonl`/`_append_jsonl`/`_now`/`SOURCE` ficam aqui porque o
  engine, langgraph_engine, council_session, external_worker, cli e memory_l4
  os usam directamente.
- The JSON Schema is validated in the test suite
  (runner/tests/test_hitl_contract.py), not at runtime.
- Python never sets expires_at (always null) and always uses
  priority="medium" and category=None. See README "What stays
  Python-specific".
- Fields follow the schema exactly; additionalProperties is false.
- W-020: `validate_decision_policy` aplica a politica de actor/rationale
  (docs/architecture/hitl/README.md Actor requirements) sem endurecer o
  schema JSON Schema required.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hitlwright
from hitlwright import (
    DECISIONS_FILE,
    REQUESTS_FILE,
    SCHEMA_ID,
    build_decision,
    latest_request,
    read_decision,
    write_decision,
)

__all__ = [
    "DECISIONS_FILE",
    "REQUESTS_FILE",
    "SCHEMA_ID",
    "SOURCE",
    "build_decision",
    "build_request",
    "latest_request",
    "read_decision",
    "validate_decision_policy",
    "write_decision",
    "write_request",
]

SOURCE = "plan_runner"


def _now() -> str:
    return datetime.now(UTC).isoformat()


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
    """Constroi o dict do pedido HITL conforme o contrato v1 (`hitlwright.build_request`).

    Nao escreve nada. Le `id`, `action` e `human_gate.allow` do objecto `step`
    do plano; `allow` invalido ou vazio cai para ["approve", "reject"].
    """
    gate = getattr(step, "human_gate", None)
    return hitlwright.build_request(
        step_id=getattr(step, "id", None),
        action=getattr(step, "action", None),
        run_id=run_id,
        plan_id=plan_id,
        completed=completed,
        allow=list(getattr(gate, "allow", None) or []),
        source=SOURCE,
        agent_id=agent_id,
        domain=domain,
        mode=mode,
    )


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
    _append_jsonl(run_dir / REQUESTS_FILE, record)
    return record["id"]


def validate_decision_policy(
    decision: dict[str, Any],
    *,
    request_source: str | None = None,
    request_priority: str | None = None,
) -> list[str]:
    """Valida a politica de actor/rationale (W-020); devolve lista de erros.

    Nao levanta excepcao. Lista vazia = conforme a politica.

    Regras (docs/architecture/hitl/README.md — Actor requirements):

    - CLI / source plan_runner: `responder_id` pode ser omitido ou `cli:*`;
      `response_comment` e opcional.
    - source node_api (ou `request_source=="node_api"`):
      - `responder_id` obrigatorio (string nao vazia);
      - `response_comment` obrigatorio se `response` in (reject, edit);
      - `response_comment` recomendado (nao erro) se approve + priority high/critical.

    O schema JSON Schema nao e alterado; esta e politica de aplicacao.
    """
    errors: list[str] = []
    if not decision:
        return ["decision vazia"]

    source = (request_source or decision.get("source") or "").strip()
    response = (decision.get("response") or "").strip()
    responder = decision.get("responder_id")
    comment = decision.get("response_comment")
    priority = (request_priority or decision.get("priority") or "medium").strip()

    strict = source == "node_api"

    if strict:
        if not isinstance(responder, str) or not responder.strip():
            errors.append("responder_id obrigatorio para decisoes node_api")
        if response in ("reject", "edit"):
            if not isinstance(comment, str) or not comment.strip():
                errors.append(
                    f"response_comment obrigatorio quando response={response!r} (node_api)"
                )
        # approve + high/critical: so aviso na docstring; nao bloqueia (recomendado)
        _ = priority  # reservado para futura promocao a erro

    return errors
