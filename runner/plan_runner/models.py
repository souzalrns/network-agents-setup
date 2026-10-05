from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HumanGate:
    level: str = "step"
    kind: str = "confirmation"
    # SEC-2d falso positivo: e uma lambda em default_factory, nao um return solto.
    # nosemgrep: return-not-in-function
    allow: list[str] = field(default_factory=lambda: ["approve", "reject"])

    @classmethod
    def from_raw(cls, raw: Any) -> HumanGate | None:
        if raw is None or raw is False:
            return None
        if raw is True:
            return cls()
        if isinstance(raw, dict):
            return cls(
                level=str(raw.get("level", "step")),
                kind=str(raw.get("kind", "confirmation")),
                allow=list(raw.get("allow") or ["approve", "reject"]),
            )
        return cls()


@dataclass
class Step:
    id: str
    action: str
    depends_on: list[str] = field(default_factory=list)
    tools_allowed: list[str] = field(default_factory=list)
    output_artifact: str | None = None
    output_schema: str | None = None
    inputs: list[str] = field(default_factory=list)
    human_gate: HumanGate | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    id: str
    version: int
    objective: str
    steps: list[Step]
    budget_max_steps: int = 20
    done_when: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        budget = data.get("budget") or {}
        steps: list[Step] = []
        for s in data.get("steps") or []:
            steps.append(
                Step(
                    id=str(s["id"]),
                    action=str(s.get("action") or s["id"]),
                    depends_on=list(s.get("depends_on") or []),
                    tools_allowed=list(s.get("tools_allowed") or []),
                    output_artifact=s.get("output_artifact"),
                    output_schema=s.get("output_schema"),
                    inputs=list(s.get("inputs") or []),
                    human_gate=HumanGate.from_raw(s.get("human_gate")),
                    raw=s,
                )
            )
        return cls(
            id=str(data.get("id") or "plan"),
            version=int(data.get("version") or 1),
            objective=str(data.get("objective") or ""),
            steps=steps,
            budget_max_steps=int(budget.get("max_steps") or 20),
            done_when=list(data.get("done_when") or []),
            raw=data,
        )


# AU-22: campos que os planos declaram mas que o runner NAO aplica (AUDIT-2 Y7-Y9).
# O motor regista-os no evento `plan_fields_ignored`, para o plano nao prometer
# garantias que nao existem. O L5 entra pelo bloco `knowledge:` do passo (S9),
# nao pelo `knowledge_refs` (decisao A do EXECUTION-PLAN, AU-22). O `done_when`
# saiu desta lista: e verificado no fim do run (done_when.py; P-10 = A).
# O `budget.max_replans` e o `steps[].on_fail` sairam do schema e dos planos do
# repo (P-10 = A; fora ate ao F3): um passo que falha para o run em `failed`. Ficam
# aqui para um plano antigo que ainda os declare continuar a ser assinalado.
IGNORED_PLAN_FIELDS = ("knowledge_refs", "budget.max_replans", "steps[].on_fail")


def ignored_plan_fields(data: dict[str, Any]) -> list[str]:
    """Campos de IGNORED_PLAN_FIELDS que o plano (YAML ja lido) declara."""
    found = [k for k in ("knowledge_refs",) if data.get(k)]
    if "max_replans" in (data.get("budget") or {}):
        found.append("budget.max_replans")
    if any(isinstance(s, dict) and "on_fail" in s for s in data.get("steps") or []):
        found.append("steps[].on_fail")
    return found
