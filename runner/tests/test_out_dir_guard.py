"""Testes do guard _validate_out_dir (C2).

Prova que --out fora de <repo>/pilots/ falha com PlanError explicito,
em vez de deixar o modo external correr com repo_root errado.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT, RUNNER_DIR, PLAN_PATH, _run_cli


def test_run_rejects_out_outside_pilots(tmp_path):
    """--out fora de pilots/ -> returncode 1 com mensagem clara."""
    out = tmp_path / "run"  # fora do repo
    proc = _run_cli(
        ["run", str(PLAN_PATH), "--engine", "native", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 1, (
        f"esperado returncode 1, obtido {proc.returncode}. stdout={proc.stdout!r}"
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "--out must be inside" in combined, (
        f"mensagem esperada em falta: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "pilots" in combined
    # Confirma que nao escreveu nada no out rejeitado
    assert not (out / "status.json").exists()
    assert not (out / "plan.yaml").exists()


def test_run_rejects_out_outside_pilots_langgraph(tmp_path):
    """Mesmo guard aplica-se ao engine langgraph (C2 simetrico)."""
    out = tmp_path / "run"
    proc = _run_cli(
        ["run", str(PLAN_PATH), "--engine", "langgraph", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 1, (
        f"esperado returncode 1, obtido {proc.returncode}. stdout={proc.stdout!r}"
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "--out must be inside" in combined


def test_run_accepts_out_inside_pilots(tmp_run_dir):
    """--out dentro de pilots/ (fixture) -> corre normalmente."""
    proc = _run_cli(
        ["run", str(PLAN_PATH), "--engine", "native", "--mode", "stub", "--out", str(tmp_run_dir)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"
    assert (tmp_run_dir / "status.json").exists()


def test_resume_rejects_out_outside_pilots(tmp_path):
    """resume fora de pilots/ -> returncode 1."""
    # Cria um run valido primeiro (dentro de pilots/)
    from uuid import uuid4
    valid_out = REPO_ROOT / "pilots" / f"_pytest_resume_{uuid4().hex[:8]}"
    try:
        valid_out.mkdir(parents=True, exist_ok=True)
        proc_run = _run_cli(
            ["run", str(PLAN_PATH), "--engine", "native", "--mode", "stub", "--out", str(valid_out)],
            cwd=RUNNER_DIR,
        )
        assert proc_run.returncode == 0, f"setup run falhou: {proc_run.stderr}"

        # Agora tenta resume com out fora de pilots/
        invalid_out = tmp_path / "run"
        proc = _run_cli(
            ["resume", str(invalid_out), "--decision", "approve"],
            cwd=RUNNER_DIR,
        )
        assert proc.returncode == 1
        combined = (proc.stdout or "") + (proc.stderr or "")
        assert "--out must be inside" in combined, (
            f"mensagem esperada em falta: stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    finally:
        import shutil
        shutil.rmtree(valid_out, ignore_errors=True)
