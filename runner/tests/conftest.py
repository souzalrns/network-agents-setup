"""Fixtures partilhadas para os testes do runner.

Cada teste corre num diretorio temporario isolado.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# Paths base
RUNNER_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = RUNNER_DIR.parent
PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "orchestration"
    / "marketing"
    / "templates"
    / "examples"
    / "ship-parallel.plan.yaml"
)


@pytest.fixture
def runner_dir() -> Path:
    """Path do diretorio runner/."""
    return RUNNER_DIR


@pytest.fixture
def plan_path() -> Path:
    """Path do plano ship-parallel."""
    if not PLAN_PATH.exists():
        pytest.skip(f"Plan nao encontrado: {PLAN_PATH}")
    return PLAN_PATH


@pytest.fixture
def tmp_run_dir(tmp_path: Path) -> Path:
    """Diretorio temporario para um run isolado."""
    return tmp_path / "run"


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Executa 'python -m plan_runner ...' e devolve o resultado."""
    return subprocess.run(
        [sys.executable, "-m", "plan_runner", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )


@pytest.fixture
def run_cli():
    """Devolve uma funcao que corre o CLI do runner."""
    def _runner(args: list[str]) -> subprocess.CompletedProcess:
        return _run_cli(args, cwd=RUNNER_DIR)
    return _runner


@pytest.fixture
def run_plan(run_cli, plan_path: Path):
    """Corre 'run' com o plano ship-parallel e devolve (proc, status)."""
    def _run(
        out_dir: Path,
        *,
        mode: str = "stub",
        engine: str = "langgraph",
    ) -> tuple[subprocess.CompletedProcess, dict]:
        proc = run_cli([
            "run",
            str(plan_path),
            "--engine", engine,
            "--mode", mode,
            "--out", str(out_dir),
        ])
        status_file = out_dir / "status.json"
        status = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
        return proc, status
    return _run


@pytest.fixture
def resume_plan(run_cli):
    """Corre 'resume' com o out_dir e decisao dados."""
    def _resume(out_dir: Path, decision: str) -> tuple[subprocess.CompletedProcess, dict]:
        proc = run_cli([
            "resume",
            str(out_dir),
            "--decision", decision,
        ])
        status_file = out_dir / "status.json"
        status = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
        return proc, status
    return _resume


@pytest.fixture
def write_result_json():
    """Escreve um result.json para um step pending (mode external)."""
    def _write(out_dir: Path, step_id: str, ok: bool = True, detail: str = "done") -> Path:
        step_dir = out_dir / "pending_steps" / step_id
        step_dir.mkdir(parents=True, exist_ok=True)
        result_file = step_dir / "result.json"
        result_file.write_text(
            json.dumps({"ok": ok, "detail": detail}),
            encoding="utf-8",
        )
        return result_file
    return _write
