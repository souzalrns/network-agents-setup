"""S30 -- liga working_memory.py (MEMORY.md por cliente) ao arranque do run.

Aditivo: planos sem `client_id` ficam inalterados (ver
test_no_client_id_is_no_op). working_memory.py continua read-only -- este
teste so exercita a leitura ja existente, chamada agora de facto pelo motor.

memory/<client_id>/MEMORY.md e escrito no repo REAL (nao um tmp_path
isolado), porque repo_root_from_out() resolve a partir do --out real
(dentro de <repo>/pilots/, exigido por _validate_out_dir) -- por isso o
teardown remove o diretorio memory/<client_id>/ criado.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from tests.conftest import REPO_ROOT, _run_cli


def _write_plan(tmp_path: Path, *, client_id: str | None) -> Path:
    client_line = f"client_id: {client_id}\n" if client_id else ""
    plan = tmp_path / "plan.yaml"
    plan.write_text(
        f"""\
id: test-client-memory
version: 1
objective: "teste S30"
{client_line}steps:
  - id: only
    action: only
""",
        encoding="utf-8",
    )
    return plan


@pytest.fixture
def client_id() -> str:
    return f"pytest-client-{uuid4().hex[:8]}"


@pytest.fixture
def real_client_memory(client_id: str):
    """Cria memory/<client_id>/MEMORY.md no repo real; remove no teardown."""
    path = REPO_ROOT / "memory" / client_id / "MEMORY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Cliente de teste\n\nPrefere respostas curtas.\n", encoding="utf-8")
    yield path
    shutil.rmtree(REPO_ROOT / "memory" / client_id, ignore_errors=True)


def test_client_memory_injected_at_run_start(tmp_path, tmp_run_dir, client_id, real_client_memory):
    plan = _write_plan(tmp_path, client_id=client_id)
    proc = _run_cli(
        ["run", str(plan), "--engine", "native", "--mode", "stub", "--out", str(tmp_run_dir)],
        cwd=REPO_ROOT / "runner",
    )
    assert proc.returncode == 0, proc.stderr

    written = tmp_run_dir / "client_memory.md"
    assert written.is_file()
    assert "Prefere respostas curtas" in written.read_text(encoding="utf-8")

    events = (tmp_run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert '"client_memory_loaded"' in events
    assert f'"client_id": "{client_id}"' in events


def test_client_memory_appears_in_pending_step_external_mode(tmp_path, tmp_run_dir, client_id, real_client_memory):
    plan = _write_plan(tmp_path, client_id=client_id)
    proc = _run_cli(
        ["run", str(plan), "--engine", "native", "--mode", "external", "--out", str(tmp_run_dir)],
        cwd=REPO_ROOT / "runner",
    )
    assert proc.returncode == 0, proc.stderr

    pending = tmp_run_dir / "pending_steps" / "only"
    assert (pending / "CLIENT_MEMORY.md").is_file()
    assert "Prefere respostas curtas" in (pending / "CLIENT_MEMORY.md").read_text(encoding="utf-8")

    req = json.loads((pending / "request.json").read_text(encoding="utf-8"))
    assert req["client_memory_path"] == "client_memory.md"


def test_client_id_set_but_memory_missing_logs_absent_no_crash(tmp_path, tmp_run_dir):
    missing_client = f"pytest-missing-{uuid4().hex[:8]}"
    assert not (REPO_ROOT / "memory" / missing_client).exists()

    plan = _write_plan(tmp_path, client_id=missing_client)
    proc = _run_cli(
        ["run", str(plan), "--engine", "native", "--mode", "stub", "--out", str(tmp_run_dir)],
        cwd=REPO_ROOT / "runner",
    )
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_run_dir / "client_memory.md").exists()

    events = (tmp_run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert '"client_memory_absent"' in events


def test_no_client_id_is_no_op(tmp_path, tmp_run_dir):
    """Nao-regressao: plano sem `client_id` (a esmagadora maioria dos planos
    reais hoje) fica exactamente como estava antes do S30."""
    plan = _write_plan(tmp_path, client_id=None)
    proc = _run_cli(
        ["run", str(plan), "--engine", "native", "--mode", "stub", "--out", str(tmp_run_dir)],
        cwd=REPO_ROOT / "runner",
    )
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_run_dir / "client_memory.md").exists()

    events = (tmp_run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "client_memory" not in events
