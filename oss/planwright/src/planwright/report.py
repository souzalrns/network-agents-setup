"""Render the engine's answers as human text or machine JSON."""

from __future__ import annotations

from .graph import Graph
from .model import HOURS_PER_DAY, Plan, Status
from .validate import Report


def _fmt_hours(hours: float) -> str:
    """Human duration: hours under a day, else days to one decimal."""
    if hours < HOURS_PER_DAY:
        n = int(hours) if hours == int(hours) else round(hours, 1)
        return f"{n}h"
    days = hours / HOURS_PER_DAY
    n = int(days) if days == int(days) else round(days, 1)
    return f"{n}d"


def status_counts(plan: Plan) -> dict[str, int]:
    counts = {s.value: 0 for s in Status}
    for it in plan:
        counts[it.status.value] += 1
    return counts


def graph_json(plan: Plan) -> dict:
    """Full machine-readable view of the plan's schedule."""
    graph = Graph(plan)
    out: dict = {
        "items": len(plan),
        "status": status_counts(plan),
        "schedulable": graph.is_schedulable(),
        "ready": [it.id for it in graph.ready()],
        "blocked": graph.blocked(),
    }
    if graph.is_schedulable():
        cp = graph.critical_path()
        out["parallel_layers"] = graph.parallel_layers()
        out["critical_path"] = {
            "ids": cp.ids,
            "hours": cp.hours,
            "human": _fmt_hours(cp.hours),
        }
    else:
        out["cycles"] = [c.nodes for c in graph.find_cycles()]
        out["dangling"] = [list(pair) for pair in graph.dangling_dependencies()]
    return out


def render_graph(plan: Plan) -> str:
    graph = Graph(plan)
    lines: list[str] = []
    counts = status_counts(plan)
    lines.append(
        f"plan: {len(plan)} items  "
        f"(todo {counts['todo']}, doing {counts['doing']}, "
        f"blocked {counts['blocked']}, done {counts['done']})"
    )

    if not graph.is_schedulable():
        lines.append("")
        lines.append("NOT SCHEDULABLE — fix these first:")
        for item_id, dep in graph.dangling_dependencies():
            lines.append(f"  dangling: {item_id} -> {dep} (no such item)")
        for cycle in graph.find_cycles():
            lines.append(f"  cycle: {cycle}")
        return "\n".join(lines)

    ready = graph.ready()
    lines.append("")
    lines.append(f"READY NOW ({len(ready)}): start these today")
    for it in ready:
        est = _fmt_hours(it.estimate_hours) if it.has_estimate else "?"
        owner = f" @{it.owner}" if it.owner else ""
        lines.append(f"  {it.id}  {it.title}  ({est}{owner})")
    if not ready:
        lines.append("  (none — every open item waits on another)")

    layers = graph.parallel_layers()
    if layers:
        lines.append("")
        lines.append(f"PARALLEL LAYERS ({len(layers)}): each layer can run at once")
        for i, layer in enumerate(layers):
            lines.append(f"  L{i}: {', '.join(layer)}")

    blocked = graph.blocked()
    if blocked:
        lines.append("")
        lines.append(f"BLOCKED ({len(blocked)}): waiting on unfinished work")
        for item_id, deps in blocked.items():
            lines.append(f"  {item_id} <- {', '.join(deps)}")

    cp = graph.critical_path()
    lines.append("")
    if cp.ids:
        lines.append(f"CRITICAL PATH: {_fmt_hours(cp.hours)} — {' -> '.join(cp.ids)}")
        lines.append("  (the floor on remaining time; shortening the plan means shortening this)")
    return "\n".join(lines)


def render_next(plan: Plan) -> str:
    """Just the ids ready to start — one per line, for piping or assignment."""
    return "\n".join(it.id for it in Graph(plan).ready())


def render_validation(report: Report) -> str:
    if not report.findings:
        return "OK: plan is valid and schedulable."
    lines = [str(f) for f in report.errors]
    lines += [str(f) for f in report.warnings]
    lines.append("")
    lines.append(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return "\n".join(lines)
