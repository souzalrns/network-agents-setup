"""W-006: os planos do runner validam contra plan_runner/plan.schema.json."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from plan_runner import plan_schema as ps
from plan_runner import router as rt
from tests.test_router import FakeRouterLLM, _mini_repo

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANS = sorted((REPO_ROOT / "docs" / "orchestration").glob("**/*.plan.yaml"))


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.delenv("AGENT_MODEL", raising=False)


def test_ha_planos_para_validar():
    assert len(PLANS) >= 13


@pytest.mark.parametrize("plan", PLANS, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_plano_do_repo_e_valido(plan):
    assert ps.file_errors(plan) == []


@pytest.mark.parametrize("reply", [
    {"mode": "agent", "agent": "eng.dev", "confidence": 0.9},
    {"mode": "plan", "confidence": 0.9, "steps": [
        {"agent": "eng.dev", "task": "fazer", "depends_on": []},
        {"agent": "eng.rev", "task": "rever", "depends_on": [1]},
    ]},
])
def test_plano_gerado_pelo_router_e_valido(tmp_path, reply):
    repo = _mini_repo(tmp_path, areas_extra=", budget: {max_steps: 3, max_tokens: 2000}")
    router = rt.Router(repo, transport=FakeRouterLLM(replies={"pedido de codigo": reply}))
    d = router.route("pedido de codigo")
    assert d.outcome == reply["mode"], d.reason
    assert ps.plan_errors(router.build_plan(d)) == []


BASE = {"id": "p", "steps": [{"id": "a", "action": "research"}]}


@pytest.mark.parametrize("patch, erro", [
    ({"stepz": []}, "Additional properties"),                                   # gralha no topo
    ({"steps": [{"id": "a", "action": "x", "depend_on": ["b"]}]}, "depend_on"),  # gralha no passo
    ({"steps": []}, "should be non-empty"),
    ({"steps": [{"id": "a"}]}, "'action' is a required property"),
    ({"budget": {"max_tokens": -1}}, "minimum"),
    ({"steps": [{"id": "a", "action": "x", "knowledge": {"kb": "security"}}]}, "'query' is a required property"),
    ({"steps": [{"id": "a", "action": "x", "human_gate": {"allow": ["aprovar"]}}]}, "human_gate"),
    ({"steps": [{"id": "a", "action": "x", "model_tier": "chefe"}]}, "model_tier"),
    # P-10 = A (AU-22): campos removidos do schema; um plano que os declare falha
    ({"steps": [{"id": "a", "action": "x", "on_fail": "human"}]}, "'on_fail' was unexpected"),
    ({"budget": {"max_replans": 2}}, "'max_replans' was unexpected"),
])
def test_erros_tipicos_sao_apanhados(patch, erro):
    errs = ps.plan_errors({**BASE, **patch})
    assert errs and any(erro in e for e in errs), errs


def test_cli(tmp_path, capsys):
    good, bad = tmp_path / "ok.plan.yaml", tmp_path / "mau.plan.yaml"
    good.write_text(yaml.safe_dump(BASE), encoding="utf-8")
    bad.write_text(yaml.safe_dump({"id": "p", "stepz": []}), encoding="utf-8")
    assert ps.main([str(good)]) == 0
    assert ps.main([str(good), str(bad)]) == 1
    out = capsys.readouterr().out
    assert "2 planos; 1 com erros" in out and "mau.plan.yaml" in out
