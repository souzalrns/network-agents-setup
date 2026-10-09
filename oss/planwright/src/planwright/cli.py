"""Command-line interface: ``planwright <command> [PLAN.md]``.

Commands
--------
- ``validate``  check the plan; exit non-zero on errors (``--strict`` also on warnings)
- ``graph``     the full schedule: ready, parallel layers, blocked, critical path
- ``next``      just the ids ready to start now (one per line)
- ``status``    a one-line status-count summary

Every command takes ``--json`` for machine output and an optional path
(default: ``PLAN.md`` in the current directory, or ``$PLANWRIGHT_PLAN``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .parse import ParseError, parse_plan
from .report import graph_json, render_graph, render_next, render_validation, status_counts
from .validate import validate_text

DEFAULT_PLAN = os.environ.get("PLANWRIGHT_PLAN", "PLAN.md")


def _load(path: str):
    return parse_plan(path)


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        with open(args.path, encoding="utf-8") as fh:
            report = validate_text(fh.read(), source=args.path)
    except FileNotFoundError:
        print(f"planwright: no such plan file: {args.path}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok(strict=args.strict),
                    "errors": [f.__dict__ for f in report.errors],
                    "warnings": [f.__dict__ for f in report.warnings],
                },
                indent=2,
            )
        )
    else:
        print(render_validation(report))
    return 0 if report.ok(strict=args.strict) else 1


def _cmd_graph(args: argparse.Namespace) -> int:
    try:
        plan = _load(args.path)
    except (FileNotFoundError, ParseError) as exc:
        print(f"planwright: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(graph_json(plan), indent=2))
    else:
        print(render_graph(plan))
    return 0


def _cmd_next(args: argparse.Namespace) -> int:
    try:
        plan = _load(args.path)
    except (FileNotFoundError, ParseError) as exc:
        print(f"planwright: {exc}", file=sys.stderr)
        return 2
    if args.json:
        from .graph import Graph

        print(json.dumps([it.id for it in Graph(plan).ready()]))
    else:
        out = render_next(plan)
        if out:
            print(out)
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    try:
        plan = _load(args.path)
    except (FileNotFoundError, ParseError) as exc:
        print(f"planwright: {exc}", file=sys.stderr)
        return 2
    counts = status_counts(plan)
    if args.json:
        print(json.dumps({"items": len(plan), "status": counts}))
    else:
        print(
            f"{len(plan)} items — todo {counts['todo']}, doing {counts['doing']}, "
            f"blocked {counts['blocked']}, done {counts['done']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="planwright", description="A maker of plans.")
    parser.add_argument("--version", action="version", version=f"planwright {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("path", nargs="?", default=DEFAULT_PLAN, help=f"plan file (default: {DEFAULT_PLAN})")
        p.add_argument("--json", action="store_true", help="machine-readable output")

    p_val = sub.add_parser("validate", help="check the plan is sound and disciplined")
    add_common(p_val)
    p_val.add_argument("--strict", action="store_true", help="treat governance warnings as failures")
    p_val.set_defaults(func=_cmd_validate)

    p_graph = sub.add_parser("graph", help="ready, parallel layers, blocked, critical path")
    add_common(p_graph)
    p_graph.set_defaults(func=_cmd_graph)

    p_next = sub.add_parser("next", help="ids ready to start now")
    add_common(p_next)
    p_next.set_defaults(func=_cmd_next)

    p_status = sub.add_parser("status", help="one-line status summary")
    add_common(p_status)
    p_status.set_defaults(func=_cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
