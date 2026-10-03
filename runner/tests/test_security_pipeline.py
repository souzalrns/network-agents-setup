"""Pipeline de security (triage -> audit -> report -> HITL) de ponta a ponta, sem rede.

Prova o que o plano demo promete e o que não promete:
- stub e external (Gemini falso) chegam ao HITL com os 3 artefactos;
- cada passo recebe o AGENT.md e a SKILL.md certos (S34 `vertical:` + A8 path-first);
- grounding `full` (área com `hitl: required`) e política `opt`;
- a triagem (JSON pequeno) NÃO é pedida em resumo (override `context.full` no report);
- em external o auditor não recebe ficheiros do repo (limite documentado: AU-22).
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner.engine import run_plan
from plan_runner.router import Router

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN = REPO_ROOT / "docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml"
ARTIFACTS = ["01-triage.json", "02-audit.md", "03-security-report.md"]


@pytest.fixture
def run_dir():
    """O runner exige o --out dentro de pilots/ (engine.py); pilots/_pytest_*/ está no .gitignore."""
    d = REPO_ROOT / "pilots" / f"_pytest_sec_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _router_llm(agent: str):
    def llm(url, headers, body, timeout):
        text = json.dumps({"mode": "agent", "agent": agent, "confidence": 0.9, "reason": "teste"})
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}}], "usageMetadata": {"totalTokenCount": 3}}
    return llm


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL", "PLAN_RUNNER_CONTEXT"):
        monkeypatch.delenv(var, raising=False)


def test_stub_chega_ao_hitl_com_os_3_artefactos(run_dir):
    st = run_plan(PLAN, mode="stub", out_dir=run_dir)
    assert st["state"] == "paused_human_gate" and st["paused_at_step"] == "hitl_security_decision"
    assert sorted(st["completed"]) == ["audit", "report", "triage"]
    assert sorted(p.name for p in (run_dir / "artifacts").iterdir()) == ARTIFACTS


def test_external_resolve_agentes_e_skills_e_nao_pede_resumo_da_triagem(run_dir):
    calls: list[dict] = []

    def fake(url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        step = re.search(r"- passo: (\S+)", user).group(1)
        calls.append({"step": step, "system": system, "user": user})
        if body["generationConfig"].get("responseMimeType") == "application/json":
            text = json.dumps({"severity": "medium", "surfaces": ["mcp", "secrets"], "needs_full_audit": True,
                               "rationale": "pedido toca configs MCP", "out_of_scope": ["ataque activo proibido"]})
        else:
            text = f"# {step}\n\nLacunas: sem acesso a ficheiros neste passo.\n"
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15}}

    ew_transport = ew.httpx_transport
    ew.httpx_transport = fake
    try:
        st = run_plan(PLAN, mode="external", out_dir=run_dir, worker="gemini")
    finally:
        ew.httpx_transport = ew_transport
    out = run_dir
    assert st["state"] == "paused_human_gate" and sorted(st["completed"]) == ["audit", "report", "triage"]
    assert sorted(p.name for p in (out / "artifacts").iterdir() if not p.name.endswith(".summary.md")) == ARTIFACTS

    by_step = {c["step"]: c for c in calls}
    assert list(by_step) == ["triage", "audit", "report"]
    expected = {"triage": ("security_triage", "Skill — security-triage"),
                "audit": ("security_audit", "Skill — security-audit"),
                "report": ("security_report", "Skill — security-report")}
    for step, (action, skill_title) in expected.items():
        res = json.loads((out / "pending_steps" / step / "result.json").read_text(encoding="utf-8"))
        ctx = res["meta"]["context"]
        assert ctx["policy"] == "opt" and ctx["grounding"] == "full", step  # área de risco: grounding completo
        assert f"- action: {action}" in by_step[step]["user"]
        assert skill_title in by_step[step]["system"], step
        assert "Nao tens tools" in by_step[step]["system"]  # tools_allowed é declarativo no worker

    # Nenhum passo pediu resumo: o report recebe a triagem completa (context.full).
    assert not (out / "artifacts/01-triage.summary.md").exists()
    for step in ("triage", "audit"):
        res = json.loads((out / "pending_steps" / step / "result.json").read_text(encoding="utf-8"))
        assert res["meta"]["context"]["summary"] == "not_needed", step
    report_inputs = json.loads((out / "pending_steps/report/result.json").read_text(encoding="utf-8"))["meta"]["context"]["inputs"]
    assert [i["mode"] for i in report_inputs] == ["full", "full"]

    # Limite documentado (AU-22): nenhum ficheiro do repo entra no prompt do auditor.
    assert "SECURITY.md" not in by_step["audit"]["user"] and "security-agents-stack" not in by_step["audit"]["user"]

    rows = [json.loads(x) for x in (out / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]
    assert [r["step_id"] for r in rows] == ["triage", "audit", "report"]
    assert [r["agent_id"] for r in rows] == ["security.triage", "meta.security-auditor", "security.reporter"]


@pytest.mark.parametrize("text", [
    "Preciso de uma security triage deste PR",
    "Mapeia a superficie de ataque do servidor MCP",
    "Plano de hardening das credenciais do CI",
])
def test_router_manda_pedidos_de_security_para_a_area_security(text):
    d = Router(transport=_router_llm("security.triage")).route(text)
    assert d.area == "security", d.to_dict()
    assert d.hitl_required and d.outcome == "agent" and d.agent == "security.triage"
    # os 3 agentes da área são candidatos do router (pipeline triage -> audit -> report)
    assert {"security.triage", "meta.security-auditor", "security.reporter"} <= set(d.candidates)


def test_threat_model_escala_para_o_conselho_de_security():
    d = Router(transport=lambda *a, **k: (_ for _ in ()).throw(AssertionError("sem LLM"))).route(
        "Precisamos de um threat model para o servidor MCP")
    assert (d.area, d.outcome, d.council) == ("security", "council", "security")
