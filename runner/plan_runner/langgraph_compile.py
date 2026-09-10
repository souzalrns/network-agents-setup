from __future__ import annotations

"""Compile plan.yaml topology into a LangGraph StateGraph (lab)."""

from typing import Any, Annotated, TypedDict
from operator import add

from .graph import PlanError, topo_order, validate_plan
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

    # START -> first wave (parallel if multiple)
    for step in waves[0]:
        builder.add_edge(START, step.id)

    for i, wave in enumerate(waves[:-1]):
        nxt = waves[i + 1]
        for a in wave:
            for b in nxt:
                # only if b depends only on completed set including a's wave
                # simpler: connect every wave[i] node to every wave[i+1] node
                # LangGraph waits for all predecessors — but multiple edges TO b from all a
                # means b runs when all a complete if we use the right pattern.
                # For linear deps, each b may not depend on all a.
                deps = set(b.depends_on)
                if not deps or any(a.id in deps or a.id in {s.id for s in waves[i]} for a in wave):
                    if not deps:
                        builder.add_edge(a.id, b.id)
                    elif any(d == a.id for d in deps) or all(
                        d in {s.id for w in waves[: i + 1] for s in w} for d in deps
                    ):
                        if all(d in {s.id for w in waves[: i + 1] for s in w} for d in deps):
                            # edge from each dependency in previous waves is enough;
                            # connect from a if a is a direct dep or we're joining wave
                            if a.id in deps or (
                                i == len(waves) - 2 and a.id in {s.id for s in wave}
                            ):
                                pass
        # Correct approach: for each step in nxt, add edges from each of its depends_on
        for b in nxt:
            preds = b.depends_on or [s.id for s in wave]
            for p in preds:
                if p in {s.id for s in plan.steps}:
                    builder.add_edge(p, b.id)

    # last wave -> END
    for step in waves[-1]:
        builder.add_edge(step.id, END)

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
