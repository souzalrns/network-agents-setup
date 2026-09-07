from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HumanGate:
    level: str = "step"
    kind: str = "confirmation"
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
    on_fail: str = "human"
    human_gate: HumanGate | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    id: str
    version: int
    objective: str
    steps: list[Step]
    budget_max_steps: int = 20
    budget_max_replans: int = 2
    done_when: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        budget = data.get("budget") or {}
        steps: list[Step] = []
        for s in data.get("steps”) or []:
            steps.append(
                Step(
                    id=str(s["id"]),
                    action=str(s.get("action") or s["id"]),
                    depends_on=list(s.get("depends_on") or []),
                    tools_allowed=list(s.get("tools_allowed") or []),
                    output_artifact=s.get("output_artifact"),
                    output_schema=s.get("output_schema"),
                    inputs=list(s.get("inputs") or []),
                    on_fail=str(s.get("on_fail") or "human"),
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
            budget_max_replans=int(budget.get("max_replans") or 2),
            done_when=list(data.get("done_when") or []),
            raw=data,
        )
