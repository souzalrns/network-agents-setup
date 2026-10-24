"""Fecho do setup: corre os runs reais que precisam das credenciais do maestro e junta a evidência.

Checklist da sessão: docs/ops/SETUP-CLOSE-SESSION.md (este script é o passo 3).

Itens (PENDENCIAS §4):
  MCP-V3       F3b-AUTH-1  o retrieve do MCP em produção responde com a v3 (metadata.authority)
  F2           F2          web-research-demo (fetch_url com allowlist e proveniência)
  F3b-GS-1     F3b-GS-1    golden set de marketing contra o MCP real (l5_eval run)
  F6-MARKET    F6          trading: market-analysis-demo (fetch_url na área trading + risco)
  F6-REVIEW    F6          trading: post-trade-review-demo (JSON do economia-trader review)
  COM-1        COM-1       comercial: comercial-demo (lead → proposta → follow-ups; dados fictícios)
  F5-ROUTE-1   F5-ROUTE-1  um run que começa no router (route --execute)
  F3-ART-1     F3-ART-1    meta.sources nos result.json dos runs acima (derivado, sem chamadas)

Uso (na raiz do repositório, com o ambiente do runner instalado):

    python scripts/setup_close_runs.py                  # tudo
    python scripts/setup_close_runs.py --only F2,F6-REVIEW
    python scripts/setup_close_runs.py --check          # só verifica ambiente e ficheiros
    python scripts/setup_close_runs.py --stub           # ensaio offline, sem credenciais

Precisa de GEMINI_API_KEY, MCP_URL e MCP_API_KEY no ambiente (falha logo se faltar alguma;
só mostra os nomes, nunca os valores). Os valores das chaves são apagados dos logs e do
relatório. Saída em pilots/setup-close-<UTC>/ (fora do git), com uma cópia do relatório em
pilots/evidence/ (versionável). Código de saída: 0 sem FAIL, 1 com algum FAIL, 2 se o
ambiente ou os ficheiros não estiverem prontos.

Nunca executa ordens nem toca em produção: os planos de trading são só leitura/preparação
e param no gate humano; nada é aprovado por este script.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "runner"
REQUIRED_ENV = ("GEMINI_API_KEY", "MCP_URL", "MCP_API_KEY")
SECRET_ENV = ("GEMINI_API_KEY", "MCP_API_KEY", "VERCEL_PROTECTION_BYPASS")
OK_STATES = ("completed", "paused_human_gate")
PLAN_TIMEOUT_S = 20 * 60
EVAL_TIMEOUT_S = 10 * 60

PLANS = {
    "F2": "docs/orchestration/marketing/templates/examples/web-research-demo.plan.yaml",
    "F6-MARKET": "docs/orchestration/trading/templates/examples/market-analysis-demo.plan.yaml",
    "F6-REVIEW": "docs/orchestration/trading/templates/examples/post-trade-review-demo.plan.yaml",
    "COM-1": "docs/orchestration/marketing/templates/examples/comercial-demo.plan.yaml",
}
# O que o maestro confere no gate do COM-1 (não se avalia o texto do modelo por heurística).
COM1_GATE_CHECK = "preços só da tabela fictícia, lacunas marcadas e o cliente C (pediu para parar) fora dos rascunhos"
TOOLS_PLANS = {"F2", "F6-MARKET"}  # usam fetch_url: PLAN_RUNNER_TOOLS=1
GOLDEN = "config/l5-golden-marketing.yaml"
ROUTE_REQUEST = (
    "Faz uma pesquisa de mercado sobre conteúdo answer-first para pesquisa com IA, "
    "com as fontes citadas"
)

# Probe do MCP: v1 (metadata null), v2 (metadata sem authority) ou v3 (com authority).
MCP_PROBE = """
import json
from plan_runner.mcp_knowledge import McpKnowledge
hits = McpKnowledge().retrieve("security", "auditoria defensiva", top_k=1, filters=None, require_citations=True)
meta = hits[0].get("metadata") if hits else None
version = "sem hits" if not hits else ("v1" if not meta else ("v3" if "authority" in meta else "v2"))
print(json.dumps({"version": version, "hits": len(hits),
                  "authority": (meta or {}).get("authority"),
                  "citation": (hits[0].get("citation") if hits else None)}, ensure_ascii=False))
"""

P81_LINE = (
    "- **P-81** (conhecimento de trading no L5): recomendada **A** (`_kb_for` genérico: kb = id da "
    "área). Falta a decisão do maestro; até lá o pack de trading lê o conhecimento por `repo_files`."
)

ITEMS = (
    ("MCP-V3", "F3b-AUTH-1", "Retrieve do MCP em produção na v3 (SQL + KNOWLEDGE_RPC_V3)"),
    ("F2", "F2", "web-research-demo (fetch_url, allowlist, proveniência)"),
    ("F3b-GS-1", "F3b-GS-1", "Golden set de marketing contra o MCP real"),
    ("F6-MARKET", "F6", "Trading: market-analysis-demo"),
    ("F6-REVIEW", "F6", "Trading: post-trade-review-demo"),
    ("COM-1", "COM-1", "Comercial: comercial-demo (lead → proposta → follow-ups)"),
    ("F5-ROUTE-1", "F5-ROUTE-1", "Run que começa no router (route --execute)"),
    ("F3-ART-1", "F3-ART-1", "meta.sources nos result.json dos runs"),
)


@dataclass
class Result:
    key: str
    pendencia: str
    title: str
    status: str = "SKIP"  # PASS | FAIL | SKIP
    detail: str = ""
    paths: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    seconds: float = 0.0


# --- utilitários ----------------------------------------------------------------------------


def missing_env(env: dict[str, str]) -> list[str]:
    return [name for name in REQUIRED_ENV if not env.get(name, "").strip()]


def redact(text: str, env: dict[str, str]) -> str:
    """Apaga os valores das chaves (nunca vão para logs nem relatório)."""
    for name in SECRET_ENV:
        value = env.get(name, "").strip()
        if len(value) >= 6:
            text = text.replace(value, f"<{name}>")
    return text


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_cmd(args: list[str], *, log: Path, env: dict[str, str], timeout: int) -> tuple[int, str]:
    """Corre em runner/ e grava o log (com as chaves apagadas). Devolve (código, saída)."""
    try:
        # Falso positivo (auditoria): lista sem shell; os elementos são o interpretador, módulos
        # fixos do runner e caminhos do repositório resolvidos aqui; nada vem de input externo.
        # nosemgrep: dangerous-subprocess-use-audit
        proc = subprocess.run(
            args, cwd=RUNNER, env=env, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
        )
        code, out = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        code, out = 124, f"TIMEOUT ao fim de {timeout}s\n{exc.stdout or ''}{exc.stderr or ''}"
    out = redact(out if isinstance(out, str) else out.decode("utf-8", "replace"), env)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"$ {' '.join(args)}\n(cwd: runner/)\n\n{out}", encoding="utf-8")
    return code, out


def step_results(run_dir: Path) -> dict[str, dict[str, Any]]:
    """result.json de cada passo de um run (pending_steps/<passo>/result.json)."""
    out: dict[str, dict[str, Any]] = {}
    for path in sorted((run_dir / "pending_steps").glob("*/result.json")):
        try:
            out[path.parent.name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def sources_of(run_dir: Path) -> list[dict[str, Any]]:
    """As fontes (meta.sources, F3-ART-1) de todos os passos do run, com o passo de origem."""
    found = []
    for step, res in step_results(run_dir).items():
        meta = res.get("meta") if isinstance(res, dict) else None
        for src in (meta or {}).get("sources") or []:
            if isinstance(src, dict):
                found.append({"step": step, **src})
    return found


def read_status(run_dir: Path) -> dict[str, Any]:
    try:
        return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def judge_run(res: Result, run_dir: Path, code: int) -> None:
    status = read_status(run_dir)
    state = status.get("state")
    res.paths += [rel(p) for p in [run_dir / "status.json", *sorted((run_dir / "pending_steps").glob("*/result.json"))] if p.exists()]
    res.sources = sources_of(run_dir)
    done = status.get("completed") or []
    if code == 0 and state in OK_STATES and done:
        res.status = "PASS"
        res.detail = f"estado {state}; passos concluídos: {', '.join(done)}"
        if state == "paused_human_gate":
            res.detail += f" (parado no gate humano `{status.get('paused_at_step')}`, como previsto)"
    else:
        res.status = "FAIL"
        res.detail = f"código {code}; estado {state or '(sem status.json)'}; concluídos: {done or 'nenhum'}"


# --- itens ----------------------------------------------------------------------------------


def do_plan(res: Result, out: Path, env: dict[str, str], *, stub: bool) -> None:
    run_dir = out / f"run-{res.key.lower()}"
    item_env = dict(env)
    if res.key in TOOLS_PLANS:
        item_env["PLAN_RUNNER_TOOLS"] = "1"
    args = [sys.executable, "-m", "plan_runner", "run", str(REPO_ROOT / PLANS[res.key]), "--out", str(run_dir)]
    args += ["--mode", "stub"] if stub else ["--mode", "external", "--worker", "gemini"]
    code, _ = run_cmd(args, log=out / "logs" / f"{res.key}.log", env=item_env, timeout=PLAN_TIMEOUT_S)
    res.paths.append(rel(out / "logs" / f"{res.key}.log"))
    judge_run(res, run_dir, code)
    if res.status == "PASS" and res.key in TOOLS_PLANS and not stub:
        # O F2 prova-se com a tool a funcionar: um passo "concluído" sem fontes web não chega.
        web = [s for s in res.sources if s.get("kind") == "web" and s.get("final_url")]
        if not web:
            res.status = "FAIL"
            res.detail += "; mas a tool fetch_url não trouxe nenhuma fonte web (ver o log e o result.json)"
        else:
            res.detail += f"; {len(web)} fonte(s) web da fetch_url"
    if res.status == "PASS" and res.key == "COM-1":
        res.detail += f"; rever no gate: {COM1_GATE_CHECK}"


def do_mcp(res: Result, out: Path, env: dict[str, str]) -> None:
    code, text = run_cmd([sys.executable, "-c", MCP_PROBE], log=out / "logs" / "MCP-V3.log", env=env, timeout=120)
    res.paths.append(rel(out / "logs" / "MCP-V3.log"))
    try:
        probe = json.loads(text.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res.status, res.detail = "FAIL", f"a probe não respondeu (código {code}); ver o log"
        return
    version = probe.get("version")
    res.status = "PASS" if version == "v3" else "FAIL"
    res.detail = f"versão do retrieve: {version}; authority do 1.º hit: {probe.get('authority')}"
    if version == "v2":
        res.detail += " (falta o SQL da v3 e/ou KNOWLEDGE_RPC_V3=1 + redeploy: checklist, passo 1)"


def do_golden(res: Result, out: Path, env: dict[str, str]) -> None:
    report = out / "l5-marketing.json"
    code, _ = run_cmd(
        [sys.executable, "-m", "plan_runner.l5_eval", "run", "--golden", str(REPO_ROOT / GOLDEN), "--out", str(report)],
        log=out / "logs" / "F3b-GS-1.log", env=env, timeout=EVAL_TIMEOUT_S,
    )
    res.paths += [rel(out / "logs" / "F3b-GS-1.log")] + ([rel(report)] if report.exists() else [])
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        res.status, res.detail = "FAIL", f"sem relatório (código {code}); ver o log"
        return
    summary, gate = data.get("summary") or {}, data.get("gate") or {}
    keys = ("chunk_hit@1", "chunk_hit@4", "source_hit@4", "mrr_chunk", "no_hits", "provenance_ok", "provenance_v2_ok")
    res.detail = "; ".join(f"{k} {summary[k]}" for k in keys if k in summary)
    res.status = "PASS" if gate.get("passed") else "FAIL"
    if gate.get("failures"):
        res.detail += f"; gate P-19 falhou: {', '.join(gate['failures'])}"


def do_route(res: Result, out: Path, env: dict[str, str]) -> None:
    run_dir = out / "run-f5-route"
    args = [sys.executable, "-m", "plan_runner", "route", ROUTE_REQUEST, "--execute", "--worker", "gemini",
            "--out", str(run_dir), "--log", str(out / "router-decisions.jsonl")]
    code, _ = run_cmd(args, log=out / "logs" / "F5-ROUTE-1.log", env=env, timeout=PLAN_TIMEOUT_S)
    res.paths.append(rel(out / "logs" / "F5-ROUTE-1.log"))
    judge_run(res, run_dir, code)
    route = run_dir / "route.json"
    if route.exists():
        res.paths.append(rel(route))
        decision = json.loads(route.read_text(encoding="utf-8"))
        res.detail = (f"área {decision.get('area')} ({decision.get('area_method')}), "
                      f"outcome {decision.get('outcome')}, agente {decision.get('agent')}; ") + res.detail
    elif res.status == "PASS":
        res.status, res.detail = "FAIL", "o run correu mas não há route.json (não partiu do router)"


def do_artifacts(res: Result, results: dict[str, Result], *, stub: bool) -> None:
    if stub:
        res.status, res.detail = "SKIP", "em stub não há worker nem tools, por isso não há fontes"
        return
    runs = [r for k, r in results.items() if k in ("F2", "F6-MARKET", "F6-REVIEW", "COM-1", "F5-ROUTE-1") and r.status != "SKIP"]
    if not runs:
        res.status, res.detail = "SKIP", "nenhum run desta sessão para ler"
        return
    with_sources = [r for r in runs if r.sources]
    res.sources = [{"run": r.key, **s} for r in with_sources for s in r.sources][:12]
    web = [s for s in res.sources if s.get("kind") == "web" and s.get("final_url")]
    res.status = "PASS" if web else "FAIL"
    res.detail = (f"{sum(len(r.sources) for r in runs)} fonte(s) em {len(with_sources)}/{len(runs)} run(s); "
                  f"{len(web)} da web com final_url")
    if not web:
        res.detail += " (o F2 e o F6-MARKET têm de trazer fontes da tool fetch_url)"


# --- relatório ------------------------------------------------------------------------------


def render(results: list[Result], out: Path, *, started: str, stub: bool) -> str:
    lines = [
        "# Fecho do setup — evidência dos runs reais",
        "",
        f"- Corrido em: {started} (UTC){' — ENSAIO EM STUB, não conta como evidência' if stub else ''}",
        f"- Pasta: `{rel(out)}`",
        f"- Comando: `python scripts/setup_close_runs.py{' --stub' if stub else ''}`",
        "",
        "| Item | Pendência | Resultado | Detalhe | Tempo |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        detail = r.detail.replace("|", "\\|")
        lines.append(f"| {r.key} | {r.pendencia} | **{r.status}** | {detail} | {r.seconds:.0f}s |")
    lines += ["", "## Ficheiros por item", ""]
    for r in results:
        if r.paths:
            lines.append(f"- **{r.key}:** " + ", ".join(f"`{p}`" for p in r.paths))
    art = next((r for r in results if r.key == "F3-ART-1"), None)
    if art and art.sources:
        lines += ["", "## Excerto de meta.sources (F3-ART-1)", "", "```json",
                  json.dumps(art.sources, ensure_ascii=False, indent=2), "```"]
    lines += [
        "",
        "## Pendente de decisão (não é deste script)",
        "",
        P81_LINE,
    ]
    return "\n".join(lines) + "\n"


def preflight(stub: bool) -> list[str]:
    problems = [f"falta o ficheiro {p}" for p in [*PLANS.values(), GOLDEN] if not (REPO_ROOT / p).is_file()]
    # Falso positivo (auditoria): lista fixa sem shell (o interpretador e um import constante).
    # nosemgrep: dangerous-subprocess-use-audit
    probe = subprocess.run([sys.executable, "-c", "import plan_runner, yaml"], cwd=RUNNER,
                           capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        problems.append("o ambiente do runner não está instalado (pip install -r runner/requirements.txt)")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python scripts/setup_close_runs.py", description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="itens separados por vírgula (ex.: F2,F6-REVIEW)")
    ap.add_argument("--check", action="store_true", help="só verifica ambiente e ficheiros; não corre nada")
    ap.add_argument("--stub", action="store_true", help="ensaio offline: planos em stub, sem credenciais")
    ap.add_argument("--out", type=Path, help="pasta de saída (omissão: pilots/setup-close-<UTC>/)")
    args = ap.parse_args(argv)
    env = dict(os.environ)

    keys = [k for k, _, _ in ITEMS]
    wanted = keys if not args.only else [k.strip().upper() for k in args.only.split(",") if k.strip()]
    unknown = sorted(set(wanted) - set(keys))
    if unknown:
        print(f"erro: itens desconhecidos {unknown}; conhecidos: {keys}", file=sys.stderr)
        return 2

    problems = preflight(args.stub)
    missing = [] if args.stub else missing_env(env)
    if missing:
        problems.append(f"faltam variáveis de ambiente: {', '.join(missing)} (só os nomes; nunca os valores)")
    if problems or args.check:
        for p in problems:
            print(f"✗ {p}", file=sys.stderr)
        if not problems:
            print("✓ ambiente e ficheiros prontos; corre sem --check para executar os itens")
        return 2 if problems else 0

    started = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    out = (args.out or REPO_ROOT / "pilots" / f"setup-close-{started}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, Result] = {}
    for key, pend, title in ITEMS:
        res = results.setdefault(key, Result(key, pend, title))
        if key not in wanted:
            res.detail = "fora do --only"
            continue
        if args.stub and key in ("MCP-V3", "F3b-GS-1", "F5-ROUTE-1"):
            res.detail = "precisa das credenciais (não corre em --stub)"
            continue
        print(f"→ {key}: {title}", flush=True)
        t0 = time.monotonic()
        if key in PLANS:
            do_plan(res, out, env, stub=args.stub)
        elif key == "MCP-V3":
            do_mcp(res, out, env)
        elif key == "F3b-GS-1":
            do_golden(res, out, env)
        elif key == "F5-ROUTE-1":
            do_route(res, out, env)
        elif key == "F3-ART-1":
            do_artifacts(res, results, stub=args.stub)
        res.seconds = time.monotonic() - t0
        # Só o resultado: o detalhe (que pode vir da saída dos subprocessos) fica no REPORT.md,
        # já redigido.
        print(f"  {res.status} ({res.seconds:.0f}s)", flush=True)

    ordered = [results[k] for k in keys]
    report = redact(render(ordered, out, started=started, stub=args.stub), env)
    (out / "REPORT.md").write_text(report, encoding="utf-8")
    (out / "report.json").write_text(
        redact(json.dumps([r.__dict__ for r in ordered], ensure_ascii=False, indent=2), env), encoding="utf-8"
    )
    print(f"\nRelatório: {rel(out / 'REPORT.md')}")
    if not args.stub:  # um ensaio em stub nunca vai para a evidência versionada
        evidence = REPO_ROOT / "pilots" / "evidence" / f"setup-close-{started}.md"
        evidence.write_text(report, encoding="utf-8")
        print(f"Cópia versionável: {rel(evidence)}")
    return 1 if any(r.status == "FAIL" for r in ordered) else 0


if __name__ == "__main__":
    raise SystemExit(main())
