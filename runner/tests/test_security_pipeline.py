"""Pipeline de security (triage -> audit -> report -> HITL) de ponta a ponta, sem rede.

Prova o que o plano demo promete e o que não promete:
- stub e external (Gemini falso) chegam ao HITL com os 3 artefactos;
- cada passo recebe o AGENT.md e a SKILL.md certos (S34 `vertical:` + A8 path-first);
- grounding `full` (área com `hitl: required`) e política `opt`;
- a triagem (JSON pequeno) NÃO é pedida em resumo (override `context.full` no report);
- em external o auditor recebe SÓ os ficheiros que o passo declara em `repo_files` (SEC-1);
  o `knowledge_refs` continua ignorado (AU-22) e os outros passos não recebem ficheiros;
- F0.5 (EXECUTION-PLAN §7): só o `audit` pede L5 (bloco `knowledge:`, kb `security`); sem MCP
  o passo continua com o aviso de falha, e com hits o prompt cita a fonte de cada um.
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
    # MCP_*: o passo `audit` tem bloco `knowledge:` (F0.5); sem estas variáveis o retrieve
    # falha de forma controlada e o teste nunca sai para a rede.
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL", "PLAN_RUNNER_CONTEXT",
                "MCP_API_KEY", "MCP_URL"):
        monkeypatch.delenv(var, raising=False)


def _fake_gemini(calls: list[dict]):
    """Gemini falso: regista o prompt de cada passo e responde JSON à triagem, Markdown ao resto."""
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
    return fake


def test_stub_chega_ao_hitl_com_os_3_artefactos(run_dir):
    st = run_plan(PLAN, mode="stub", out_dir=run_dir)
    assert st["state"] == "paused_human_gate" and st["paused_at_step"] == "hitl_security_decision"
    assert sorted(st["completed"]) == ["audit", "report", "triage"]
    assert sorted(p.name for p in (run_dir / "artifacts").iterdir()) == ARTIFACTS


def test_external_resolve_agentes_e_skills_e_nao_pede_resumo_da_triagem(run_dir):
    calls: list[dict] = []
    ew_transport = ew.httpx_transport
    ew.httpx_transport = _fake_gemini(calls)
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

    # SEC-1: o auditor recebe os ficheiros declarados em `repo_files` (e só esses).
    declared = ["runner/requirements.txt", "runner/requirements-langgraph.txt", "package.json",
                ".github/workflows/runner-tests.yml", "config/security-capabilities.yaml"]
    audit_user = by_step["audit"]["user"]
    assert "## Ficheiros do repo (so leitura)" in audit_user
    for rel in declared:
        assert f"### {rel}" in audit_user, rel
    assert "policy:\n  offensive: forbidden" in audit_user  # conteúdo real do security-capabilities.yaml
    audit_ctx = json.loads((out / "pending_steps/audit/result.json").read_text(encoding="utf-8"))["meta"]["context"]
    assert [(m["path"], m["status"]) for m in audit_ctx["repo_files"]] == [(r, "included") for r in declared]
    assert sum(m["bytes_in_prompt"] for m in audit_ctx["repo_files"]) < 50 * 1024
    for step in ("triage", "report"):  # só o passo que declara recebe ficheiros
        assert "Ficheiros do repo" not in by_step[step]["user"], step
    # AU-22 continua: o `knowledge_refs` do plano não é lido.
    assert "security-agents-stack" not in audit_user and "### docs/architecture/SECURITY.md" not in audit_user
    # F0.5: só o `audit` pede L5; sem MCP_API_KEY o retrieve falha de forma controlada,
    # o passo continua e o modelo é avisado (nunca inventar o contexto que faltou).
    assert "## Conhecimento recuperado (L5)" in audit_user and "[L5 CONTEXT: FALHA]" in audit_user
    for step in ("triage", "report"):
        assert "Conhecimento recuperado (L5)" not in by_step[step]["user"], step
        assert not (out / "pending_steps" / step / "knowledge_context.md").exists(), step
    events = [json.loads(x) for x in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    failed = [e["payload"] for e in events if e["type"] == "knowledge_context_failed"]
    assert [(p["step_id"], p["kb"]) for p in failed] == [("audit", "security")]

    rows = [json.loads(x) for x in (out / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]
    assert [r["step_id"] for r in rows] == ["triage", "audit", "report"]
    assert [r["agent_id"] for r in rows] == ["security.triage", "meta.security-auditor", "security.reporter"]


def test_audit_recebe_o_l5_de_security_com_a_fonte_citada(run_dir, monkeypatch):
    """F0.5 com hits: o pedido ao MCP usa kb `security` e a query do plano; o prompt do
    auditor traz cada excerto com a fonte (proveniência mínima actual: só `source`, F0.8)."""
    from plan_runner import knowledge_wiring as kw

    asked: list[dict] = []

    class FakeMcp:
        def retrieve(self, kb, query, *, top_k, filters, require_citations):
            asked.append({"kb": kb, "query": query, "top_k": top_k})
            return [{"content": "A área security é só defensiva: ler, classificar, auditar passivamente e reportar.",
                     "citation": {"source": "docs/knowledge/security-agents-stack.md", "locator": None}}]

    monkeypatch.setattr(kw, "McpKnowledge", FakeMcp)
    calls: list[dict] = []
    monkeypatch.setattr(ew, "httpx_transport", _fake_gemini(calls))
    st = run_plan(PLAN, mode="external", out_dir=run_dir, worker="gemini")
    assert st["state"] == "paused_human_gate"
    assert [a["kb"] for a in asked] == ["security"] and asked[0]["top_k"] == 5
    assert "security-auditor" in asked[0]["query"]
    audit_user = next(c["user"] for c in calls if c["step"] == "audit")
    assert "A área security é só defensiva" in audit_user
    assert "[Fonte: docs/knowledge/security-agents-stack.md @ ?]" in audit_user
    events = [json.loads(x) for x in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    injected = [e["payload"] for e in events if e["type"] == "knowledge_context_injected"]
    assert injected == [{"step_id": "audit", "kb": "security", "hit_count": 1}]


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
