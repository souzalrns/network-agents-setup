"""P-18 = C / E-003: o plano real de engenharia (ship_gate) resolve os agentes certos.

O ship-parallel.plan.yaml continua a ser o exemplo do motor (fixture de
conftest.py e test_real_plans.py, sem alteracoes); este e o plano de dominio.
O guarda do AU-32 (test_skills.py) cobre-o por estar fora de marketing/.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from plan_runner.engine import resume_run, run_plan
from plan_runner.skills import resolve_agent_path, resolve_skill_path

REPO = Path(__file__).resolve().parents[2]
PLAN = REPO / "docs/orchestration/engenharia/templates/ship-gate.plan.yaml"

ESPERADO = {
    "code_review": ("agents/engenharia/revisor-codigo.agent.md", "skills/claude/code-review-and-quality/SKILL.md"),
    "security_review": ("agents/meta/security_auditor.agent.md", "skills/meta/security-audit/SKILL.md"),
    "test_review": ("agents/engenharia/guia-tdd.agent.md", "skills/claude/test-driven-development/SKILL.md"),
}


def test_cada_review_resolve_o_agente_e_a_skill_de_engenharia():
    steps = {s["id"]: s for s in yaml.safe_load(PLAN.read_text(encoding="utf-8"))["steps"]}
    for sid, (agent, skill) in ESPERADO.items():
        step = steps[sid]
        a = resolve_agent_path(REPO, step["action"], step["vertical"])
        k = resolve_skill_path(REPO, step["action"], step["vertical"])
        assert a is not None and a.relative_to(REPO).as_posix() == agent, sid
        assert k is not None and k.relative_to(REPO).as_posix() == skill, sid


def test_os_3_reviews_correm_em_paralelo_antes_do_gate():
    steps = yaml.safe_load(PLAN.read_text(encoding="utf-8"))["steps"]
    reviews = [s for s in steps if not s.get("human_gate")]
    assert {s["id"] for s in reviews} == set(ESPERADO)
    assert all(not s.get("depends_on") for s in reviews)
    [gate] = [s for s in steps if s.get("human_gate")]
    assert set(gate["depends_on"]) == set(ESPERADO)


def test_corre_em_stub_e_o_done_when_passa(tmp_run_dir):
    assert run_plan(PLAN, mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    status = resume_run(tmp_run_dir, "approve")
    assert status["state"] == "done"
    events = [json.loads(x) for x in (tmp_run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    [chk] = [e for e in events if e["type"] == "done_when_checked"]
    assert chk["payload"]["failed"] == [] and chk["payload"]["unverifiable"] == []
    assert len(chk["payload"]["passed"]) == 4
