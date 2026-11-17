from __future__ import annotations

"""Compile plan.yaml topology into a LangGraph StateGraph (lab)."""

from operator import add
from typing import Annotated, Any, TypedDict

from .graph import PlanError, validate_plan
from .models import Plan, Step


def parallel_groups(plan: Plan) -> list[list[Step]]:
    """Partition steps into waves: same wave => all deps satisfied by prior waves only.

    Within a wave, steps are independent (no depends_on among themselves) => parallelizable.
    """
    validate_plan(plan)
    remaining = {s.id: s for s in plan.steps}
    done: set[str] = set()
    waves: list[list[Step]] = []
    while remaining:
        wave = [
            s
            for s in remaining.values()
            if all(d in done for d in s.depends_on)
        ]
        if not wave:
            raise PlanError("cycle or unsatisfiable depends_on")
        # stable order by original plan order
        order_idx = {s.id: i for i, s in enumerate(plan.steps)}
        wave.sort(key=lambda s: order_idx[s.id])
        waves.append(wave)
        for s in wave:
            done.add(s.id)
            del remaining[s.id]
    return waves


def add_dependency_edges(builder: Any, waves: list[list[Step]], start: Any, end: Any) -> None:
    """Arestas do grafo: cada passo espera por TODAS as suas dependências (M-011).

    Duas arestas separadas para o mesmo destino (`add_edge(a, c)` e `add_edge(b, c)`) fazem o `c` correr
    quando a PRIMEIRA origem acaba: um gate humano era pedido antes de a revisão e a compliance de que
    depende terem acabado, com a impressão digital sem esses artefactos. Uma lista de origens
    (`add_edge([a, b], c)`) é a junção do LangGraph que espera por todas.
    """
    for step in waves[0]:
        builder.add_edge(start, step.id)
    for i, wave in enumerate(waves[:-1]):
        for b in waves[i + 1]:
            preds = list(dict.fromkeys(b.depends_on or [s.id for s in wave]))
            builder.add_edge(preds if len(preds) > 1 else preds[0], b.id)
    for step in waves[-1]:
        builder.add_edge(step.id, end)


def build_graph(plan: Plan, *, node_runner: Any):
    """Build compiled LangGraph. node_runner(step_id: str, state: dict) -> dict updates."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as e:
        raise PlanError(
            "langgraph not installed; pip install -r requirements-langgraph.txt"
        ) from e

    class PlanState(TypedDict, total=False):
        plan_id: str
        completed: Annotated[list[str], add]
        artifacts: dict[str, str]
        paused_at: str
        decision: str
        error: str
        log: Annotated[list[str], add]

    builder = StateGraph(PlanState)

    def make_node(step: Step):
        def _node(state: PlanState) -> dict:
            return node_runner(step, state)

        _node.__name__ = f"step_{step.id}"
        return _node

    for step in plan.steps:
        builder.add_node(step.id, make_node(step))

    waves = parallel_groups(plan)
    if not waves:
        builder.add_edge(START, END)
        return builder.compile(), waves

    add_dependency_edges(builder, waves, START, END)

    # human_gate nodes: interrupt_before
    interrupt_before = [s.id for s in plan.steps if s.human_gate]
    graph = builder.compile(interrupt_before=interrupt_before or None)
    return graph, waves


def compile_report(plan: Plan) -> dict[str, Any]:
    waves = parallel_groups(plan)
    return {
        "plan_id": plan.id,
        "engine": "langgraph",
        "waves": [[s.id for s in w] for w in waves],
        "parallel_waves": [len(w) > 1 for w in waves],
        "interrupt_before": [s.id for s in plan.steps if s.human_gate],
        "node_count": len(plan.steps),
    }
