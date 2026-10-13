"""D6: custo em USD de um run, a partir do ledger de tokens (docs/ops/BUDGET.md).

O tecto `budget.max_cost_usd` usa os precos de config/model-prices.yaml. So
contam os precos confirmados (numeros >= 0): um modelo com preco `null`, ou
ausente, nao tem custo conhecido, e o worker recusa gastar com um tecto de
custo activo (falha fechada, antes da chamada).

Saida = tokens_total - tokens_in quando o total existe: inclui os tokens de
raciocinio, que o Gemini cobra como saida e que nao vem em tokens_out.
Linhas sem tokens (ex.: missing_usage, embeddings) contam 0, como no tecto de
tokens.

O motor (custo por linha, soma do ledger, falha fechada em preco desconhecido) vem
do pacote publicado `tokenwright` (PyPI, extraido de oss/tokenwright; zero
dependencias). Devolvido em 2026-10-13 (flywheel,
docs/initiatives/REPO-EVAL-PLAYBOOK.md). Este modulo fica como a cola do runner:
le o `config/model-prices.yaml` em YAML e e chamado pelo `external_worker`; o
`token_projection.py` NAO foi extraido (e exploratorio e acoplado).
"""
from __future__ import annotations

from pathlib import Path

import yaml
from tokenwright import CostUnknown, Prices, ledger_cost_usd, prices_from_mapping, row_cost_usd

__all__ = ["PRICES_PATH", "CostUnknown", "ledger_cost_usd", "load_prices", "row_cost_usd"]

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICES_PATH = REPO_ROOT / "config" / "model-prices.yaml"


def load_prices(path: Path | None = None) -> Prices:
    """{modelo: {"in": USD por 1M, "out": USD por 1M}}, so com precos confirmados."""
    path = path or PRICES_PATH
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return prices_from_mapping(data.get("models") or {})
