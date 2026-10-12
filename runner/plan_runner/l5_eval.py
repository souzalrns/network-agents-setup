"""F0.7: golden set do L5 (docs/architecture/EXECUTION-PLAN.md §7, F0.7a/F0.7b).

Mede o retrieve REAL do L5 (tool `retrieve_knowledge` do agent-network-mcp →
`match_knowledge` → `knowledge_chunks`) contra um golden set versionado
(config/l5-golden-security.yaml). Mede se o excerto certo é devolvido, não se
o excerto está certo (validade: EXECUTION-PLAN §15.8).

    python -m plan_runner.l5_eval validate [--golden ...]   # offline: âncoras vs chunking real
    python -m plan_runner.l5_eval run [--golden ...] [--out report.json]   # F0.7b, MCP real

O `run` precisa de MCP_URL + MCP_API_KEY (as mesmas do McpKnowledge). Sem elas
falha logo, sem medir nada.

R-011 (P-19 mantida pelo maestro, 2026-10-07): o limiar do gate M1 é a regra de
regressão de todos os runs. `provenance_ok` = 1.0 e `source_hit@k` >= 0.8 (15 dos
18 casos do golden de security); abaixo disso o `run` sai com 1 e diz que métrica
falhou. O `chunk_hit` e o MRR continuam só registados (sem alvo, decisão da P-19). Pede `require_citations=False` ao retrieve para que
um hit sem fonte conte como falha de proveniência, em vez de desaparecer.
Python puro: o DeepEval/Ragas está bloqueado (S19).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from groundwright import Retrieve, anchor_errors, evaluate
from groundwright import load_golden as _validate_golden
from groundwright import regression_failures as _regression_failures

GOLDEN_DEFAULT = Path("config") / "l5-golden-security.yaml"
# P-19 (opção A): mínimos de proveniência e de fonte; a linha de base do F0.7b é 1.0 e 1.0.
MIN_PROVENANCE_OK = 1.0
MIN_SOURCE_HIT = 0.8
REPO_ROOT = Path(__file__).resolve().parents[2]

# Backend de recuperação PLUGGABLE por este seam (RE1 = B, 2026-10-10): uma função
# `(kb, query, k) -> hits`. `evaluate()` nunca fala com um MCP — recebe um `Retrieve`
# qualquer, por isso corre offline com qualquer retriever (ver os testes com
# retrievers falsos). `mcp_retrieve()` e so o default (o MCP do L5).
# Decisao e porque: docs/initiatives/RE1-RAG-EVAL-DECISION.md.
#
# DEVOLVIDO (flywheel, 5ª volta, RAG-EVAL-1): o motor desta porta de grounding vem do
# pacote `groundwright` (PyPI, extraído de `oss/groundwright`): `evaluate`,
# `regression_failures`, `anchor_errors` e a validação do golden. Este módulo fica só com
# a cola do runner: ler o YAML, o default `mcp_retrieve()`, o `_local_chunks` pelo nosso
# chunking e os limiares da P-19/R-011. NÃO é um avaliador de RAG genérico (RE1 = B).
__all__ = ["Retrieve", "anchor_errors", "evaluate", "load_golden", "mcp_retrieve", "regression_failures"]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def load_golden(path: Path) -> dict[str, Any]:
    """Lê o golden set (YAML) e valida-o com o groundwright. Lança ValueError com todos os erros."""
    return _validate_golden(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def regression_failures(summary: dict[str, Any]) -> list[str]:
    """R-011: o que falha no limiar da P-19. Lista vazia = o run passa."""
    return _regression_failures(summary, min_provenance_ok=MIN_PROVENANCE_OK, min_source_hit=MIN_SOURCE_HIT)


def _local_chunks(golden: dict[str, Any]) -> list[dict[str, Any]]:
    from .chunking import chunk_markdown

    sources = {golden["source"]} | {c["source"] for c in golden["cases"] if c.get("source")}
    out: list[dict[str, Any]] = []
    for rel in sorted(sources):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        out += chunk_markdown(text, source_path=rel, agent_id=golden["kb"], kb=golden["kb"])
    return out


def mcp_retrieve() -> Retrieve:
    from .knowledge import retrieve_knowledge
    from .mcp_knowledge import McpKnowledge

    backend = McpKnowledge()

    def _r(kb: str, query: str, k: int) -> list[dict[str, Any]]:
        return retrieve_knowledge(kb, query, top_k=k, backend=backend, require_citations=False)
    return _r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m plan_runner.l5_eval", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in (("validate", "Valida o golden set contra o chunking real (offline)"),
                        ("run", "Mede o golden set contra o MCP real (F0.7b; MCP_URL + MCP_API_KEY)")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--golden", type=Path, default=REPO_ROOT / GOLDEN_DEFAULT)
        if name == "run":
            p.add_argument("--out", type=Path, help="Grava o relatório completo em JSON")
    args = ap.parse_args(argv)

    golden = load_golden(args.golden)
    if args.cmd == "validate":
        errors = anchor_errors(golden, _local_chunks(golden))
        for e in errors:
            print(f"ERRO {e}")
        print(f"{len(golden['cases'])} casos; {len(errors)} erros")
        return 1 if errors else 0

    report = evaluate(golden, mcp_retrieve())
    for row in report["cases"]:
        mark = "ok " if row["chunk_rank"] else "-- "
        print(f"{mark}{row['id']} chunk_rank={row['chunk_rank']} source_rank={row['source_rank']} "
              f"hits={row['hits']}{' (stale)' if row['stale'] else ''}")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    failures = regression_failures(report["summary"])
    report["gate"] = {"min_provenance_ok": MIN_PROVENANCE_OK, "min_source_hit": MIN_SOURCE_HIT,
                      "passed": not failures, "failures": failures}
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in failures:
        print(f"REGRESSAO {f}")
    print("gate P-19: " + ("passou" if not failures else f"FALHOU ({len(failures)})"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
