"""COM-1 (D2 = A, maestro, 2026-10-24): pack Comercial — leads inbound, propostas e follow-ups.

O que se prova sem rede e sem credenciais:
- os 3 agentes estão ligados (E7), as capabilities são `implemented` por um plano real e
  nenhuma executa (prepare/read; act_in_production: forbidden);
- as skills trazem o contrato: não inventar preços, orçamento/decisor nunca estimados, quem
  pede para parar sai da lista, nada é enviado;
- o plano de demo é válido, usa só dados FICTÍCIOS e corre em stub até ao gate humano;
- no escritório, os 3 aparecem no departamento Comercial e o gate deixa-o "precisa de ti".
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from plan_runner import areas as ar
from plan_runner import office
from plan_runner.engine import run_plan
from plan_runner.plan_schema import plan_errors
from plan_runner.router import score_areas
from plan_runner.skills import resolve_skill_path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "docs/orchestration/marketing/templates/examples"
PLAN = EXAMPLES / "comercial-demo.plan.yaml"
FIXTURE = EXAMPLES / "fixtures/comercial-pedido-ficticio.md"
PACK = {
    "lead_qualification": "marketing.inbound_qualification",
    "proposal": "marketing.proposals",
    "follow_up": "marketing.follow_ups",
}


@pytest.fixture
def run_dir():
    """O runner exige o --out dentro de pilots/; pilots/_pytest_*/ está no .gitignore."""
    d = REPO_ROOT / "pilots" / f"_pytest_com1_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL",
                "PLAN_RUNNER_CONTEXT", "MCP_API_KEY", "MCP_URL", "PLAN_RUNNER_TOOLS"):
        monkeypatch.delenv(var, raising=False)


def _yaml(rel: str):
    return yaml.safe_load((REPO_ROOT / rel).read_text(encoding="utf-8"))


def test_e7_valida_o_pack_comercial() -> None:
    assert ar.validate_areas(REPO_ROOT) == []
    marketing = next(a for a in _yaml("config/areas.yaml")["areas"] if a["id"] == "marketing")
    assert set(PACK.values()) <= set(marketing["agents"])


def test_capabilities_implemented_e_nenhuma_executa() -> None:
    caps = _yaml("config/marketing-capabilities.yaml")
    assert caps["policy"]["act_in_production"] == "forbidden"
    by_action = {c["action"]: c for c in caps["capabilities"]}
    for action, agent in PACK.items():
        cap = by_action[action]
        assert cap["agent"] == agent and cap["status"] == "implemented"
        assert set(cap["levels"]) <= {"read", "prepare"}


def test_skills_trazem_o_contrato_comercial() -> None:
    text = {a: resolve_skill_path(REPO_ROOT, a, "marketing").read_text(encoding="utf-8") for a in PACK}
    for body in text.values():
        assert "## Contrato do runner (obrigatório)" in body
        assert "act_in_production: forbidden" in body and "plan_approve" in body
    assert "Nunca inventar" in text["proposal"] and "[[A DEFINIR" in text["proposal"]
    assert "Orçamento e decisor só se o pedido os disser" in text["lead_qualification"]
    assert "Quem pediu para parar não recebe mais nada" in text["follow_up"]


def test_plano_valido_e_so_com_dados_ficticios() -> None:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    assert plan_errors(plan) == []
    actions = [s["action"] for s in plan["steps"]]
    assert actions == ["lead_qualification", "proposal", "follow_up", "plan_approve"]
    fixture = FIXTURE.read_text(encoding="utf-8")
    assert "FICTÍCIO" in fixture and "Tabela de referência FICTÍCIA" in fixture
    assert "@" not in fixture  # nenhum email, nem fictício, no git


def test_stub_vai_ate_ao_gate_e_o_comercial_fica_precisa_de_ti(run_dir) -> None:
    status = run_plan(PLAN, mode="stub", out_dir=run_dir)
    assert status["state"] == "paused_human_gate"
    for name in ("01-qualificacao.md", "02-proposta.md", "03-follow-ups.md"):
        assert (run_dir / "artifacts" / name).exists(), name
    snap = office.snapshot(REPO_ROOT, [run_dir])
    assert snap["unattributed"] == []
    comercial = next(d for d in snap["departments"] if d["id"] == "comercial")
    assert comercial["state"] == "needs"
    seats = {s["id"]: s["state"] for s in comercial["seats"]}
    assert seats["comercial-follow-ups"] == "needs"
    assert seats["comercial-leads"] == "idle" and seats["comercial-propostas"] == "idle"


@pytest.mark.parametrize("request_text, only_marketing", [
    ("Prepara uma proposta para este pedido de remodelação de casa de banho", True),
    ("Faz o follow-up das propostas que estão paradas há duas semanas", True),
    # Casam também noutra área ("site" -> software, "cliente" -> ops): o router já trata o
    # empate pela margem (clarificação), como antes; o que muda é o marketing passar a contar.
    ("Qualifica estes leads que chegaram pelo formulário do site", False),
    ("Preciso de um follow up educado para o cliente da cozinha", False),
])
def test_router_do_runner_leva_pedidos_comerciais_ao_marketing(request_text, only_marketing) -> None:
    """P-84 = A (maestro, 2026-10-24): keywords comerciais na área marketing."""
    hits = score_areas(request_text, _yaml("config/areas.yaml")["areas"])
    winners = [area for area, kws in hits.items() if kws]
    assert "marketing" in winners, hits
    if only_marketing:
        assert winners == ["marketing"], hits


def test_orcamento_continua_nas_financas() -> None:
    """A P-84 não mexe no "orçamento" (fica em finance; ver docs/ops/COMERCIAL.md § Router)."""
    hits = score_areas("Prepara o orçamento anual de despesas", _yaml("config/areas.yaml")["areas"])
    assert hits["finance"] and not hits["marketing"]
