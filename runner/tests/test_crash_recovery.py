"""Testes de crash recovery do motor LangGraph.

Cobre os 3 cenarios validados manualmente:
1. Processo morre a meio com state="running" -> resume retoma
2. Crash a meio da wave -> completed e preservado
3. status.json corrompido -> erro claro, nao JSONDecodeError cru
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _corrupt_status(status_file: Path) -> None:
    """Simula crash: reescreve status.json com state='running'."""
    status = json.loads(status_file.read_text(encoding="utf-8"))
    status["state"] = "running"
    status_file.write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ============================================================
# CENARIO 1: crash com state="running" -> resume retoma
# ============================================================

def test_crash_recovery_running_state_resumes(run_plan, resume_plan, tmp_run_dir: Path):
    """Crash apos run --mode external deixa state=running; resume deve retomar."""
    proc, status = run_plan(tmp_run_dir, mode="external")
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"
    assert status.get("state") == "waiting_external"

    status_file = tmp_run_dir / "status.json"
    _corrupt_status(status_file)

    proc, status = resume_plan(tmp_run_dir, "approve")
    assert proc.returncode == 0, (
        f"resume apos crash falhou: stderr={proc.stderr!r}"
    )

    final_state = status.get("state")
    assert final_state in ("waiting_external", "paused_human_gate", "done"), (
        f"Estado final inesperado apos crash recovery: {final_state!r}"
    )

    events_file = tmp_run_dir / "events.jsonl"
    assert events_file.exists(), "events.jsonl nao existe"
    lines = events_file.read_text(encoding="utf-8").splitlines()
    tipos = [json.loads(l)["type"] for l in lines if l.strip()]
    assert "resume_after_interrupt" in tipos, (
        f"evento resume_after_interrupt em falta. Tipos: {tipos}"
    )


# ============================================================
# CENARIO 2: crash a meio da wave -> completed preservado
# ============================================================

def test_crash_recovery_preserves_completed(
    run_plan, resume_plan, write_result_json, tmp_run_dir: Path
):
    """Crash apos prepare concluido deve preservar 'prepare' em completed."""
    proc, status = run_plan(tmp_run_dir, mode="external")
    assert status.get("state") == "waiting_external"

    write_result_json(tmp_run_dir, "prepare")
    proc, status = resume_plan(tmp_run_dir, "approve")
    assert "prepare" in (status.get("completed") or []), (
        f"prepare nao esta em completed antes do crash: {status.get('completed')}"
    )

    status_file = tmp_run_dir / "status.json"
    _corrupt_status(status_file)

    proc, status = resume_plan(tmp_run_dir, "approve")
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"

    completed = status.get("completed") or []
    assert "prepare" in completed, (
        f"crash recovery perdeu 'prepare' de completed: {completed}"
    )


# ============================================================
# CENARIO 3: status.json corrompido -> erro claro
# ============================================================

def test_crash_recovery_corrupt_status_json(run_plan, tmp_run_dir: Path):
    """status.json corrompido nao pode causar JSONDecodeError cru."""
    from tests.conftest import _run_cli, RUNNER_DIR

    proc, status = run_plan(tmp_run_dir, mode="external")
    assert status.get("state") == "waiting_external"

    status_file = tmp_run_dir / "status.json"
    status_file.write_text("{ isto nao e json valido", encoding="utf-8")

    # Correr resume diretamente (sem passar pela fixture, que faria json.loads)
    proc = _run_cli(
        ["resume", str(tmp_run_dir), "--decision", "approve"],
        cwd=RUNNER_DIR,
    )

    assert proc.returncode != 0, (
        f"resume devia falhar com status.json corrompido. "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )

    stderr = proc.stderr or ""
    assert "JSONDecodeError" not in stderr or "PlanError" in stderr, (
        f"JSONDecodeError cru vazou para o utilizador: {stderr!r}"
    )
