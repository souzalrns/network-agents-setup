"""B1-bis: projeccao de tokens de um plano em modo legacy vs opt, sem Gemini.

!!! REFUTADA PELO RUN REAL (B1-bis-R, 2026-10-01): projectou -16%, o real deu
-2,6%. NAO USAR PARA DECISOES -- so com usageMetadata real (ou o endpoint
countTokens da API Gemini). Licao de metodo em docs/ops/WORKER-EXTERNAL.md.
Fica como ferramenta exploratoria (e e usada nos testes de test_context_opt.py).

Corre o plano REAL pelo worker REAL (prompt construido como em producao), com
um Gemini falso que devolve artefactos do tamanho medido no B1 real. O
tokens_in de cada passo e estimado assim:

    tokens_in = (caracteres do prompt - caracteres injectados) / chars_por_token_do_passo
                + tokens dos inputs injectados

- chars_por_token_do_passo: calibrado no B1 (prompt-base real / tokens base
  reais: research 3,50, seo_brief 3,36, copy 3,42, critic 3,29). Com isto, o
  modo legacy reproduz o B1 -- e a verificacao da calibracao, nao uma prova;
- tokens dos inputs: o tokens_out real do passo que os produziu (B1); um
  resumo conta `summary_tokens`; um JSON compacto conta so METADE do corte de
  caracteres (os espacos de indentacao tokenizam barato) -- estimativa prudente.

E uma PROJECCAO. A medicao que conta e um run real (o B1-bis do maestro):
    PLAN_RUNNER_CONTEXT=legacy|opt python -m plan_runner run ... --worker gemini

CLI: python -m plan_runner.token_projection [plano.yaml]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from . import context_policy as cp
from . import external_worker as ew

REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_DEMO = REPO_ROOT / "docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml"

# B1 real (2026-10-01, docs/ops/WORKER-EXTERNAL.md): (tokens_in, tokens_out)
B1_REAL = {"research": (1426, 467), "seo_brief": (2189, 1226), "copy": (2270, 1389), "critic": (3819, 344)}
# prompt-base real / tokens base reais (tokens_in - inputs injectados), ver docstring
B1_CHARS_PER_TOKEN = {"research": 3.50, "seo_brief": 3.36, "copy": 3.42, "critic": 3.29}
ARTIFACT_CHARS_PER_TOKEN = 3.4
WORDS = ("conteudo citavel resposta directa pergunta frequente estrutura secao fonte autoridade "
         "modelo linguagem descoberta pesquisa marca audiencia exemplo dados verificavel claro").split()


def _text(tokens: int, seed: int) -> str:
    target = int(tokens * ARTIFACT_CHARS_PER_TOKEN)
    out, i = [], seed
    while sum(len(w) + 1 for w in out) < target:
        out.append(WORDS[i % len(WORDS)])
        i += 7
    return " ".join(out)


def _json_artifact(tokens: int, seed: int) -> dict[str, Any]:
    """Objecto com a forma de um brief (listas de strings), ~`tokens` quando indentado."""
    obj: dict[str, Any] = {"titulo": _text(15, seed), "keyword_principal": "ai findability"}
    n = 0
    while len(json.dumps(obj, indent=2, ensure_ascii=False)) < tokens * ARTIFACT_CHARS_PER_TOKEN:
        obj.setdefault(f"seccao_{n // 6}", []).append(_text(18, seed + n))
        n += 1
    return obj


def _summary(tokens: int) -> dict[str, list[str]]:
    per = max(1, tokens // len(cp.SUMMARY_KEYS))
    return {k: [_text(per, i)] for i, (k, _) in enumerate(cp.SUMMARY_KEYS)}


class _SizingGemini:
    def __init__(self, out_tokens: dict[str, int], summary_tokens: int):
        self.out_tokens, self.summary_tokens = out_tokens, summary_tokens
        self.calls: list[dict[str, Any]] = []

    def __call__(self, url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        step = re.search(r"- passo: (\S+)", user).group(1)
        wants_json = body["generationConfig"].get("responseMimeType") == "application/json"
        wants_summary = cp.SUMMARY_MARKER in system or "`resumo`" in system
        t = self.out_tokens.get(step, 400)
        if wants_json:
            art = _json_artifact(t, len(self.calls))
            payload = {"artifact": art, "resumo": _summary(self.summary_tokens)} if wants_summary else art
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = _text(t, len(self.calls))
            if wants_summary:
                text += f"\n{cp.SUMMARY_MARKER}\n" + cp.render_summary(_summary(self.summary_tokens))
        self.calls.append({"step": step, "system": system, "user": user, "summary": wants_summary})
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0}}


_INPUT_RE = re.compile(r"^## Input( \(resumo\))?: (.+?)\n\n(.*?)(?=^## |\Z)", re.S | re.M)


def project(
    plan_path: Path = SEO_DEMO,
    *,
    context: str,
    out_tokens: dict[str, int] | None = None,
    chars_per_token: dict[str, float] | None = None,
    summary_tokens: int = 300,
) -> list[dict[str, Any]]:
    """Linhas {step, tokens_in, tokens_out, total, injected} estimadas para o modo `context`."""
    from .engine import resume_run, run_plan

    out_tokens = out_tokens or {k: v[1] for k, v in B1_REAL.items()}
    ratios = chars_per_token or B1_CHARS_PER_TOKEN
    fake = _SizingGemini(out_tokens, summary_tokens)
    out = REPO_ROOT / "pilots" / f"_projection_{uuid.uuid4().hex[:8]}"
    saved = (ew.httpx_transport, os.environ.get(cp.CONTEXT_ENV), os.environ.get("GEMINI_API_KEY"))
    ew.httpx_transport = fake
    os.environ[cp.CONTEXT_ENV] = context
    os.environ.setdefault("GEMINI_API_KEY", "projeccao-sem-rede")
    try:
        status = run_plan(plan_path, mode="external", out_dir=out, worker="gemini")
        while status["state"] == "paused_human_gate":  # gates: aprovar para medir o plano inteiro
            status = resume_run(out, decision="approve")
        sizes: dict[str, tuple[int, int]] = {}  # artefacto -> (chars indentados, tokens)
        for c in fake.calls:
            step_raw = next(s for s in __import__("yaml").safe_load(plan_path.read_text())["steps"] if s["id"] == c["step"])
            art = step_raw.get("output_artifact")
            if art and (out / art).is_file():
                sizes[art] = (len((out / art).read_text(encoding="utf-8")), out_tokens.get(c["step"], 400))
        rows = []
        for c in fake.calls:
            injected_chars, injected_tokens, notes = 0, 0, []
            for m in _INPUT_RE.finditer(c["user"]):
                is_summary, rel, body = bool(m.group(1)), m.group(2).strip(), m.group(3)
                injected_chars += len(body)
                full_chars, full_tokens = sizes.get(rel, (len(body), round(len(body) / ARTIFACT_CHARS_PER_TOKEN)))
                if is_summary:
                    tok = summary_tokens
                    notes.append(f"{rel} (resumo)")
                elif len(body.rstrip()) < full_chars * 0.97:  # JSON compacto: so metade do corte conta
                    tok = round(full_tokens * (1 - 0.5 * (1 - len(body) / full_chars)))
                    notes.append(f"{rel} (completo, JSON compacto)")
                else:
                    tok = full_tokens
                    notes.append(f"{rel} (completo)")
                injected_tokens += tok
            base_chars = len(c["system"]) + len(c["user"]) - injected_chars
            t_in = round(base_chars / ratios.get(c["step"], 3.4)) + injected_tokens
            t_out = out_tokens.get(c["step"], 400) + (summary_tokens if c["summary"] else 0)
            rows.append({"step": c["step"], "tokens_in": t_in, "tokens_out": t_out, "total": t_in + t_out,
                         "injected": notes, "summary_generated": c["summary"]})
        return rows
    finally:
        ew.httpx_transport = saved[0]
        for key, val in ((cp.CONTEXT_ENV, saved[1]), ("GEMINI_API_KEY", saved[2])):
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        shutil.rmtree(out, ignore_errors=True)


def table(before: list[dict], after: list[dict]) -> str:
    lines = ["| Passo | in antes | out antes | total antes | in depois | out depois | total depois | Δ total |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for b, a in zip(before, after, strict=True):
        d = (a["total"] - b["total"]) / b["total"] * 100
        lines.append(f"| {b['step']} | {b['tokens_in']} | {b['tokens_out']} | {b['total']} | {a['tokens_in']} | "
                     f"{a['tokens_out']} | {a['total']} | {d:+.0f}% |")
    tb, ta = sum(r["total"] for r in before), sum(r["total"] for r in after)
    lines.append(f"| **TOTAL** | | | **{tb}** | | | **{ta}** | **{(ta - tb) / tb * 100:+.0f}%** |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plan_runner.token_projection")
    ap.add_argument("plan", nargs="?", type=Path, default=SEO_DEMO)
    ap.add_argument("--summary-tokens", type=int, default=300)
    args = ap.parse_args(argv)
    before = project(args.plan, context="legacy", summary_tokens=args.summary_tokens)
    after = project(args.plan, context="opt", summary_tokens=args.summary_tokens)
    print("AVISO: projeccao exploratoria, refutada pelo run real (-16% projectado vs -2,6% real, B1-bis-R).")
    print("       Nao usar para decisoes: medir com usageMetadata real. Ver docs/ops/WORKER-EXTERNAL.md.\n")
    print(table(before, after))
    for r in after:
        print(f"  {r['step']}: {', '.join(r['injected']) or 'sem inputs'}{' + gera resumo' if r['summary_generated'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
