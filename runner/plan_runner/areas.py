"""Registo de áreas (config/areas.yaml): carregar e validar contra agents/.

E7 (docs/audit/PLANO-DE-ACAO.md §13.2): o CI falha se o YAML divergir dos
agentes reais. Fica no runner porque é aqui (núcleo Python, D1) que o router
hierárquico da D2 vai ler este ficheiro; a validação é a primeira peça dele.

Regras (do cabeçalho de config/areas.yaml):
  - agents[] e horizontals[] usam o `id:` do frontmatter de agents/**/*.agent.md;
  - cada agente aparece em exactamente uma lista agents[] (nenhum inalcançável);
  - router (D2, plan_runner/router.py): keywords[] normalizadas (minúsculas, sem
    acentos) e cada uma numa só área; `routing:` com limiares em ]0, 1] e uma
    fallback_area que exista; `budget` null ou {max_steps: int > 0}; `hitl` null
    ou "required"; `delegation` (opcional) auto | agent | plan.

CLI:  cd runner && python -m plan_runner.areas   (sai 1 e lista os erros)
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import yaml

from .skills import _frontmatter

AREAS_FILE = Path("config") / "areas.yaml"
DELEGATION = ("auto", "agent", "plan")
ROUTING_DEFAULTS = {"area_min_confidence": 0.6, "agent_min_confidence": 0.6, "fallback_area": "horizontal"}


def normalize(text: str) -> str:
    """Minúsculas e sem acentos (a mesma forma em que as keywords estão escritas)."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def agent_ids(repo_root: Path) -> tuple[dict[str, Path], list[str]]:
    """`id:` do frontmatter de cada agents/**/*.agent.md -> ficheiro.

    Devolve também os erros de ids em falta ou repetidos."""
    ids: dict[str, Path] = {}
    errors: list[str] = []
    for p in sorted((repo_root / "agents").glob("**/*.agent.md")):
        rel = p.relative_to(repo_root)
        aid = _frontmatter(p).get("id")
        if not isinstance(aid, str) or not aid:
            errors.append(f"{rel}: frontmatter sem `id:`")
        elif aid in ids:
            errors.append(f"{rel}: id `{aid}` repetido (já em {ids[aid].relative_to(repo_root)})")
        else:
            ids[aid] = p
    return ids, errors


def load_registry(repo_root: Path) -> dict:
    """Lê config/areas.yaml inteiro (areas + routing). Lança ValueError se inválido."""
    path = repo_root / AREAS_FILE
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ValueError(f"{AREAS_FILE}: não é YAML legível ({e})") from e
    if not isinstance(data, dict) or not isinstance(data.get("areas"), list) or not data["areas"]:
        raise ValueError(f"{AREAS_FILE}: falta a lista `areas:` (não vazia) no topo")
    return data


def load_areas(repo_root: Path) -> list[dict]:
    """Lê config/areas.yaml e devolve a lista `areas`. Lança ValueError se inválido."""
    return load_registry(repo_root)["areas"]


def routing_config(registry: dict) -> dict:
    """Bloco `routing:` com as omissões aplicadas."""
    raw = registry.get("routing")
    return {**ROUTING_DEFAULTS, **(raw if isinstance(raw, dict) else {})}


def _validate_router_fields(registry: dict, areas: list, errors: list[str]) -> None:
    area_ids = {a.get("id") for a in areas if isinstance(a, dict)}
    routing = registry.get("routing")
    if routing is not None and not isinstance(routing, dict):
        errors.append("`routing` tem de ser um objecto")
        routing = {}
    for key in ("area_min_confidence", "agent_min_confidence"):
        v = (routing or {}).get(key, ROUTING_DEFAULTS[key])
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 < v <= 1:
            errors.append(f"routing.{key} tem de ser um número em ]0, 1] (got {v!r})")
    fallback = (routing or {}).get("fallback_area", ROUTING_DEFAULTS["fallback_area"])
    if fallback not in area_ids:
        errors.append(f"routing.fallback_area `{fallback}` não é uma área declarada")

    seen_kw: dict[str, str] = {}
    for area in areas:
        if not isinstance(area, dict):
            continue
        aid = area.get("id")
        kws = area.get("keywords", [])
        if not isinstance(kws, list) or not all(isinstance(k, str) and k.strip() for k in kws):
            errors.append(f"área `{aid}`: `keywords` tem de ser uma lista de strings")
            kws = []
        for k in kws:
            if normalize(k).strip() != k:
                errors.append(f"área `{aid}`: keyword `{k}` tem de estar em minúsculas, sem acentos e sem espaços nas pontas")
            elif k in seen_kw and seen_kw[k] != aid:
                errors.append(f"keyword `{k}` está em mais de uma área: {seen_kw[k]}, {aid}")
            seen_kw.setdefault(k, aid)
        budget = area.get("budget")
        if budget is not None and not (
            isinstance(budget, dict)
            and isinstance(budget.get("max_steps"), int)
            and not isinstance(budget.get("max_steps"), bool)
            and budget["max_steps"] > 0
        ):
            errors.append(f"área `{aid}`: `budget` tem de ser null ou {{max_steps: inteiro > 0}}")
        if area.get("hitl") not in (None, "required"):
            errors.append(f"área `{aid}`: `hitl` tem de ser null ou required")
        if area.get("delegation", "auto") not in DELEGATION:
            errors.append(f"área `{aid}`: `delegation` tem de ser um de {', '.join(DELEGATION)}")


def _id_list(area_id: str, area: dict, key: str, errors: list[str]) -> list[str]:
    value = area.get(key)
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        errors.append(f"área `{area_id}`: `{key}` tem de ser uma lista de ids (pode ser [])")
        return []
    return value


def validate_areas(repo_root: Path) -> list[str]:
    """Todos os erros encontrados; lista vazia = válido."""
    try:
        registry = load_registry(repo_root)
    except ValueError as e:
        return [str(e)]
    areas = registry["areas"]

    known, errors = agent_ids(repo_root)
    where: dict[str, list[str]] = {}  # agent id -> áreas cujo agents[] o lista
    seen_areas: set[str] = set()

    for i, area in enumerate(areas):
        if not isinstance(area, dict):
            errors.append(f"areas[{i}]: tem de ser um objecto")
            continue
        area_id = area.get("id")
        if not isinstance(area_id, str) or not area_id:
            errors.append(f"areas[{i}]: falta `id`")
            area_id = f"areas[{i}]"
        elif area_id in seen_areas:
            errors.append(f"área `{area_id}`: id de área repetido")
        seen_areas.add(area_id)
        if not isinstance(area.get("description"), str) or not area["description"].strip():
            errors.append(f"área `{area_id}`: falta `description`")

        for aid in _id_list(area_id, area, "agents", errors):
            where.setdefault(aid, []).append(area_id)
            if aid not in known:
                errors.append(f"área `{area_id}`: agents[] refere `{aid}`, que não existe em agents/**/*.agent.md")
        for aid in _id_list(area_id, area, "horizontals", errors):
            if aid not in known:
                errors.append(f"área `{area_id}`: horizontals[] refere `{aid}`, que não existe em agents/**/*.agent.md")

    for aid, in_areas in sorted(where.items()):
        if len(in_areas) > 1:
            errors.append(f"agente `{aid}` está em agents[] de mais de uma área: {', '.join(in_areas)}")
    for aid, path in sorted(known.items()):
        if aid not in where:
            errors.append(
                f"agente órfão `{aid}` ({path.relative_to(repo_root)}): não está em agents[] de nenhuma área"
            )
    _validate_router_fields(registry, areas, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(argv[0]) if argv else Path(__file__).resolve().parents[2]
    errors = validate_areas(repo_root)
    if errors:
        print(f"✗ {AREAS_FILE} diverge dos agentes reais ({len(errors)} erro(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    areas = load_areas(repo_root)
    n_agents = sum(len(a.get("agents") or []) for a in areas)
    print(f"✓ {AREAS_FILE} válido: {len(areas)} áreas, {n_agents} agentes, todos existentes e sem órfãos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
