"""Testes do engine legacy em --mode external + ramos de erro.

Cobre ramos do run_plan/resume_run que os testes de fluxo nao exercitam:
budget abort, external waiting, step failed, plan_done sem HITL.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import _run_cli, RUNNER_DIR


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def _run(out_dir, plan_path, mode="stub", engine="native"):
    return _run_cli(
        [
            "run", str(plan_path),
            "--engine", engine,
            "--mode", mode,
            "--out", str(out_dir),
        ],
        cwd=RUNNER_DIR,
    )


def _resume(out_dir, decision="approve"):
    return _run_cli(
        ["resume", str(out_dir), "--decision", decision],
        cwd=RUNNER_DIR,
    )


def _status(out_dir):
    return json.loads((out_dir / "status.json").read_text(encoding="utf-8"))


# ============================================================
# run_plan: budget abort
# ============================================================

def test_native_run_aborts_when_budget_exceeded(tmp_path):
    """Plano com 2 steps e budget=1 -> aborted_budget no segundo step."""
    plan = _write_plan(tmp_path, """
id: tiny
objective: teste budget
budget:
  max_steps: 1
steps:
  - id: a
    action: do_a
  - id: b
    action: do_b
    depends_on: [a]
""")
    out = tmp_path / "run"
    proc = _run(out, plan, mode="stub")
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"

    status = _status(out)
    assert status["state"] == "aborted_budget"
    # so o primeiro step correu
    assert status.get("completed") == ["a"]


# ============================================================
# run_plan: external waiting
# ============================================================

def test_native_external_waits_for_worker(tmp_path):
    """--mode external deve parar em waiting_external e criar pending_steps."""
    plan = _write_plan(tmp_path, """
id: ext
objective: teste external
steps:
  - id: prep
    action: prep
""")
    out = tmp_path / "run"
    proc = _run(out, plan, mode="external")
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"

    status = _status(out)
    assert status["state"] == "waiting_external"
    assert status["paused_at_step"] == "prep"

    pending = out / "pending_steps" / "prep"
    assert pending.exists()
    assert (pending / "request.json").exists()


# ============================================================
# run_plan: step failed (external ok=false)
# ============================================================

def test_native_external_step_fails(tmp_path):
    """result.json com ok=false -> state=failed."""
    plan = _write_plan(tmp_path, """
id: fail
objective: teste fail
steps:
  - id: prep
    action: prep
""")
    out = tmp_path / "run"

    # 1. Run external -> waiting
    _run(out, plan, mode="external")

    # 2. Escrever result.json com ok=false
    pending = out / "pending_steps" / "prep"
    (pending / "result.json").write_text(
        json.dumps({"ok": False, "detail": "boom"}),
        encoding="utf-8",
    )

    # 3. Resume -> deve marcar failed
    proc = _resume(out)
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"

    status = _status(out)
    assert status["state"] == "failed"
    # Nota: resume_run (L264-268) nao escreve status["failed_step"] nem
    # status["detail"] (so run_plan escreve). Validamos apenas o estado.


# ============================================================
# run_plan: plan_done sem HITL
# ============================================================

def test_native_run_completes_without_hitl(tmp_path):
    """Plano sem human_gate corre ate ao fim -> state=done."""
    plan = _write_plan(tmp_path, """
id: simple
objective: teste done
steps:
  - id: a
    action: do_a
  - id: b
    action: do_b
    depends_on: [a]
""")
    out = tmp_path / "run"
    proc = _run(out, plan, mode="stub")
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"

    status = _status(out)
    assert status["state"] == "done"
    assert status.get("completed") == ["a", "b"]
    assert status.get("current_step") is None


# ============================================================
# resume_run: external accumula e completa
# ============================================================

def test_native_resume_external_completes(tmp_path):
    """resume apos result.json preenchido -> done (sem HITL)."""
    plan = _write_plan(tmp_path, """
id: ext2
objective: teste resume external
steps:
  - id: prep
    action: prep
""")
    out = tmp_path / "run"

    # 1. Run external -> waiting
    _run(out, plan, mode="external")

    # 2. Preencher result.json
    pending = out / "pending_steps" / "prep"
    (pending / "result.json").write_text(
        json.dumps({"ok": True, "detail": "done"}),
        encoding="utf-8",
    )

    # 3. Resume -> deve completar
    proc = _resume(out)
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"

    status = _status(out)
    assert status["state"] == "done"
    assert "prep" in (status.get("completed") or [])


# ============================================================
# run sobre out_dir nao-resumivel -> PlanError
# ============================================================

def test_native_run_rejects_non_resumable_out_dir(tmp_path):
    """Se out_dir tem estado terminal (done), novo run deve falhar."""
    plan = _write_plan(tmp_path, """
id: reuse
objective: teste reuse
steps:
  - id: a
    action: do_a
""")
    out = tmp_path / "run"

    # 1. Primeiro run -> done
    _run(out, plan, mode="stub")
    assert _status(out)["state"] == "done"

    # 2. Segundo run sobre o mesmo out_dir -> PlanError
    proc = _run(out, plan, mode="stub")
    assert proc.returncode == 1, (
        f"esperado returncode 1, obtido {proc.returncode}. stderr={proc.stderr!r}"
    )
    assert "not empty and not resumable" in (proc.stderr or "") or \
           "not empty and not resumable" in (proc.stdout or "")
