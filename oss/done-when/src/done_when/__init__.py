"""done-when: accept a task only when its done-ness is proven by evidence.

An agent (or a plan) declares *done_when* conditions in plain strings. This
package classifies each one as **passed**, **failed** or **unverifiable** by
checking real evidence — never the agent's own word that it finished.

Two evidence kinds are understood (the only two that verify without
interpreting free text):

- ``<path> exists`` — the file exists under the run's root directory. The path
  is resolved and must stay inside the root (no ``../`` escape).
- ``human_gate_resolved on <step>`` — a human approval for ``<step>`` was
  recorded. "Was it recorded?" is answered by a caller-supplied predicate
  (``gate_resolved``), so this package never depends on any particular event
  store, queue or database.

A condition in any other shape is **not failed** — it is reported as
``unverifiable`` so the caller can decide. Refusing to fail on what you cannot
check by evidence is as important as refusing to pass on an agent's say-so.

    from pathlib import Path
    from done_when import evaluate, is_satisfied

    result = evaluate(Path("runs/42"), ["artifacts/report.md exists"])
    assert is_satisfied(result)

The return value is a plain JSON-serializable dict so it drops straight into a
log or an event. ``is_satisfied`` is true iff there are no failures;
unverifiable conditions do not make a run fail.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

__all__ = ["GateResolved", "__version__", "evaluate", "is_satisfied"]

# "Was the human gate on <step> resolved?" — the one thing this package cannot
# check from the filesystem. The caller supplies it (bound to its own event log,
# queue, DB, …). Default: nothing is resolved, so gate conditions fail closed.
GateResolved = Callable[[str], bool]

_EXISTS = re.compile(r"^(?P<path>\S+)\s+exists$")
_GATE = re.compile(r"^human_gate_resolved\s+on\s+(?P<step>\S+)$")


def evaluate(
    root: str | Path,
    conditions: list[str],
    gate_resolved: GateResolved | None = None,
) -> dict[str, list[Any]]:
    """Classify each condition into ``passed``, ``failed`` or ``unverifiable``.

    ``root`` is the run directory that ``<path> exists`` conditions resolve
    against; a path that escapes it fails. ``gate_resolved(step) -> bool``
    answers ``human_gate_resolved on <step>``; when omitted, no gate is
    considered resolved (fail-closed).

    Returns ``{"passed": [...], "failed": [...], "unverifiable": [...]}``.
    ``passed`` and ``failed`` items are ``{"kind", "target"}``
    (kind = ``file_exists`` | ``gate_resolved``); ``failed`` items also carry
    ``{"condition", "reason"}``. ``unverifiable`` keeps the original strings.
    Passed items omit the original text so a reader scanning for the literal
    ``human_gate_resolved`` does not confuse an accepted condition with the
    real approval event.
    """
    resolved = gate_resolved if gate_resolved is not None else (lambda _step: False)
    result: dict[str, list[Any]] = {"passed": [], "failed": [], "unverifiable": []}
    base = Path(root).resolve()
    for raw in conditions:
        cond = str(raw).strip()
        m = _EXISTS.match(cond)
        if m:
            item = {"kind": "file_exists", "target": m.group("path")}
            target = (base / m.group("path")).resolve()
            if not target.is_relative_to(base):
                result["failed"].append({**item, "condition": cond, "reason": "path outside the run directory"})
            elif target.is_file():
                result["passed"].append(item)
            else:
                result["failed"].append({**item, "condition": cond, "reason": "file missing"})
            continue
        m = _GATE.match(cond)
        if m:
            item = {"kind": "gate_resolved", "target": m.group("step")}
            if resolved(m.group("step")):
                result["passed"].append(item)
            else:
                result["failed"].append({**item, "condition": cond, "reason": "gate not resolved"})
            continue
        result["unverifiable"].append(cond)
    return result


def is_satisfied(result: dict[str, list[Any]]) -> bool:
    """True iff nothing failed. Unverifiable conditions do not fail a run."""
    return not result["failed"]
