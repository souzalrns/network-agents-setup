"""D5: `model_tier` de um passo -> modelo (config/model-tiers.yaml).

O `model_tier` (planner | executor | verifier) vem do Plan.schema.json e ate ao
D5 nenhum codigo o lia. Agora o worker le-o do passo e resolve o modelo pela
config. Um tier mapeado para `null` (omissao) usa o modelo normal do worker
(AGENT_MODEL ou DEFAULT_MODEL): sem config, nada muda. Um tier desconhecido e
erro (falha antes de chamar o modelo).

Alternativa registada (AUDIT-EVALUATION §4): LiteLLM Router por tier. Fica para
quando houver mais de um provider; e uma dependencia nova (decisao do DEV).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TIERS_PATH = REPO_ROOT / "config" / "model-tiers.yaml"
TIERS = ("planner", "executor", "verifier")
COMPLEXITY = ("C1", "C2", "C3", "C4")  # sinal de complexidade da planwright (export)


class ModelTierError(ValueError):
    """`model_tier` desconhecido ou config invalida."""


def _load_map(section: str, valid: tuple[str, ...], path: Path | None = None) -> dict[str, str | None]:
    path = path or TIERS_PATH
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, str | None] = {}
    for name, model in (data.get(section) or {}).items():
        if name not in valid:
            raise ModelTierError(f"{path.name}: {section} {name!r} desconhecido (validos: {', '.join(valid)})")
        if model is not None and (not isinstance(model, str) or not model.strip()):
            raise ModelTierError(f"{path.name}: o modelo de {name!r} tem de ser texto ou null")
        out[name] = model.strip() if isinstance(model, str) else None
    return out


def load_tiers(path: Path | None = None) -> dict[str, str | None]:
    return _load_map("tiers", TIERS, path)


def load_complexity(path: Path | None = None) -> dict[str, str | None]:
    """C1..C4 -> modelo (config/model-tiers.yaml, seccao `complexity`). Vazio = sem config."""
    return _load_map("complexity", COMPLEXITY, path)


def resolve_model(
    step: dict[str, Any] | None,
    default: str,
    path: Path | None = None,
    *,
    complexity: str | None = None,
) -> tuple[str, str | None]:
    """(modelo, tier). Precedencia: `model_tier` do passo (papel) > sinal `complexity` > default.

    O `model_tier` manda sempre: com ele, a complexidade e ignorada (papel e autoridade).
    Sem `model_tier`, um sinal `complexity` (C1..C4) que a config mapeie escolhe o modelo
    (cheap->expensive); um sinal desconhecido ou sem mapa cai no default -- nunca parte o run,
    porque a complexidade informa, nao decide sozinha. Devolve tier=None quando nao ha papel.
    """
    tier = (step or {}).get("model_tier")
    if tier is not None:
        if tier not in TIERS:
            raise ModelTierError(f"model_tier {tier!r} desconhecido (validos: {', '.join(TIERS)})")
        return load_tiers(path).get(tier) or default, tier
    if complexity is not None:
        model = load_complexity(path).get(str(complexity))
        if model:
            return model, None
    return default, None
