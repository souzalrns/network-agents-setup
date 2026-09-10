"""Testes do engine legacy (--engine native).

O engine legacy (plan_runner/engine.py) corre quando se passa
--engine native (ou quando o LangGraph nao esta instalado). Por omissao
os testes usam --engine langgraph, deixando o legacy a 20% de cobertura.

Estes testes exercitam run_plan + resume_run + ramos do CLI.
"""
from __future__ import annotations

import json

from tests.conftest import RUNNER_DIR, _run_cli


def _run(out_dir, plan_path, mode="stub", engine="native"):
    return _run_cli(
        [
            "run",
            str(plan_path),
            "--engine", engine,
            "--mode", mode,
            "--out", str(out_dir),
        ],
        cwd=RUNNER_DIR,
    )


def _resume(out_dir, decision):
    return _run_cli(
        ["resume", str(out_dir), "--decision", decision],
        cwd=RUNNER_DIR,
    )


def _status(out_dir):
    return json.loads((out_dir / "status.json").read_text(encoding="utf-8"))


# ============================================================
# RUN --engine native
# ============================================================

def test_native_run_dry_run_returns_order(plan_path, tmp_run_dir):
    """--mode dry-run devolve order/actions sem escrever estado."""
    proc = _run(tmp_run_dir, plan_path, mode="dry-run")
    assert proc.returncode == 0, f"dry-run falhou: {proc.stderr}"

    result = json.loads(proc.stdout)
    assert result["mode"] == "dry-run"
    assert "order" in result and isinstance(result["order"], list)
    assert "actions" in result and isinstance(result["actions"], list)
    assert "hitl" in result["order"]

    # dry-run nao cria status.json
    assert not (tmp_run_dir / "status.json").exists()


def test_native_run_stub_pauses_at_hitl(plan_path, tmp_run_dir):
    """run --engine native --mode stub deve parar em paused_human_gate."""
    proc = _run(tmp_run_dir, plan_path, mode="stub")
    assert proc.returncode == 0, f"run native falhou: {proc.stderr}"

    status = _status(tmp_run_dir)
    assert status.get("state") == "paused_human_gate"
    assert status.get("paused_at_step") == "hitl"
    assert status.get("engine") in (None, "native", "")

    # artefactos esperados
    assert (tmp_run_dir / "plan.yaml").exists()
    assert (tmp_run_dir / "events.jsonl").exists()
    assert (tmp_run_dir / "HITL.md").exists()


def test_native_resume_approve_completes_plan(plan_path, tmp_run_dir):
    """resume approve no engine native deve levar a done."""
    _run(tmp_run_dir, plan_path, mode="stub")
    proc = _resume(tmp_run_dir, "approve")
    assert proc.returncode == 0, f"resume native falhou: {proc.stderr}"

    status = _status(tmp_run_dir)
    assert status.get("state") == "done"
    completed = status.get("completed") or []
    assert "hitl" in completed


def test_native_resume_reject_sets_rejected(plan_path, tmp_run_dir):
    """resume reject no engine native deve marcar rejected."""
    _run(tmp_run_dir, plan_path, mode="stub")
    proc = _resume(tmp_run_dir, "reject")
    assert proc.returncode == 0, f"resume native falhou: {proc.stderr}"

    status = _status(tmp_run_dir)
    assert status.get("state") == "rejected"


# ============================================================
# CLI — ramos nao cobertos pelos testes LangGraph
# ============================================================

def test_cli_compile_graph(plan_path):
    """compile-graph devolve o relatorio de waves."""
    proc = _run_cli(["compile-graph", str(plan_path)], cwd=RUNNER_DIR)
    assert proc.returncode == 0, f"compile-graph falhou: {proc.stderr}"

    result = json.loads(proc.stdout)
    # estrutura minima esperada (compile_report)
    assert isinstance(result, dict)


def test_cli_resume_payload_file_not_found(plan_path, tmp_run_dir):
    """--payload-file inexistente deve falhar com PlanError, nao traceback."""
    # Usar langgraph (default) para que o cli.py leia --payload-file.
    _run(tmp_run_dir, plan_path, mode="stub", engine="langgraph")

    proc = _run_cli(
        [
            "resume",
            str(tmp_run_dir),
            "--decision", "edit",
            "--payload-file", str(tmp_run_dir / "nao-existe.json"),
        ],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 1, f"esperado returncode 1, obtido {proc.returncode}"

    stderr = (proc.stderr or "") + (proc.stdout or "")
    assert "payload file not found" in stderr, (
        f"mensagem esperada em falta: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
