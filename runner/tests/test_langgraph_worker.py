"""W-005: worker inline no engine langgraph (antes so no native)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from plan_runner import external_worker as ew  # noqa: E402
from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph  # noqa: E402
from tests.test_external_worker import FakeGemini  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake(monkeypatch):
    f = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", f)
    return f


SEQ = (
    "steps:\n"
    "  - {id: research, action: research, output_artifact: artifacts/01.md}\n"
    "  - {id: copy, action: copy_social, depends_on: [research], output_artifact: artifacts/02.md}\n"
)
PAR = (
    "steps:\n"
    "  - {id: a, action: research, output_artifact: artifacts/a.md}\n"
    "  - {id: b, action: research, output_artifact: artifacts/b.md}\n"
    "  - {id: c, action: copy_social, depends_on: [a, b], output_artifact: artifacts/c.md}\n"
)


def _plan(tmp_path: Path, steps: str = SEQ) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text("id: lg-worker\nobjective: x\n" + steps, encoding="utf-8")
    return p


def test_worker_inline_corre_o_plano_ate_ao_fim(tmp_path, tmp_run_dir, fake):
    status = run_plan_langgraph(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done" and status["worker"] == "gemini"
    assert len(fake.calls) == 2
    assert (tmp_run_dir / "artifacts/01.md").exists() and (tmp_run_dir / "artifacts/02.md").exists()
    steps = [json.loads(x)["step_id"] for x in (tmp_run_dir / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]
    assert steps == ["research", "copy"]


def test_ondas_paralelas_com_worker(tmp_path, tmp_run_dir, fake):
    status = run_plan_langgraph(_plan(tmp_path, PAR), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done" and sorted(status["completed"]) == ["a", "b", "c"]
    assert len(fake.calls) == 3


def test_sem_worker_continua_em_waiting_external(tmp_path, tmp_run_dir, fake):
    status = run_plan_langgraph(_plan(tmp_path), mode="external", out_dir=tmp_run_dir)
    assert status["state"] == "waiting_external" and status["paused_at_step"] == "research"
    assert fake.calls == [] and "worker" not in status


def test_erro_do_worker_fica_no_status(tmp_path, tmp_run_dir, monkeypatch):
    monkeypatch.setattr(ew, "httpx_transport", FakeGemini(status=429, error="quota"))
    status = run_plan_langgraph(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "waiting_external" and "429" in status["worker_error"]


def test_resume_com_worker_a_partir_de_waiting_external(tmp_path, tmp_run_dir, fake):
    run_plan_langgraph(_plan(tmp_path), mode="external", out_dir=tmp_run_dir)  # sem worker: para no 1.o passo
    status = resume_plan_langgraph(tmp_run_dir, decision="approve", worker="gemini")
    assert status["state"] == "done" and len(fake.calls) == 2


def test_worker_invalido_e_recusado(tmp_path, tmp_run_dir):
    from plan_runner.graph import PlanError

    with pytest.raises(PlanError):
        run_plan_langgraph(_plan(tmp_path), mode="stub", out_dir=tmp_run_dir, worker="gemini")  # worker so em external
