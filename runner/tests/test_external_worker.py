"""AU-23: worker do modo external (plan_runner/external_worker.py).

O Gemini e sempre falso (transport injectado): nenhum teste sai para a rede
nem escreve no Supabase (SUPABASE_* removidas do ambiente em cada teste).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner.engine import PlanError, resume_run, run_plan

REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_DEMO = REPO_ROOT / "docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml"

USAGE = {
    "promptTokenCount": 812,
    "candidatesTokenCount": 143,
    "totalTokenCount": 955,
    "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 812}],
    "serviceTier": "standard",
}
LEDGER_COLUMNS = {
    "run_id", "agent_id", "call_kind", "model", "model_version", "tokens_in", "tokens_out",
    "tokens_total", "status", "raw_usage", "service_tier", "response_id",
}


class FakeGemini:
    """Responde como o generateContent real (formato confirmado a 2026-09-30)."""

    def __init__(self, *, status: int = 200, error: str = "", usage: dict | None = USAGE):
        self.calls: list[dict] = []
        self.status = status
        self.error = error
        self.usage = usage

    def __call__(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body})
        if self.status != 200:
            return self.status, {"error": {"code": self.status, "message": self.error}}
        wants_json = body["generationConfig"].get("responseMimeType") == "application/json"
        text = json.dumps({"titulo": f"saida {len(self.calls)}"}) if wants_json else f"# Saida {len(self.calls)}\n\nTexto."
        resp = {
            "candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": "STOP"}],
            "modelVersion": "gemini-3.5-flash-lite",
            "responseId": f"resp-{len(self.calls)}",
        }
        if self.usage is not None:
            resp["usageMetadata"] = self.usage
        return 200, resp


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


def _plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(body, encoding="utf-8")
    return p


ONE_STEP = """
id: worker-um-passo
objective: Explicar AI Findability em poucas linhas.
steps:
  - id: research
    action: research
    output_artifact: artifacts/01-research.md
"""

WITH_GATE = """
id: worker-com-gate
objective: Brief interno.
steps:
  - id: research
    action: research
    output_artifact: artifacts/01-research.md
  - id: aprovar
    action: plan_approve
    depends_on: [research]
    human_gate: {level: step, kind: output_review, allow: [approve, reject]}
    output_artifact: artifacts/02-hitl.json
  - id: brief
    action: internal_brief
    depends_on: [aprovar]
    output_artifact: artifacts/03-brief.md
"""


def _ledger(out: Path) -> list[dict]:
    p = out / ew.LEDGER_FILE
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


# --------------------------------------------------------------------------
# request.json -> Gemini -> result.json -> token_usage
# --------------------------------------------------------------------------

def test_le_request_chama_gemini_escreve_result_e_regista_tokens(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "done", status
    assert status["worker"] == "gemini"

    # 1 chamada, ao modelo barato, com a chave no header e nao no URL
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["url"].endswith("/models/gemini-flash-lite-latest:generateContent")
    assert "key=" not in call["url"]
    assert call["headers"] == {"x-goog-api-key": "chave-de-teste"}

    # O prompt vem do request.json + AGENT.md + SKILL.md copiados pelo executor
    pending = tmp_run_dir / "pending_steps" / "research"
    request = json.loads((pending / "request.json").read_text(encoding="utf-8"))
    system = call["body"]["systemInstruction"]["parts"][0]["text"]
    user = call["body"]["contents"][0]["parts"][0]["text"]
    assert (pending / "AGENT.md").read_text(encoding="utf-8").strip()[:200] in system
    assert (pending / "SKILL.md").read_text(encoding="utf-8").strip()[:200] in system
    assert "Directiva de grounding" in system
    assert request["output_artifact"] in system
    assert "Explicar AI Findability" in user
    assert "responseMimeType" not in call["body"]["generationConfig"]  # .md -> texto

    # result.json no formato que o executor le, e o artefacto escrito pelo executor
    result = json.loads((pending / "result.json").read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["detail"] == "gemini:gemini-3.5-flash-lite"
    assert result["meta"]["tokens_total"] == 955
    assert (tmp_run_dir / "artifacts/01-research.md").read_text(encoding="utf-8").startswith("# Saida 1")

    # Ledger J6: 1 linha, mesmo contrato da tabela token_usage
    [row] = _ledger(tmp_run_dir)
    assert row["call_kind"] == "agent"
    assert row["agent_id"] == "marketing.research"
    assert row["model"] == "gemini-flash-lite-latest"
    assert row["model_version"] == "gemini-3.5-flash-lite"
    assert (row["tokens_in"], row["tokens_out"], row["tokens_total"]) == (812, 143, 955)
    assert row["status"] == "ok" and row["service_tier"] == "standard"
    assert row["raw_usage"] == USAGE and row["response_id"] == "resp-1"
    assert row["run_id"] == ew.ledger_run_uuid(status["run_id"])
    assert row["runner_run_id"] == status["run_id"] and row["step_id"] == "research"
    assert row["remote"] == "skipped"  # sem SUPABASE_* no ambiente

    events = [json.loads(line)["type"] for line in (tmp_run_dir / "events.jsonl").read_text().splitlines()]
    assert "step_waiting_external" not in events and events[-1] == "plan_done"


def test_artefacto_json_pede_json_e_grava_objecto(tmp_path, tmp_run_dir, fake):
    plan = _plan(tmp_path, """
id: worker-json
objective: Brief SEO.
steps:
  - id: seo_brief
    action: seo_brief
    output_artifact: artifacts/02-seo-brief.json
    output_schema: SeoBrief
""")
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")["state"] == "done"
    gen = fake.calls[0]["body"]["generationConfig"]
    assert gen["responseMimeType"] == "application/json"
    assert "SeoBrief" in fake.calls[0]["body"]["systemInstruction"]["parts"][0]["text"]
    assert json.loads((tmp_run_dir / "artifacts/02-seo-brief.json").read_text()) == {"titulo": "saida 1"}


def test_inputs_e_artefactos_das_dependencias_entram_no_prompt(tmp_path, tmp_run_dir, fake):
    plan = _plan(tmp_path, """
id: worker-deps
objective: x
steps:
  - id: research
    action: research
    output_artifact: artifacts/01-research.md
  - id: brief
    action: internal_brief
    depends_on: [research]
    output_artifact: artifacts/02-brief.md
""")
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")["state"] == "done"
    user = fake.calls[1]["body"]["contents"][0]["parts"][0]["text"]
    assert "## Input: artifacts/01-research.md" in user and "# Saida 1" in user


# --------------------------------------------------------------------------
# HITL
# --------------------------------------------------------------------------

def test_hitl_para_o_worker_no_gate_e_continua_depois_da_decisao(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path, WITH_GATE), mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "paused_human_gate"
    assert status["paused_at_step"] == "aprovar"
    assert len(fake.calls) == 1  # so o research; o passo humano nunca vai ao Gemini
    assert not (tmp_run_dir / "pending_steps" / "aprovar" / "result.json").exists()
    assert (tmp_run_dir / "hitl-requests.jsonl").read_text(encoding="utf-8").strip()

    # O worker recusa avancar enquanto ha decisao humana pendente
    with pytest.raises(ew.HumanGateBlocked, match="paused_human_gate"):
        ew.GeminiWorker(transport=fake).process(tmp_run_dir, "brief")
    assert len(fake.calls) == 1

    # Depois do approve, o resume usa o mesmo worker (guardado no status) ate ao fim
    status = resume_run(tmp_run_dir, decision="approve")
    assert status["state"] == "done", status
    assert len(fake.calls) == 2
    assert [r["step_id"] for r in _ledger(tmp_run_dir)] == ["research", "brief"]


def test_worker_nunca_executa_um_passo_com_human_gate(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, WITH_GATE), mode="external", out_dir=tmp_run_dir, worker="gemini")
    status = json.loads((tmp_run_dir / "status.json").read_text())
    status["state"] = "running"  # mesmo sem o run pausado, o passo e humano
    (tmp_run_dir / "status.json").write_text(json.dumps(status))
    with pytest.raises(ew.HumanGateBlocked, match="human_gate"):
        ew.GeminiWorker(transport=fake).process(tmp_run_dir, "aprovar")
    assert len(fake.calls) == 1


def test_reject_no_gate_termina_sem_mais_chamadas(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, WITH_GATE), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert resume_run(tmp_run_dir, decision="reject")["state"] == "rejected"
    assert len(fake.calls) == 1


# --------------------------------------------------------------------------
# Falhas: o passo fica em waiting_external e o resume tenta outra vez
# --------------------------------------------------------------------------

def test_erro_do_gemini_deixa_waiting_external_sem_result_e_resume_recupera(tmp_path, tmp_run_dir, monkeypatch):
    bad = FakeGemini(status=429, error="Resource has been exhausted")
    monkeypatch.setattr(ew, "httpx_transport", bad)
    status = run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir, worker="gemini")

    assert status["state"] == "waiting_external"
    assert "HTTP 429" in status["worker_error"]
    pending = tmp_run_dir / "pending_steps" / "research"
    assert not (pending / "result.json").exists()
    assert "Resource has been exhausted" in json.loads((pending / ew.ERROR_FILE).read_text())["error"]
    assert _ledger(tmp_run_dir) == []  # pedido recusado: sem tokens gastos
    events = [json.loads(line) for line in (tmp_run_dir / "events.jsonl").read_text().splitlines()]
    assert any(e["type"] == "step_waiting_external" and "HTTP 429" in e["payload"]["worker_error"] for e in events)

    good = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", good)
    status = resume_run(tmp_run_dir, decision="approve")
    assert status["state"] == "done" and "worker_error" not in status
    assert not (pending / ew.ERROR_FILE).exists()
    assert len(_ledger(tmp_run_dir)) == 1


def test_sem_chave_fica_em_waiting_external_com_motivo(tmp_path, tmp_run_dir, fake, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    status = run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "waiting_external"
    assert "GEMINI_API_KEY" in status["worker_error"]
    assert fake.calls == []


def test_resposta_vazia_e_json_invalido_nao_escrevem_result(tmp_path, tmp_run_dir):
    run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir)  # sem worker
    empty = lambda *a: (200, {"candidates": [{"content": {"parts": []}, "finishReason": "SAFETY"}], "usageMetadata": USAGE})  # noqa: E731
    with pytest.raises(ew.WorkerError, match="finishReason=SAFETY"):
        ew.GeminiWorker(transport=empty).process(tmp_run_dir, "research")
    assert not (tmp_run_dir / "pending_steps/research/result.json").exists()
    assert len(_ledger(tmp_run_dir)) == 1  # a chamada gastou tokens: fica registada

    pending = tmp_run_dir / "pending_steps/research"
    req = json.loads((pending / "request.json").read_text())
    req["output_artifact"] = "artifacts/x.json"
    (pending / "request.json").write_text(json.dumps(req))
    bad_json = lambda *a: (200, {"candidates": [{"content": {"parts": [{"text": "isto nao e json"}]}}]})  # noqa: E731
    with pytest.raises(ew.WorkerError, match="JSON invalido"):
        ew.GeminiWorker(transport=bad_json).process(tmp_run_dir, "research")


def test_worker_so_com_mode_external(tmp_path, tmp_run_dir):
    with pytest.raises(PlanError, match="--mode external"):
        run_plan(_plan(tmp_path, ONE_STEP), mode="stub", out_dir=tmp_run_dir, worker="gemini")


def test_sem_worker_o_contrato_antigo_fica_igual(tmp_path, tmp_run_dir, fake):
    status = run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir)
    assert status["state"] == "waiting_external" and "worker" not in status
    assert fake.calls == []


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

def test_ledger_remoto_recebe_so_colunas_da_tabela_e_falha_nao_parte_o_passo(tmp_path, tmp_run_dir, fake):
    run_plan(_plan(tmp_path, ONE_STEP), mode="external", out_dir=tmp_run_dir)
    sent: list[dict] = []
    ew.GeminiWorker(transport=fake, remote_ledger=sent.append).process(tmp_run_dir, "research")
    assert set(sent[0]) == LEDGER_COLUMNS
    assert _ledger(tmp_run_dir)[0]["remote"] == "ok"

    (tmp_run_dir / "pending_steps/research/result.json").unlink()

    def broken(row):
        raise RuntimeError("HTTP 401: Invalid API key")

    result = ew.GeminiWorker(transport=fake, remote_ledger=broken).process(tmp_run_dir, "research")
    assert result["ok"] is True
    assert _ledger(tmp_run_dir)[1]["remote"].startswith("error: HTTP 401")


def test_supabase_so_com_as_duas_variaveis(monkeypatch):
    assert ew.supabase_sink_from_env() is None
    monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
    assert ew.supabase_sink_from_env() is None
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    assert callable(ew.supabase_sink_from_env())


def test_usage_ausente_grava_missing_usage():
    row = ew.build_usage_row(run_id="run_abc", agent_id="a", model="m", response={"modelVersion": "v"})
    assert row["status"] == "missing_usage"
    assert row["tokens_in"] is row["tokens_total"] is row["raw_usage"] is None
    assert row["run_id"] == ew.ledger_run_uuid("run_abc") != ew.ledger_run_uuid("run_abd")


# --------------------------------------------------------------------------
# CLI standalone (runs ja parados em waiting_external)
# --------------------------------------------------------------------------

def test_cli_standalone_executa_o_passo_pendente_e_retoma(tmp_path, tmp_run_dir, fake, capsys):
    plan = _plan(tmp_path, ONE_STEP.replace(
        "    output_artifact: artifacts/01-research.md\n",
        "    output_artifact: artifacts/01-research.md\n"
        "  - id: brief\n    action: internal_brief\n    depends_on: [research]\n"
        "    output_artifact: artifacts/02-brief.md\n",
    ))
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir)["state"] == "waiting_external"

    assert ew.main([str(tmp_run_dir)]) == 0
    assert (tmp_run_dir / "pending_steps/research/result.json").exists()
    assert len(fake.calls) == 1

    assert ew.main([str(tmp_run_dir)]) == 0  # idempotente: o result.json ja existe
    assert len(fake.calls) == 1
    capsys.readouterr()
    status = resume_run(tmp_run_dir, decision="approve", worker="gemini")
    assert status["state"] == "done" and len(fake.calls) == 2


def test_cli_standalone_recusa_run_em_paused_human_gate(tmp_path, tmp_run_dir, fake, capsys):
    run_plan(_plan(tmp_path, WITH_GATE), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert ew.main([str(tmp_run_dir), "--resume"]) == 2
    assert "hitl:" in capsys.readouterr().err
    assert len(fake.calls) == 1


# --------------------------------------------------------------------------
# DONE: plano de exemplo real, do inicio ao fim, em modo external
# --------------------------------------------------------------------------

def test_plano_seo_demo_do_inicio_ao_fim_com_worker(tmp_run_dir, fake):
    status = run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate" and status["paused_at_step"] == "hitl_publish_decision"
    assert status["completed"] == ["copy", "critic", "research", "seo_brief"]

    status = resume_run(tmp_run_dir, decision="approve")
    assert status["state"] == "done", status

    for art in ("01-research.md", "02-seo-brief.json", "03-copy.md", "04-critic.json", "05-hitl.json"):
        assert (tmp_run_dir / "artifacts" / art).is_file(), art
    json.loads((tmp_run_dir / "artifacts/04-critic.json").read_text())  # JSON valido
    rows = _ledger(tmp_run_dir)
    assert [r["step_id"] for r in rows] == ["research", "seo_brief", "copy", "critic"]
    assert {r["agent_id"] for r in rows} == {
        "marketing.research", "marketing.seo_brief", "marketing.copy_answer_first", "marketing.critic_item13",
    }
    assert len({r["run_id"] for r in rows}) == 1 and sum(r["tokens_total"] for r in rows) == 4 * 955
