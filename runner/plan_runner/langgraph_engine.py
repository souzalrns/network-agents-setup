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

from . import approval, done_when, hitl
from .engine import (
    _check_max_cost,
    _check_max_tokens,
    _load_client_memory,
    _log_ignored_fields,
    _paused_budget,
    _paused_tool_approval,
    _resolve_tool_approval,
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
from .langgraph_compile import add_dependency_edges, build_graph, compile_report, parallel_groups
from .models import Plan, Step
from .skills import skill_ref


def merge_artifacts(left: dict | None, right: dict | None) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged

def _gate_node(
    out: Path,
    plan: Plan,
    step: Step,
    run_id: str,
    log: EventLog,
    completed: list[str],
    mode: str,
    gate_fps: dict[str, dict[str, Any]],
) -> dict:
    """Nó de um gate humano, igual no run e no resume.

    M-010: a decisão só entra por uma resposta dirigida a ESTA interrupção
    (`Command(resume={id_da_interrupção: {...}})`). O valor tem de nomear o gate e trazer uma decisão
    explícita, válida e prevista no `allow`; qualquer outra coisa não decide nada (nunca `approve`
    por omissão).
    """
    from langgraph.types import interrupt

    if not log.has_event("human_gate_requested", run_id, step_id=step.id):
        log.append(
            "human_gate_requested",
            run_id,
            {
                "step_id": step.id,
                "allow": step.human_gate.allow,
                **approval.request_payload(out, plan, step.id),  # M-009
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

    value = interrupt(
        {
            "type": "human_gate",
            "step_id": step.id,
            "allow": step.human_gate.allow,
        }
    )

    if not isinstance(value, dict) or value.get("gate") != step.id:
        raise approval.ApprovalError(
            f"resposta sem destinatário para o gate `{step.id}`: nada foi decidido")
    decision = approval.check_decision(step, value.get("decision"))
    edited_payload = value.get("payload")

    log.append(
        "human_gate_resolved",
        run_id,
        {
            "step_id": step.id,
            "decision": decision,
            "has_payload": edited_payload is not None,
            **(gate_fps.get(step.id) or {"fingerprint": approval.fingerprint(out, plan, step.id)}),  # M-009
        },
        actor={"kind": "human", "id": "cli"},
    )

    if decision == "reject":
        return {
            "error": f"{step.id}:rejected",
            "log": [f"rejected:{step.id}"],
        }

    artifacts: dict[str, str] = {}
    if step.output_artifact:
        p = out / step.output_artifact
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            content = edited_payload if edited_payload is not None else {"decision": decision, "step_id": step.id}
            p.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
        artifacts[step.id] = step.output_artifact

    return {
        "completed": [step.id],
        "artifacts": artifacts,
        "log": [f"hitl:{step.id}:{decision}"],
    }


def _decided_now(log: EventLog, run_id: str, target: str | None, decision: str | None) -> set[str]:
    """O gate alvo, se esta retoma o aprovou mesmo (o passo que parou o invoke não vê a escrita dele)."""
    if target and decision in approval.APPROVED and log.has_event(
            "human_gate_resolved", run_id, step_id=target, decision=decision):
        return {target}
    return set()


def _interrupt_id(graph: Any, config: dict[str, Any], gate_id: str) -> str | None:
    """Id da interrupção pendente do gate no checkpoint (M-010: é por ele que a decisão é entregue)."""
    for task in graph.get_state(config).tasks:
        for it in getattr(task, "interrupts", ()) or ():
            v = it.value
            if isinstance(v, dict) and v.get("type") == "human_gate" and v.get("step_id") == gate_id:
                return it.id
    return None


def _settle(out: Path, plan: Plan, log: EventLog, run_id: str, status: dict[str, Any], completed: list[str]) -> None:
    """Estado final de um invoke sem erro: done, ou parado nos gates que foram mesmo pedidos."""
    if all(s.id in completed for s in plan.steps):
        status.pop("paused_at_step", None)
        status.pop("pending_gates", None)
        if done_when.check(out, plan.done_when, log, run_id, status):
            status["state"] = "done"
            status["current_step"] = None
            log.append("plan_done", run_id, {"completed": completed, "engine": "langgraph"})
        return
    waiting = [g for g in approval.pending_gates(out, run_id) if g not in completed]
    if not waiting:  # run antigo sem o evento do pedido: o primeiro gate por fazer
        waiting = [s.id for s in plan.steps if s.human_gate and s.id not in completed][:1]
    if waiting:
        status["state"] = "paused_human_gate"
        status["paused_at_step"] = waiting[0]
        status["current_step"] = waiting[0]
        status["pending_gates"] = waiting  # M-010: cada um pede a sua decisão
    elif done_when.check(out, plan.done_when, log, run_id, status):
        status["state"] = "done"
        status["current_step"] = None


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
    plan = load_plan(out / "plan.yaml")  # M-008: verifica-se a cópia que vai correr, não o original
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

    def node_runner(step: Step, state: dict) -> dict:
        completed = list(state.get("completed") or [])
        if step.id in completed:
            return {}
        if not log.has_event("step_started", run_id, step_id=step.id):
            log.append("step_started", run_id, {"step_id": step.id, "action": step.action, "engine": "langgraph", "skill": skill_ref(out, step)})
            inject_knowledge_context(out, step, log, run_id)

        if step.human_gate:
            return _gate_node(out, plan, step, run_id, log, completed, mode, {})

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

        add_dependency_edges(builder, waves, START, END)


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

    except _ToolApproval as t:
        _paused_tool_approval(out, log, run_id, status, t.step_id, t.result, set(t.partial_state.get("completed") or []))
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
    else:
        _settle(out, plan, log, run_id, status, completed)

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


class _ToolApproval(Exception):
    """AU-20: o worker inline parou numa tool de nivel act; o run pausa em paused_human_gate."""

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
    if result.detail == "awaiting_tool_approval":
        raise _ToolApproval(step.id, result, partial_state=dict(state))
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
                log.append("human_gate_requested", run_id, {"step_id": step.id, **approval.request_payload(out, plan, step.id)})
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
                if result.detail == "awaiting_tool_approval":  # AU-20
                    _paused_tool_approval(out, log, run_id, status, step.id, result, completed)
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
    decision: str | None = None,
    payload: str | None = None,
    worker: str | None = None,
    max_tokens: int | None = None,
    max_cost_usd: float | None = None,
    gate: str | None = None,
) -> dict[str, Any]:
    """Retoma a execução a partir do checkpoint do LangGraph.

    M-010: `decision` só decide um gate humano quando a retoma se dirige a ele: o run está parado num
    gate (e é o único à espera) ou `gate` nomeia-o. Retomar por outro motivo (passo externo, orçamento,
    interrupção, aprovação de uma tool) deixa todos os gates à espera, com ou sem `decision`.
    Sem `decision` (None) a retoma só continua o que não depende de uma pessoa.
    """
    out_dir = _validate_out_dir(out_dir)

    if decision is not None and decision not in approval.VALID:
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
    # M-010: que gate (se algum) esta retoma decide. Um `Command(resume=valor)` simples responderia a
    # TODAS as interrupções à espera no checkpoint; por isso a decisão vai só para a interrupção do gate
    # alvo, pelo id dela, e as outras ficam à espera.
    step_by_id = {s.id: s for s in plan.steps}
    tool_pause = state == "paused_human_gate" and bool(status.get("tool_approval"))
    pending = approval.pending_gates(out_dir, run_id)
    target: str | None = None
    if tool_pause:
        if gate is not None:
            raise PlanError("há a aprovação de uma tool à espera: decide-a primeiro (sem --gate); "
                            "o gate do plano fica à espera da sua própria decisão")
    elif gate is not None or state == "paused_human_gate":
        target = approval.target_gate(pending, gate)
        approval.check_decision(step_by_id[target], decision)
    # M-009: as aprovações já dadas têm de bater com o disco (um reject pode sempre parar o run).
    if decision != "reject":
        approval.verify_past(out_dir, plan, log, run_id)
    # M-009: o gate alvo tem de ter o conteúdo que foi pedido (os outros não são decididos aqui).
    gate_fps: dict[str, dict[str, Any]] = {}
    if target is not None:
        gate_fps[target] = approval.check_pending(out_dir, plan, target, str(decision), log, run_id)
    left = [g for g in pending if g != target]
    if left:
        log.append("human_gate_left_pending", run_id, {"gates": left, "resume_for": target or state})
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

    # AU-20: aprovacao de uma tool `act`. A decisao vai para o contrato HITL e o passo
    # volta a correr; um reject recusa so a chamada (o modelo continua), nao o run.
    if state == "paused_human_gate" and status.get("tool_approval"):
        if decision not in {"approve", "reject"}:
            raise PlanError("aprovacao de tool: decision must be approve|reject")
        _resolve_tool_approval(out_dir, log, run_id, status, decision)
        status["state"] = "running"
        save_status(out_dir, status)

    # Reject não precisa de continuar o grafo: regista a decisão e encerra como o motor nativo.
    # (Na aprovação de uma tool o reject recusa só a chamada; o run continua.)
    if decision == "reject" and not tool_pause:
        paused = target or status.get("paused_at_step")

        log.append(
            "human_gate_resolved",
            run_id,
            {
                "step_id": paused,
                "decision": decision,
                **gate_fps.get(target or "", {}),
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
                return _gate_node(out_dir, plan, step, run_id, log, completed, mode, gate_fps)

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

        add_dependency_edges(builder, waves, START, END)

        with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            graph = builder.compile(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }

            command = None  # sem gate alvo: continua o que está por correr, sem responder a ninguém
            if target is not None:
                interrupt_id = _interrupt_id(graph, config, target)
                if interrupt_id is None:
                    raise approval.ApprovalError(
                        f"o gate `{target}` não está à espera no checkpoint do run; nada foi decidido")
                resume_value: dict[str, Any] = {"decision": decision, "gate": target}
                if decision == "edit" and payload:
                    # Aceita BOM se existir (Set-Content -Encoding UTF8 do PowerShell adiciona BOM)
                    resume_value["payload"] = json.loads(payload.removeprefix("\ufeff"))
                command = Command(resume={interrupt_id: resume_value})

            result = graph.invoke(command, config)

    except _WaitExternal as w:
        status["state"] = "waiting_external"
        status["paused_at_step"] = w.step_id
        status["current_step"] = w.step_id
        if w.worker_error:
            status["worker_error"] = w.worker_error
        # Uniao: completed anterior + completed novo (do partial_state) + o gate decidido nesta retoma
        previous = set(status.get("completed") or [])
        new = set(w.partial_state.get("completed") or [])
        union = sorted(previous | new | _decided_now(log, run_id, target, decision))
        if union:
            status["completed"] = union
        save_status(out_dir, status)
        return status

    except _PausedBudget as b:
        done = (set(status.get("completed") or []) | set(b.partial_state.get("completed") or [])
                | _decided_now(log, run_id, target, decision))
        _paused_budget(out_dir, log, run_id, status, b.step_id, b.result, done)
        return status

    except _ToolApproval as t:
        done = (set(status.get("completed") or []) | set(t.partial_state.get("completed") or [])
                | _decided_now(log, run_id, target, decision))
        _paused_tool_approval(out_dir, log, run_id, status, t.step_id, t.result, done)
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
    if decision is not None:
        status["decision"] = decision

    if result.get("error"):
        status["state"] = "failed"
        status["detail"] = result["error"]
    else:
        _settle(out_dir, plan, log, run_id, status, union)

    save_status(out_dir, status)
    return status
