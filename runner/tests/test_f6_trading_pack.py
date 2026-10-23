"""F6 (EXECUTION-PLAN §7; P-79 = A): domínio de prova trading, sem tocar no core.

Prova o "done" do F6 que se pode provar sem credenciais (docs/ops/F6-TRADING-DOC.md):
- o pack regista-se só com ficheiros de domínio e passa no E7 (áreas, capabilities, allowlist);
- nenhuma capability tem o nível `act` e a política proíbe execução;
- o router manda pedidos de trading para a área `trading` (e já não para a `finance`);
- os 2 planos são válidos e correm em stub até ao gate humano;
- em external (Gemini falso), cada passo recebe a skill de trading, o grounding completo e os
  ficheiros do `repo_files` (o conhecimento do domínio);
- o core (runner/plan_runner/) não sabe que o domínio existe: DOC(core) = 0;
- a allowlist de trading só usa domínios já aprovados para a `finance` (sem domínio novo);
- a revisão de exemplo é saída do `economia-trader review` em modo paper (nada real).
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from plan_runner import areas as ar
from plan_runner import external_worker as ew
from plan_runner.engine import run_plan
from plan_runner.plan_schema import plan_errors
from plan_runner.router import score_areas
from plan_runner.skills import resolve_skill_path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXAMPLES = REPO_ROOT / "docs/orchestration/trading/templates/examples"
MARKET = EXAMPLES / "market-analysis-demo.plan.yaml"
REVIEW = EXAMPLES / "post-trade-review-demo.plan.yaml"
FIXTURE = EXAMPLES / "fixtures/paper-review-sample.json"
ACTIONS = ("market_analysis", "risk_review", "post_trade_review")


@pytest.fixture
def run_dir():
    """O runner exige o --out dentro de pilots/; pilots/_pytest_*/ está no .gitignore."""
    d = REPO_ROOT / "pilots" / f"_pytest_f6_{uuid.uuid4().hex[:8]}"
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


def _area(area_id: str) -> dict:
    return next(a for a in _yaml("config/areas.yaml")["areas"] if a["id"] == area_id)


# --- registo e política ----------------------------------------------------------------------


def test_e7_valida_o_pack_de_trading() -> None:
    assert ar.validate_areas(REPO_ROOT) == []
    area = _area("trading")
    assert area["hitl"] == "required"
    assert sorted(area["agents"]) == [f"trading.{a}" for a in sorted(ACTIONS)]


def test_nenhuma_capability_de_trading_executa() -> None:
    caps = _yaml("config/trading-capabilities.yaml")
    assert caps["policy"]["act_in_production"] == "forbidden" and caps["policy"]["hitl"] == "required"
    assert {c["action"] for c in caps["capabilities"]} == set(ACTIONS)
    for cap in caps["capabilities"]:
        assert "act" not in cap["levels"] and set(cap["levels"]) <= {"read", "prepare"}, cap["id"]


def test_router_manda_trading_para_a_area_trading() -> None:
    areas = _yaml("config/areas.yaml")["areas"]
    for pedido in ("Faz a revisão do backtest da estratégia de cripto",
                   "Como está a bolsa hoje para um trader de curto prazo?"):
        hits = {a: h for a, h in score_areas(pedido, areas).items() if h}
        assert list(hits) == ["trading"], (pedido, hits)
    assert "trading" not in _area("finance")["keywords"]


def test_allowlist_de_trading_nao_traz_dominios_novos() -> None:
    allow = _yaml("config/web-allowlist.yaml")["areas"]
    assert allow["trading"] and set(allow["trading"]) <= set(allow["finance"])


# --- planos ----------------------------------------------------------------------------------


@pytest.mark.parametrize("plan", [MARKET, REVIEW], ids=["market", "review"])
def test_planos_validos_e_actions_resolvem_skills_de_trading(plan) -> None:
    raw = yaml.safe_load(plan.read_text(encoding="utf-8"))
    assert plan_errors(raw) == []
    for step in raw["steps"]:
        if step["action"] == "plan_approve":
            continue
        assert step["vertical"] == "trading"
        skill = resolve_skill_path(REPO_ROOT, step["action"], "trading")
        assert skill == REPO_ROOT / "skills/trading" / step["action"] / "SKILL.md", step["id"]
    assert raw["steps"][-1]["action"] == "plan_approve"  # a decisão é sempre humana


def test_stub_dos_2_planos_para_no_gate_humano(run_dir) -> None:
    st = run_plan(MARKET, mode="stub", out_dir=run_dir / "market")
    assert st["state"] == "paused_human_gate" and sorted(st["completed"]) == ["analysis", "risk"]
    st = run_plan(REVIEW, mode="stub", out_dir=run_dir / "review")
    assert st["state"] == "paused_human_gate" and st["completed"] == ["review"]


def test_external_recebe_skill_grounding_completo_e_o_conhecimento(run_dir) -> None:
    calls: list[dict] = []

    def fake(url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        calls.append({"step": re.search(r"- passo: (\S+)", user).group(1), "system": system, "user": user})
        text = "# Revisão pós-trade\n\nSem dados novos.\n"
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15}}

    transport = ew.httpx_transport
    ew.httpx_transport = fake
    try:
        st = run_plan(REVIEW, mode="external", out_dir=run_dir, worker="gemini")
    finally:
        ew.httpx_transport = transport
    assert st["state"] == "paused_human_gate" and st["completed"] == ["review"]
    (call,) = calls
    assert "Skill — post_trade_review" in call["system"]
    res = json.loads((run_dir / "pending_steps/review/result.json").read_text(encoding="utf-8"))
    assert res["meta"]["context"]["grounding"] == "full"  # área de risco
    prompt = call["system"] + call["user"]
    assert "major break" in prompt and '"expectancy_r"' in prompt  # método + JSON da revisão


# --- DOC(core) = 0 e a revisão de exemplo ------------------------------------------------------


def test_core_nao_sabe_que_o_dominio_existe() -> None:
    """DOC(core) = 0 (EXECUTION-PLAN §15.9): nenhum ficheiro do core nomeia o domínio."""
    core = sorted((REPO_ROOT / "runner/plan_runner").glob("*.py")) + [
        REPO_ROOT / "runner/plan_runner/plan.schema.json"
    ]
    assert core
    named = [p.name for p in core if re.search(r"\btrading\b", p.read_text(encoding="utf-8"))]
    assert named == [], f"o core passou a conhecer o domínio trading: {named}"


def test_revisao_de_exemplo_e_do_economia_trader_em_paper() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["method"].startswith("process graded apart from outcome")
    assert data["trades"] and all(t["mode"] == "paper" for t in data["trades"])
    assert data["weeks"] and data["open"] == [] and data["orphan_sells"] == 0
