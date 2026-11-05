"""Planos de teste que cumprem config/plan-policy.yaml (M-008).

Os testes do motor (orçamento, tools, done_when, workers...) usam acções de marketing como passos
de exemplo. Desde o M-008 o motor recusa um plano de marketing sem `delivery`, sem
`budget.max_steps` e sem `knowledge:` em cada passo. Este helper acrescenta só o que falta, com os
valores que mantêm o comportamento antigo:
- `delivery: internal` (os testes não publicam nada);
- `budget.max_steps: 20` (o valor por omissão de antes);
- em cada passo de marketing sem `knowledge:`, `{kb: marketing, query: "<acção>: plano de teste"}`.

Não desliga nenhuma regra: o plano que sai daqui passa pelas mesmas verificações de qualquer outro.
"""
from __future__ import annotations

from typing import Any

import yaml


def politica_dict(plan: dict[str, Any]) -> dict[str, Any]:
    out = dict(plan)
    out.setdefault("delivery", "internal")
    budget = dict(out.get("budget") or {})
    budget.setdefault("max_steps", 20)
    out["budget"] = budget
    steps = []
    for s in out.get("steps") or []:
        s = dict(s)
        gate = bool(s.get("human_gate")) or s.get("action") == "plan_approve"
        marketing = (s.get("vertical") or "marketing") == "marketing"
        if not gate and marketing and "knowledge" not in s:
            s["knowledge"] = {"kb": "marketing", "query": f"{s.get('action') or s.get('id')}: plano de teste"}
        steps.append(s)
    out["steps"] = steps
    return out


def politica(plan_yaml: str) -> str:
    """O mesmo plano (YAML), com os campos que o motor exige e que faltavam."""
    data = yaml.safe_load(plan_yaml)
    return yaml.safe_dump(politica_dict(data), allow_unicode=True, sort_keys=False)
