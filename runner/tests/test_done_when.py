"""AU-22 / P-10 = A: o done_when e verificado no fim do run (plan_runner/done_when.py).

Formas verificaveis: `<caminho> exists` e `human_gate_resolved on <passo>`.
Uma condicao noutra forma gera `done_when_unverifiable` e nao falha o run.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner.engine import resume_run, run_plan

REPO = Path(__file__).resolve().parents[2]

STEPS = (
    "steps:\n"
    "  - {id: a, action: research, output_artifact: artifacts/a.md}\n"
    "  - {id: b, action: internal_brief, depends_on: [a], output_artifact: artifacts/b.md}\n"
)

GATE_STEPS = STEPS + (
    "  - id: hitl\n"
    "    action: plan_approve\n"
    "    depends_on: [b]\n"
    "    human_gate: {level: step, kind: confirmation, allow: [approve, reject]}\n"
    "    output_artifact: artifacts/hitl.json\n"
)


def _plan(tmp_path: Path, done_when: list[str], steps: str = STEPS) -> Path:
    p = tmp_path / "plan.yaml"
    dw = "done_when:\n" + "".join(f"  - {json.dumps(c)}\n" for c in done_when)
    p.write_text("id: dw\nobjective: x\n" + steps + dw, encoding="utf-8")
    return p


def _events(out: Path, kind: str) -> list[dict]:
    lines = (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["type"] == kind]


# ---- forma 1: "<caminho> exists"


def test_exists_cumprido_termina_em_done(tmp_path, tmp_run_dir):
    status = run_plan(_plan(tmp_path, ["artifacts/b.md exists"]), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "done"
    [ev] = _events(tmp_run_dir, "done_when_checked")
    assert ev["payload"] == {"passed": [{"kind": "file_exists", "target": "artifacts/b.md"}], "failed": [], "unverifiable": []}
    assert len(_events(tmp_run_dir, "plan_done")) == 1


def test_exists_em_falta_falha_o_run_com_o_motivo(tmp_path, tmp_run_dir):
    status = run_plan(_plan(tmp_path, ["artifacts/zz.md exists"]), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "failed"
    assert status["detail"] == "done_when"
    assert status["done_when_failed"] == [
        {"kind": "file_exists", "target": "artifacts/zz.md", "condition": "artifacts/zz.md exists", "reason": "ficheiro em falta"}
    ]
    assert _events(tmp_run_dir, "plan_done") == []
    [ev] = _events(tmp_run_dir, "done_when_failed")
    assert ev["payload"]["failed"][0]["condition"] == "artifacts/zz.md exists"
    # o status gravado em disco e o mesmo que o devolvido
    assert json.loads((tmp_run_dir / "status.json").read_text(encoding="utf-8"))["state"] == "failed"


def test_exists_fora_do_directorio_do_run_falha(tmp_path, tmp_run_dir):
    status = run_plan(_plan(tmp_path, ["../plan.yaml exists"]), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "failed"
    assert status["done_when_failed"][0]["reason"] == "caminho fora do directorio do run"


# ---- forma 2: "human_gate_resolved on <passo>"


def test_gate_resolvido_termina_em_done(tmp_path, tmp_run_dir):
    plan = _plan(tmp_path, ["human_gate_resolved on hitl", "artifacts/b.md exists"], GATE_STEPS)
    assert run_plan(plan, mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    status = resume_run(tmp_run_dir, "approve")
    assert status["state"] == "done"
    [ev] = _events(tmp_run_dir, "done_when_checked")
    assert ev["payload"]["passed"] == [
        {"kind": "gate_resolved", "target": "hitl"},
        {"kind": "file_exists", "target": "artifacts/b.md"},
    ]


def test_gate_nao_resolvido_falha_o_run(tmp_path, tmp_run_dir):
    plan = _plan(tmp_path, ["human_gate_resolved on hitl_publish"], GATE_STEPS)
    run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    status = resume_run(tmp_run_dir, "approve")
    assert status["state"] == "failed"
    assert status["done_when_failed"] == [
        {"kind": "gate_resolved", "target": "hitl_publish", "condition": "human_gate_resolved on hitl_publish", "reason": "gate nao resolvido"}
    ]
    assert "paused_at_step" not in status
    assert _events(tmp_run_dir, "plan_done") == []


def test_condicoes_cumpridas_nao_repetem_o_texto_do_gate_no_events(tmp_path, tmp_run_dir):
    """O test_langgraph_flow conta linhas com o texto `human_gate_resolved`: so o evento do gate o pode ter."""
    plan = _plan(tmp_path, ["human_gate_resolved on hitl"], GATE_STEPS)
    run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    resume_run(tmp_run_dir, "approve")
    linhas = [x for x in (tmp_run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if "human_gate_resolved" in x]
    assert [json.loads(x)["type"] for x in linhas] == ["human_gate_resolved"]


# ---- forma nao interpretavel: evento, sem falhar


def test_condicao_nao_interpretavel_gera_evento_e_nao_falha(tmp_path, tmp_run_dir):
    cond = "no ad_account_mutation without approve"
    status = run_plan(_plan(tmp_path, [cond, "artifacts/b.md exists"]), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "done"
    [ev] = _events(tmp_run_dir, "done_when_unverifiable")
    assert ev["payload"] == {"condition": cond, "item": "AU-22b"}
    [chk] = _events(tmp_run_dir, "done_when_checked")
    assert chk["payload"]["unverifiable"] == [cond] and chk["payload"]["failed"] == []


def test_plano_sem_done_when_nao_regista_nada(tmp_path, tmp_run_dir):
    p = tmp_path / "plan.yaml"
    p.write_text("id: dw\nobjective: x\n" + STEPS, encoding="utf-8")
    assert run_plan(p, mode="stub", out_dir=tmp_run_dir)["state"] == "done"
    assert _events(tmp_run_dir, "done_when_checked") == []


def test_paid_pack_real_marca_a_condicao_livre_como_nao_verificavel(tmp_path):
    """O unico plano com uma condicao em linguagem livre (AU-22b)."""
    import yaml

    from plan_runner.done_when import evaluate
    from plan_runner.events import EventLog

    data = yaml.safe_load((REPO / "docs/orchestration/marketing/templates/paid-pack.plan.yaml").read_text(encoding="utf-8"))
    r = evaluate(tmp_path, data["done_when"], EventLog(tmp_path / "events.jsonl"), "run_x")
    assert r["unverifiable"] == ["no ad_account_mutation without approve"]


# ---- engine langgraph (mesma verificacao)


def test_langgraph_exists_em_falta_falha(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    status = run_plan_langgraph(_plan(tmp_path, ["artifacts/zz.md exists"]), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "failed" and status["detail"] == "done_when"
    assert _events(tmp_run_dir, "plan_done") == []


def test_langgraph_cumprido_e_nao_interpretavel_termina_em_done(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    plan = _plan(tmp_path, ["artifacts/b.md exists", "no ad_account_mutation without approve"])
    status = run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "done"
    assert len(_events(tmp_run_dir, "done_when_unverifiable")) == 1


def test_langgraph_gate_resolvido_no_resume_termina_em_done(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph

    plan = _plan(tmp_path, ["human_gate_resolved on hitl"], GATE_STEPS)
    assert run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    status = resume_plan_langgraph(tmp_run_dir, "approve")
    assert status["state"] == "done"
    [ev] = _events(tmp_run_dir, "done_when_checked")
    assert ev["payload"]["passed"] == [{"kind": "gate_resolved", "target": "hitl"}]


def test_langgraph_gate_nao_resolvido_no_resume_falha(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph

    plan = _plan(tmp_path, ["human_gate_resolved on outro_gate"], GATE_STEPS)
    run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)
    status = resume_plan_langgraph(tmp_run_dir, "approve")
    assert status["state"] == "failed" and status["detail"] == "done_when"
