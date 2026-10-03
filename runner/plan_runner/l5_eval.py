"""F0.7: golden set do L5 (docs/architecture/EXECUTION-PLAN.md §7, F0.7a/F0.7b).

Mede o retrieve REAL do L5 (tool `retrieve_knowledge` do agent-network-mcp →
`match_knowledge` → `knowledge_chunks`) contra um golden set versionado
(config/l5-golden-security.yaml). Mede se o excerto certo é devolvido, não se
o excerto está certo (validade: EXECUTION-PLAN §15.8).

    python -m plan_runner.l5_eval validate [--golden ...]   # offline: âncoras vs chunking real
    python -m plan_runner.l5_eval run [--golden ...] [--out report.json]   # F0.7b, MCP real

O `run` precisa de MCP_URL + MCP_API_KEY (as mesmas do McpKnowledge). Sem elas
falha logo, sem medir nada. Pede `require_citations=False` ao retrieve para que
um hit sem fonte conte como falha de proveniência, em vez de desaparecer.
Python puro: o DeepEval/Ragas está bloqueado (S19).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

GOLDEN_DEFAULT = Path("config") / "l5-golden-security.yaml"
REPO_ROOT = Path(__file__).resolve().parents[2]

Retrieve = Callable[[str, str, int], list[dict[str, Any]]]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def load_golden(path: Path) -> dict[str, Any]:
    """Lê e valida o golden set. Lança ValueError com todos os erros."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    for key in ("kb", "source"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"`{key}` em falta")
    if not isinstance(data.get("k"), int) or data["k"] < 1:
        errors.append("`k` tem de ser inteiro >= 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("`cases` vazio")
        cases = []
    seen: set[str] = set()
    for i, case in enumerate(cases):
        cid = case.get("id") if isinstance(case, dict) else None
        if not cid or cid in seen:
            errors.append(f"caso {i}: `id` em falta ou repetido")
        seen.add(cid)
        for key in ("question", "anchor"):
            if not isinstance(case, dict) or not str(case.get(key) or "").strip():
                errors.append(f"{cid or i}: `{key}` em falta")
    if errors:
        raise ValueError("golden set inválido: " + "; ".join(errors))
    return data


def anchor_errors(golden: dict[str, Any], chunks: list[dict[str, Any]]) -> list[str]:
    """Cada âncora tem de cair em exactamente 1 chunk da fonte esperada (chunking real)."""
    errors = []
    for case in golden["cases"]:
        source = case.get("source", golden["source"])
        n = sum(1 for c in chunks
                if c["citation"]["source"] == source and _norm(case["anchor"]) in _norm(c["content"]))
        if n != 1:
            errors.append(f"{case['id']}: âncora {case['anchor']!r} em {n} chunks de {source} (esperado 1)")
    return errors


def evaluate(golden: dict[str, Any], retrieve: Retrieve) -> dict[str, Any]:
    kb, k = golden["kb"], golden["k"]
    rows = []
    for case in golden["cases"]:
        source = case.get("source", golden["source"])
        hits = (retrieve(kb, case["question"], k) or [])[:k]
        sources = [((h.get("citation") or {}).get("source") or "") for h in hits]
        src_rank = next((i for i, s in enumerate(sources, 1) if s == source), None)
        chunk_rank = next((i for i, (s, h) in enumerate(zip(sources, hits), 1)
                           if s == source and _norm(case["anchor"]) in _norm(h.get("content", ""))), None)
        rows.append({
            "id": case["id"], "question": case["question"], "hits": len(hits),
            "source_rank": src_rank, "chunk_rank": chunk_rank,
            "provenance_ok": bool(hits) and all(sources),
            "retrieved_sources": sources, "stale": bool(case.get("stale")),
        })
    n = len(rows)

    def at(r: int) -> float:
        return round(sum(1 for x in rows if x["chunk_rank"] and x["chunk_rank"] <= r) / n, 3)

    with_hits = [x for x in rows if x["hits"]]
    summary = {
        "kb": kb, "source": golden["source"], "k": k, "cases": n,
        "chunk_hit@1": at(1), "chunk_hit@3": at(min(3, k)), f"chunk_hit@{k}": at(k),
        f"source_hit@{k}": round(sum(1 for x in rows if x["source_rank"]) / n, 3),
        "mrr_chunk": round(sum(1 / x["chunk_rank"] for x in rows if x["chunk_rank"]) / n, 3),
        "no_hits": n - len(with_hits),
        "provenance_ok": round(sum(1 for x in with_hits if x["provenance_ok"]) / len(with_hits), 3) if with_hits else None,
    }
    return {"summary": summary, "cases": rows}


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
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
