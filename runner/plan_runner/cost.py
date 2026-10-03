"""D6: custo em USD de um run, a partir do ledger de tokens (docs/ops/BUDGET.md).

O tecto `budget.max_cost_usd` usa os precos de config/model-prices.yaml. So
contam os precos confirmados (numeros >= 0): um modelo com preco `null`, ou
ausente, nao tem custo conhecido, e o worker recusa gastar com um tecto de
custo activo (falha fechada, antes da chamada).

Saida = tokens_total - tokens_in quando o total existe: inclui os tokens de
raciocinio, que o Gemini cobra como saida e que nao vem em tokens_out.
Linhas sem tokens (ex.: missing_usage, embeddings) contam 0, como no tecto de
tokens.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICES_PATH = REPO_ROOT / "config" / "model-prices.yaml"


class CostUnknown(Exception):
    """Um modelo usado (ou a usar) nao tem preco confirmado."""


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def _int(v: Any) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def load_prices(path: Path | None = None) -> dict[str, dict[str, float]]:
    """{modelo: {"in": USD por 1M, "out": USD por 1M}}, so com precos confirmados."""
    path = path or PRICES_PATH
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    prices: dict[str, dict[str, float]] = {}
    for name, p in (data.get("models") or {}).items():
        p = p or {}
        i, o = p.get("usd_per_1m_input"), p.get("usd_per_1m_output")
        if _num(i) and _num(o):
            prices[str(name)] = {"in": float(i), "out": float(o)}
    return prices


def row_cost_usd(row: dict[str, Any], prices: dict[str, dict[str, float]]) -> float:
    tokens_in = _int(row.get("tokens_in")) or 0
    total = _int(row.get("tokens_total"))
    tokens_out = (total - tokens_in) if total is not None else (_int(row.get("tokens_out")) or 0)
    if tokens_in <= 0 and tokens_out <= 0:
        return 0.0
    model = str(row.get("model"))
    if model not in prices:
        raise CostUnknown(model)
    p = prices[model]
    return (tokens_in * p["in"] + max(tokens_out, 0) * p["out"]) / 1_000_000


def ledger_cost_usd(ledger_path: Path, prices: dict[str, dict[str, float]]) -> float:
    """Custo ja gasto pelo run (soma das linhas do token_usage.jsonl local)."""
    if not ledger_path.is_file():
        return 0.0
    total = 0.0
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            total += row_cost_usd(row, prices)
    return total
