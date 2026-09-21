from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hitl
from .engine import PlanError, resume_run, run_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_runner", description="Lab Plan-Execute runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a plan.yaml")
    p_run.add_argument("plan", type=Path)
    p_run.add_argument("--mode", choices=["dry-run", "stub", "external"], default="stub")
    p_run.add_argument("--out", type=Path, default=None, help="Output run directory")
    p_run.add_argument(
        "--engine",
        choices=["native", "langgraph"],
        default="native",
        help="native = sequential plan_runner; langgraph = graph waves / LG when installed",
    )

    p_res = sub.add_parser("resume", help="Resume a paused run")
    p_res.add_argument("out", type=Path, help="Run directory with status.json")
    p_res.add_argument("--decision", default="approve", help="approve|reject|edit")
    p_res.add_argument("--payload-file", type=Path, default=None, help="Ficheiro JSON com payload para edit (opcional)")

    p_compile = sub.add_parser("compile-graph", help="Show LangGraph wave compilation for a plan")
    p_compile.add_argument("plan", type=Path)

    # S31: expoe session_search.py (B11/M1) -- ate agora so tinha o proprio
    # CLI standalone (`python -m plan_runner.session_search`), nunca ligado
    # ao resto do runner. Aditivo: reindexacao automatica se o indice ainda
    # nao existir (ja era o comportamento de search()).
    p_search = sub.add_parser("search", help="Search events.jsonl of a run (FTS5, B11/M1)")
    p_search.add_argument("out", type=Path, help="Run directory with events.jsonl")
    p_search.add_argument("query", help="FTS5 query syntax (matched against event payloads)")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "compile-graph":
            from .engine import load_plan
            from .langgraph_compile import compile_report

            plan = load_plan(args.plan)
            result = compile_report(plan)
        elif args.cmd == "search":
            from .session_search import search

            result = {"hits": search(args.out, args.query)}
        elif args.cmd == "run":
            if args.engine == "langgraph":
                from .langgraph_engine import run_plan_langgraph

                result = run_plan_langgraph(args.plan, mode=args.mode, out_dir=args.out)
            else:
                result = run_plan(args.plan, mode=args.mode, out_dir=args.out)
        else:
            st = None
            try:
                from .engine import load_status

                st = load_status(args.out)
            except Exception:
                pass

            # B1: tenta a decisao escrita pelo lado Node (hitl-decisions.jsonl)
            # primeiro; se nao houver, cai no --decision explicito da CLI
            # (nao-regressao: o uso actual continua a funcionar sem alteracao).
            hitl_decision = hitl.read_decision(args.out)
            decision = hitl_decision["response"] if hitl_decision else args.decision

            if st and st.get("engine", "").startswith("langgraph"):
                from .langgraph_engine import resume_plan_langgraph

                payload = None
                if args.payload_file:
                    if not args.payload_file.exists():
                        raise PlanError(f"payload file not found: {args.payload_file}")
                    payload = args.payload_file.read_text(encoding="utf-8-sig")
                result = resume_plan_langgraph(args.out, decision=decision, payload=payload)
            else:
                result = resume_run(args.out, decision=decision)
    except PlanError as e:
        print(f"error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"error: {e}")
        return 1
    except ImportError as e:
        print(f"error: {e}")
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
