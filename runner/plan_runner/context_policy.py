"""B1-bis: politica de contexto do worker (o que entra no prompt de cada passo).

Medicao que motivou isto (B1 real, docs/ops/WORKER-EXTERNAL.md): dos 13 130
tokens do seo-article-demo, 41% eram prompt-base (AGENT+SKILL+grounding), 33%
artefactos injectados completos e 26% saidas. O modo `opt` (omissao) ataca as
duas primeiras partes sem tocar no conteudo das skills nem nas saidas:

1. Artefacto dual + injeccao por politica (pin + resumos):
   - cada input de um passo e `full` ou `summary`. Omissao: o ULTIMO input e o
     pin (vai completo -- e o alvo/o mais recente); os anteriores vao como
     resumo. Override no plano: `context: {full: [...], summary: [...]}`;
   - o resumo e gerado pelo passo que produz o artefacto, NA MESMA chamada
     (sem chamada extra), com schema fixo, a partir do proprio artefacto --
     nunca resumo de resumo -- e so quando algum passo seguinte o vai consumir
     como resumo;
   - sem resumo (o modelo nao o devolveu), o consumidor recebe o completo.
2. Grounding por area: `grounding: slim` em config/areas.yaml (marketing, docs,
   research) usa agents/_shared/grounding.slim.md; omissao `full` -- finance,
   legal e security nunca perdem a directiva completa.
3. Sem frontmatter YAML nos AGENT.md/SKILL.md (metadados), so a `description`
   numa linha. JSON injectado compacto (sem indentacao).

`PLAN_RUNNER_CONTEXT=legacy` repoe o prompt anterior byte a byte (A/B e rollback).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONTEXT_ENV = "PLAN_RUNNER_CONTEXT"
MODES = ("opt", "legacy")
SUMMARY_MARKER = "=====RESUMO====="
SUMMARY_KEYS = (
    ("factos", "Factos (com fonte)"),
    ("keywords", "Keywords"),
    ("estrutura", "Estrutura"),
    ("tom", "Tom"),
    ("restricoes", "Restricoes"),
    ("decisoes", "Decisoes"),
)
SUMMARY_WORDS = 200


def context_mode(explicit: str | None = None) -> str:
    mode = (explicit or os.environ.get(CONTEXT_ENV) or "opt").strip().lower()
    if mode not in MODES:
        raise ValueError(f"{CONTEXT_ENV} tem de ser um de {', '.join(MODES)} (got {mode!r})")
    return mode


def strip_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """(frontmatter, corpo). Sem frontmatter valido: ({}, texto inteiro)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}, text
    return (fm if isinstance(fm, dict) else {}), parts[2].lstrip("\n")


@lru_cache(maxsize=8)
def _areas(areas_file: str, mtime: float) -> tuple[dict, ...]:  # mtime invalida a cache
    data = yaml.safe_load(Path(areas_file).read_text(encoding="utf-8")) or {}
    return tuple(a for a in data.get("areas") or [] if isinstance(a, dict))


def grounding_for(repo_root: Path, agent_id: str | None) -> tuple[str, str]:
    """(nivel, texto). `slim` so se a area do agente o pedir E o ficheiro existir."""
    full = repo_root / "agents" / "_shared" / "grounding.directive.md"
    slim = repo_root / "agents" / "_shared" / "grounding.slim.md"
    level = "full"
    areas_file = repo_root / "config" / "areas.yaml"
    if agent_id and areas_file.is_file():
        for area in _areas(str(areas_file), areas_file.stat().st_mtime):
            if agent_id in (area.get("agents") or []):
                level = str(area.get("grounding") or "full")
                break
    if level == "slim" and slim.is_file():
        return "slim", slim.read_text(encoding="utf-8")
    return "full", full.read_text(encoding="utf-8") if full.is_file() else ""


def _step(plan_raw: dict, step_id: str) -> dict:
    for s in plan_raw.get("steps") or []:
        if isinstance(s, dict) and str(s.get("id")) == step_id:
            return s
    return {}


def step_inputs(plan_raw: dict, step_id: str, declared: list[str] | None = None) -> list[str]:
    """Inputs declarados; sem eles, os artefactos dos passos de que este depende."""
    inputs = list(declared if declared is not None else (_step(plan_raw, step_id).get("inputs") or []))
    if not inputs:
        for dep in _step(plan_raw, step_id).get("depends_on") or []:
            art = _step(plan_raw, str(dep)).get("output_artifact")
            if art:
                inputs.append(str(art))
    return inputs


def input_modes(plan_raw: dict, step_id: str, inputs: list[str]) -> dict[str, str]:
    """`full` | `summary` por input. Override do plano > pin no ultimo input."""
    ctx = _step(plan_raw, step_id).get("context") or {}
    full = set(ctx.get("full") or []) if isinstance(ctx, dict) else set()
    summ = set(ctx.get("summary") or []) if isinstance(ctx, dict) else set()
    modes = {}
    for i, rel in enumerate(inputs):
        if rel in full:
            modes[rel] = "full"
        elif rel in summ:
            modes[rel] = "summary"
        else:
            modes[rel] = "full" if i == len(inputs) - 1 else "summary"
    return modes


def needs_summary(plan_raw: dict, step_id: str, artifact: str | None) -> bool:
    """O artefacto deste passo vai ser consumido como resumo por algum outro passo?"""
    if not artifact:
        return False
    for s in plan_raw.get("steps") or []:
        sid = str(s.get("id")) if isinstance(s, dict) else ""
        if not sid or sid == step_id:
            continue
        ins = step_inputs(plan_raw, sid)
        if artifact in ins and input_modes(plan_raw, sid, ins)[artifact] == "summary":
            return True
    return False


def summary_path(out_root: Path, artifact: str) -> Path:
    """artifacts/02-seo-brief.json -> artifacts/02-seo-brief.summary.md"""
    p = out_root / artifact
    return p.with_name(f"{p.stem}.summary.md")


def compact_json(text: str) -> str:
    """JSON sem indentacao (mesmo conteudo, menos tokens). Texto nao-JSON fica igual."""
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
    except (json.JSONDecodeError, ValueError):
        return text


def summary_instruction(wants_json: bool) -> str:
    keys = ", ".join(k for k, _ in SUMMARY_KEYS)
    if wants_json:
        return (
            "Devolve UM objecto JSON com duas chaves: `artifact` (o objecto do artefacto, completo) e "
            f"`resumo` (objecto com as chaves {keys}; cada uma lista curta de strings, ou \"n/a\"). "
            f"O resumo (max. ~{SUMMARY_WORDS} palavras) serve os passos seguintes: so o que esta no "
            "artefacto, com as fontes dos factos; nada novo."
        )
    titles = " / ".join(f"### {t}" for _, t in SUMMARY_KEYS)
    return (
        f"Depois do artefacto, escreve uma linha so com `{SUMMARY_MARKER}` e a seguir um resumo para os "
        f"passos seguintes (max. ~{SUMMARY_WORDS} palavras) com estas seccoes, por esta ordem e so estas: "
        f"{titles}. Usa \"n/a\" numa seccao vazia. So o que esta no artefacto acima, com as fontes; nada novo."
    )


def render_summary(resumo: dict[str, Any]) -> str:
    lines = []
    for key, title in SUMMARY_KEYS:
        val = resumo.get(key, "n/a")
        items = val if isinstance(val, list) else [val]
        bullets = [f"- {x}" for x in items if str(x).strip()]
        lines += [f"### {title}", *(bullets or ["- n/a"]), ""]
    return "\n".join(lines).strip() + "\n"


def split_summary(content: Any, wants_json: bool) -> tuple[Any, str | None]:
    """(artefacto, resumo|None) a partir da resposta do modelo."""
    if wants_json:
        if isinstance(content, dict) and set(content) >= {"artifact", "resumo"} and isinstance(content["resumo"], dict):
            return content["artifact"], render_summary(content["resumo"])
        return content, None
    text = str(content)
    marker = f"\n{SUMMARY_MARKER}"
    if marker in "\n" + text:
        body, _, summ = ("\n" + text).partition(marker)
        summ = summ.strip()
        return body.strip() + "\n", (summ + "\n") if summ else None
    return text, None
