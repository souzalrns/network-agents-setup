"""Render a plan as Mermaid diagrams — so a manager *sees* the plan.

Two views, both plain text that GitHub, VS Code and most Markdown viewers render
natively (zero dependencies, nothing to install):

- **deps**: a dependency flowchart (what blocks what), nodes coloured by status.
- **board**: a Kanban-style board (Ready / Doing / Blocked / Done), so the
  parallelism and the bottlenecks are visible at a glance.

Output is wrapped in ```mermaid fences so it can be pasted straight into a
Markdown document. Node ids are assigned by an injective per-plan map, so two
distinct item ids that sanitise to the same token (``A-1`` and ``A_1``) never
collide; labels still show the original id.
"""

from __future__ import annotations

from .graph import Graph
from .model import HOURS_PER_DAY, Plan, Status

# Status → Mermaid classDef style. Colours chosen to read in light and dark.
_CLASSDEFS = [
    "classDef done fill:#1a7f37,stroke:#0b5",
    "classDef doing fill:#9a6700,stroke:#7a5",
    "classDef blocked fill:#cf222e,stroke:#a11,color:#fff",
    "classDef ready fill:#0969da,stroke:#06c,color:#fff",
    "classDef todo fill:#6e7781,stroke:#555,color:#fff",
]


def _node_map(plan: Plan) -> dict[str, str]:
    """Assign each item id a unique Mermaid-safe node token.

    Sanitises non-alphanumerics to '_', prefixes a leading digit, and
    disambiguates collisions with a numeric suffix so the map is injective.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for it in plan:
        base = "".join(c if c.isalnum() else "_" for c in it.id) or "n"
        if base[0].isdigit():
            base = "n" + base
        name = base
        i = 2
        while name in used:
            name = f"{base}__{i}"
            i += 1
        used.add(name)
        mapping[it.id] = name
    return mapping


def _label(item_id: str, title: str, *, max_len: int = 40) -> str:
    """A single-line, quote-safe label `id: title` for a Mermaid node."""
    t = " ".join(title.split())  # collapse newlines/runs of whitespace
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    # Inside a "..." Mermaid label, the only hard breaker is the double quote;
    # backticks can also confuse some renderers. Neutralise both.
    t = t.replace('"', "'").replace("`", "'")
    head = str(item_id).replace('"', "'").replace("`", "'")
    sep = ": " if t else ""
    return f"{head}{sep}{t}"


def _status_class(graph: Graph, item_id: str, ready_ids: set[str]) -> str:
    it = graph.plan.get(item_id)
    if it is None:
        return "todo"
    if it.status is Status.DONE:
        return "done"
    if it.status is Status.DOING:
        return "doing"
    if item_id in ready_ids:
        return "ready"
    return "blocked"


def render_deps(plan: Plan) -> str:
    """Dependency flowchart: an edge dep --> item, nodes coloured by status."""
    graph = Graph(plan)
    ready_ids = {it.id for it in graph.ready()}
    node = _node_map(plan)
    lines = ["```mermaid", "flowchart LR"]
    if len(plan) == 0:
        lines.append('  empty["(plano vazio)"]')
        lines.append("```")
        return "\n".join(lines)

    for it in plan:
        lines.append(f'  {node[it.id]}["{_label(it.id, it.title)}"]')
    lines.append("")
    for it in plan:
        for dep in it.depends:
            if plan.has(dep):
                lines.append(f"  {node[dep]} --> {node[it.id]}")
    lines.append("")
    for cd in _CLASSDEFS:
        lines.append(f"  {cd}")
    for it in plan:
        lines.append(f"  class {node[it.id]} {_status_class(graph, it.id, ready_ids)}")
    lines.append("```")
    return "\n".join(lines)


def render_board(plan: Plan) -> str:
    """Kanban board: one subgraph per bucket (Ready / Doing / Blocked / Done)."""
    graph = Graph(plan)
    node = _node_map(plan)
    ready = [it.id for it in graph.ready()]
    ready_set = set(ready)
    done = [it.id for it in plan if it.status is Status.DONE]
    doing = [it.id for it in plan if it.status is Status.DOING]
    blocked = [it.id for it in plan if it.status not in (Status.DONE, Status.DOING) and it.id not in ready_set]

    buckets = [
        ("Ready", "Pronto para começar", ready),
        ("Doing", "Em curso", doing),
        ("Blocked", "Bloqueado", blocked),
        ("Done", "Concluído", done),
    ]
    lines = ["```mermaid", "flowchart TB"]
    for key, label, ids in buckets:
        lines.append(f'  subgraph {key}["{label} ({len(ids)})"]')
        if ids:
            for item_id in ids:
                lines.append(f'    {node[item_id]}["{_label(item_id, _title(plan, item_id))}"]')
        else:
            lines.append(f"    {key}_empty[ ]")
        lines.append("  end")
    lines.append("")
    for cd in _CLASSDEFS:
        lines.append(f"  {cd}")
    for bucket_ids, cls in ((done, "done"), (doing, "doing"), (ready, "ready"), (blocked, "blocked")):
        for item_id in bucket_ids:
            lines.append(f"  class {node[item_id]} {cls}")
    lines.append("```")
    return "\n".join(lines)


def _title(plan: Plan, item_id: str) -> str:
    it = plan.get(item_id)
    return it.title if it else item_id


def _gantt_duration(hours: float | None) -> str:
    """Estimate hours → a Mermaid gantt duration. Unsized → a nominal 1d."""
    if not hours or hours <= 0:
        return "1d"  # nominal bar for an unsized item (see the view's note)
    if hours >= HOURS_PER_DAY and hours % HOURS_PER_DAY == 0:
        return f"{int(hours // HOURS_PER_DAY)}d"
    if hours == int(hours):
        return f"{int(hours)}h"
    return f"{round(hours, 1)}h"


def render_gantt(plan: Plan) -> str:
    """A Mermaid gantt of **relative effort** (not a calendar).

    The time axis is relative to t0 (plan day 0); bars are effort from `Est` and
    are placed by dependency order (`after`), so it shows "effort and what waits on
    what", never "delivered on Friday". Critical-path items are marked `crit`.
    Unsized items get a nominal 1d bar. Sections are `Track`.
    """
    graph = Graph(plan)
    header = [
        "```mermaid",
        "gantt",
        "    title Plano — esforço relativo (não é calendário)",
        "    dateFormat X",
        "    axisFormat %s",
    ]
    if len(plan) == 0:
        return "\n".join([*header, "    section plano", "    (plano vazio) :done, empty, 0, 1d", "```"])
    if not graph.is_schedulable():
        # Um ciclo/dependência pendente não tem ordenação: não desenhar algo falso.
        return "\n".join([
            "```text",
            "gantt indisponível: o plano tem ciclo ou dependência inexistente.",
            "Corre `planwright validate` e corrige antes de desenhar o gantt.",
            "```",
        ])

    node = _node_map(plan)
    crit = set(graph.critical_path().ids)
    order = [i for layer in graph.parallel_layers() for i in layer]
    # itens já concluídos não entram nas layers (são passado); mostra-os primeiro.
    done_ids = [it.id for it in plan if it.status is Status.DONE]
    ordered = done_ids + [i for i in order if i not in set(done_ids)]

    # agrupa por track preservando a ordem topológica
    sections: list[tuple[str, list[str]]] = []
    seen_tracks: dict[str, list[str]] = {}
    for item_id in ordered:
        it = plan.get(item_id)
        track = (it.track if it and it.track else "plano")
        if track not in seen_tracks:
            seen_tracks[track] = []
            sections.append((track, seen_tracks[track]))
        seen_tracks[track].append(item_id)

    lines = list(header)
    for track, ids in sections:
        lines.append(f"    section {track}")
        for item_id in ids:
            it = plan.get(item_id)
            tags: list[str] = []
            if item_id in crit:
                tags.append("crit")
            if it and it.status is Status.DONE:
                tags.append("done")
            elif it and it.status is Status.DOING:
                tags.append("active")
            deps = [node[d] for d in (it.depends if it else []) if plan.has(d)]
            start = f"after {' '.join(deps)}" if deps else "0"
            dur = _gantt_duration(it.estimate_hours if it else None)
            meta = ", ".join([*tags, node[item_id], start, dur])
            # Em gantt o `:` separa nome de metadados — o nome tem de ser colon-free.
            label = _label(item_id, it.title if it else item_id).replace(":", " —")
            lines.append(f"    {label} :{meta}")
    lines.append("```")
    return "\n".join(lines)


def render_all(plan: Plan) -> str:
    return (
        "### Dependencies\n\n" + render_deps(plan)
        + "\n\n### Board\n\n" + render_board(plan)
        + "\n\n### Gantt (relative effort)\n\n" + render_gantt(plan) + "\n"
    )
