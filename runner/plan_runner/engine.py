from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from . import done_when, hitl, working_memory
from .events import EventLog
from .executor import execute_external_request, execute_stub
from .graph import PlanError, topo_order, validate_plan
from .knowledge_wiring import inject_knowledge_context
from .models import Plan, ignored_plan_fields
from .skills import repo_root_from_out, skill_ref


def load_plan(path: Path) -> Plan:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise PlanError("plan root must be a mapping")
    plan = Plan.from_dict(data)
    validate_plan(plan)
    return plan


def _status_path(out: Path) -> Path:
    return out / "status.json"


def _load_client_memory(out: Path, plan: Plan, log: EventLog, run_id: str) -> None:
    """S30: injecta o MEMORY.md do cliente (working_memory.py) no arranque
    do run, se o plan.yaml tiver `client_id` de topo. Aditivo -- planos sem
    `client_id` ficam 100% inalterados (working_memory.py continua
    read-only, nao ganhou nenhuma funcao de escrita).

    Escreve `out/client_memory.md` (visivel a qualquer step do run);
    `executor.py::execute_external_request` copia-o para
    `pending_steps/<id>/CLIENT_MEMORY.md`, ao lado de SKILL.md/AGENT.md.
    """
    client_id = plan.raw.get("client_id") if isinstance(plan.raw, dict) else None
    if not client_id:
        return
    repo_root = repo_root_from_out(out)
    text = working_memory.read_memory(str(client_id), repo_root=repo_root)
    if text is None:
        log.append("client_memory_absent", run_id, {"client_id": client_id})
        return
    (out / "client_memory.md").write_text(text, encoding="utf-8")
    log.append("client_memory_loaded", run_id, {"client_id": client_id, "chars": len(text)})


def save_status(out: Path, status: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _status_path(out).write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_status(out: Path) -> dict[str, Any] | None:
    p = _status_path(out)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # status.json corrompido -> tratar como ausente.
        # O resume_run/resume_plan_langgraph ja convertem None em PlanError("no status.json").
        return None


_RESUMABLE = frozenset({"paused_human_gate", "waiting_external", "running", "paused_budget"})


def _validate_out_dir(out: Path) -> Path:
    """Reject out dirs outside <repo>/pilots/.

    Mode external derives repo_root from the out dir (see skills.repo_root_from_out).
    Outside pilots/, that derivation silently returns the wrong root: skill_path and
    agent_path come back as None, the external worker gets a blind request, and the
    run stalls in waiting_external with no error. Validate upfront instead.
    """
    resolved = out.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    pilots = (repo_root / "pilots").resolve()
    try:
        resolved.relative_to(pilots)
    except ValueError:
        raise PlanError(
            f"--out must be inside {pilots} (got {resolved}). "
            "Mode external derives repo_root from the out dir; paths outside pilots/ break it."
        )
    return resolved


def _check_max_tokens(max_tokens: int | None) -> None:
    if max_tokens is not None and (isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 0):
        raise PlanError(f"--max-tokens tem de ser um inteiro >= 0 (got {max_tokens!r})")


def _check_max_cost(max_cost_usd: float | None) -> None:
    if max_cost_usd is not None and (
        isinstance(max_cost_usd, bool) or not isinstance(max_cost_usd, (int, float)) or max_cost_usd < 0
    ):
        raise PlanError(f"--max-cost-usd tem de ser um numero >= 0 (got {max_cost_usd!r})")


def _worker_for(mode: str, name: str | None) -> Any:
    """AU-23: worker inline do modo external (None = esperar por result.json, como sempre)."""
    if name in (None, "", "none"):
        return None
    if mode != "external":
        raise PlanError(f"--worker {name} so faz sentido com --mode external (got {mode!r})")
    from .external_worker import make_worker

    try:
        return make_worker(name)
    except ValueError as e:
        raise PlanError(str(e)) from e


def _waiting_external(log: EventLog, run_id: str, status: dict[str, Any], step_id: str, result: Any) -> None:
    payload: dict[str, Any] = {"step_id": step_id}
    if result.worker_error:
        payload["worker_error"] = result.worker_error
        status["worker_error"] = result.worker_error
    log.append("step_waiting_external", run_id, payload)


def _paused_budget(out: Path, log: EventLog, run_id: str, status: dict[str, Any], step_id: str, result: Any, completed: set[str]) -> None:
    """PLANO item 4: tecto de tokens atingido. Pausa (nao mata): o resume com --max-tokens continua daqui."""
    budget = result.budget or {}
    log.append("budget_exceeded", run_id, {"step_id": step_id, **budget})
    status["state"] = "paused_budget"
    status["paused_at_step"] = step_id
    status["completed"] = sorted(completed)
    status["budget_spent"] = budget.get("spent")
    usd = budget.get("unit") == "usd"
    if usd:
        status["budget_unit"] = "usd"
    save_status(out, status)
    what, flag = ("custo", "--max-cost-usd") if usd else ("tokens", "--max-tokens")
    spent = f"US$ {budget.get('spent'):.6f} gastos" if usd else f"{budget.get('spent')} tokens gastos"
    cap = f"US$ {budget.get('cap')}" if usd else f"{budget.get('cap')}"
    (out / "BUDGET.md").write_text(
        f"# Orcamento de {what}\n\nRun `{run_id}` parado antes do passo `{step_id}`: "
        f"{spent} >= tecto {cap}.\n\n"
        f"Passos feitos: {sorted(completed)}\n\n"
        f"Retomar com um tecto maior (docs/ops/BUDGET.md):\n```\n"
        f"python -m plan_runner resume {out} {flag} <novo tecto>\n```\n",
        encoding="utf-8",
    )


def _paused_tool_approval(out: Path, log: EventLog, run_id: str, status: dict[str, Any], step_id: str, result: Any, completed: set[str]) -> None:
    """AU-20: uma tool de nivel act espera por um humano. O passo nao acabou: o resume decide e volta a corre-lo."""
    approval = result.approval or {}
    log.append("human_gate_requested", run_id, {"step_id": step_id, "kind": "tool_approval", **approval})
    status["state"] = "paused_human_gate"
    status["paused_at_step"] = step_id
    status["completed"] = sorted(completed)
    status["tool_approval"] = {"step_id": step_id, **approval}
    save_status(out, status)
    (out / "HITL.md").write_text(
        f"# HITL: aprovacao de tool\n\nRun `{run_id}` parado no passo `{step_id}`: o modelo pediu "
        f"{', '.join(approval.get('tools') or [])} (nivel act). Nada correu ainda.\n\n"
        f"Pedido `{approval.get('request_id')}` em `hitl-requests.jsonl` (argumentos em `context.tool_calls`).\n\n"
        f"Aprovar ou recusar:\n```\npython -m plan_runner resume {out} --decision approve\n"
        f"python -m plan_runner resume {out} --decision reject\n```\n",
        encoding="utf-8",
    )


def _resolve_tool_approval(out: Path, log: EventLog, run_id: str, status: dict[str, Any], decision: str) -> None:
    """Resume de um paused_human_gate de tool: grava a decisao no contrato HITL (se o lado Node nao o fez) e segue."""
    approval = status.pop("tool_approval")
    if decision not in {"approve", "reject"}:
        raise PlanError("aprovacao de tool: decision must be approve|reject")
    request_id = approval.get("request_id")
    already = any(d.get("id") == request_id for d in hitl._read_jsonl(out / hitl.DECISIONS_FILE))
    if not already:
        hitl.write_decision(out, request_id, response=decision, responder_id="cli")
    log.append(
        "human_gate_resolved",
        run_id,
        {"step_id": approval.get("step_id"), "decision": decision, "kind": "tool_approval", "request_id": request_id},
        actor={"kind": "human", "id": "cli"},
    )


def _log_ignored_fields(plan_path: Path, log: EventLog, run_id: str) -> None:
    """AU-22: regista os campos do plano que o runner nao aplica (models.IGNORED_PLAN_FIELDS)."""
    try:
        data = yaml.safe_load(Path(plan_path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return
    fields = ignored_plan_fields(data) if isinstance(data, dict) else []
    if fields:
        log.append("plan_fields_ignored", run_id, {"fields": fields, "doc": "docs/ops/WORKER-EXTERNAL.md#limites-actuais"})


def run_plan(
    plan_path: Path,
    *,
    mode: str = "stub",
    out_dir: Path | None = None,
    worker: str | None = None,
    max_tokens: int | None = None,
    max_cost_usd: float | None = None,
) -> dict[str, Any]:
    plan = load_plan(plan_path)
    order = topo_order(plan)

    if mode == "dry-run":
        return {
            "mode": "dry-run",
            "plan_id": plan.id,
            "order": [s.id for s in order],
            "actions": [s.action for s in order],
        }

    worker_obj = _worker_for(mode, worker)
    _check_max_tokens(max_tokens)
    _check_max_cost(max_cost_usd)
    run_id = f"run_{uuid4().hex[:10]}"
    out = _validate_out_dir(out_dir) if out_dir else Path("pilots") / run_id
    if out.exists() and any(out.iterdir()):
        st = load_status(out)
        if not st or st.get("state") not in _RESUMABLE:
            raise PlanError(f"out dir not empty and not resumable: {out}")

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, out / "plan.yaml")
    log = EventLog(out / "events.jsonl")
    log.append("plan_created", run_id, {"plan_id": plan.id, "mode": mode, "objective": plan.objective})
    _log_ignored_fields(plan_path, log, run_id)
    _load_client_memory(out, plan, log, run_id)

    completed: set[str] = set()
    steps_run = 0
    status: dict[str, Any] = {
        "run_id": run_id,
        "plan_id": plan.id,
        "mode": mode,
        "state": "running",
        "completed": [],
        "current_step": None,
    }
    if worker_obj is not None:
        status["worker"] = worker_obj.name
    if max_tokens is not None:
        status["max_tokens"] = max_tokens  # tem prioridade sobre o budget.max_tokens do plano
    if max_cost_usd is not None:
        status["max_cost_usd"] = max_cost_usd  # D6: idem para o budget.max_cost_usd

    for step in order:
        if steps_run >= plan.budget_max_steps:
            log.append("plan_aborted", run_id, {"reason": "max_steps"})
            status["state"] = "aborted_budget"
            save_status(out, status)
            return status

        if not all(d in completed for d in step.depends_on):
            raise PlanError(f"internal: deps not met for {step.id}")

        status["current_step"] = step.id
        save_status(out, status)
        log.append(
            "step_started",
            run_id,
            {"step_id": step.id, "action": step.action, "tools_allowed": step.tools_allowed, "skill": skill_ref(out, step)},
            actor={"kind": "system", "id": "plan_runner"},
        )
        inject_knowledge_context(out, step, log, run_id)

        if step.human_gate:
            log.append(
                "human_gate_requested",
                run_id,
                {
                    "step_id": step.id,
                    "level": step.human_gate.level,
                    "kind": step.human_gate.kind,
                    "allow": step.human_gate.allow,
                },
            )
            hitl.write_request(
                out,
                step=step,
                run_id=run_id,
                plan_id=plan.id,
                completed=sorted(completed),
                mode=mode,
            )
            status["state"] = "paused_human_gate"
            status["paused_at_step"] = step.id
            status["completed"] = sorted(completed)
            save_status(out, status)
            (out / "HITL.md").write_text(
                f"# HITL\n\nRun `{run_id}` paused at step `{step.id}` ({step.action}).\n\n"
                f"Allow: {step.human_gate.allow}\n\n"
                f"Resume:\n```\npython -m plan_runner resume {out} --decision approve\n```\n",
                encoding="utf-8",
            )
            return status

        if mode == "stub":
            result = execute_stub(out, step)
        elif mode == "external":
            result = execute_external_request(out, step, worker_obj)
            if result.detail == "budget_exceeded":
                _paused_budget(out, log, run_id, status, step.id, result, completed)
                return status
            if result.detail == "awaiting_tool_approval":
                _paused_tool_approval(out, log, run_id, status, step.id, result, completed)
                return status
            if result.detail == "waiting_external":
                _waiting_external(log, run_id, status, step.id, result)
                status["state"] = "waiting_external"
                status["paused_at_step"] = step.id
                status["completed"] = sorted(completed)
                save_status(out, status)
                return status
        else:
            raise PlanError(f"unknown mode {mode!r}")

        steps_run += 1
        if not result.ok:
            log.append("step_failed", run_id, {"step_id": step.id, "detail": result.detail})
            status["state"] = "failed"
            status["failed_step"] = step.id
            status["detail"] = result.detail
            save_status(out, status)
            return status

        log.append(
            "step_finished",
            run_id,
            {"step_id": step.id, "detail": result.detail, "artifact": result.artifact},
        )
        completed.add(step.id)
        status["completed"] = sorted(completed)
        save_status(out, status)

    if not done_when.check(out, plan.done_when, log, run_id, status):
        save_status(out, status)
        return status
    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    save_status(out, status)
    return status


def resume_run(
    out_dir: Path,
    decision: str,
    worker: str | None = None,
    max_tokens: int | None = None,
    max_cost_usd: float | None = None,
) -> dict[str, Any]:
    out_dir = _validate_out_dir(out_dir)
    status = load_status(out_dir)
    if not status:
        raise PlanError("no status.json")
    state = status.get("state")
    if state not in _RESUMABLE:
        raise PlanError(f"cannot resume from state {state!r}")

    run_id = status["run_id"]
    log = EventLog(out_dir / "events.jsonl")
    plan = load_plan(out_dir / "plan.yaml")
    order = topo_order(plan)
    completed = set(status.get("completed") or [])
    mode = status.get("mode") or "stub"
    # --worker no resume tem prioridade; sem ele, o worker com que o run arrancou.
    worker_name = worker if worker is not None else status.get("worker")
    worker_obj = _worker_for(mode, worker_name)
    if worker is not None:
        if worker_obj is None:
            status.pop("worker", None)
        else:
            status["worker"] = worker_obj.name
    status.pop("worker_error", None)
    _check_max_tokens(max_tokens)
    _check_max_cost(max_cost_usd)
    if max_tokens is not None:
        status["max_tokens"] = max_tokens
    if max_cost_usd is not None:
        status["max_cost_usd"] = max_cost_usd
    if state == "paused_budget":
        payload = {"step_id": status.get("paused_at_step"), "spent": status.get("budget_spent"), "max_tokens": status.get("max_tokens")}
        if status.get("max_cost_usd") is not None:
            payload["max_cost_usd"] = status["max_cost_usd"]
        log.append("budget_resumed", run_id, payload, actor={"kind": "human", "id": "cli"})
        status.pop("budget_spent", None)  # se voltar a parar, _paused_budget grava o valor novo
        status.pop("budget_unit", None)

    # Crash recovery: state left as "running" mid-step — continue like waiting_external
    if state == "running":
        log.append(
            "resume_after_interrupt",
            run_id,
            {"current_step": status.get("current_step"), "paused_at_step": status.get("paused_at_step")},
        )

    if state == "paused_human_gate" and status.get("tool_approval"):
        # AU-20: o passo parou numa tool `act`; reject recusa a chamada (o modelo continua), nao o run.
        _resolve_tool_approval(out_dir, log, run_id, status, decision)
    elif state == "paused_human_gate":
        if decision not in {"approve", "reject", "edit"}:
            raise PlanError("decision must be approve|reject|edit")
        paused = status.get("paused_at_step")
        log.append(
            "human_gate_resolved",
            run_id,
            {"step_id": paused, "decision": decision},
            actor={"kind": "human", "id": "cli"},
        )
        if decision == "reject":
            status["state"] = "rejected"
            save_status(out_dir, status)
            return status
        if paused:
            completed.add(paused)
            step_gate = next(s for s in plan.steps if s.id == paused)
            if step_gate.output_artifact:
                p = out_dir / step_gate.output_artifact
                p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists():
                    p.write_text(
                        json.dumps({"decision": decision, "step_id": paused}, indent=2) + "\n",
                        encoding="utf-8",
                    )

    status["state"] = "running"
    status["completed"] = sorted(completed)
    save_status(out_dir, status)

    steps_run = len(completed)
    for step in order:
        if step.id in completed:
            continue
        if steps_run >= plan.budget_max_steps:
            log.append("plan_aborted", run_id, {"reason": "max_steps"})
            status["state"] = "aborted_budget"
            save_status(out_dir, status)
            return status
        if not all(d in completed for d in step.depends_on):
            continue

        status["current_step"] = step.id
        save_status(out_dir, status)
        log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "skill": skill_ref(out_dir, step)})
        inject_knowledge_context(out_dir, step, log, run_id)

        if step.human_gate:
            log.append(
                "human_gate_requested",
                run_id,
                {"step_id": step.id, "allow": step.human_gate.allow},
            )
            hitl.write_request(
                out_dir,
                step=step,
                run_id=run_id,
                plan_id=plan.id,
                completed=sorted(completed),
                mode=mode,
            )
            status["state"] = "paused_human_gate"
            status["paused_at_step"] = step.id
            status["completed"] = sorted(completed)
            save_status(out_dir, status)
            return status

        if mode == "stub":
            result = execute_stub(out_dir, step)
        else:
            result = execute_external_request(out_dir, step, worker_obj)
            if result.detail == "budget_exceeded":
                _paused_budget(out_dir, log, run_id, status, step.id, result, completed)
                return status
            if result.detail == "awaiting_tool_approval":
                _paused_tool_approval(out_dir, log, run_id, status, step.id, result, completed)
                return status
            if result.detail == "waiting_external":
                _waiting_external(log, run_id, status, step.id, result)
                status["state"] = "waiting_external"
                status["paused_at_step"] = step.id
                status["completed"] = sorted(completed)
                save_status(out_dir, status)
                return status

        steps_run += 1
        if not result.ok:
            log.append("step_failed", run_id, {"step_id": step.id, "detail": result.detail})
            status["state"] = "failed"
            save_status(out_dir, status)
            return status

        log.append("step_finished", run_id, {"step_id": step.id, "artifact": result.artifact})
        completed.add(step.id)
        status["completed"] = sorted(completed)
        save_status(out_dir, status)

    if not done_when.check(out_dir, plan.done_when, log, run_id, status):
        status.pop("paused_at_step", None)
        save_status(out_dir, status)
        return status
    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    status.pop("paused_at_step", None)
    status.pop("budget_spent", None)
    status.pop("budget_unit", None)
    save_status(out_dir, status)
    return status
