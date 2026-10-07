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
        "--worker",
        choices=["none", "gemini"],
        default=None,
        help="Mode external: executa cada passo com este worker em vez de parar em waiting_external (engine native)",
    )
    p_run.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Tecto de tokens do run (worker; tem prioridade sobre budget.max_tokens do plano). Ver docs/ops/BUDGET.md",
    )
    p_run.add_argument(
        "--max-cost-usd",
        type=float,
        default=None,
        help="D6: tecto de custo do run em USD (precos em config/model-prices.yaml; prioridade sobre budget.max_cost_usd)",
    )
    p_run.add_argument(
        "--engine",
        choices=["native", "langgraph"],
        default="native",
        help="native = sequential plan_runner; langgraph = graph waves / LG when installed",
    )

    p_res = sub.add_parser("resume", help="Resume a paused run")
    p_res.add_argument("out", type=Path, help="Run directory with status.json")
    p_res.add_argument("--decision", default=None,
                       help="approve|reject|edit (omissao: approve; obrigatorio na aprovacao de uma tool act)")
    p_res.add_argument("--payload-file", type=Path, default=None, help="Ficheiro JSON com payload para edit (opcional)")
    p_res.add_argument(
        "--worker",
        choices=["none", "gemini"],
        default=None,
        help="Worker do modo external (omissao: o do run; engine native)",
    )
    p_res.add_argument("--max-tokens", type=int, default=None, help="Novo tecto de tokens (retoma um run em paused_budget)")
    p_res.add_argument("--max-cost-usd", type=float, default=None, help="D6: novo tecto de custo em USD (retoma um run em paused_budget)")

    p_compile = sub.add_parser("compile-graph", help="Show LangGraph wave compilation for a plan")
    p_compile.add_argument("plan", type=Path)

    # S31: expoe session_search.py (B11/M1) -- ate agora so tinha o proprio
    # CLI standalone (`python -m plan_runner.session_search`), nunca ligado
    # ao resto do runner. Aditivo: reindexacao automatica se o indice ainda
    # nao existir (ja era o comportamento de search()).
    p_search = sub.add_parser("search", help="Search events.jsonl of a run (FTS5, B11/M1)")
    p_search.add_argument("out", type=Path, help="Run directory with events.jsonl")
    p_search.add_argument("query", help="FTS5 query syntax (matched against event payloads)")

    # D2: router hierarquico hibrido (plan_runner/router.py, docs/ops/ROUTER.md)
    p_route = sub.add_parser("route", help="Escolhe area + agente/plano para um pedido (e opcionalmente executa)")
    p_route.add_argument("request", help="Pedido em linguagem natural (com --clarify-from: a resposta a pergunta)")
    p_route.add_argument(
        "--clarify-from", type=Path, default=None,
        help="W-002: JSON de um `route` anterior que acabou em clarify; o pedido passa a ser a resposta",
    )
    p_route.add_argument("--execute", action="store_true", help="Corre a decisao no plan_runner (mode external + worker)")
    p_route.add_argument("--out", type=Path, default=None, help="Directorio do run (dentro de pilots/; omissao: pilots/run-router-<id>)")
    p_route.add_argument("--worker", choices=["none", "gemini"], default="gemini", help="Worker dos passos executados")
    p_route.add_argument("--embeddings", action="store_true", help="Embeddings Gemini quando nenhuma keyword casa")
    p_route.add_argument("--log", type=Path, default=None, help="jsonl das decisoes (omissao: pilots/router-decisions.jsonl)")
    p_route.add_argument("--no-council", action="store_true", help="Nao escala pedidos estruturais para conselho")

    # Bloco C: conselho interno (plan_runner/council_session.py, docs/ops/COUNCIL.md)
    sub.add_parser("council", help="Conselho interno: run|decide|resume|status|cost|validate (ver `council -h`)",
                   add_help=False)

    if argv is None:
        import sys

        argv = sys.argv[1:]
    if argv and argv[0] == "council":
        from .council_session import main as council_main

        return council_main(argv[1:])

    args = parser.parse_args(argv)
    try:
        if args.cmd == "route":
            return _route(args)
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
                # W-005: worker inline e tectos tambem no langgraph (paridade com o native)
                from .langgraph_engine import run_plan_langgraph

                result = run_plan_langgraph(
                    args.plan, mode=args.mode, out_dir=args.out, worker=args.worker,
                    max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd,
                )
            else:
                result = run_plan(
                    args.plan, mode=args.mode, out_dir=args.out, worker=args.worker,
                    max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd,
                )
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
            approval = (st or {}).get("tool_approval")
            if approval:
                # AU-20: so conta a decisao DESTE pedido (por id), nunca a ultima do ficheiro, e
                # sem ela o --decision tem de ser explicito: aprovar uma tool act nunca e o default.
                node = next((d for d in reversed(hitl._read_jsonl(args.out / hitl.DECISIONS_FILE))
                             if d.get("id") == approval.get("request_id")), None)
                decision = node["response"] if node else args.decision
                if decision is None:
                    raise PlanError(
                        f"aprovacao de tool pendente ({approval.get('request_id')}: "
                        f"{', '.join(approval.get('tools') or [])}): passa --decision approve|reject"
                    )
            else:
                hitl_decision = hitl.read_decision(args.out)
                decision = hitl_decision["response"] if hitl_decision else (args.decision or "approve")

            if st and st.get("engine", "").startswith("langgraph"):
                from .langgraph_engine import resume_plan_langgraph

                payload = None
                if args.payload_file:
                    if not args.payload_file.exists():
                        raise PlanError(f"payload file not found: {args.payload_file}")
                    payload = args.payload_file.read_text(encoding="utf-8-sig")
                result = resume_plan_langgraph(
                    args.out, decision=decision, payload=payload, worker=args.worker,
                    max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd,
                )
            else:
                result = resume_run(
                    args.out, decision=decision, worker=args.worker,
                    max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd,
                )
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


def _route(args: argparse.Namespace) -> int:
    from uuid import uuid4

    from .router import REPO_ROOT, Router, log_decision

    embed = None
    if args.embeddings:
        from . import external_worker as ew
        from .embedder import EmbedderError, embed_text

        def embed(text: str) -> list[float]:
            try:
                return embed_text(text)
            except EmbedderError as e:
                raise ew.WorkerError(str(e)) from e

    router = Router(embed=embed, councils=not args.no_council)
    if args.clarify_from is not None:
        try:
            previous = json.loads(args.clarify_from.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: --clarify-from: {e}")
            return 1
        decision = router.clarify(previous, args.request)
    else:
        decision = router.route(args.request)
    log_decision(decision, args.log or REPO_ROOT / "pilots" / "router-decisions.jsonl")
    if args.execute and decision.outcome in ("agent", "plan", "hitl", "council"):
        out = args.out or REPO_ROOT / "pilots" / f"run-router-{uuid4().hex[:8]}"
        try:
            result = router.execute(decision, out_dir=out, worker=args.worker)
        except PlanError as e:
            print(f"error: {e}")
            return 1
    else:
        result = {"executed": False, "decision": decision.to_dict()}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if decision.outcome == "error" else 0
