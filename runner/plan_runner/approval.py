"""M-009 (fase 2): a aprovação humana fica presa ao conteúdo que foi aprovado.

Cada pedido de aprovação (`human_gate_requested` de um passo com `human_gate`) leva a impressão
digital do que está em cima da mesa: o sha256 do `plan.yaml` do run e de cada artefacto que já existe
no run nesse momento (de qualquer passo, não só dos que vêm antes do gate), com o resumo
`.summary.md` de cada um quando existe (é o que os passos seguintes podem ler em vez do artefacto).

- **Antes de decidir** (`check_pending`): se o plano ou um desses ficheiros mudou desde o pedido, um
  `approve` não é aceite: o motor regista um pedido novo, com a impressão nova, e pede para rever outra
  vez. Um `edit` aceita (é a pessoa a mudar o conteúdo) e a decisão grava o que mudou (`changed`).
- **Depois de aprovar** (`verify_past`): em cada retoma (menos num `reject`), os ficheiros gravados em
  cada aprovação têm de estar iguais no disco. Se o plano ou um deles mudou, o run não continua.
  Ficheiros que só aparecem depois da aprovação não a invalidam (não foram aprovados).
- **Fail-closed:** um pedido sem impressão (run antigo) conta como mudado; uma aprovação sem impressão
  não deixa continuar.

O publicador (postiz.py) confere o plano e os artefactos que envia contra a impressão da aprovação.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .events import EventLog
from .graph import PlanError
from .models import Plan

APPROVED = ("approve", "edit")


class ApprovalError(PlanError):
    """A aprovação não corresponde ao que está no run (plano ou artefactos mudaram)."""


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _summary(rel: str) -> str:
    p = Path(rel)
    return (p.with_name(f"{p.stem}.summary.md")).as_posix()


def fingerprint(out: Path, plan: Plan, gate_id: str | None = None) -> dict[str, Any]:
    """sha256 do plan.yaml do run e de cada artefacto (e resumo) que existe no run agora."""
    arts: dict[str, str] = {}
    for s in plan.steps:
        if s.human_gate is not None or not s.output_artifact:
            continue  # o artefacto de um gate é o registo da própria decisão
        for rel in (s.output_artifact, _summary(s.output_artifact)):
            h = _sha(out / rel)
            if h:
                arts[rel] = h
    return {"plan_sha256": _sha(out / "plan.yaml"), "artifacts": arts}


def changed_since(out: Path, fp: Any) -> list[str]:
    """O que mudou no disco face a uma impressão gravada (só os ficheiros que ela tem)."""
    if not isinstance(fp, dict):
        return ["(sem impressão digital)"]
    out_list = []
    if fp.get("plan_sha256") != _sha(out / "plan.yaml"):
        out_list.append("plan.yaml")
    for rel, h in sorted((fp.get("artifacts") or {}).items()):
        if _sha(out / rel) != h:
            out_list.append(rel)
    return out_list


def _events(out: Path) -> list[dict[str, Any]]:
    path = out / "events.jsonl"
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _is_tool(payload: dict[str, Any]) -> bool:
    """Pedido de aprovação de uma tool `act` (AU-20), não de um gate do plano."""
    return "request_id" in payload or "tools" in payload


def request_payload(out: Path, plan: Plan, gate_id: str) -> dict[str, Any]:
    """O que juntar ao payload do `human_gate_requested` de um gate."""
    return {"fingerprint": fingerprint(out, plan, gate_id)}


def _last_request(out: Path, run_id: str, gate_id: str) -> dict[str, Any] | None:
    last = None
    for evt in _events(out):
        p = evt.get("payload") or {}
        if evt.get("type") == "human_gate_requested" and evt.get("run_id") == run_id \
                and p.get("step_id") == gate_id and not _is_tool(p):
            last = evt
    return last


def pending_gates(out: Path, run_id: str) -> list[str]:
    """Gates pedidos (pelo motor, ao chegar a eles) e ainda sem decisão, pela ordem do pedido."""
    asked: list[str] = []
    done: set[str] = set()
    for evt in _events(out):
        p = evt.get("payload") or {}
        if evt.get("run_id") != run_id or _is_tool(p) or not p.get("step_id"):
            continue
        if evt.get("type") == "human_gate_requested" and p["step_id"] not in asked:
            asked.append(p["step_id"])
        elif evt.get("type") == "human_gate_resolved":
            done.add(p["step_id"])
    return [g for g in asked if g not in done]


def check_pending(out: Path, plan: Plan, gate_id: str, decision: str, log: EventLog, run_id: str) -> dict[str, Any]:
    """Antes de aceitar a decisão de um gate. Devolve o que juntar ao `human_gate_resolved`."""
    now = fingerprint(out, plan, gate_id)
    if decision not in APPROVED:
        return {"fingerprint": now}
    req = _last_request(out, run_id, gate_id)
    old = ((req or {}).get("payload") or {}).get("fingerprint")
    changed = changed_since(out, old) if isinstance(old, dict) else ["(pedido sem impressão digital)"]
    if decision == "edit":
        # é a pessoa a mudar o conteúdo: o aprovado é o que está agora, e fica escrito o que mudou
        return {"fingerprint": now, "changed": changed}
    if changed:
        log.append("human_gate_requested", run_id, {"step_id": gate_id, "renewed": True, "changed": changed,
                                                    "fingerprint": now})
        (out / "HITL.md").write_text(
            f"# HITL\n\nRun `{run_id}`: o pedido de aprovação do passo `{gate_id}` foi renovado porque mudou "
            f"desde o pedido: {', '.join(changed)}.\n\nRevê outra vez e decide:\n```\n"
            f"python -m plan_runner resume {out} --decision approve\n```\n",
            encoding="utf-8",
        )
        raise ApprovalError(
            f"a aprovação de `{gate_id}` não foi aceite: mudou desde o pedido ({', '.join(changed)}). "
            "O pedido foi renovado; revê o conteúdo e decide outra vez.")
    return {"fingerprint": now}


def verify_past(out: Path, plan: Plan, log: EventLog, run_id: str) -> None:
    """Os ficheiros de cada aprovação já dada têm de estar iguais no disco; senão o run não continua."""
    for evt in _events(out):
        p = evt.get("payload") or {}
        if evt.get("type") != "human_gate_resolved" or evt.get("run_id") != run_id \
                or p.get("decision") not in APPROVED or _is_tool(p):
            continue
        changed = changed_since(out, p.get("fingerprint"))
        if changed == ["(sem impressão digital)"]:
            changed = ["(aprovação sem impressão digital)"]
        if changed:
            gid = p.get("step_id")
            log.append("approval_invalidated", run_id, {"step_id": gid, "changed": changed})
            raise ApprovalError(
                f"a aprovação de `{gid}` deixou de valer: mudou depois de aprovado ({', '.join(changed)}). "
                "O run não continua; repõe o conteúdo aprovado ou começa um run novo.")
