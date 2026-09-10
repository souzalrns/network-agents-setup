from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from .events import EventLog
from .executor import execute_external_request, execute_stub
from .graph import PlanError
from .langgraph_compile import build_graph, compile_report, parallel_groups
from .models import Plan, Step
from .engine import load_plan, load_status, save_status


def run_plan_langgraph(
    plan_path: Path,
    *,
    mode: str = "stub",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    plan = load_plan(plan_path)
    report = compile_report(plan)

    if mode == "dry-run":
        return {"mode": "dry-run", **report, "order_flat": [s.id for w in parallel_groups(plan) for s in w]}

    run_id = f"run_{uuid4().hex[:10]}"
    out = out_dir or Path("pilots") / run_id
    if out.exists() and any(out.iterdir()):
        st = load_status(out)
        if not st or st.get("state") not in {
            "paused_human_gate",
            "waiting_external",
            "running",
            "interrupted",
        }:
            raise PlanError(f"out dir not empty and not resumable: {out}")

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(plan_path, out / "plan.yaml")
    (out / "langgraph_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    log = EventLog(out / "events.jsonl")
    log.append("plan_created", run_id, {"plan_id": plan.id, "mode": mode, "engine": "langgraph"})

    step_by_id = {s.id: s for s in plan.steps}

    def node_runner(step: Step, state: dict) -> dict:
        completed = list(state.get("completed") or [])
        if step.id in completed:
            return {}
        log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "engine": "langgraph"})

        if step.human_gate:
            # LangGraph interrupt_before should stop before this node;
            # if we enter, treat as gate artifact
            log.append("human_gate_requested", run_id, {"step_id": step.id})
            return {"paused_at": step.id, "log": [f"hitl:{step.id}"]}

        if mode == "stub":
            result = execute_stub(out, step)
        else:
            result = execute_external_request(out, step)
            if result.detail == "waiting_external":
                log.append("step_waiting_external", run_id, {"step_id": step.id})
                raise _WaitExternal(step.id)

        if not result.ok:
            log.append("step_failed", run_id, {"step_id": step.id, "detail": result.detail})
            return {"error": f"{step.id}:{result.detail}"}

        log.append("step_finished", run_id, {"step_id": step.id, "artifact": result.artifact})
        arts = dict(state.get("artifacts") or {})
        if result.artifact:
            arts[step.id] = result.artifact
        return {
            "completed": [step.id],
            "artifacts": arts,
            "log": [f"ok:{step.id}"],
        }

    try:
        graph, waves = build_graph(plan, node_runner=node_runner)
    except PlanError:
        raise

    thread_id = run_id
    config = {"configurable": {"thread_id": thread_id}}

    status: dict[str, Any] = {
        "run_id": run_id,
        "plan_id": plan.id,
        "mode": mode,
        "engine": "langgraph",
        "state": "running",
        "completed": [],
        "waves": [[s.id for s in w] for w in waves],
        "thread_id": thread_id,
    }
    save_status(out, status)

    try:
        # Prefer invoke with checkpointer if available
        try:
            from langgraph.checkpoint.memory import MemorySaver

            memory = MemorySaver()
            graph, waves = build_graph(plan, node_runner=node_runner)
            # rebuild with checkpointer
            from langgraph.graph import END, START, StateGraph
            from typing import Annotated, TypedDict
            from operator import add

            class PlanState(TypedDict, total=False):
                plan_id: str
                completed: Annotated[list[str], add]
                artifacts: dict
                paused_at: str
                decision: str
                error: str
                log: Annotated[list[str], add]

            builder = StateGraph(PlanState)

            def make_node(step: Step):
                def _node(state: PlanState) -> dict:
                    return node_runner(step, state)

                return _node

            for step in plan.steps:
                builder.add_node(step.id, make_node(step))

            for step in waves[0]:
                builder.add_edge(START, step.id)
            for i, wave in enumerate(waves[:-1]):
                for b in waves[i + 1]:
                    preds = b.depends_on or [s.id for s in wave]
                    for p in preds:
                        builder.add_edge(p, b.id)
            for step in waves[-1]:
                builder.add_edge(step.id, END)

            interrupt_before = [s.id for s in plan.steps if s.human_gate]
            graph = builder.compile(
                checkpointer=memory,
                interrupt_before=interrupt_before or None,
            )
        except Exception:
            pass

        result = graph.invoke(
            {"plan_id": plan.id, "completed": [], "artifacts": {}, "log": []},
            config if "memory" in dir() else None,
        )
    except _WaitExternal as w:
        status["state"] = "waiting_external"
        status["paused_at_step"] = w.step_id
        status["current_step"] = w.step_id
        save_status(out, status)
        return status
    except Exception as e:
        # Fallback: sequential wave execution without full graph runtime quirks
        return _run_waves_fallback(plan, out, run_id, mode, log, status)

    completed = list(result.get("completed") or [])
    status["completed"] = completed
    if result.get("error"):
        status["state"] = "failed"
        status["detail"] = result["error"]
    elif any(step_by_id[s].human_gate for s in step_by_id if s not in completed):
        # interrupted before hitl
        pending_hitl = [s.id for s in plan.steps if s.human_gate and s.id not in completed]
        if pending_hitl:
            status["state"] = "paused_human_gate"
            status["paused_at_step"] = pending_hitl[0]
            status["current_step"] = pending_hitl[0]
        else:
            status["state"] = "done"
    else:
        status["state"] = "done"
        status["current_step"] = None
        log.append("plan_done", run_id, {"completed": completed, "engine": "langgraph"})

    save_status(out, status)
    return status


class _WaitExternal(Exception):
    def __init__(self, step_id: str):
        self.step_id = step_id


def _run_waves_fallback(
    plan: Plan,
    out: Path,
    run_id: str,
    mode: str,
    log: EventLog,
    status: dict[str, Any],
) -> dict[str, Any]:
    """Execute by parallel waves using the same stub/external executors (no LG runtime)."""
    waves = parallel_groups(plan)
    completed: set[str] = set()
    status["engine"] = "langgraph_waves_fallback"
    status["waves"] = [[s.id for s in w] for w in waves]

    for wave in waves:
        # sequential within wave for stub determinism; mark as parallel group in status
        status["current_wave"] = [s.id for s in wave]
        save_status(out, status)
        for step in wave:
            if step.id in completed:
                continue
            status["current_step"] = step.id
            save_status(out, status)
            log.append("step_started", run_id, {"step_id": step.id, "action": step.action})

            if step.human_gate:
                log.append("human_gate_requested", run_id, {"step_id": step.id})
                status["state"] = "paused_human_gate"
                status["paused_at_step"] = step.id
                status["completed"] = sorted(completed)
                save_status(out, status)
                return status

            if mode == "stub":
                result = execute_stub(out, step)
            else:
                result = execute_external_request(out, step)
                if result.detail == "waiting_external":
                    status["state"] = "waiting_external"
                    status["paused_at_step"] = step.id
                    status["completed"] = sorted(completed)
                    save_status(out, status)
                    return status

            if not result.ok:
                status["state"] = "failed"
                status["detail"] = result.detail
                save_status(out, status)
                return status

            log.append("step_finished", run_id, {"step_id": step.id, "artifact": result.artifact})
            completed.add(step.id)
            status["completed"] = sorted(completed)
            save_status(out, status)

    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    save_status(out, status)
    return status


def resume_plan_langgraph(out_dir: Path, decision: str) -> dict[str, Any]:
    """Resume: reuse sequential resume semantics (HITL / external)."""
    from .engine import resume_run

    return resume_run(out_dir, decision=decision)
