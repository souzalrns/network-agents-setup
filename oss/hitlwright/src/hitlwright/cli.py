"""hitlwright CLI: write a request, record a decision, inspect what's pending.

hitlwright request <run_dir> --step STEP [--action A] [--allow approve --allow reject]
                             [--title T] [--run-id R] [--plan-id P]
hitlwright decide  <run_dir> <request_id> --response approve|reject|edit
                             [--by WHO] [--comment C]
hitlwright pending <run_dir>        # the latest request still awaiting a human (exit 0),
                                    # or nothing pending (exit 1)
hitlwright decision <run_dir>       # the latest decision as JSON (exit 0), or none (exit 1)
"""

from __future__ import annotations

import argparse
import json
import sys

from . import (
    __version__,
    pending_request,
    read_decision,
    write_decision,
    write_request,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hitlwright", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"hitlwright {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("request", help="Write a HITL request")
    r.add_argument("run_dir")
    r.add_argument("--step", required=True)
    r.add_argument("--action")
    r.add_argument("--allow", action="append", metavar="DECISION")
    r.add_argument("--title")
    r.add_argument("--run-id")
    r.add_argument("--plan-id")

    d = sub.add_parser("decide", help="Record a decision for a request")
    d.add_argument("run_dir")
    d.add_argument("request_id")
    d.add_argument("--response", required=True, choices=sorted(["approve", "reject", "edit"]))
    d.add_argument("--by", default="cli")
    d.add_argument("--comment")

    p = sub.add_parser("pending", help="Show the latest request awaiting a human")
    p.add_argument("run_dir")

    s = sub.add_parser("decision", help="Show the latest decision")
    s.add_argument("run_dir")

    args = ap.parse_args(argv)

    if args.cmd == "request":
        rid = write_request(
            args.run_dir,
            step_id=args.step,
            action=args.action,
            allow=args.allow,
            title=args.title,
            run_id=args.run_id,
            plan_id=args.plan_id,
        )
        print(rid)
        return 0
    if args.cmd == "decide":
        rec = write_decision(
            args.run_dir, args.request_id, response=args.response, responder_id=args.by, comment=args.comment
        )
        print(json.dumps(rec, ensure_ascii=False))
        return 0
    if args.cmd == "pending":
        req = pending_request(args.run_dir)
        if req is None:
            print("nothing pending", file=sys.stderr)
            return 1
        print(json.dumps(req, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "decision":
        dec = read_decision(args.run_dir)
        if dec is None:
            print("no decision yet", file=sys.stderr)
            return 1
        print(json.dumps(dec, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
