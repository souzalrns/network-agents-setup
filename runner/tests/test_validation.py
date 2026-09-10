"""Testes de validacao de planos (graph.py) e HumanGate (models.py)."""
from __future__ import annotations

from pathlib import Path

import pytest

from plan_runner.engine import load_plan
from plan_runner.graph import PlanError, topo_order
from plan_runner.models import HumanGate, Plan, Step


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(body, encoding="utf-8")
    return p


# ============================================================
# graph.py: validacao
# ============================================================

def test_validate_step_ids_must_be_unique(tmp_path):
    p = _write_plan(tmp_path, """
id: dup
objective: teste
steps:
  - id: a
    action: x
  - id: a
    action: y
""")
    with pytest.raises(PlanError, match="step ids must be unique"):
        load_plan(p)


def test_validate_unknown_dependency(tmp_path):
    p = _write_plan(tmp_path, """
id: deps
objective: teste
steps:
  - id: a
    action: x
    depends_on: [b]
""")
    with pytest.raises(PlanError, match="depends on unknown"):
        load_plan(p)


def test_validate_cycle_detected(tmp_path):
    p = _write_plan(tmp_path, """
id: cycle
objective: teste
steps:
  - id: a
    action: x
    depends_on: [b]
  - id: b
    action: y
    depends_on: [a]
""")
    with pytest.raises(PlanError, match="cycle detected"):
        load_plan(p)


# ============================================================
# models.py: HumanGate.from_raw branches
# ============================================================

def test_human_gate_from_raw_true():
    g = HumanGate.from_raw(True)
    assert g is not None
    assert g.level == "step"
    assert g.kind == "confirmation"


def test_human_gate_from_raw_none_and_false():
    assert HumanGate.from_raw(None) is None
    assert HumanGate.from_raw(False) is None


def test_human_gate_from_raw_dict():
    g = HumanGate.from_raw({"level": "plan", "kind": "approval", "allow": ["approve"]})
    assert g is not None
    assert g.level == "plan"
    assert g.kind == "approval"
    assert g.allow == ["approve"]


def test_human_gate_from_raw_unknown_value():
    # Valor desconhecido (ex: string) -> devolve HumanGate() default
    g = HumanGate.from_raw("sim")
    assert g is not None
    assert g.level == "step"
