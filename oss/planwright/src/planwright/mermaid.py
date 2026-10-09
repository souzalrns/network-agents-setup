"""Render a plan as Mermaid diagrams — so a manager *sees* the plan.

Two views, both plain text that GitHub, VS Code and most Markdown viewers render
natively (zero dependencies, nothing to install):

- **deps**: a dependency flowchart (what blocks what), nodes coloured by status.
- **board**: a Kanban-style board (Done / Doing / Ready / Blocked), so the
  parallelism and the bottlenecks are visible at a glance.

Output is wrapped in ```mermaid fences so it can be pasted straight into a
Markdown document.
"""

from __future__ import annotations

from .graph import Graph
from .model import Plan, Status

# Status → Mermaid classDef style. Colours chosen to read in light and dark.
_CLASSDEFS = [
    "classDef done fill:#1a7f37,stroke:#0b5",
    "classDef doing fill:#9a6700,stroke:#7a5",
    "classDef blocked fill:#cf222e,stroke:#a11,color:#fff",
    "classDef ready fill:#0969da,stroke:#06c,color:#fff",
    "classDef todo fill:#6e7781,stroke:#555,color:#fff",
]


def _node_id(item_id: str) -> str:
    """Mermaid node ids must be identifier-safe; map anything else to '_'."""
    return "".join(c if c.isalnum() else "_" for c in item_id)


def _label(item_id: str, title: str, *, max_len: int = 40) -> str:
    t = title.strip()
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    # Escape double quotes for the Mermaid "..." label.
    t = t.replace('"', "'")
    return f"{item_id}: {t}"


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
    lines = ["```mermaid", "flowchart LR"]

    for it in plan:
        nid = _node_id(it.id)
        lines.append(f'  {nid}["{_label(it.id, it.title)}"]')
    lines.append("")
    for it in plan:
        nid = _node_id(it.id)
        for dep in it.depends:
            if plan.has(dep):
                lines.append(f"  {_node_id(dep)} --> {nid}")
    lines.append("")
    for cd in _CLASSDEFS:
        lines.append(f"  {cd}")
    for it in plan:
        cls = _status_class(graph, it.id, ready_ids)
        lines.append(f"  class {_node_id(it.id)} {cls}")
    lines.append("```")
    return "\n".join(lines)


def render_board(plan: Plan) -> str:
    """Kanban board: one subgraph per bucket (Done / Doing / Ready / Blocked)."""
    graph = Graph(plan)
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
                lines.append(f'    {_node_id(item_id)}["{_label(item_id, _title(plan, item_id))}"]')
        else:
            lines.append(f"    {key}_empty[ ]")
        lines.append("  end")
    lines.append("")
    for cd in _CLASSDEFS:
        lines.append(f"  {cd}")
    for item_id in done:
        lines.append(f"  class {_node_id(item_id)} done")
    for item_id in doing:
        lines.append(f"  class {_node_id(item_id)} doing")
    for item_id in ready:
        lines.append(f"  class {_node_id(item_id)} ready")
    for item_id in blocked:
        lines.append(f"  class {_node_id(item_id)} blocked")
    lines.append("```")
    return "\n".join(lines)


def _title(plan: Plan, item_id: str) -> str:
    it = plan.get(item_id)
    return it.title if it else item_id


def render_all(plan: Plan) -> str:
    return "### Dependencies\n\n" + render_deps(plan) + "\n\n### Board\n\n" + render_board(plan) + "\n"
