"""O evento step_started regista a skill que o passo carrega (medir o uso real das skills).

Antes so tinha step_id/action: nao havia forma de saber que skills correm.
Contagem a partir dos runs:
    cat pilots/*/events.jsonl | jq -r 'select(.type=="step_started") | .payload.skill' | sort | uniq -c
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner.engine import resume_run, run_plan

STEPS = (
    "steps:\n"
    "  - {id: a, action: research, output_artifact: artifacts/a.md}\n"
    "  - {id: b, action: ux_flow, vertical: design, depends_on: [a], output_artifact: artifacts/b.md}\n"
    "  - id: hitl\n"
    "    action: plan_approve\n"
    "    depends_on: [b]\n"
    "    human_gate: {level: step, kind: confirmation, allow: [approve, reject]}\n"
    "    output_artifact: artifacts/hitl.json\n"
)


def _plan(tmp_path: Path) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text("id: uso\nobjective: x\n" + STEPS, encoding="utf-8")
    return p


def _skills(out: Path) -> dict[str, str | None]:
    evs = [json.loads(x) for x in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    return {e["payload"]["step_id"]: e["payload"].get("skill") for e in evs if e["type"] == "step_started"}


def test_native_regista_a_skill_de_cada_passo(tmp_path, tmp_run_dir):
    run_plan(_plan(tmp_path), mode="stub", out_dir=tmp_run_dir)
    assert _skills(tmp_run_dir) == {
        "a": "skills/marketing/research/SKILL.md",
        "b": "skills/design/ux_flow/SKILL.md",
        "hitl": None,  # gate humano: sem skill
    }


def test_resume_tambem_regista_a_skill(tmp_path, tmp_run_dir):
    plan = tmp_path / "plan.yaml"
    plan.write_text(
        "id: uso\nobjective: x\nsteps:\n"
        "  - id: hitl\n    action: plan_approve\n"
        "    human_gate: {level: step, kind: confirmation, allow: [approve, reject]}\n"
        "  - {id: depois, action: research, depends_on: [hitl], output_artifact: artifacts/d.md}\n",
        encoding="utf-8",
    )
    run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    assert resume_run(tmp_run_dir, "approve")["state"] == "done"
    assert _skills(tmp_run_dir)["depois"] == "skills/marketing/research/SKILL.md"


def test_langgraph_regista_a_skill(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    run_plan_langgraph(_plan(tmp_path), mode="stub", out_dir=tmp_run_dir)
    got = _skills(tmp_run_dir)
    assert got["a"] == "skills/marketing/research/SKILL.md"
    assert got["b"] == "skills/design/ux_flow/SKILL.md"
