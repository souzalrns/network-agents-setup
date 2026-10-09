#!/usr/bin/env python3
"""Claude Code hook: keep the plan honest.

Wired as a PostToolUse hook on Edit|Write (see ``hooks/hooks.json``). After the
agent edits a plan file, this validates it and, on an error (a cycle, a
dangling dependency, a duplicate id), blocks with exit code 2 so the agent sees
the problem and fixes it before moving on — the discipline a stateless prompt
never enforces on its own.

A file is treated as a plan when its name is ``PLAN.md`` or ends in
``.plan.md`` (override with ``$PLANWRIGHT_PLAN_GLOB``, a comma-separated list of
fnmatch patterns). Set ``$PLANWRIGHT_STRICT=1`` to also block on governance
warnings (work started without an estimate, etc.).

Input: hook JSON on stdin (``tool_input.file_path``). Output: on a problem,
a human reason on stderr + exit 2; otherwise exit 0 (silent).

Standard library only, so it runs wherever Python does — even if the
``planwright`` package is not installed, by importing from the bundled ``src``.
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys
from pathlib import Path

# Make the bundled engine importable without requiring `pip install planwright`.
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from planwright.validate import validate_text
except Exception as exc:  # pragma: no cover - defensive: never break the session
    print(f"planwright hook: could not load engine ({exc}); skipping", file=sys.stderr)
    sys.exit(0)

DEFAULT_GLOBS = ["PLAN.md", "*.plan.md"]


def _globs() -> list[str]:
    raw = os.environ.get("PLANWRIGHT_PLAN_GLOB", "")
    patterns = [p.strip() for p in raw.split(",") if p.strip()]
    return patterns or DEFAULT_GLOBS


def _is_plan_file(path: str) -> bool:
    name = os.path.basename(path)
    return any(fnmatch.fnmatch(name, pat) for pat in _globs())


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not our business; let the session continue

    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path or not _is_plan_file(path):
        return 0

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return 0  # file gone or unreadable: nothing to validate

    strict = os.environ.get("PLANWRIGHT_STRICT", "") not in ("", "0", "false", "False")
    report = validate_text(text, source=path)
    if report.ok(strict=strict):
        return 0

    lines = [f"planwright: {os.path.basename(path)} is not a sound plan — fix before continuing:"]
    lines += [f"  - {f}" for f in report.errors]
    if strict:
        lines += [f"  - {f}" for f in report.warnings]
    print("\n".join(lines), file=sys.stderr)
    return 2  # PostToolUse: feeds stderr back to the agent as a blocking reason


if __name__ == "__main__":
    sys.exit(main())
