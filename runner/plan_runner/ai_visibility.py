"""M-006: medição de visibilidade em IA (GEO/AEO) para o agente `marketing.ai_visibility`.

Contrato (docs/ops/AI-VISIBILITY.md):

- **Painel fixo:** um YAML com a marca (nome, nomes alternativos, domínios), 0 a 6 concorrentes e
  1 a 25 perguntas. O painel é a régua: medições com painéis diferentes não se comparam.
- **Dois caminhos, a mesma pontuação:**
  - `medir`: pergunta ao Gemini com pesquisa Google (grounding). Simula por omissão; só chama a API
    com `--run`, no máximo 25 pedidos, sem novas tentativas. Um 429/403 (quota) pára e guarda o que já
    foi medido.
  - `importar`: respostas coladas de qualquer motor (ChatGPT, Perplexity, Claude…), sem API e sem custo.
- **Pontuação:** *mencionada* = o nome ou um nome alternativo aparece no texto (sem acentos nem
  maiúsculas, palavra inteira); *citada* = uma fonte é de um domínio da marca (ou subdomínio).
  O mesmo para cada concorrente.
- **Saída:** `medicao-<motor>-<data>.json`, `historico.jsonl` (uma linha por medição) e `resumo.md`
  com a variação face à medição anterior do mesmo motor e painel.
- **Sem invenção:** o que não foi medido fica `nao_medida`; o resumo diz o tamanho da amostra.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import jsonschema
import yaml

MAX_QUESTIONS = 25
MAX_COMPETITORS = 6
ANSWER_MAX_CHARS = 4000
STOP_CODES = (401, 403, 429)  # chave inválida ou quota: parar, não insistir
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_ENTITY = {
    "type": "object", "required": ["nome"], "additionalProperties": False,
    "properties": {
        "nome": {"type": "string", "minLength": 2},
        "aliases": {"type": "array", "items": {"type": "string", "minLength": 2}},
        "dominios": {"type": "array", "items": {"type": "string", "pattern": r"^[a-z0-9.-]+\.[a-z]{2,}$"}},
    },
}
PANEL_SCHEMA: dict[str, Any] = {
    "type": "object", "required": ["marca", "perguntas"], "additionalProperties": False,
    "properties": {
        "marca": _ENTITY,
        "concorrentes": {"type": "array", "maxItems": MAX_COMPETITORS, "items": _ENTITY},
        "idioma": {"type": "string"},
        "perguntas": {"type": "array", "minItems": 1, "maxItems": MAX_QUESTIONS, "items": {
            "type": "object", "required": ["id", "texto"], "additionalProperties": False,
            "properties": {"id": {"type": "string", "pattern": r"^[a-z0-9_-]{1,40}$"},
                           "texto": {"type": "string", "minLength": 5, "maxLength": 500}},
        }},
    },
}
ANSWERS_SCHEMA: dict[str, Any] = {
    "type": "array", "items": {
        "type": "object", "required": ["pergunta", "resposta"],
        "properties": {"pergunta": {"type": "string"}, "resposta": {"type": "string"},
                       "fontes": {"type": "array", "items": {"type": "string"}}},
    },
}


class VisibilityError(RuntimeError):
    """Painel ou respostas inválidos, ou falta de credencial: nada é medido."""


# --------------------------------------------------------------------------- painel e pontuação


def load_panel(path: Path) -> dict[str, Any]:
    panel = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    try:
        jsonschema.validate(panel, PANEL_SCHEMA)
    except jsonschema.ValidationError as e:
        raise VisibilityError(f"painel inválido: {e.message}") from e
    ids = [q["id"] for q in panel["perguntas"]]
    if len(set(ids)) != len(ids):
        raise VisibilityError("painel inválido: ids de pergunta repetidos")
    return panel


def panel_sha(panel: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(panel, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def mentioned(entity: dict[str, Any], text: str) -> bool:
    body = _norm(text)
    for name in [entity["nome"], *(entity.get("aliases") or [])]:
        if re.search(r"(?<!\w)" + re.escape(_norm(name)) + r"(?!\w)", body):
            return True
    return False


def host(source: str) -> str:
    s = (source or "").strip().lower()
    parsed = urlparse(s if "://" in s else "//" + s)
    return (parsed.hostname or "").removeprefix("www.")


def cited(entity: dict[str, Any], sources: list[str]) -> bool:
    hosts = {host(s) for s in sources}
    return any(h == d or h.endswith("." + d) for h in hosts for d in entity.get("dominios") or [])


def score(panel: dict[str, Any], answers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for q in panel["perguntas"]:
        a = answers.get(q["id"])
        if a is None or a.get("erro"):
            rows.append({"pergunta": q["id"], "estado": "nao_medida", **({"erro": a["erro"]} if a else {})})
            continue
        text, sources = a.get("resposta") or "", list(a.get("fontes") or [])
        rows.append({
            "pergunta": q["id"], "estado": "medida",
            "marca": {"mencionada": mentioned(panel["marca"], text), "citada": cited(panel["marca"], sources)},
            "concorrentes": {c["nome"]: {"mencionada": mentioned(c, text), "citada": cited(c, sources)}
                             for c in panel.get("concorrentes") or []},
            "fontes": sources[:20],
            "resposta": text[:ANSWER_MAX_CHARS],
            **({"pesquisas": a["pesquisas"]} if a.get("pesquisas") else {}),
        })
    return rows


def summary(panel: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [r for r in rows if r["estado"] == "medida"]
    n = len(measured)

    def pct(k: int) -> float | None:
        return round(100 * k / n, 1) if n else None

    def counts(get: Callable[[dict[str, Any]], dict[str, bool]]) -> dict[str, Any]:
        m = sum(get(r)["mencionada"] for r in measured)
        c = sum(get(r)["citada"] for r in measured)
        return {"mencionada": m, "citada": c, "mencionada_pct": pct(m), "citada_pct": pct(c)}

    return {
        "perguntas": len(rows), "medidas": n,
        "marca": counts(lambda r: r["marca"]),
        "concorrentes": {c["nome"]: counts(lambda r, name=c["nome"]: r["concorrentes"][name])
                         for c in panel.get("concorrentes") or []},
    }


# --------------------------------------------------------------------------- Gemini (grounding)

Send = Callable[[str, dict[str, str], dict[str, Any], float], tuple[int, dict[str, Any]]]


def _gemini_answer(resp: dict[str, Any]) -> dict[str, Any]:
    cand = (resp.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts") or [])
    meta = cand.get("groundingMetadata") or {}
    sources = []
    for ch in meta.get("groundingChunks") or []:
        web = ch.get("web") or {}
        # o `uri` do grounding é um redireccionamento do Google; o domínio vem em `domain` ou no `title`
        src = web.get("domain") or web.get("title") or web.get("uri")
        if src:
            sources.append(str(src))
    return {"resposta": text, "fontes": sources, "pesquisas": list(meta.get("webSearchQueries") or [])}


def ask_gemini(panel: dict[str, Any], *, api_key: str, model: str, send: Send,
               timeout: float = 60.0) -> dict[str, dict[str, Any]]:
    answers: dict[str, dict[str, Any]] = {}
    lang = panel.get("idioma")
    for q in panel["perguntas"]:
        text = q["texto"] + (f"\n\n(Responde em {lang}.)" if lang else "")
        body = {"contents": [{"role": "user", "parts": [{"text": text}]}], "tools": [{"google_search": {}}]}
        try:
            code, resp = send(GEMINI_URL.format(model=model), {"x-goog-api-key": api_key}, body, timeout)
        except Exception as e:  # noqa: BLE001 -- rede/proxy/timeout: parar e guardar o que já foi medido
            answers[q["id"]] = {"erro": f"rede: {type(e).__name__}: parado ({str(e)[:120]})"}
            break
        if code in STOP_CODES:
            answers[q["id"]] = {"erro": f"HTTP {code}: parado (chave ou quota)"}
            break
        if code != 200:
            answers[q["id"]] = {"erro": f"HTTP {code}"}
            continue
        answers[q["id"]] = _gemini_answer(resp)
    return answers


# --------------------------------------------------------------------------- registo


def _previous(out: Path, engine: str, sha: str) -> dict[str, Any] | None:
    hist = out / "historico.jsonl"
    if not hist.is_file():
        return None
    last = None
    for line in hist.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("motor") == engine and rec.get("painel_sha") == sha:
                last = rec
    return last


def _delta(now: float | None, before: float | None) -> str:
    if now is None:
        return "—"
    if before is None:
        return f"{now}%"
    d = round(now - before, 1)
    return f"{now}% ({'+' if d >= 0 else ''}{d})"


def record(panel: dict[str, Any], rows: list[dict[str, Any]], *, engine: str, out: Path,
           when: datetime | None = None) -> dict[str, Any]:
    when = when or datetime.now(UTC)
    out.mkdir(parents=True, exist_ok=True)
    sha = panel_sha(panel)
    prev = _previous(out, engine, sha)
    summ = summary(panel, rows)
    stamp = when.strftime("%Y%m%dT%H%M%SZ")
    result = {"motor": engine, "em": when.isoformat(), "painel_sha": sha, "marca": panel["marca"]["nome"],
              "resumo": summ, "linhas": rows}
    (out / f"medicao-{engine}-{stamp}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "historico.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: result[k] for k in ("motor", "em", "painel_sha", "marca", "resumo")}, ensure_ascii=False) + "\n")

    pb = (prev or {}).get("resumo") or {}
    lines = [
        f"# Visibilidade em IA — {panel['marca']['nome']}", "",
        f"Motor: **{engine}** · {when.date().isoformat()} · painel `{sha}` · {summ['medidas']} de {summ['perguntas']} perguntas medidas"
        + ("" if prev else " · primeira medição deste painel neste motor"), "",
        "| Quem | Mencionada | Citada como fonte |", "|---|---|---|",
        f"| **{panel['marca']['nome']}** | {_delta(summ['marca']['mencionada_pct'], (pb.get('marca') or {}).get('mencionada_pct'))} "
        + f"| {_delta(summ['marca']['citada_pct'], (pb.get('marca') or {}).get('citada_pct'))} |",
    ]
    for name, c in summ["concorrentes"].items():
        b = (pb.get("concorrentes") or {}).get(name) or {}
        lines.append(f"| {name} | {_delta(c['mencionada_pct'], b.get('mencionada_pct'))} | {_delta(c['citada_pct'], b.get('citada_pct'))} |")
    lines += ["", "| Pergunta | Marca mencionada | Marca citada |", "|---|---|---|"]
    for r in rows:
        if r["estado"] == "medida":
            lines.append(f"| {r['pergunta']} | {'sim' if r['marca']['mencionada'] else 'não'} | {'sim' if r['marca']['citada'] else 'não'} |")
        else:
            lines.append(f"| {r['pergunta']} | não medida | {r.get('erro', '')} |")
    if summ["medidas"] < 10:
        lines += ["", f"Amostra pequena ({summ['medidas']} perguntas): as percentagens variam muito entre medições."]
    (out / "resumo.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


# --------------------------------------------------------------------------- CLI


def _load_answers(path: Path) -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    try:
        jsonschema.validate(data, ANSWERS_SCHEMA)
    except jsonschema.ValidationError as e:
        raise VisibilityError(f"respostas inválidas: {e.message}") from e
    return {a["pergunta"]: a for a in data}


def main(argv: list[str] | None = None, *, send: Send | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m plan_runner.ai_visibility",
                                description="Mede se a marca é mencionada e citada por assistentes de IA.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pm = sub.add_parser("medir", help="Gemini com pesquisa Google (simula sem --run)")
    pm.add_argument("painel", type=Path)
    pm.add_argument("--out", type=Path, required=True)
    pm.add_argument("--run", action="store_true", help="Chama a API (1 pedido por pergunta, máximo 25)")
    pm.add_argument("--model", default=None, help="Modelo Gemini (omissão: AI_VISIBILITY_MODEL ou o do worker)")
    pi = sub.add_parser("importar", help="Pontua respostas coladas de outro motor (sem API)")
    pi.add_argument("painel", type=Path)
    pi.add_argument("respostas", type=Path)
    pi.add_argument("--motor", required=True, help="ex.: chatgpt, perplexity, claude")
    pi.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        panel = load_panel(a.painel)
        if a.cmd == "importar":
            if not re.fullmatch(r"[a-z0-9_-]{2,30}", a.motor):
                raise VisibilityError("--motor: só letras minúsculas, números, _ e -")
            result = record(panel, score(panel, _load_answers(a.respostas)), engine=a.motor, out=a.out)
        else:
            from . import external_worker as ew

            model = a.model or os.environ.get("AI_VISIBILITY_MODEL") or ew.DEFAULT_MODEL
            n = len(panel["perguntas"])
            if not a.run:
                print(f"simulação: {n} perguntas ao {model} com pesquisa Google = {n} pedidos. "
                      "Nada foi enviado; corre com --run para medir.")
                for q in panel["perguntas"]:
                    print(f"  {q['id']}: {q['texto']}")
                return 0
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                raise VisibilityError("--run precisa de GEMINI_API_KEY no ambiente")
            answers = ask_gemini(panel, api_key=key, model=model, send=send or ew.httpx_transport)
            result = record(panel, score(panel, answers), engine="gemini", out=a.out)
    except (VisibilityError, OSError, yaml.YAMLError) as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 1
    s = result["resumo"]
    print(f"{result['motor']}: {s['medidas']}/{s['perguntas']} medidas · marca mencionada {s['marca']['mencionada_pct']}% "
          f"· citada {s['marca']['citada_pct']}% · resumo em {a.out / 'resumo.md'}")
    return 0 if s["medidas"] == s["perguntas"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
