"""P-89 (M-006): modos de skill por passo.

Um agente herdeiro carrega as funções de agentes fundidos como `modes/<mode>.md` da sua skill.
O modo só entra no passo que o pede (`mode:` no plano) e um modo inexistente faz o passo falhar
antes de chamar o modelo (fail-closed). Sem rede: repos pequenos em tmp e LLMs falsos.
A prova com as fusões reais do repo está em test_m006_transferencias.py.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from plan_runner import router as rt
from plan_runner import skill_activation as sa
from plan_runner.capabilities import action_key, actions_by_plan, validate_capabilities
from plan_runner.executor import execute_external_request, execute_stub
from plan_runner.models import Plan, Step
from plan_runner.plan_schema import plan_errors
from plan_runner.skills import list_modes, resolve_mode_path

MODE_BODY = "---\nname: pricing\nmode: pricing\ndescription: \"Decide precos e planos.\"\n---\n\n# Modo pricing\n\nRegras de preco.\n"


def _w(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _repo(tmp_path: Path, *, with_mode: bool = True) -> Path:
    """Repo minimo: agente `marketing.offers` + skill `offers` com (ou sem) o modo `pricing`."""
    _w(tmp_path / "agents/marketing/offers.agent.md",
       "---\nid: marketing.offers\naction: offers\ndescription: \"Desenha ofertas.\"\n"
       "skill: skills/marketing/offers/SKILL.md\nvertical: marketing\n---\n# offers\n")
    _w(tmp_path / "skills/marketing/offers/SKILL.md", "---\nname: offers\naction: offers\n---\n# Skill offers\n")
    if with_mode:
        _w(tmp_path / "skills/marketing/offers/modes/pricing.md", MODE_BODY)
    (tmp_path / "runner" / "plan_runner").mkdir(parents=True, exist_ok=True)  # repo_root_from_out
    return tmp_path


def _step(mode: str | None = "pricing", action: str = "offers") -> Step:
    raw = {"id": "s1", "action": action, **({"mode": mode} if mode else {}), "output_artifact": "artifacts/01.md"}
    return Plan.from_dict({"id": "p", "steps": [raw]}).steps[0]


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv(sa.OFFLINE_ENV, "1")


# --------------------------------------------------------------------------- resolução


def test_resolve_e_lista_modos(tmp_path):
    skill = _repo(tmp_path) / "skills/marketing/offers/SKILL.md"
    assert resolve_mode_path(skill, "pricing") == (skill.parent / "modes/pricing.md").resolve()
    assert list_modes(skill) == {"pricing": "Decide precos e planos."}


@pytest.mark.parametrize("mode", ["../SKILL", "Pricing", "pri cing", "", "x" * 41, "inexistente"])
def test_modo_invalido_ou_inexistente_nao_resolve(tmp_path, mode):
    skill = _repo(tmp_path) / "skills/marketing/offers/SKILL.md"
    assert resolve_mode_path(skill, mode) is None


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_modo_symlink_nunca_resolve(tmp_path):
    skill = _repo(tmp_path, with_mode=False) / "skills/marketing/offers/SKILL.md"
    target = _w(tmp_path / "fora.md", "segredo")
    (skill.parent / "modes").mkdir()
    (skill.parent / "modes/link.md").symlink_to(target)
    assert resolve_mode_path(skill, "link") is None and list_modes(skill) == {}


def test_schema_do_plano_aceita_modo_valido_e_recusa_invalido():
    ok = {"id": "p", "steps": [{"id": "s", "action": "offers", "mode": "pricing"}]}
    assert plan_errors(ok) == []
    bad = {"id": "p", "steps": [{"id": "s", "action": "offers", "mode": "../x"}]}
    assert plan_errors(bad)
    assert Plan.from_dict(ok).steps[0].mode == "pricing"
    assert Plan.from_dict({"id": "p", "steps": [{"id": "s", "action": "offers"}]}).steps[0].mode is None


# --------------------------------------------------------------------------- activação + executor


def test_activacao_resolve_o_modo_e_materializa_mode_md(tmp_path):
    repo = _repo(tmp_path)
    act = sa.activate_for_task(repo, _step())
    assert act.mode == "pricing" and act.mode_error is None
    assert act.mode_rel == "skills/marketing/offers/modes/pricing.md" and len(act.mode_sha256) == 64
    pending = tmp_path / "pending"
    pending.mkdir()
    sa.materialize_activation(pending, act)
    assert (pending / sa.MODE_MD).read_text(encoding="utf-8") == MODE_BODY
    data = json.loads((pending / sa.ACTIVATION_JSON).read_text(encoding="utf-8"))
    assert data["mode"] == {"name": "pricing", "path": act.mode_rel, "sha256": act.mode_sha256, "error": None}
    assert act.to_request_fields()["mode"] == "pricing"


def test_passo_sem_modo_nao_muda_nada(tmp_path):
    repo = _repo(tmp_path)
    act = sa.activate_for_task(repo, _step(mode=None))
    assert act.mode is None and "mode" not in act.to_json() and "mode" not in act.to_request_fields()
    pending = tmp_path / "pending"
    pending.mkdir()
    _w(pending / sa.MODE_MD, "antigo")  # resume: um MODE.md de uma activação anterior
    sa.materialize_activation(pending, act)
    assert not (pending / sa.MODE_MD).exists()


def test_modo_inexistente_falha_fechado_sem_chamar_o_worker(tmp_path):
    repo = _repo(tmp_path, with_mode=False)
    out = repo / "pilots" / "run"
    out.mkdir(parents=True)

    class Boom:
        def process(self, *a, **k):
            raise AssertionError("o modelo nao pode ser chamado sem o modo")

    res = execute_external_request(out, _step(), worker=Boom())
    assert not res.ok and res.detail.startswith("mode_missing:") and "pricing" in res.detail
    data = json.loads((out / "pending_steps/s1" / sa.ACTIVATION_JSON).read_text(encoding="utf-8"))
    assert data["mode"]["error"] and not (out / "pending_steps/s1" / sa.MODE_MD).exists()


def test_stub_tambem_falha_com_modo_inexistente(tmp_path):
    out = _repo(tmp_path, with_mode=False) / "pilots" / "run"
    out.mkdir(parents=True)
    res = execute_stub(out, _step())
    assert not res.ok and res.detail.startswith("mode_missing:")
    out_ok = _repo(tmp_path / "ok") / "pilots" / "run"
    out_ok.mkdir(parents=True)
    assert execute_stub(out_ok, _step()).ok


# --------------------------------------------------------------------------- router


def _router(tmp_path: Path, reply: dict) -> tuple[rt.Router, list]:
    repo = _repo(tmp_path)
    _w(repo / "agents/marketing/copy.agent.md", "---\nid: marketing.copy\naction: copy\ndescription: \"Escreve copy.\"\n---\n")
    _w(repo / "config/areas.yaml", yaml.safe_dump({
        "routing": {"area_min_confidence": 0.6, "agent_min_confidence": 0.6, "fallback_area": "marketing"},
        "areas": [{"id": "marketing", "description": "Marketing.", "keywords": ["preco"],
                   "agents": ["marketing.offers", "marketing.copy"], "horizontals": []}],
    }))
    calls: list = []

    def transport(url, headers, body, timeout):
        calls.append(body)
        return 200, {"candidates": [{"content": {"parts": [{"text": json.dumps(reply)}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2}}

    return rt.Router(repo, transport=transport, api_key="k"), calls


def test_router_mostra_os_modos_e_aceita_um_modo_valido(tmp_path):
    router, calls = _router(tmp_path, {"mode": "agent", "agent": "marketing.offers", "skill_mode": "pricing", "confidence": 0.9})
    d = router.route("define o preco do plano anual")
    assert (d.outcome, d.agent, d.mode) == ("agent", "marketing.offers", "pricing")
    prompt = calls[-1]["contents"][0]["parts"][0]["text"]
    assert "Modos: `pricing` = Decide precos e planos." in prompt
    [step] = router.build_plan(d)["steps"]
    assert step["mode"] == "pricing" and step["id"] == "p1_offers-pricing" and plan_errors(router.build_plan(d)) == []


@pytest.mark.parametrize("reply", [
    {"mode": "agent", "agent": "marketing.offers", "skill_mode": "inventado", "confidence": 0.9},
    {"mode": "agent", "agent": "marketing.copy", "skill_mode": "pricing", "confidence": 0.9},
    {"mode": "plan", "confidence": 0.9, "steps": [{"agent": "marketing.copy"}, {"agent": "marketing.offers", "skill_mode": "x"}]},
])
def test_router_recusa_modo_que_o_agente_nao_tem(tmp_path, reply):
    router, _ = _router(tmp_path, reply)
    d = router.route("define o preco do plano anual")
    assert d.outcome == "error" and "modo" in d.reason


def test_router_plano_com_modo_num_passo(tmp_path):
    router, _ = _router(tmp_path, {"mode": "plan", "confidence": 0.9, "steps": [
        {"agent": "marketing.offers", "skill_mode": "pricing", "task": "preco"},
        {"agent": "marketing.copy", "task": "texto", "depends_on": [1]},
    ]})
    d = router.route("define o preco e escreve o anuncio")
    assert d.outcome == "plan" and [s.get("mode") for s in d.steps] == ["pricing", None]
    assert rt.check_case(d, {"plan_modes": ["pricing", None]}) == []
    plan = router.build_plan(d)
    assert [s.get("mode") for s in plan["steps"]] == ["pricing", None] and plan_errors(plan) == []


# --------------------------------------------------------------------------- capabilities


def _caps_repo(tmp_path: Path, cap: dict, *, plan_mode: str | None = None, with_mode: bool = True) -> Path:
    repo = _repo(tmp_path, with_mode=with_mode)
    areas = [{"id": "marketing", "description": "M.", "keywords": ["x"], "agents": ["marketing.offers"]}]
    _w(repo / "config/marketing-capabilities.yaml", yaml.safe_dump({
        "version": 1, "domain": "marketing",
        "policy": {"offensive": "forbidden", "act_in_production": "forbidden", "default_level": "prepare"},
        "capabilities": [cap],
    }))
    if plan_mode is not None:
        _w(repo / "docs/orchestration/marketing/x.plan.yaml",
           yaml.safe_dump({"id": "x", "steps": [{"id": "s", "action": "offers", "mode": plan_mode}]}))
    return repo, areas


def _cap(**kw) -> dict:
    return {"id": "pricing_strategy", "description": "Precos.", "levels": ["prepare"], "status": "partial",
            "action": "offers", "agent": "marketing.offers", "skill": "skills/marketing/offers/SKILL.md",
            "mode": "pricing", **kw}


def _known(repo: Path) -> dict:
    return {"marketing.offers": repo / "agents/marketing/offers.agent.md"}


def test_capability_de_modo_valida(tmp_path):
    repo, areas = _caps_repo(tmp_path, _cap())
    assert validate_capabilities(repo, _known(repo), areas) == []


def test_capability_de_modo_sem_ficheiro_falha(tmp_path):
    repo, areas = _caps_repo(tmp_path, _cap(), with_mode=False)
    assert any("modo `pricing` não existe" in e for e in validate_capabilities(repo, _known(repo), areas))


def test_capability_de_modo_sem_skill_falha(tmp_path):
    cap = _cap(status="planned")
    cap.pop("skill")
    repo, areas = _caps_repo(tmp_path, cap)
    assert any("`mode` exige `skill`" in e for e in validate_capabilities(repo, _known(repo), areas))


def test_implemented_de_modo_exige_plano_com_action_e_modo(tmp_path):
    repo, areas = _caps_repo(tmp_path, _cap(status="implemented"), plan_mode="outro")
    errs = validate_capabilities(repo, _known(repo), areas)
    assert any("e o modo `pricing`" in e for e in errs)
    repo2, areas2 = _caps_repo(tmp_path / "b", _cap(status="implemented"), plan_mode="pricing")
    assert validate_capabilities(repo2, _known(repo2), areas2) == []
    assert actions_by_plan(repo2) == {"docs/orchestration/marketing/x.plan.yaml": [action_key("offers", "pricing")]}
