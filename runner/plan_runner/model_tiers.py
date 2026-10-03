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


class ModelTierError(ValueError):
    """`model_tier` desconhecido ou config invalida."""


def load_tiers(path: Path | None = None) -> dict[str, str | None]:
    path = path or TIERS_PATH
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tiers = data.get("tiers") or {}
    out: dict[str, str | None] = {}
    for name, model in tiers.items():
        if name not in TIERS:
            raise ModelTierError(f"{path.name}: tier {name!r} desconhecido (validos: {', '.join(TIERS)})")
        if model is not None and (not isinstance(model, str) or not model.strip()):
            raise ModelTierError(f"{path.name}: o modelo do tier {name!r} tem de ser texto ou null")
        out[name] = model.strip() if isinstance(model, str) else None
    return out


def resolve_model(step: dict[str, Any] | None, default: str, path: Path | None = None) -> tuple[str, str | None]:
    """(modelo, tier). Sem `model_tier` no passo: (default, None)."""
    tier = (step or {}).get("model_tier")
    if tier is None:
        return default, None
    if tier not in TIERS:
        raise ModelTierError(f"model_tier {tier!r} desconhecido (validos: {', '.join(TIERS)})")
    return load_tiers(path).get(tier) or default, tier
