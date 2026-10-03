"""D5: o worker le o `model_tier` do passo e resolve o modelo (config/model-tiers.yaml)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import model_tiers as mt
from plan_runner.engine import run_plan
from tests.test_external_worker import FakeGemini


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


@pytest.fixture
def tiers(tmp_path, monkeypatch):
    def _write(mapping: dict) -> Path:
        p = tmp_path / "model-tiers.yaml"
        p.write_text(json.dumps({"tiers": mapping}), encoding="utf-8")
        monkeypatch.setattr(mt, "TIERS_PATH", p)
        return p

    return _write


def _plan(tmp_path: Path, tiers: tuple[str | None, str | None]) -> Path:
    def line(sid, action, tier, dep=""):
        t = f", model_tier: {tier}" if tier else ""
        d = f", depends_on: [{dep}]" if dep else ""
        return f"  - {{id: {sid}, action: {action}{t}{d}, output_artifact: artifacts/{sid}.md}}\n"

    p = tmp_path / "plan.yaml"
    p.write_text("id: tiers\nobjective: x\nsteps:\n" + line("research", "research", tiers[0])
                 + line("copy", "copy_social", tiers[1], "research"), encoding="utf-8")
    return p


def _models(fake: FakeGemini) -> list[str]:
    return [c["url"].split("/models/")[1].split(":")[0] for c in fake.calls]


def test_tiers_diferentes_chamam_modelos_diferentes(tmp_path, tmp_run_dir, fake, tiers):
    tiers({"planner": "modelo-forte", "executor": "modelo-barato", "verifier": None})
    status = run_plan(_plan(tmp_path, ("planner", "executor")), mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "done"
    assert _models(fake) == ["modelo-forte", "modelo-barato"]
    ledger = [json.loads(x) for x in (tmp_run_dir / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]
    assert [r["model"] for r in ledger] == ["modelo-forte", "modelo-barato"]
    meta = json.loads((tmp_run_dir / "pending_steps/research/result.json").read_text(encoding="utf-8"))["meta"]
    assert meta["model"] == "modelo-forte" and meta["model_tier"] == "planner"


def test_tier_a_null_e_passo_sem_tier_usam_o_modelo_do_worker(tmp_path, tmp_run_dir, fake, tiers, monkeypatch):
    monkeypatch.setenv("AGENT_MODEL", "modelo-do-ambiente")
    tiers({"planner": None})
    run_plan(_plan(tmp_path, ("planner", None)), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert _models(fake) == ["modelo-do-ambiente", "modelo-do-ambiente"]
    meta = json.loads((tmp_run_dir / "pending_steps/copy/result.json").read_text(encoding="utf-8"))["meta"]
    assert "model_tier" not in meta


def test_sem_config_nada_muda(tmp_path, tmp_run_dir, fake, monkeypatch):
    monkeypatch.setattr(mt, "TIERS_PATH", tmp_path / "nao-existe.yaml")
    run_plan(_plan(tmp_path, ("executor", "verifier")), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert _models(fake) == [ew.DEFAULT_MODEL, ew.DEFAULT_MODEL]


def test_tier_desconhecido_falha_antes_de_chamar_o_modelo(tmp_path, tmp_run_dir, fake, tiers):
    tiers({})
    status = run_plan(_plan(tmp_path, ("chefe", None)), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert fake.calls == [] and status["state"] == "waiting_external"
    assert "model_tier" in status["worker_error"] and "chefe" in status["worker_error"]


def test_config_com_tier_desconhecido_ou_modelo_invalido_e_recusada(tmp_path, tiers):
    with pytest.raises(mt.ModelTierError, match="desconhecido"):
        mt.load_tiers(tiers({"chefe": "x"}))
    with pytest.raises(mt.ModelTierError, match="texto ou null"):
        mt.load_tiers(tiers({"planner": 3}))


def test_tecto_de_custo_usa_o_preco_do_modelo_do_tier(tmp_path, tmp_run_dir, fake, tiers, monkeypatch):
    """D5 + D6: o worker verifica o preco do modelo resolvido pelo tier, nao o do worker."""
    from plan_runner import cost

    prices = tmp_path / "prices.yaml"
    prices.write_text(json.dumps({"models": {ew.DEFAULT_MODEL: {"usd_per_1m_input": 1, "usd_per_1m_output": 1}}}),
                      encoding="utf-8")
    monkeypatch.setattr(cost, "PRICES_PATH", prices)
    tiers({"planner": "modelo-sem-preco"})
    status = run_plan(_plan(tmp_path, ("planner", None)), mode="external", out_dir=tmp_run_dir, worker="gemini",
                      max_cost_usd=1.0)
    assert fake.calls == [] and "modelo-sem-preco" in status["worker_error"]


def test_config_real_valida_e_sem_modelos_escolhidos():
    """config/model-tiers.yaml existe, carrega e esta tudo a null (o DEV escolhe os modelos)."""
    assert mt.load_tiers() == {"planner": None, "executor": None, "verifier": None}
