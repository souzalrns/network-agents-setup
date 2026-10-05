"""AU-22: campos de plano que o runner nao aplica + max_steps no engine langgraph."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner.engine import run_plan
from plan_runner.models import ignored_plan_fields

STEPS = (
    "steps:\n"
    "  - {id: a, action: research, output_artifact: artifacts/a.md}\n"
    "  - {id: b, action: internal_brief, depends_on: [a], output_artifact: artifacts/b.md}\n"
)


def _plan(tmp_path: Path, head: str = "", steps: str = STEPS) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text("id: campos\nobjective: x\n" + head + steps, encoding="utf-8")
    return p


def _events(out: Path, kind: str) -> list[dict]:
    lines = (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["type"] == kind]


def test_ignored_plan_fields_lista_cada_campo_declarado():
    data = {
        "knowledge_refs": ["docs/x.md"],
        "done_when": ["artifacts/a.md exists"],
        "budget": {"max_steps": 5, "max_replans": 1},
        "steps": [{"id": "a", "on_fail": "human"}, {"id": "b"}],
    }
    # P-10 = A: o done_when deixou de ser ignorado (verificado no fim do run, done_when.py)
    assert ignored_plan_fields(data) == ["knowledge_refs", "budget.max_replans", "steps[].on_fail"]
    assert ignored_plan_fields({"budget": {"max_steps": 5}, "steps": [{"id": "a"}]}) == []


def test_native_regista_os_campos_ignorados(tmp_path, tmp_run_dir):
    head = "knowledge_refs: [docs/x.md]\ndone_when: [artifacts/b.md exists]\n"
    status = run_plan(_plan(tmp_path, head), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "done"
    [ev] = _events(tmp_run_dir, "plan_fields_ignored")
    assert ev["payload"]["fields"] == ["knowledge_refs"]


def test_plano_sem_campos_mortos_nao_regista_nada(tmp_path, tmp_run_dir):
    run_plan(_plan(tmp_path), mode="stub", out_dir=tmp_run_dir)
    assert _events(tmp_run_dir, "plan_fields_ignored") == []


def test_planos_reais_declaram_campos_ignorados():
    """Os planos de exemplo usam on_fail: o evento existe para os runs reais (o done_when ja nao e ignorado)."""
    import yaml

    plan = Path(__file__).resolve().parents[2] / "docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml"
    fields = ignored_plan_fields(yaml.safe_load(plan.read_text(encoding="utf-8")))
    assert "steps[].on_fail" in fields and "done_when" not in fields


def test_langgraph_respeita_max_steps(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    status = run_plan_langgraph(_plan(tmp_path, "budget:\n  max_steps: 1\n"), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "aborted_budget" and status["completed"] == []
    assert _events(tmp_run_dir, "step_started") == []
    [ev] = _events(tmp_run_dir, "plan_aborted")
    assert ev["payload"] == {"reason": "max_steps", "engine": "langgraph", "steps": 2, "max_steps": 1}


def test_langgraph_dentro_do_max_steps_corre_normalmente(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    status = run_plan_langgraph(_plan(tmp_path, "budget:\n  max_steps: 2\n"), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "done"
