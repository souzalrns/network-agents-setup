"""M-009 (fase 2): a aprovação humana fica presa ao conteúdo que foi aprovado.

Cada pedido de aprovação (`human_gate_requested` de um passo com `human_gate`) leva a impressão
digital do que está em cima da mesa: o sha256 do `plan.yaml` do run e de cada artefacto que os passos
antes do gate produziram. A decisão (`human_gate_resolved`) leva a impressão do momento da decisão.

- **Antes de decidir** (`check_pending`): se o plano ou um artefacto mudou desde o pedido, um `approve`
  não é aceite (um `edit` aceita, porque é a pessoa a mudar o conteúdo, e fica preso ao que está agora); o motor regista um pedido novo, com a impressão nova, e pede para rever outra vez.
- **Depois de aprovar** (`verify_past`): em cada retoma, todas as aprovações do run têm de bater com o
  que está no disco. Se o plano ou um artefacto aprovado mudou, o run não continua.
- **Fail-closed:** um pedido sem impressão (run antigo) conta como mudado; uma aprovação sem impressão
  não deixa continuar.

O publicador (postiz.py) confere os artefactos que envia contra a impressão da aprovação.
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


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ancestors(plan: Plan, sid: str) -> set[str]:
    by_id = {s.id: s for s in plan.steps}
    seen: set[str] = set()
    stack = list(by_id[sid].depends_on)
    while stack:
        d = stack.pop()
        if d not in seen:
            seen.add(d)
            stack.extend(by_id[d].depends_on)
    return seen


def fingerprint(out: Path, plan: Plan, gate_id: str) -> dict[str, Any]:
    """sha256 do plan.yaml do run e dos artefactos (que existem) dos passos antes do gate."""
    by_id = {s.id: s for s in plan.steps}
    arts: dict[str, str] = {}
    for sid in sorted(_ancestors(plan, gate_id)):
        rel = by_id[sid].output_artifact
        if rel and (out / rel).is_file():
            arts[rel] = _sha(out / rel)
    plan_file = out / "plan.yaml"
    return {"plan_sha256": _sha(plan_file) if plan_file.is_file() else None, "artifacts": arts}


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


def _diff(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    out = []
    if old.get("plan_sha256") != new.get("plan_sha256"):
        out.append("plan.yaml")
    a, b = old.get("artifacts") or {}, new.get("artifacts") or {}
    out += sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return out


def request_payload(out: Path, plan: Plan, gate_id: str) -> dict[str, Any]:
    """O que juntar ao payload do `human_gate_requested`."""
    return {"fingerprint": fingerprint(out, plan, gate_id)}


def _last_request(out: Path, run_id: str, gate_id: str) -> dict[str, Any] | None:
    last = None
    for evt in _events(out):
        p = evt.get("payload") or {}
        if evt.get("type") == "human_gate_requested" and evt.get("run_id") == run_id \
                and p.get("step_id") == gate_id and p.get("kind") != "tool_approval":
            last = evt
    return last


def check_pending(out: Path, plan: Plan, gate_id: str, decision: str, log: EventLog, run_id: str) -> dict[str, Any]:
    """Antes de aceitar approve/edit: o conteúdo tem de ser o do pedido. Devolve a impressão a gravar."""
    now = fingerprint(out, plan, gate_id)
    if decision != "approve":
        # reject não precisa de prova; edit é a pessoa a mudar o conteúdo: o aprovado é o que está agora
        return {"fingerprint": now}
    req = _last_request(out, run_id, gate_id)
    old = ((req or {}).get("payload") or {}).get("fingerprint")
    changed = _diff(old, now) if isinstance(old, dict) else ["(pedido sem impressão digital)"]
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
    """Cada aprovação já dada no run tem de bater com o disco; senão o run não continua."""
    gates = {s.id for s in plan.steps if s.human_gate is not None}
    for evt in _events(out):
        p = evt.get("payload") or {}
        if evt.get("type") != "human_gate_resolved" or evt.get("run_id") != run_id \
                or p.get("decision") not in APPROVED or p.get("kind") == "tool_approval":
            continue
        gid = p.get("step_id")
        if gid not in gates:
            # o gate saiu do plano depois de aprovado: o plano mudou
            changed = ["plan.yaml"]
        else:
            fp = p.get("fingerprint")
            changed = _diff(fp, fingerprint(out, plan, gid)) if isinstance(fp, dict) else ["(aprovação sem impressão digital)"]
        if changed:
            log.append("approval_invalidated", run_id, {"step_id": gid, "changed": changed})
            raise ApprovalError(
                f"a aprovação de `{gid}` deixou de valer: mudou depois de aprovado ({', '.join(changed)}). "
                "O run não continua; repõe o conteúdo aprovado ou começa um run novo.")
