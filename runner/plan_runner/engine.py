from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from .events import EventLog
from .executor import execute_external_request, execute_stub
from .graph import PlanError, topo_order, validate_plan
from .models import Plan


def load_plan(path: Path) -> Plan:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise PlanError("plan root must be a mapping")
    plan = Plan.from_dict(data)
    validate_plan(plan)
    return plan


def _status_path(out: Path) -> Path:
    return out / "status.json"


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


_RESUMABLE = frozenset({"paused_human_gate", "waiting_external", "running"})


def run_plan(
    plan_path: Path,
    *,
    mode: str = "stub",
    out_dir: Path | None = None,
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

    run_id = f"run_{uuid4().hex[:10]}"
    out = out_dir or Path("pilots") / run_id
    if out.exists() and any(out.iterdir()):
        st = load_status(out)
        if not st or st.get("state") not in _RESUMABLE:
            raise PlanError(f"out dir not empty and not resumable: {out}")

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, out / "plan.yaml")
    log = EventLog(out / "events.jsonl")
    log.append("plan_created", run_id, {"plan_id": plan.id, "mode": mode, "objective": plan.objective})

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
            {"step_id": step.id, "action": step.action, "tools_allowed": step.tools_allowed},
            actor={"kind": "system", "id": "plan_runner"},
        )

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
            result = execute_external_request(out, step)
            if result.detail == "waiting_external":
                log.append("step_waiting_external", run_id, {"step_id": step.id})
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

    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    save_status(out, status)
    return status


def resume_run(out_dir: Path, decision: str) -> dict[str, Any]:
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

    # Crash recovery: state left as "running" mid-step — continue like waiting_external
    if state == "running":
        log.append(
            "resume_after_interrupt",
            run_id,
            {"current_step": status.get("current_step"), "paused_at_step": status.get("paused_at_step")},
        )

    if state == "paused_human_gate":
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
        log.append("step_started", run_id, {"step_id": step.id, "action": step.action})

        if step.human_gate:
            log.append(
                "human_gate_requested",
                run_id,
                {"step_id": step.id, "allow": step.human_gate.allow},
            )
            status["state"] = "paused_human_gate"
            status["paused_at_step"] = step.id
            status["completed"] = sorted(completed)
            save_status(out_dir, status)
            return status

        if mode == "stub":
            result = execute_stub(out_dir, step)
        else:
            result = execute_external_request(out_dir, step)
            if result.detail == "waiting_external":
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

    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    status.pop("paused_at_step", None)
    save_status(out_dir, status)
    return status
