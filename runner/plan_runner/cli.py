from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import PlanError, resume_run, run_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_runner", description="Lab Plan-Execute runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a plan.yaml")
    p_run.add_argument("plan", type=Path)
    p_run.add_argument("--mode", choices=["dry-run", "stub", "external"], default="stub")
    p_run.add_argument("--out", type=Path, default=None, help="Output run directory")

    p_res = sub.add_parser("resume", help="Resume a paused run")
    p_res.add_argument("out", type=Path, help="Run directory with status.json")
    p_res.add_argument("--decision", default="approve", help="approve|reject|edit")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "run":
            result = run_plan(args.plan, mode=args.mode, out_dir=args.out)
        else:
            result = resume_run(args.out, decision=args.decision)
    except PlanError as e:
        print(f"error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"error: {e}")
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
