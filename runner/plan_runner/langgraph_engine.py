from __future__ import annotations

import json
import shutil
import sys
import traceback
from operator import add
from pathlib import Path
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver

from . import done_when, hitl
from .engine import (
    _check_max_cost,
    _check_max_tokens,
    _load_client_memory,
    _log_ignored_fields,
    _paused_budget,
    _validate_out_dir,
    _worker_for,
    load_plan,
    load_status,
    save_status,
)
from .events import EventLog
from .executor import execute_external_request, execute_stub
from .graph import PlanError
from .knowledge_wiring import inject_knowledge_context
from .langgraph_compile import build_graph, compile_report, parallel_groups
from .models import Plan, Step
from .skills import skill_ref


def merge_artifacts(left: dict | None, right: dict | None) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged

def run_plan_langgraph(
    plan_path: Path,
    *,
    mode: str = "stub",
    out_dir: Path | None = None,
    worker: str | None = None,
    max_tokens: int | None = None,
    max_cost_usd: float | None = None,
) -> dict[str, Any]:
    plan = load_plan(plan_path)
    report = compile_report(plan)

    if mode == "dry-run":
        return {"mode": "dry-run", **report, "order_flat": [s.id for w in parallel_groups(plan) for s in w]}

    worker_obj = _worker_for(mode, worker)  # W-005: worker inline, como no native
    _check_max_tokens(max_tokens)
    _check_max_cost(max_cost_usd)
    run_id = f"run_{uuid4().hex[:10]}"
    out = _validate_out_dir(out_dir) if out_dir else Path("pilots") / run_id
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
    _log_ignored_fields(plan_path, log, run_id)
    _load_client_memory(out, plan, log, run_id)

    # AU-22: o native aplica budget.max_steps passo a passo (engine.py); aqui as ondas
    # correm em paralelo, por isso a garantia (nunca mais de max_steps passos) e
    # verificada antes de arrancar: um plano maior nao corre nenhum passo.
    runnable = [s.id for s in plan.steps if not s.human_gate]
    if len(runnable) > plan.budget_max_steps:
        log.append("plan_aborted", run_id, {
            "reason": "max_steps", "engine": "langgraph", "steps": len(runnable), "max_steps": plan.budget_max_steps,
        })
        status = {"run_id": run_id, "plan_id": plan.id, "mode": mode, "engine": "langgraph",
                  "state": "aborted_budget", "completed": []}
        save_status(out, status)
        return status

    step_by_id = {s.id: s for s in plan.steps}

    def node_runner(step: Step, state: dict) -> dict:
        completed = list(state.get("completed") or [])
        if step.id in completed:
            return {}
        if not log.has_event("step_started", run_id, step_id=step.id):
            log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "engine": "langgraph", "skill": skill_ref(out, step)})
            inject_knowledge_context(out, step, log, run_id)

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
                hitl.write_request(
                    out,
                    step=step,
                    run_id=run_id,
                    plan_id=plan.id,
                    completed=completed,
                    mode=mode,
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
            result = _external(out, step, worker_obj, log, run_id, state)

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
    if worker_obj is not None:
        status["worker"] = worker_obj.name
    if max_tokens is not None:
        status["max_tokens"] = max_tokens
    if max_cost_usd is not None:
        status["max_cost_usd"] = max_cost_usd
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
        if w.worker_error:
            status["worker_error"] = w.worker_error
        if w.partial_state.get("completed"):
            status["completed"] = list(w.partial_state["completed"])
        save_status(out, status)
        return status

    except _PausedBudget as b:
        _paused_budget(out, log, run_id, status, b.step_id, b.result, set(b.partial_state.get("completed") or []))
        return status

    except Exception as e:
        # LangGraph compile/invoke falhou. Registar e fazer fallback.
        print(f"[langgraph] compile/invoke falhou: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        log.append("langgraph_fallback", run_id, {
            "error": str(e),
            "type": type(e).__name__,
        })
        return _run_waves_fallback(plan, out, run_id, mode, log, status, worker_obj)

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
        elif done_when.check(out, plan.done_when, log, run_id, status):
            status["state"] = "done"
    elif done_when.check(out, plan.done_when, log, run_id, status):
        status["state"] = "done"
        status["current_step"] = None
        log.append("plan_done", run_id, {"completed": completed, "engine": "langgraph"})

    save_status(out, status)
    return status


class _WaitExternal(Exception):
    def __init__(self, step_id: str, partial_state: dict | None = None, worker_error: str | None = None):
        super().__init__(step_id)
        self.step_id = step_id
        self.partial_state = partial_state or {}
        self.worker_error = worker_error


class _PausedBudget(Exception):
    """W-005: o worker inline encontrou um tecto (tokens ou custo); o run pausa em paused_budget."""

    def __init__(self, step_id: str, result: Any, partial_state: dict | None = None):
        super().__init__(step_id)
        self.step_id = step_id
        self.result = result
        self.partial_state = partial_state or {}


def _external(out: Path, step: Step, worker_obj: Any, log: EventLog, run_id: str, state: dict) -> Any:
    """Passo external. W-005: com worker inline o passo corre ja, como no engine native;
    sem worker fica em waiting_external (standalone + resume), como antes."""
    result = execute_external_request(out, step, worker_obj)
    if result.detail == "budget_exceeded":
        raise _PausedBudget(step.id, result, partial_state=dict(state))
    if result.detail == "waiting_external":
        payload: dict[str, Any] = {"step_id": step.id}
        if result.worker_error:
            payload["worker_error"] = result.worker_error
        log.append("step_waiting_external", run_id, payload)
        raise _WaitExternal(step.id, partial_state=dict(state), worker_error=result.worker_error)
    return result


def _run_waves_fallback(
    plan: Plan,
    out: Path,
    run_id: str,
    mode: str,
    log: EventLog,
    status: dict[str, Any],
    worker_obj: Any = None,
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
            log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "skill": skill_ref(out, step)})
            inject_knowledge_context(out, step, log, run_id)

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
                result = execute_external_request(out, step, worker_obj)
                if result.detail == "budget_exceeded":  # W-005
                    _paused_budget(out, log, run_id, status, step.id, result, completed)
                    return status
                if result.detail == "waiting_external":
                    if result.worker_error:
                        status["worker_error"] = result.worker_error
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

    if not done_when.check(out, plan.done_when, log, run_id, status):
        save_status(out, status)
        return status
    log.append("plan_done", run_id, {"completed": sorted(completed)})
    status["state"] = "done"
    status["current_step"] = None
    save_status(out, status)
    return status


def resume_plan_langgraph(
    out_dir: Path,
    decision: str,
    payload: str | None = None,
    worker: str | None = None,
    max_tokens: int | None = None,
    max_cost_usd: float | None = None,
) -> dict[str, Any]:
    out_dir = _validate_out_dir(out_dir)
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
        "paused_budget",
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
    # W-005: --worker no resume tem prioridade; sem ele, o worker com que o run arrancou.
    worker_obj = _worker_for(mode, worker if worker is not None else status.get("worker"))
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
        resumed = {"step_id": status.get("paused_at_step"), "spent": status.get("budget_spent"), "max_tokens": status.get("max_tokens")}
        if status.get("max_cost_usd") is not None:
            resumed["max_cost_usd"] = status["max_cost_usd"]
        log.append("budget_resumed", run_id, resumed, actor={"kind": "human", "id": "cli"})
        status.pop("budget_spent", None)
        status.pop("budget_unit", None)
    save_status(out_dir, status)  # o worker le os tectos do status.json em disco (token_cap/cost_cap)
    # Crash recovery: state left as "running" mid-step — continue like waiting_external.
    # Mesmo evento do engine legacy (engine.py:183) para paridade de observabilidade.
    if state == "running":
        log.append(
            "resume_after_interrupt",
            run_id,
            {
                "current_step": status.get("current_step"),
                "paused_at_step": status.get("paused_at_step"),
            },
        )

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
                        "skill": skill_ref(out_dir, step),
                    },
                )
                inject_knowledge_context(out_dir, step, log, run_id)

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
                    hitl.write_request(
                        out_dir,
                        step=step,
                        run_id=run_id,
                        plan_id=plan.id,
                        completed=completed,
                        mode=mode,
                    )

                decision_value = interrupt(
                    {
                        "type": "human_gate",
                        "step_id": step.id,
                        "allow": step.human_gate.allow,
                    }
                )

                # Aceita tanto string ("approve") como dict ({"decision": "edit", "payload": {...}})
                if isinstance(decision_value, dict):
                    edited_payload = decision_value.get("payload")
                    decision_str = decision_value.get("decision", "approve")
                else:
                    edited_payload = None
                    decision_str = decision_value

                if decision_str not in {"approve", "reject", "edit"}:
                    raise PlanError("decision must be approve|reject|edit")

                log.append(
                    "human_gate_resolved",
                    run_id,
                    {
                        "step_id": step.id,
                        "decision": decision_str,
                        "has_payload": edited_payload is not None,
                    },
                    actor={"kind": "human", "id": "cli"},
                )

                if decision_str == "reject":
                    return {
                        "error": f"{step.id}:rejected",
                        "log": [f"rejected:{step.id}"],
                    }

                artifacts = {}

                if step.output_artifact:
                    p = out_dir / step.output_artifact
                    p.parent.mkdir(parents=True, exist_ok=True)

                    if not p.exists():
                        if edited_payload is not None:
                            content_to_write = edited_payload
                        else:
                            content_to_write = {
                                "decision": decision_str,
                                "step_id": step.id,
                            }
                        p.write_text(
                            json.dumps(content_to_write, indent=2) + "\n",
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
                result = _external(out_dir, step, worker_obj, log, run_id, state)

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

            if decision == "edit" and payload:
                # Aceita BOM se existir (Set-Content -Encoding UTF8 do PowerShell adiciona BOM)
                payload = payload.removeprefix("\ufeff")
                payload_dict = json.loads(payload)
                resume_value = {"decision": decision, "payload": payload_dict}
            else:
                resume_value = decision

            result = graph.invoke(
                Command(resume=resume_value),
                config,
            )

    except _WaitExternal as w:
        status["state"] = "waiting_external"
        status["paused_at_step"] = w.step_id
        status["current_step"] = w.step_id
        if w.worker_error:
            status["worker_error"] = w.worker_error
        # Uniao: completed anterior + completed novo (do partial_state)
        previous = set(status.get("completed") or [])
        new = set(w.partial_state.get("completed") or [])
        union = sorted(previous | new)
        if union:
            status["completed"] = union
        save_status(out_dir, status)
        return status

    except _PausedBudget as b:
        done = set(status.get("completed") or []) | set(b.partial_state.get("completed") or [])
        _paused_budget(out_dir, log, run_id, status, b.step_id, b.result, done)
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
        status.pop("paused_at_step", None)
        if done_when.check(out_dir, plan.done_when, log, run_id, status):
            status["state"] = "done"
            status["current_step"] = None
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
        elif done_when.check(out_dir, plan.done_when, log, run_id, status):
            status["state"] = "done"
            status["current_step"] = None

    save_status(out_dir, status)
    return status
