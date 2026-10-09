"""Validate a plan.

Two severities:

- **error**: the plan is not a sound schedule — a parse failure, a duplicate id,
  a dependency that names no item, or a cycle. The graph cannot be trusted.
- **warning (governance)**: the plan is schedulable but undisciplined — work is
  marked started without an estimate, or a done item still depends on unfinished
  work. These are the rules that keep a plan honest; a team can choose to treat
  them as hard failures (``--strict``) so nothing starts undefined.

The hook (see ``scripts/planwright_hook.py``) calls :func:`validate_plan` and
blocks on errors, and on warnings when configured strict.
"""

from __future__ import annotations

from dataclasses import dataclass

from .graph import Graph
from .model import Plan
from .parse import ParseError, parse_text


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str
    message: str
    item_id: str = ""

    def __str__(self) -> str:
        where = f" [{self.item_id}]" if self.item_id else ""
        return f"{self.level.upper()} {self.code}{where}: {self.message}"


@dataclass
class Report:
    findings: list[Finding]

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]

    def ok(self, *, strict: bool = False) -> bool:
        if self.errors:
            return False
        return not (strict and self.warnings)


def _duplicate_ids(plan: Plan) -> list[str]:
    seen: set[str] = set()
    dups: list[str] = []
    for it in plan:
        if it.id in seen and it.id not in dups:
            dups.append(it.id)
        seen.add(it.id)
    return dups


def validate_plan(plan: Plan) -> Report:
    findings: list[Finding] = []
    graph = Graph(plan)

    # -- errors: the schedule is unsound --------------------------------
    for dup in _duplicate_ids(plan):
        findings.append(Finding("error", "duplicate-id", f"id {dup!r} appears more than once", dup))

    for item_id, dep in graph.dangling_dependencies():
        findings.append(Finding("error", "dangling-dependency", f"depends on {dep!r}, which is not an item", item_id))

    for item_id in graph.self_dependencies():
        findings.append(Finding("error", "self-dependency", "depends on itself", item_id))

    for cycle in graph.find_cycles():
        findings.append(Finding("error", "cycle", f"dependency cycle: {cycle}", cycle.nodes[0]))

    # -- warnings: the plan is sloppy but schedulable -------------------
    for it in plan:
        if it.status.started and not it.has_estimate:
            findings.append(
                Finding(
                    "warning",
                    "started-without-estimate",
                    f"status is {it.status.value!r} but has no estimate; size the work before starting it",
                    it.id,
                )
            )
        if it.status.completed:
            for dep in it.depends:
                d = plan.get(dep)
                if d is not None and not d.status.completed:
                    findings.append(
                        Finding(
                            "warning",
                            "done-before-dependency",
                            f"is done but depends on {dep!r}, which is not done",
                            it.id,
                        )
                    )
    return Report(findings)


def validate_text(text: str, *, source: str = "<text>") -> Report:
    """Validate from raw text, turning a parse failure into an error Finding."""
    try:
        plan = parse_text(text, source=source)
    except ParseError as exc:
        return Report([Finding("error", "parse", str(exc))])
    return validate_plan(plan)
