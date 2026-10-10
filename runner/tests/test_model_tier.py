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


# --------------------------------------------------------------------------
# Sinal de complexidade (C1..C4) da planwright -> modelo (router.signals)
# --------------------------------------------------------------------------

def test_config_real_de_complexidade_valida_e_a_null():
    """A seccao `complexity` existe, carrega e esta tudo a null: o sinal viaja, nao muda modelo."""
    assert mt.load_complexity() == {"C1": None, "C2": None, "C3": None, "C4": None}


def test_complexidade_escolhe_o_modelo_quando_nao_ha_model_tier(tmp_path, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C1": "barato", "C4": "forte"}}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    assert mt.resolve_model({}, "default", complexity="C4") == ("forte", None)
    assert mt.resolve_model({}, "default", complexity="C1") == ("barato", None)
    # sinal sem mapa ou desconhecido -> default, nunca parte (informa, nao decide)
    assert mt.resolve_model({}, "default", complexity="C2") == ("default", None)
    assert mt.resolve_model({}, "default", complexity="C9") == ("default", None)


def test_model_tier_manda_sempre_sobre_a_complexidade(tmp_path, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"tiers": {"planner": "modelo-do-papel"}, "complexity": {"C4": "forte"}}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    # com model_tier, a complexidade e ignorada: o papel e a autoridade
    assert mt.resolve_model({"model_tier": "planner"}, "default", complexity="C4") == ("modelo-do-papel", "planner")


def _plan_com_sinais(tmp_path: Path, complexities: dict[str, str]) -> Path:
    plan = {
        "id": "sinais", "objective": "x",
        "router": {"signals": {sid: {"complexity": c} for sid, c in complexities.items()}},
        "steps": [
            {"id": "research", "action": "research", "output_artifact": "artifacts/research.md"},
            {"id": "copy", "action": "copy_social", "depends_on": ["research"], "output_artifact": "artifacts/copy.md"},
        ],
    }
    p = tmp_path / "plan.yaml"
    p.write_text(json.dumps(plan), encoding="utf-8")  # JSON e YAML valido
    return p


def test_run_le_a_complexidade_de_router_signals_e_escolhe_o_modelo(tmp_path, tmp_run_dir, fake, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C1": "modelo-barato", "C4": "modelo-forte"}}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    plan = _plan_com_sinais(tmp_path, {"research": "C1", "copy": "C4"})
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "done"
    assert _models(fake) == ["modelo-barato", "modelo-forte"]
    meta = json.loads((tmp_run_dir / "pending_steps/copy/result.json").read_text(encoding="utf-8"))["meta"]
    assert meta["model"] == "modelo-forte" and meta["complexity"] == "C4" and "model_tier" not in meta


def test_sem_signals_a_complexidade_nao_entra(tmp_path, tmp_run_dir, fake, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C4": "modelo-forte"}}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    plan = _plan_com_sinais(tmp_path, {})  # plano sem router.signals
    run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert _models(fake) == [ew.DEFAULT_MODEL, ew.DEFAULT_MODEL]
    meta = json.loads((tmp_run_dir / "pending_steps/copy/result.json").read_text(encoding="utf-8"))["meta"]
    assert "complexity" not in meta


def test_config_com_complexidade_invalida_e_recusada(tmp_path):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C9": "x"}}), encoding="utf-8")
    with pytest.raises(mt.ModelTierError, match="desconhecido"):
        mt.load_complexity(p)


# --------------------------------------------------------------------------
# Disponibilidade (A, ADR-002): o modelo de SINAL degrada para o default se não
# estiver em `available`; o `model_tier` explícito não é filtrado.
# --------------------------------------------------------------------------

def test_config_real_de_disponibilidade_vazia():
    """`available` existe, carrega e está vazia: sem restrição (comportamento de antes)."""
    assert mt.load_available() == []


def test_sinal_indisponivel_degrada_para_default(tmp_path, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({
        "complexity": {"C1": "flash", "C4": "pro-caro"},
        "available": ["flash"],  # o DEV só confirmou o flash
    }), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    assert mt.resolve_model({}, "default", complexity="C1") == ("flash", None)      # disponível
    assert mt.resolve_model({}, "default", complexity="C4") == ("default", None)    # indisponível -> default


def test_available_vazia_nao_restringe(tmp_path, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C4": "pro-caro"}, "available": []}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    assert mt.resolve_model({}, "default", complexity="C4") == ("pro-caro", None)


def test_disponibilidade_nao_filtra_o_model_tier_explicito(tmp_path, monkeypatch):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({
        "tiers": {"planner": "pro-caro"}, "available": ["flash"],
    }), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    # papel é autoridade do DEV: não é filtrado pela disponibilidade
    assert mt.resolve_model({"model_tier": "planner"}, "default") == ("pro-caro", "planner")


def test_available_invalida_e_recusada(tmp_path):
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"available": [1, 2]}), encoding="utf-8")
    with pytest.raises(mt.ModelTierError, match="available"):
        mt.load_available(p)


def test_run_degrada_modelo_de_sinal_indisponivel(tmp_path, tmp_run_dir, fake, monkeypatch):
    """End-to-end: um C4 que mapeia para um modelo fora de `available` corre no default."""
    p = tmp_path / "mt.yaml"
    p.write_text(json.dumps({"complexity": {"C4": "pro-indisponivel"}, "available": ["so-este"]}), encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", p)
    plan = _plan_com_sinais(tmp_path, {"research": "C4", "copy": "C4"})
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    assert _models(fake) == [ew.DEFAULT_MODEL, ew.DEFAULT_MODEL]  # degradou para o default
