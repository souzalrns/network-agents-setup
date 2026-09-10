from __future__ import annotations

from langgraph.checkpoint.sqlite import SqliteSaver
import json
import shutil
import sys
import traceback
from pathlib import Path
from typing import Annotated, Any, TypedDict
from uuid import uuid4
from operator import add
from .events import EventLog
from .executor import execute_external_request, execute_stub
from .graph import PlanError
from .langgraph_compile import build_graph, compile_report, parallel_groups
from .models import Plan, Step
from .engine import load_plan, load_status, save_status


def merge_artifacts(left: dict | None, right: dict | None) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged

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

    # Limpar status antigo, para nÃ£o confundir
    old_status = out / "status.json"
    if old_status.exists():
        old_status.unlink()

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
        if not log.has_event("step_started", run_id, step_id=step.id):
            log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "engine": "langgraph"})

        if step.human_gate:
            from langgraph.types import interrupt

            if not log.has_event("human_gate_requested", run_id, step_id=step.id):
                log.append(
                    "human_gate_requested",
                    run_id,
                    {
                        "step_id": step.id,
                        "allow": step.human_gate.allow,
                    },
                )

            decision = interrupt(
                {
                    "type": "human_gate",
                    "step_id": step.id,
                    "allow": step.human_gate.allow,
                }
            )

            if decision not in {"approve", "reject", "edit"}:
                raise PlanError("decision must be approve|reject|edit")

            log.append(
                "human_gate_resolved",
                run_id,
                {
                    "step_id": step.id,
                    "decision": decision,
                },
                actor={"kind": "human", "id": "cli"},
            )

            if decision == "reject":
                return {
                    "error": f"{step.id}:rejected",
                    "log": [f"rejected:{step.id}"],
                }

            if step.output_artifact:
                p = out / step.output_artifact
                p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists():
                    p.write_text(
                        json.dumps(
                            {
                                "decision": decision,
                                "step_id": step.id,
                            },
                            indent=2,
                        ) + "\n",
                        encoding="utf-8",
                    )

            return {
                "completed": [step.id],
                "artifacts": {
                    step.id: step.output_artifact
                } if step.output_artifact else {},
                "log": [f"hitl:{step.id}:{decision}"],
            }

        if mode == "stub":
            result = execute_stub(out, step)
        else:
            result = execute_external_request(out, step)
            if result.detail == "waiting_external":
                log.append("step_waiting_external", run_id, {"step_id": step.id})
                raise _WaitExternal(step.id, partial_state=dict(state))

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

    graph, waves = build_graph(plan, node_runner=node_runner)

    thread_id = run_id

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

    result: dict[str, Any] | None = None

    try:
        from langgraph.graph import END, START, StateGraph
        class PlanState(TypedDict, total=False):
            plan_id: str
            completed: Annotated[list[str], add]
            artifacts: Annotated[dict, merge_artifacts]
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


        checkpoint_path = out / "checkpoints.db"
        with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            graph = builder.compile(
                checkpointer=checkpointer,
            )
            result = graph.invoke(
                {"plan_id": plan.id, "completed": [], "artifacts": {}, "log": []},
                {"configurable": {"thread_id": run_id}},
            )

    except _WaitExternal as w:
        status["state"] = "waiting_external"
        status["paused_at_step"] = w.step_id
        status["current_step"] = w.step_id
        if w.partial_state.get("completed"):
            status["completed"] = list(w.partial_state["completed"])
        save_status(out, status)
        return status

    except Exception as e:
        # LangGraph compile/invoke falhou. Registar e fazer fallback.
        print(f"[langgraph] compile/invoke falhou: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        log.append("langgraph_fallback", run_id, {
            "error": str(e),
            "type": type(e).__name__,
        })
        return _run_waves_fallback(plan, out, run_id, mode, log, status)

    # Sucesso do LangGraph
    completed = list(result.get("completed") or [])
    status["completed"] = completed
    if result.get("error"):
        status["state"] = "failed"
        status["detail"] = result["error"]
    elif any(step_by_id[s].human_gate for s in step_by_id if s not in completed):
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
    def __init__(self, step_id: str, partial_state: dict | None = None):
        super().__init__(step_id)
        self.step_id = step_id
        self.partial_state = partial_state or {}


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
    """Resume a execuÃ§Ã£o usando o checkpoint real do LangGraph."""

    if decision not in {"approve", "reject", "edit"}:
        raise PlanError("decision must be approve|reject|edit")

    status = load_status(out_dir)
    if not status:
        raise PlanError("no status.json")

    state = status.get("state")
    if state not in {
        "paused_human_gate",
        "waiting_external",
        "running",
        "interrupted",
    }:
        raise PlanError(f"cannot resume from state {state!r}")

    run_id = status.get("run_id")
    thread_id = status.get("thread_id") or run_id

    if not run_id or not thread_id:
        raise PlanError("missing run_id/thread_id")

    plan_path = out_dir / "plan.yaml"
    if not plan_path.exists():
        raise PlanError("no plan.yaml")

    plan = load_plan(plan_path)
    mode = status.get("mode") or "stub"
    log = EventLog(out_dir / "events.jsonl")

    # Reject nÃ£o precisa continuar o grafo.
    # Registramos a decisÃ£o e encerramos exatamente como o engine tradicional.
    if decision == "reject":
        paused = status.get("paused_at_step")

        log.append(
            "human_gate_resolved",
            run_id,
            {
                "step_id": paused,
                "decision": decision,
            },
            actor={"kind": "human", "id": "cli"},
        )

        status["state"] = "rejected"
        status["decision"] = decision
        save_status(out_dir, status)
        return status

    checkpoint_path = out_dir / "checkpoints.db"

    if not checkpoint_path.exists():
        raise PlanError(f"no LangGraph checkpoint: {checkpoint_path}")

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Command

        class PlanState(TypedDict, total=False):
            plan_id: str
            completed: Annotated[list[str], add]
            artifacts: Annotated[dict, merge_artifacts]
            paused_at: str
            decision: str
            error: str
            log: Annotated[list[str], add]

        step_by_id = {s.id: s for s in plan.steps}

        def node_runner(step: Step, state: dict) -> dict:
            completed = list(state.get("completed") or [])

            if step.id in completed:
                return {}

            if not log.has_event("step_started", run_id, step_id=step.id):
                log.append(
                    "step_started",
                    run_id,
                    {
                        "step_id": step.id,
                        "action": step.action,
                        "engine": "langgraph",
                    },
                )

            if step.human_gate:
                from langgraph.types import interrupt

                if not log.has_event("human_gate_requested", run_id, step_id=step.id):
                    log.append(
                        "human_gate_requested",
                        run_id,
                        {
                            "step_id": step.id,
                            "allow": step.human_gate.allow,
                        },
                    )

                decision_value = interrupt(
                    {
                        "type": "human_gate",
                        "step_id": step.id,
                        "allow": step.human_gate.allow,
                    }
                )

                if decision_value not in {"approve", "reject", "edit"}:
                    raise PlanError("decision must be approve|reject|edit")

                log.append(
                    "human_gate_resolved",
                    run_id,
                    {
                        "step_id": step.id,
                        "decision": decision_value,
                    },
                    actor={"kind": "human", "id": "cli"},
                )

                if decision_value == "reject":
                    return {
                        "error": f"{step.id}:rejected",
                        "log": [f"rejected:{step.id}"],
                    }

                artifacts = {}

                if step.output_artifact:
                    p = out_dir / step.output_artifact
                    p.parent.mkdir(parents=True, exist_ok=True)

                    if not p.exists():
                        p.write_text(
                            json.dumps(
                                {
                                    "decision": decision_value,
                                    "step_id": step.id,
                                },
                                indent=2,
                            ) + "\n",
                            encoding="utf-8",
                        )

                    artifacts[step.id] = step.output_artifact

                return {
                    "completed": [step.id],
                    "artifacts": artifacts,
                    "log": [f"hitl:{step.id}:{decision_value}"],
                }

            if mode == "stub":
                result = execute_stub(out_dir, step)
            else:
                result = execute_external_request(out_dir, step)

                if result.detail == "waiting_external":
                    log.append(
                        "step_waiting_external",
                        run_id,
                        {"step_id": step.id},
                    )
                    raise _WaitExternal(step.id, partial_state=dict(state))

            if not result.ok:
                log.append(
                    "step_failed",
                    run_id,
                    {
                        "step_id": step.id,
                        "detail": result.detail,
                    },
                )
                return {
                    "error": f"{step.id}:{result.detail}"
                }

            log.append(
                "step_finished",
                run_id,
                {
                    "step_id": step.id,
                    "artifact": result.artifact,
                },
            )

            arts = {}

            if result.artifact:
                arts[step.id] = result.artifact

            return {
                "completed": [step.id],
                "artifacts": arts,
                "log": [f"ok:{step.id}"],
            }

        waves = parallel_groups(plan)
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

        with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            graph = builder.compile(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }

            result = graph.invoke(
                Command(resume=decision),
                config,
            )

    except _WaitExternal as w:
        status["state"] = "waiting_external"
        status["paused_at_step"] = w.step_id
        status["current_step"] = w.step_id
        # Uniao: completed anterior + completed novo (do partial_state)
        previous = set(status.get("completed") or [])
        new = set(w.partial_state.get("completed") or [])
        union = sorted(previous | new)
        if union:
            status["completed"] = union
        save_status(out_dir, status)
        return status

    except Exception as e:
        print(
            f"[langgraph] resume falhou: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        traceback.print_exc()

        log.append(
            "langgraph_resume_failed",
            run_id,
            {
                "error": str(e),
                "type": type(e).__name__,
                "decision": decision,
            },
        )

        raise

    completed = list(result.get("completed") or [])
    # Uniao: completed anterior + completed novo (do LangGraph)
    previous = set(status.get("completed") or [])
    new = set(completed)
    union = sorted(previous | new)
    if union:
        status["completed"] = union
    status["decision"] = decision

    if result.get("error"):
        status["state"] = "failed"
        status["detail"] = result["error"]

    elif all(s.id in completed for s in plan.steps):
        status["state"] = "done"
        status["current_step"] = None
        status.pop("paused_at_step", None)

        log.append(
            "plan_done",
            run_id,
            {
                "completed": completed,
                "engine": "langgraph",
            },
        )

    else:
        pending = [
            s.id
            for s in plan.steps
            if s.human_gate and s.id not in completed
        ]

        if pending:
            status["state"] = "paused_human_gate"
            status["paused_at_step"] = pending[0]
            status["current_step"] = pending[0]
        else:
            status["state"] = "done"
            status["current_step"] = None

    save_status(out_dir, status)
    return status
