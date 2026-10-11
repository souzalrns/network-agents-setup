"""groundwright CLI: validate a golden set against a chunking (offline), or print a
report from a precomputed cases/summary JSON.

    groundwright validate <golden.json> <chunks.json>
        # each anchor must fall in exactly one chunk of its source; exit 1 on errors.
    groundwright gate <report.json> [--min-provenance-ok 1.0] [--min-source-hit 0.8]
        # <report.json> is the {"summary": ...} produced by evaluate(); exit 1 if the
        # regression gate fails.

Retrieval needs a live retriever, so it is driven from Python (``evaluate``), not the
CLI. The CLI covers the two offline checks: golden↔chunking anchoring and the gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, anchor_errors, load_golden, regression_failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="groundwright", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"groundwright {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Check each anchor falls in exactly one chunk of its source")
    v.add_argument("golden")
    v.add_argument("chunks")

    g = sub.add_parser("gate", help="Apply the regression gate to an evaluate() report")
    g.add_argument("report")
    g.add_argument("--min-provenance-ok", type=float, default=1.0)
    g.add_argument("--min-source-hit", type=float, default=0.8)

    args = ap.parse_args(argv)

    if args.cmd == "validate":
        golden = load_golden(json.loads(Path(args.golden).read_text(encoding="utf-8")))
        chunks = json.loads(Path(args.chunks).read_text(encoding="utf-8"))
        errors = anchor_errors(golden, chunks)
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print(f"{len(golden['cases'])} cases; {len(errors)} errors")
        return 1 if errors else 0

    if args.cmd == "gate":
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        summary = report.get("summary", report)
        failures = regression_failures(
            summary, min_provenance_ok=args.min_provenance_ok, min_source_hit=args.min_source_hit
        )
        for f in failures:
            print(f"REGRESSION {f}", file=sys.stderr)
        print("gate: " + ("passed" if not failures else f"FAILED ({len(failures)})"))
        return 1 if failures else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
