"""Orcamento de tokens por run (PLANO item 4, docs/ops/BUDGET.md).

O Gemini e falso: cada chamada gasta 955 tokens (USAGE de test_external_worker).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import router as rt
from plan_runner.engine import PlanError, resume_run, run_plan
from tests.test_external_worker import FakeGemini
from tests.test_router import FakeRouterLLM, _mini_repo

PER_CALL = 955


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


def _plan(tmp_path: Path, max_tokens: int | None = None) -> Path:
    budget = f"budget:\n  max_tokens: {max_tokens}\n" if max_tokens is not None else ""
    p = tmp_path / "plan.yaml"
    p.write_text(
        "id: orcamento-tres-passos\nobjective: x\n" + budget + "steps:\n"
        "  - {id: research, action: research, output_artifact: artifacts/01.md}\n"
        "  - {id: brief, action: internal_brief, depends_on: [research], output_artifact: artifacts/02.md}\n"
        "  - {id: copy, action: copy_social, depends_on: [brief], output_artifact: artifacts/03.md}\n",
        encoding="utf-8",
    )
    return p


def _events(out: Path) -> list[dict]:
    return [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def _ledger_steps(out: Path) -> list[str]:
    return [json.loads(line)["step_id"] for line in (out / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]


# --------------------------------------------------------------------------
# O worker para ao atingir o tecto
# --------------------------------------------------------------------------

def test_worker_para_ao_atingir_o_tecto_sem_chamar_o_gemini(tmp_path, tmp_run_dir, fake):
    # 1500: o passo 1 corre (0 < 1500), o 2 tambem (955 < 1500), o 3 ja nao (1910 >= 1500)
    status = run_plan(_plan(tmp_path, max_tokens=1500), mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "paused_budget"
    assert status["paused_at_step"] == "copy"
    assert status["completed"] == ["brief", "research"]
    assert status["budget_spent"] == 2 * PER_CALL
    assert len(fake.calls) == 2  # o passo 3 nunca chegou ao Gemini
    assert _ledger_steps(tmp_run_dir) == ["research", "brief"]

    pending = tmp_run_dir / "pending_steps" / "copy"
    assert (pending / "request.json").exists()  # o pedido ficou pronto para o resume
    assert not (pending / "result.json").exists()
    assert not (pending / ew.ERROR_FILE).exists()  # pausa de orcamento nao e erro

    [ev] = [e for e in _events(tmp_run_dir) if e["type"] == "budget_exceeded"]
    assert ev["payload"] == {"step_id": "copy", "spent": 1910, "cap": 1500}
    note = (tmp_run_dir / "BUDGET.md").read_text(encoding="utf-8")
    assert "1910 tokens gastos >= tecto 1500" in note and "--max-tokens" in note


def test_resume_com_tecto_maior_continua_de_onde_parou(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, max_tokens=1500), mode="external", out_dir=tmp_run_dir, worker="gemini")
    research_before = (tmp_run_dir / "artifacts/01.md").read_text(encoding="utf-8")

    status = resume_run(tmp_run_dir, decision="approve", max_tokens=5000)

    assert status["state"] == "done", status
    assert status["completed"] == ["brief", "copy", "research"]
    assert status["max_tokens"] == 5000 and "budget_spent" not in status
    assert len(fake.calls) == 3  # so o passo que faltava; research e brief nao repetiram
    assert _ledger_steps(tmp_run_dir) == ["research", "brief", "copy"]
    assert (tmp_run_dir / "artifacts/01.md").read_text(encoding="utf-8") == research_before
    resumed = [e for e in _events(tmp_run_dir) if e["type"] == "budget_resumed"]
    assert resumed[0]["payload"] == {"step_id": "copy", "spent": 1910, "max_tokens": 5000}


def test_resume_sem_subir_o_tecto_volta_a_parar_no_mesmo_passo(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, max_tokens=1500), mode="external", out_dir=tmp_run_dir, worker="gemini")
    status = resume_run(tmp_run_dir, decision="approve")
    assert status["state"] == "paused_budget" and status["paused_at_step"] == "copy"
    assert len(fake.calls) == 2


def test_tecto_que_ainda_nao_chega_para_ao_passo_seguinte(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, max_tokens=1500), mode="external", out_dir=tmp_run_dir, worker="gemini")
    status = resume_run(tmp_run_dir, decision="approve", max_tokens=2000)  # deixa correr 1 passo, nao mais
    assert status["state"] == "done"  # 1910 < 2000 -> o passo 3 corre; nao ha passo 4
    assert len(fake.calls) == 3


def test_max_tokens_do_run_tem_prioridade_sobre_o_plano(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path, max_tokens=100000), mode="external", out_dir=tmp_run_dir, worker="gemini", max_tokens=900)
    assert status["state"] == "paused_budget" and status["paused_at_step"] == "brief"
    assert status["max_tokens"] == 900 and len(fake.calls) == 1


def test_tecto_zero_para_antes_do_primeiro_passo(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini", max_tokens=0)
    assert status["state"] == "paused_budget" and status["paused_at_step"] == "research"
    assert fake.calls == [] and status["completed"] == []


def test_sem_tecto_nada_muda(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done" and len(fake.calls) == 3 and "max_tokens" not in status


def test_max_tokens_invalido(tmp_path, tmp_run_dir):
    with pytest.raises(PlanError, match="inteiro >= 0"):
        run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini", max_tokens=-1)


def test_linhas_do_ledger_sem_tokens_contam_zero(tmp_run_dir):
    (tmp_run_dir / ew.LEDGER_FILE).write_text(
        '{"tokens_total": 100}\n{"tokens_total": null}\nlixo\n{"tokens_total": 50}\n', encoding="utf-8"
    )
    assert ew.ledger_spent(tmp_run_dir) == 150


# --------------------------------------------------------------------------
# CLI (run --max-tokens, resume --max-tokens) e worker standalone
# --------------------------------------------------------------------------

def test_cli_run_e_resume_com_max_tokens(tmp_path, tmp_run_dir, fake, capsys):
    from plan_runner.cli import main

    assert main(["run", str(_plan(tmp_path)), "--mode", "external", "--worker", "gemini",
                 "--max-tokens", "1500", "--out", str(tmp_run_dir)]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "paused_budget"

    assert main(["resume", str(tmp_run_dir), "--max-tokens", "5000"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "done"


def test_cli_langgraph_recusa_max_tokens(tmp_path, tmp_run_dir, capsys):
    from plan_runner.cli import main

    assert main(["run", str(_plan(tmp_path)), "--engine", "langgraph", "--mode", "external",
                 "--max-tokens", "10", "--out", str(tmp_run_dir)]) == 1
    assert "--max-tokens so no engine native" in capsys.readouterr().out


def test_worker_standalone_respeita_o_tecto(tmp_path, tmp_run_dir, fake, capsys):
    run_plan(_plan(tmp_path, max_tokens=1500), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert ew.main([str(tmp_run_dir)]) == 3
    assert "budget:" in capsys.readouterr().err and len(fake.calls) == 2


# --------------------------------------------------------------------------
# Tecto por area (config/areas.yaml -> router -> plano)
# --------------------------------------------------------------------------

def test_tecto_da_area_passa_para_o_plano_menos_o_que_o_router_gastou(tmp_path):
    repo = _mini_repo(tmp_path, areas_extra=", budget: {max_steps: 3, max_tokens: 2000}")
    llm = FakeRouterLLM(replies={"pedido de codigo": {"mode": "agent", "agent": "eng.dev", "confidence": 0.9}})
    router = rt.Router(repo, transport=llm)
    d = router.route("pedido de codigo")
    assert d.usage[0]["tokens_total"] == 680  # FakeRouterLLM
    assert router.build_plan(d)["budget"] == {"max_steps": 3, "max_tokens": 2000 - 680}


def test_area_real_com_tecto_para_o_run_executado_pelo_router(tmp_run_dir, fake, monkeypatch):
    router = rt.Router(transport=FakeRouterLLM())
    router.areas["marketing"]["budget"] = {"max_tokens": 680}  # tudo gasto pelo router
    d = router.route("Faz um post de Instagram para o lançamento da nova coleção de verão")
    status = router.execute(d, out_dir=tmp_run_dir)["status"]
    assert status["state"] == "paused_budget" and status["paused_at_step"] == "p1_copy_social"
    assert fake.calls == []
    assert resume_run(tmp_run_dir, decision="approve", max_tokens=5000)["state"] == "done"


def test_validador_aceita_max_tokens_e_recusa_lixo(tmp_path):
    from plan_runner.areas import validate_areas
    from tests.test_areas import AGENTS, VALID
    from tests.test_areas import _repo as areas_repo

    def repo(name: str, yaml_text: str) -> Path:
        (tmp_path / name).mkdir()
        return areas_repo(tmp_path / name, yaml_text, AGENTS)

    ok = VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    budget: {max_tokens: 20000}\n")
    assert validate_areas(repo("ok", ok)) == []
    for i, bad in enumerate(("{max_tokens: 0}", "{max_tokens: muitos}", "{tokens: 10}", "{}")):
        y = VALID.replace("    agents: [eng.dev]\n", f"    agents: [eng.dev]\n    budget: {bad}\n")
        errors = validate_areas(repo(f"bad{i}", y))
        assert any("`budget` tem de ser null" in e for e in errors), (bad, errors)
