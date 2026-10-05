"""F5: resumo de evidência de um run real de ponta a ponta (sem segredos, sem conteúdo).

Lê só o directório de um run do plan_runner e escreve um resumo em Markdown (ou JSON) para
colar em `docs/ops/F5-E2E-RUN.md`. Não imprime prompts, conteúdo de artefactos nem variáveis
de ambiente: só estado, contagens, tokens, custo, fontes citadas, nomes e hashes.

Critérios do veredicto (todos obrigatórios para PASSOU):
1. o run chegou ao fim ou parou no gate humano (`done` / `paused_human_gate`);
2. o L5 entrou: pelo menos 1 `knowledge_context_injected` com `hit_count` > 0;
3. o modelo correu: pelo menos 1 linha no `token_usage.jsonl` com tokens;
4. sem `worker_error` nem `knowledge_context_failed`;
5. pelo menos 1 artefacto escrito.

Uso (a partir da raiz do repo):

    python scripts/f5_evidence.py pilots/f5-run [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

FINAL_STATES = ("done", "paused_human_gate")
SOURCE_RE = re.compile(r"\[Fonte:\s*([^\]@|]+)")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def collect(run_dir: Path) -> dict[str, Any]:
    status = {}
    if (run_dir / "status.json").is_file():
        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    events = _jsonl(run_dir / "events.jsonl")
    ledger = _jsonl(run_dir / "token_usage.jsonl")
    by_type = Counter(e.get("type") for e in events)
    knowledge = [
        {
            "step_id": e["payload"].get("step_id"),
            "kb": e["payload"].get("kb"),
            "hit_count": e["payload"].get("hit_count"),
        }
        for e in events
        if e.get("type") == "knowledge_context_injected" and isinstance(e.get("payload"), dict)
    ]
    sources: set[str] = set()
    for ctx in sorted(run_dir.glob("pending_steps/*/knowledge_context.md")):
        sources.update(m.strip() for m in SOURCE_RE.findall(ctx.read_text(encoding="utf-8")))
    tokens = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "tokens_total": 0}
    models: Counter[str] = Counter()
    for row in ledger:
        tokens["calls"] += 1
        for key in ("tokens_in", "tokens_out", "tokens_total"):
            value = row.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                tokens[key] += value
        models[str(row.get("model_version") or row.get("model") or "?")] += 1
    artifacts = [
        {
            "path": p.relative_to(run_dir).as_posix(),
            "bytes": p.stat().st_size,
            "sha256_12": hashlib.sha256(p.read_bytes()).hexdigest()[:12],
        }
        for p in sorted((run_dir / "artifacts").rglob("*"))
        if p.is_file()
    ]
    checks = {
        "estado_final": status.get("state") in FINAL_STATES,
        "l5_injectado": any((k.get("hit_count") or 0) > 0 for k in knowledge),
        "modelo_correu": tokens["calls"] > 0 and tokens["tokens_total"] > 0,
        "sem_erros": by_type.get("worker_error", 0) == 0
        and by_type.get("knowledge_context_failed", 0) == 0,
        "artefactos": bool(artifacts),
    }
    return {
        "run_id": next((e.get("run_id") for e in events if e.get("run_id")), None),
        "plan_id": status.get("plan_id"),
        "mode": status.get("mode"),
        "state": status.get("state"),
        "completed": status.get("completed") or [],
        "events": dict(sorted(by_type.items(), key=lambda kv: str(kv[0]))),
        "knowledge": knowledge,
        "sources_cited": sorted(sources),
        "tokens": tokens,
        "models": dict(models),
        "artifacts": artifacts,
        "checks": checks,
        "verdict": "PASSOU" if all(checks.values()) else "INCOMPLETO",
    }


def to_markdown(ev: dict[str, Any]) -> str:
    lines = [
        f"**Veredicto: {ev['verdict']}**",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| run_id / plano | `{ev['run_id']}` / `{ev['plan_id']}` |",
        f"| modo / estado | `{ev['mode']}` / `{ev['state']}` |",
        f"| passos concluídos | {', '.join(ev['completed']) or '—'} |",
        "| L5 (knowledge) | "
        + (
            ", ".join(
                f"{k['step_id']}: kb={k['kb']}, hits={k['hit_count']}" for k in ev["knowledge"]
            )
            or "nenhum"
        )
        + " |",
        f"| fontes citadas | {', '.join(f'`{s}`' for s in ev['sources_cited']) or '—'} |",
        f"| chamadas ao modelo | {ev['tokens']['calls']} ({', '.join(f'{m} ×{n}' for m, n in ev['models'].items()) or '—'}) |",
        f"| tokens in / out / total | {ev['tokens']['tokens_in']} / {ev['tokens']['tokens_out']} / {ev['tokens']['tokens_total']} |",
        "| artefactos | "
        + (
            ", ".join(f"`{a['path']}` ({a['bytes']} B, {a['sha256_12']})" for a in ev["artifacts"])
            or "—"
        )
        + " |",
        "",
        "| Critério | OK? |",
        "|---|---|",
        *(f"| {name} | {'sim' if ok else '**não**'} |" for name, ok in ev["checks"].items()),
        "",
        "Eventos: " + ", ".join(f"{k} ×{v}" for k, v in ev["events"].items()),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resumo de evidência de um run (F5).")
    parser.add_argument("run_dir")
    parser.add_argument("--json", action="store_true")
    opts = parser.parse_args(argv)
    run_dir = Path(opts.run_dir)
    if not (run_dir / "events.jsonl").is_file():
        print(f"{run_dir}: não é um directório de run (falta events.jsonl)", file=sys.stderr)
        return 2
    ev = collect(run_dir)
    print(json.dumps(ev, ensure_ascii=False, indent=2) if opts.json else to_markdown(ev))
    return 0 if ev["verdict"] == "PASSOU" else 1


if __name__ == "__main__":
    raise SystemExit(main())
