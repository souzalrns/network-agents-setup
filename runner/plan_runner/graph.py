from __future__ import annotations

from .models import Plan, Step


class PlanError(Exception):
    pass


def validate_plan(plan: Plan) -> None:
    ids = {s.id for s in plan.steps}
    if len(ids) != len(plan.steps):
        raise PlanError("step ids must be unique")
    for s in plan.steps:
        for d in s.depends_on:
            if d not in ids:
                raise PlanError(f"step {s.id!r} depends on unknown {d!r}")
    # cycle check
    visiting: set[str] = set()
    done: set[str] = set()
    by_id = {s.id: s for s in plan.steps}

    def dfs(sid: str) -> None:
        if sid in done:
            return
        if sid in visiting:
            raise PlanError(f"cycle detected at {sid!r}")
        visiting.add(sid)
        for d in by_id[sid].depends_on:
            dfs(d)
        visiting.remove(sid)
        done.add(sid)

    for s in plan.steps:
        dfs(s.id)


def topo_order(plan: Plan) -> list[Step]:
    validate_plan(plan)
    by_id = {s.id: s for s in plan.steps}
    indeg = {s.id: 0 for s in plan.steps}
    for s in plan.steps:
        for d in s.depends_on:
            indeg[s.id] += 1
    # Kahn but preserve plan file order among zeros
    ready = [s.id for s in plan.steps if indeg[s.id] == 0]
    order: list[Step] = []
    seen: set[str] = set()
    while ready:
        sid = ready.pop(0)
        if sid in seen:
            continue
        seen.add(sid)
        order.append(by_id[sid])
        for s in plan.steps:
            if sid in s.depends_on:
                indeg[s.id] -= 1
                if indeg[s.id] == 0:
                    ready.append(s.id)
    if len(order) != len(plan.steps):
        raise PlanError("could not order steps")
    return order
