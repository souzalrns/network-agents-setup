"""doneproof CLI: check acceptance conditions by evidence, exit 0/1.

    doneproof check <root> [CONDITION ...] [--resolved STEP ...] [--json]

Exit 0 when nothing failed (unverifiable conditions do not fail), 1 otherwise.
``--resolved STEP`` marks a human gate as resolved (repeatable); without it,
``human_gate_resolved on <step>`` fails closed. ``--json`` prints the full
structured result instead of the human summary.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, evaluate, is_satisfied


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="doneproof", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"doneproof {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="Check conditions against evidence under <root>")
    c.add_argument("root", help="The run directory that `<path> exists` resolves against")
    c.add_argument("conditions", nargs="*", help="doneproof conditions, e.g. 'artifacts/r.md exists'")
    c.add_argument(
        "--resolved", action="append", default=[], metavar="STEP", help="Mark a human gate as resolved (repeatable)"
    )
    c.add_argument("--json", action="store_true", help="Print the full structured result")
    args = ap.parse_args(argv)

    resolved = set(args.resolved)
    result = evaluate(args.root, args.conditions, gate_resolved=lambda step: step in resolved)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in result["passed"]:
            print(f"ok   {item['kind']}: {item['target']}")
        for item in result["failed"]:
            print(f"FAIL {item['kind']}: {item['target']} ({item['reason']})")
        for cond in result["unverifiable"]:
            print(f"?    unverifiable: {cond}")
        print(
            f"doneproof: {'satisfied' if is_satisfied(result) else 'FAILED'} "
            f"({len(result['failed'])} failed, {len(result['unverifiable'])} unverifiable)"
        )
    return 0 if is_satisfied(result) else 1


if __name__ == "__main__":
    sys.exit(main())
