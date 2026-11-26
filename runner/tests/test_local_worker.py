"""Worker local (servidor OpenAI-compatível). O servidor é falso, em HTTP real na máquina de teste."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import local_worker as lw
from plan_runner.engine import run_plan
from tests.politica import politica

ONE_STEP = """
id: local-um-passo
objective: Explicar AI Findability em poucas linhas.
steps:
  - id: research
    action: research
    output_artifact: artifacts/01-research.md
"""


class _Handler(BaseHTTPRequestHandler):
    seen: list[dict] = []
    status = 200

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        if type(self).status != 200:
            out = {"error": {"message": "modelo não encontrado"}}
        else:
            out = {"model": body["model"], "choices": [{"message": {"role": "assistant", "content": "# Saída local\n\nTexto."},
                                                         "finish_reason": "stop"}],
                   "usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150}}
        raw = json.dumps(out).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *a):  # silêncio
        pass


@pytest.fixture
def server(monkeypatch):
    _Handler.seen = []
    _Handler.status = 200
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    monkeypatch.setenv("LOCAL_LLM_URL", f"http://127.0.0.1:{srv.server_port}/v1")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "qwen2.5:3b")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "GEMINI_API_KEY", "LOCAL_LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    yield _Handler
    srv.shutdown()


# -- tradução --------------------------------------------------------------------
def test_pedido_gemini_vira_chat_completions():
    body = {"systemInstruction": {"parts": [{"text": "sê breve"}]},
            "contents": [{"role": "user", "parts": [{"text": "olá"}]}],
            "generationConfig": {"maxOutputTokens": 99, "responseMimeType": "application/json"}}
    req = lw.to_openai_request("https://x/v1beta/models/qwen2.5:3b:generateContent", body)
    assert req["model"] == "qwen2.5:3b"  # o `:` da tag do modelo não pode ser cortado
    assert req["messages"] == [{"role": "system", "content": "sê breve"}, {"role": "user", "content": "olá"}]
    assert req["max_tokens"] == 99 and req["response_format"] == {"type": "json_object"}


def test_tools_e_conversa_com_chamadas_de_ferramentas():
    body = {"contents": [
        {"role": "user", "parts": [{"text": "pesquisa"}]},
        {"role": "model", "parts": [{"functionCall": {"name": "buscar", "args": {"q": "x"}}}]},
        {"role": "user", "parts": [{"functionResponse": {"name": "buscar", "response": {"ok": True}}}]}],
        "tools": [{"functionDeclarations": [{"name": "buscar", "description": "d",
                                              "parameters": {"type": "OBJECT", "properties": {"q": {"type": "STRING"}}}}]}]}
    req = lw.to_openai_request("https://x/models/m:generateContent", body)
    assert req["tools"][0]["function"]["parameters"] == {"type": "object", "properties": {"q": {"type": "string"}}}
    assistant = req["messages"][1]
    assert assistant["tool_calls"][0]["function"] == {"name": "buscar", "arguments": '{"q": "x"}'}
    tool = req["messages"][2]
    assert tool["role"] == "tool" and tool["tool_call_id"] == assistant["tool_calls"][0]["id"]


def test_resposta_openai_volta_no_formato_gemini():
    resp = {"model": "m", "choices": [{"message": {"content": "olá", "tool_calls": [
        {"function": {"name": "f", "arguments": '{"a": 1}'}}]}, "finish_reason": "length"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}}
    g = lw.to_gemini_response(resp)
    parts = g["candidates"][0]["content"]["parts"]
    assert parts[0] == {"text": "olá"} and parts[1] == {"functionCall": {"name": "f", "args": {"a": 1}}}
    assert g["candidates"][0]["finishReason"] == "MAX_TOKENS"
    assert g["usageMetadata"] == {"promptTokenCount": 5, "candidatesTokenCount": 7, "totalTokenCount": 12}


# -- worker ----------------------------------------------------------------------
def test_sem_modelo_falha_com_mensagem_clara(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_MODEL", raising=False)
    with pytest.raises(ew.WorkerError, match="LOCAL_LLM_MODEL"):
        lw.LocalWorker()


def test_run_completo_contra_servidor_local(tmp_path, tmp_run_dir, server):
    plan = tmp_path / "plan.yaml"
    plan.write_text(politica(ONE_STEP), encoding="utf-8")
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="local")
    assert status["state"] == "done", status
    assert (tmp_run_dir / "artifacts/01-research.md").read_text(encoding="utf-8").startswith("# Saída local")
    assert len(server.seen) == 1 and server.seen[0]["path"] == "/v1/chat/completions"
    assert server.seen[0]["body"]["model"] == "qwen2.5:3b" and server.seen[0]["auth"] is None
    ledger = [json.loads(line) for line in (tmp_run_dir / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]
    assert ledger[0]["tokens_in"] == 120 and ledger[0]["tokens_out"] == 30 and ledger[0]["model"] == "qwen2.5:3b"


def test_tecto_de_usd_nao_bloqueia_o_modelo_local(tmp_path, tmp_run_dir, server):
    plan = tmp_path / "plan.yaml"
    plan.write_text(politica(ONE_STEP.replace("steps:", "budget: {max_cost_usd: 0.01}\nsteps:")), encoding="utf-8")
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="local")["state"] == "done"


def test_servidor_em_baixo_deixa_waiting_external_com_motivo(tmp_path, tmp_run_dir, monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_URL", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "m")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(var, raising=False)
    plan = tmp_path / "plan.yaml"
    plan.write_text(politica(ONE_STEP), encoding="utf-8")
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="local")
    assert status["state"] == "waiting_external"
    assert "servidor local sem resposta" in Path(tmp_run_dir / "pending_steps/research/worker_error.json").read_text(encoding="utf-8")


def test_erro_http_do_servidor_vira_workererror(tmp_path, tmp_run_dir, server):
    server.status = 404
    plan = tmp_path / "plan.yaml"
    plan.write_text(politica(ONE_STEP), encoding="utf-8")
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="local")["state"] == "waiting_external"


def test_chave_opcional_vai_no_header(server, monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_API_KEY", "segredo")
    w = lw.LocalWorker()
    w.transport("https://x/models/m:generateContent", {}, {"contents": [{"role": "user", "parts": [{"text": "a"}]}]}, 5.0)
    assert server.seen[-1]["auth"] == "Bearer segredo"
