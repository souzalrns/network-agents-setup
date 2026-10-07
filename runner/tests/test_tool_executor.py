"""AU-20 (P-37 = B): executor de tools do worker. O Gemini é sempre falso (guião de respostas).

Unidade: autorização (tools_allowed ∩ registo; `read` corre, `act` pára no HITL), kb
permitido ao passo, validação dos args,
limites, dados-não-instruções, thought signatures preservadas, conhecimento com
backend falso. Integração: run_plan real com o worker, com a flag ligada e
desligada (sem a flag, o passo faz a chamada única de sempre).
"""
from __future__ import annotations

import copy
import json
import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import tool_executor as te
from plan_runner.engine import run_plan

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRET = "SEGREDO-NAO-PODE-SAIR-123"
USAGE = {"promptTokenCount": 100, "candidatesTokenCount": 10, "totalTokenCount": 110}


def _call(name: str, args: dict, *, id_: str | None = None, signature: str | None = None) -> dict:
    part: dict = {"functionCall": {"name": name, "args": args}}
    if id_:
        part["functionCall"]["id"] = id_
    if signature:
        part["thoughtSignature"] = signature
    return {"candidates": [{"content": {"role": "model", "parts": [part]}, "finishReason": "STOP"}],
            "usageMetadata": USAGE, "modelVersion": "gemini-test", "responseId": "r"}


def _text(text: str) -> dict:
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": "STOP"}],
            "usageMetadata": USAGE, "modelVersion": "gemini-test", "responseId": "r"}


class Script:
    """Transport do Gemini com um guião: devolve as respostas por ordem e guarda os bodies."""

    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.bodies: list[dict] = []

    def __call__(self, url, headers, body, timeout):
        self.bodies.append(copy.deepcopy(body))
        if not self.responses:
            raise AssertionError("o worker pediu mais turnos do que o guião tem")
        return 200, self.responses.pop(0)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL", "PLAN_RUNNER_CONTEXT", te.ENV_FLAG):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def run_dir():
    d = REPO_ROOT / "pilots" / f"_pytest_tools_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _plan(tmp_path: Path, steps: list[dict], **top) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump({"id": "teste-tools", "version": 1, "objective": "testar tools", **top, "steps": steps}), encoding="utf-8")
    return p


def _events(run_dir: Path, type_: str) -> list[dict]:
    lines = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["type"] == type_]


def _ctx(tmp_path: Path, backend=None) -> te.ToolContext:
    return te.ToolContext(repo_root=REPO_ROOT, out_root=tmp_path, step_id="s", knowledge_backend=backend)


# --------------------------------------------------------------------------- política


def test_plano_de_tools_intersecta_com_o_registo():
    plan = te.plan_tools(["read_repo_file", "web_search", "read_repo_file", "retrieve_knowledge"], kbs=["marketing"])
    assert plan.allowed == ["read_repo_file", "retrieve_knowledge"] and plan.needs_approval == []
    assert plan.unsupported == ["web_search"] and plan.active
    act = te.Tool("apagar", "x", {"type": "object"}, "act", lambda a, c: {"ok": True})
    prep = te.Tool("rascunho", "x", {"type": "object"}, "prepare", lambda a, c: {"ok": True})
    plan2 = te.plan_tools(["apagar", "rascunho"], registry={"apagar": act, "rascunho": prep})
    assert plan2.allowed == ["apagar"] and plan2.needs_approval == ["apagar"]  # act: autorizada, com aprovação
    assert plan2.refused_level == ["rascunho"]  # prepare continua recusado
    assert not te.plan_tools([]).active and not te.plan_tools(None).active


def test_retrieve_knowledge_sem_kb_do_passo_nao_e_oferecido():
    plan = te.plan_tools(["read_repo_file", "retrieve_knowledge"])
    assert plan.allowed == ["read_repo_file"] and plan.refused_policy == ["retrieve_knowledge"]


def test_kb_permitidos_vem_do_passo():
    assert te.step_kbs({}) == ([], [])
    assert te.step_kbs({"knowledge": {"kb": "marketing", "query": "q"}}) == (["marketing"], [])
    # tool_kbs manda sobre o knowledge.kb
    assert te.step_kbs({"tool_kbs": ["legal", "global"], "knowledge": {"kb": "marketing"}}) == (["legal", "global"], [])
    kbs, w = te.step_kbs({"tool_kbs": ["legal", "legal", "a b", 7, "x" * 41]})
    assert kbs == ["legal"] and len(w) == 3
    assert te.step_kbs({"tool_kbs": "legal"})[0] == [] and te.step_kbs({"tool_kbs": "legal"})[1]


def test_declaracao_do_retrieve_knowledge_restringe_o_kb():
    plan = te.plan_tools(["retrieve_knowledge"], kbs=["legal", "global"])
    decl = te.declarations_for(plan)[0]
    assert decl["parameters"]["properties"]["kb"]["enum"] == ["legal", "global"]
    assert "enum" not in te.REGISTRY["retrieve_knowledge"].parameters["properties"]["kb"]  # o registo não muda


def test_flag_so_liga_com_valores_explicitos():
    assert te.tools_enabled_from_env({te.ENV_FLAG: "1"}) and te.tools_enabled_from_env({te.ENV_FLAG: "true"})
    assert not te.tools_enabled_from_env({}) and not te.tools_enabled_from_env({te.ENV_FLAG: "0"})


def test_limites_do_passo_com_tecto_rigido():
    assert te.ToolLimits.from_step({}) == (te.ToolLimits(), [])
    lim, w = te.ToolLimits.from_step({"tool_limits": {"max_turns": 3, "max_tool_calls": 999}})
    assert lim == te.ToolLimits(3, te.HARD_MAX_TOOL_CALLS) and any("tecto" in x for x in w)
    lim, w = te.ToolLimits.from_step({"tool_limits": {"max_turns": 0, "max_tool_calls": True}})
    assert lim == te.ToolLimits() and len(w) == 2
    assert te.ToolLimits.from_step({"tool_limits": [1]})[1]


# --------------------------------------------------------------------------- uma chamada


def test_tool_nao_autorizada_nao_corre(tmp_path):
    ran = []
    reg = {**te.REGISTRY, "espiao": te.Tool("espiao", "x", {"type": "object"}, "read", lambda a, c: ran.append(1) or {"ok": True})}
    plan = te.plan_tools(["read_repo_file"], registry=reg)
    resp, rec = te.execute_call({"name": "espiao", "args": {}}, plan, _ctx(tmp_path), reg)
    assert resp["error"] == "tool_not_allowed" and not rec["ok"] and ran == []


def test_tool_act_exige_aprovacao_e_nao_corre(tmp_path):
    ran = []
    act = te.Tool("apagar", "x", {"type": "object"}, "act", lambda a, c: ran.append(1) or {"ok": True})
    plan = te.ToolPlan(allowed=["apagar"])  # mesmo que algo a deixe passar no plano, a execução recusa
    resp, _ = te.execute_call({"name": "apagar", "args": {}}, plan, _ctx(tmp_path), {"apagar": act})
    assert resp["error"] == "requires_approval" and ran == []
    no, rec = te.execute_call({"name": "apagar", "args": {}}, plan, _ctx(tmp_path), {"apagar": act}, approval="reject")
    assert no["error"] == "rejected_by_human" and rec["approval"] == "reject" and ran == []
    yes, rec = te.execute_call({"name": "apagar", "args": {}}, plan, _ctx(tmp_path), {"apagar": act}, approval="approve")
    assert yes["ok"] and rec["approval"] == "approve" and ran == [1]


@pytest.mark.parametrize("args", [{}, {"path": ""}, {"path": "a", "extra": 1}, {"path": 7}])
def test_args_invalidos_sao_recusados_antes_de_executar(tmp_path, args):
    plan = te.plan_tools(["read_repo_file"])
    resp, rec = te.execute_call({"name": "read_repo_file", "args": args}, plan, _ctx(tmp_path))
    assert resp["error"] == "invalid_args" and "args_sha256" in rec


def test_read_repo_file_le_e_recusa_segredos(tmp_path):
    plan = te.plan_tools(["read_repo_file"])
    ok, rec = te.execute_call({"name": "read_repo_file", "args": {"path": "runner/requirements.txt"}}, plan, _ctx(tmp_path))
    assert ok["ok"] and "PyYAML" in ok["content"] and rec["sources"] == ["runner/requirements.txt"]
    assert ok["note"] == te.DATA_NOTE
    for path in (".env", "../fora.txt", "secrets/x.txt", "nao/existe.md"):
        resp, _ = te.execute_call({"name": "read_repo_file", "args": {"path": path}}, plan, _ctx(tmp_path))
        assert not resp["ok"], path


class FakeKnowledge:
    def __init__(self):
        self.calls = []

    def retrieve(self, kb, query, *, top_k, filters, require_citations):
        self.calls.append((kb, query, top_k, require_citations))
        return [{"content": "Prazo de contestação: 15 dias úteis.", "source": "legal/direito-br-pt.md",
                 "citation": {"uri": "https://exemplo/lei", "source": "legal/direito-br-pt.md"}}]


def test_retrieve_knowledge_com_backend_falso(tmp_path):
    kb = FakeKnowledge()
    plan = te.plan_tools(["retrieve_knowledge"], kbs=["legal"])
    resp, rec = te.execute_call({"name": "retrieve_knowledge", "args": {"kb": "legal", "query": "prazo", "top_k": 3}},
                                plan, _ctx(tmp_path, backend=lambda: kb))
    assert resp["ok"] and resp["hits"] == 1 and "15 dias" in resp["content"]
    assert kb.calls == [("legal", "prazo", 3, True)] and rec["sources"] == ["legal/direito-br-pt.md"]
    bad, _ = te.execute_call({"name": "retrieve_knowledge", "args": {"kb": "legal; drop", "query": "x"}},
                             plan, _ctx(tmp_path, backend=lambda: kb))
    assert bad["error"] == "invalid_args" and len(kb.calls) == 1
    # kb válido mas não permitido ao passo: não chega ao L5
    other, rec = te.execute_call({"name": "retrieve_knowledge", "args": {"kb": "security", "query": "x"}},
                                 plan, _ctx(tmp_path, backend=lambda: kb))
    assert other["error"] == "kb_not_allowed" and "legal" in other["detail"] and len(kb.calls) == 1 and not rec["ok"]


def test_tool_que_rebenta_volta_como_erro(tmp_path):
    def boom(args, ctx):
        raise RuntimeError("falhou")
    reg = {"x": te.Tool("x", "x", {"type": "object"}, "read", boom)}
    resp, rec = te.execute_call({"name": "x", "args": {}}, te.ToolPlan(allowed=["x"]), _ctx(tmp_path), reg)
    assert resp["error"] == "tool_error" and resp["detail"] == "RuntimeError" and not rec["ok"]


def test_output_grande_e_cortado(tmp_path):
    reg = {"x": te.Tool("x", "x", {"type": "object"}, "read", lambda a, c: {"ok": True, "content": "a" * 50}, max_output_chars=10)}
    resp, rec = te.execute_call({"name": "x", "args": {}}, te.ToolPlan(allowed=["x"]), _ctx(tmp_path), reg)
    assert resp["truncated"] and resp["content"].startswith("a" * 10) and "cortado" in resp["content"] and rec["truncated"]


# --------------------------------------------------------------------------- loop


def _gen(script: Script):
    def generate(contents, declarations):
        return script(None, None, {"contents": contents, "declarations": declarations}, 0)[1]
    return generate


def test_loop_preserva_thought_signature_e_ids(tmp_path):
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"}, id_="c1", signature="SIG=="), _text("fim")])
    res = te.run_tool_loop(user="pedido", plan=te.plan_tools(["read_repo_file"]), ctx=_ctx(tmp_path),
                           limits=te.ToolLimits(), generate=_gen(script))
    assert res.turns == 2 and len(res.calls) == 1 and res.calls[0]["ok"]
    second = script.bodies[1]["contents"]
    assert second[1] == {"role": "model", "parts": [{"functionCall": {"name": "read_repo_file", "args": {"path": "runner/requirements.txt"}, "id": "c1"}, "thoughtSignature": "SIG=="}]}
    fr = second[2]["parts"][0]["functionResponse"]
    assert fr["name"] == "read_repo_file" and fr["id"] == "c1" and fr["response"]["ok"]
    assert [d["name"] for d in script.bodies[0]["declarations"]] == ["read_repo_file"]


def test_loop_para_no_max_turns(tmp_path):
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"})] * 5)
    with pytest.raises(te.ToolLoopError) as e:
        te.run_tool_loop(user="u", plan=te.plan_tools(["read_repo_file"]), ctx=_ctx(tmp_path),
                         limits=te.ToolLimits(max_turns=2, max_tool_calls=10), generate=_gen(script))
    assert e.value.reason == "max_turns" and len(script.bodies) == 2


def test_loop_para_no_max_tool_calls(tmp_path):
    many = {"candidates": [{"content": {"role": "model", "parts": [
        {"functionCall": {"name": "read_repo_file", "args": {"path": "runner/requirements.txt"}}}] * 3}}], "usageMetadata": USAGE}
    script = Script([many])
    with pytest.raises(te.ToolLoopError) as e:
        te.run_tool_loop(user="u", plan=te.plan_tools(["read_repo_file"]), ctx=_ctx(tmp_path),
                         limits=te.ToolLimits(max_turns=5, max_tool_calls=2), generate=_gen(script))
    assert e.value.reason == "max_tool_calls"


def test_before_turn_corre_antes_de_cada_turno_extra(tmp_path):
    seen = []
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"}), _text("fim")])
    te.run_tool_loop(user="u", plan=te.plan_tools(["read_repo_file"]), ctx=_ctx(tmp_path), limits=te.ToolLimits(),
                     generate=_gen(script), before_turn=seen.append)
    assert seen == [2]


# --------------------------------------------------------------------------- worker (run_plan real)


STEP = {"id": "s", "action": "research", "output_artifact": "artifacts/01.md", "tools_allowed": ["read_repo_file", "web_search"]}


def test_sem_flag_o_passo_faz_a_chamada_unica_de_sempre(tmp_path, run_dir, monkeypatch):
    script = Script([_text("# artefacto\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [STEP]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    body = script.bodies[0]
    assert "tools" not in body and len(script.bodies) == 1
    assert ew.NO_TOOLS_SENTENCE in body["systemInstruction"]["parts"][0]["text"]
    result = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))
    # P-42 = A (AU-20b): a flag desligada fica escrita no resultado, não só pela ausência do campo
    assert result["meta"]["tools"] == {"enabled": False, "reason": "PLAN_RUNNER_TOOLS desligada",
                                       "flag": "PLAN_RUNNER_TOOLS", "tools_allowed": ["read_repo_file", "web_search"]}


@pytest.mark.parametrize("context", ["opt", "legacy"])
def test_com_flag_o_worker_usa_a_tool_e_audita(tmp_path, run_dir, monkeypatch, context):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    monkeypatch.setenv("PLAN_RUNNER_CONTEXT", context)
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"}, id_="c1"), _text("# artefacto final\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [STEP]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"

    first, second = script.bodies
    system = first["systemInstruction"]["parts"][0]["text"]
    assert ew.NO_TOOLS_SENTENCE not in system and "SÓ DE LEITURA" in system and te.DATA_NOTE in system
    assert first["tools"] == [{"functionDeclarations": [te.REGISTRY["read_repo_file"].declaration()]}]  # web_search nunca é declarada
    assert "responseMimeType" not in first["generationConfig"]
    assert second["contents"][2]["parts"][0]["functionResponse"]["response"]["ok"]

    result = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))
    tools = result["meta"]["tools"]
    assert tools["enabled"] and tools["turns"] == 2 and tools["unsupported"] == ["web_search"]
    assert tools["calls"][0]["tool"] == "read_repo_file" and tools["calls"][0]["ok"]
    assert result["meta"]["tokens_total"] == 2 * USAGE["totalTokenCount"]  # soma dos turnos
    assert (run_dir / "artifacts/01.md").read_text(encoding="utf-8").startswith("# artefacto final")

    ev = _events(run_dir, "tool_called")
    assert len(ev) == 1 and ev[0]["payload"]["step_id"] == "s" and len(ev[0]["payload"]["args_sha256"]) == 64
    assert "runner/requirements.txt" not in json.dumps(ev[0]["payload"].get("args", ""))  # args em claro nunca
    ledger = (run_dir / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()
    assert len(ledger) == 2  # 1 linha por turno


def test_com_flag_segredo_nunca_chega_ao_modelo(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    secret_rel = f"pilots/{run_dir.name}-env/.env"
    secret = REPO_ROOT / secret_rel
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text(SECRET, encoding="utf-8")
    try:
        script = Script([_call("read_repo_file", {"path": secret_rel}), _text("# ok\n")])
        monkeypatch.setattr(ew, "httpx_transport", script)
        assert run_plan(_plan(tmp_path, [STEP]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
        assert SECRET not in json.dumps(script.bodies)
        result = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))
        assert result["meta"]["tools"]["calls"][0]["error"] == "excluded"
    finally:
        shutil.rmtree(secret.parent, ignore_errors=True)


def test_com_flag_limite_deixa_o_passo_em_waiting_external(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    step = {**STEP, "tool_limits": {"max_turns": 2}}
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"})] * 3)
    monkeypatch.setattr(ew, "httpx_transport", script)
    st = run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")
    assert st["state"] == "waiting_external" and len(script.bodies) == 2
    pending = run_dir / "pending_steps/s"
    assert not (pending / "result.json").exists()
    assert "max_turns" in json.loads((pending / ew.ERROR_FILE).read_text(encoding="utf-8"))["error"]


def test_com_flag_orcamento_para_antes_do_turno_seguinte(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"}), _text("# nunca chega\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    st = run_plan(_plan(tmp_path, [STEP], budget={"max_tokens": 100}), mode="external", out_dir=run_dir, worker="gemini")
    assert st["state"] == "paused_budget" and len(script.bodies) == 1  # o 2.º turno nunca é pedido


def test_com_flag_passo_sem_tools_do_registo_fica_igual(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    step = {**STEP, "tools_allowed": ["web_search"]}
    script = Script([_text("# ok\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    assert "tools" not in script.bodies[0] and len(script.bodies) == 1
    result = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))
    assert result["meta"]["tools"] == {"enabled": False, "reason": "nenhuma tool do passo esta no registo",
                                      "unsupported": ["web_search"], "refused_level": []}


def test_com_flag_artefacto_json_continua_a_ser_lido(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    step = {**STEP, "output_artifact": "artifacts/01.json"}
    script = Script([_call("read_repo_file", {"path": "runner/requirements.txt"}), _text('```json\n{"ok": 1}\n```')])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    assert json.loads((run_dir / "artifacts/01.json").read_text(encoding="utf-8")) == {"ok": 1}


# --------------------------------------------------------------------------- nível act: HITL por chamada


def _calls(*calls: tuple[str, dict, str | None]) -> dict:
    parts = []
    for name, args, id_ in calls:
        fc: dict = {"name": name, "args": args}
        if id_:
            fc["id"] = id_
        parts.append({"functionCall": fc})
    return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}],
            "usageMetadata": USAGE, "modelVersion": "gemini-test", "responseId": "r"}


PUBLICAR_PARAMS = {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"],
                   "additionalProperties": False}


def _publicar(ran: list) -> te.Tool:
    return te.Tool("publicar", "Publica um texto (muda coisas).", PUBLICAR_PARAMS, "act",
                   lambda a, c: ran.append(a) or {"ok": True, "content": "publicado"})


def test_loop_act_para_antes_de_correr_qualquer_chamada_do_turno(tmp_path):
    ran, audit = [], []
    reg = {**te.REGISTRY, "publicar": _publicar(ran)}
    plan = te.plan_tools(["read_repo_file", "publicar"], registry=reg)
    script = Script([_calls(("read_repo_file", {"path": "runner/requirements.txt"}, "c1"), ("publicar", {"texto": "ola"}, "c2"))])
    with pytest.raises(te.ToolApprovalRequired) as exc:
        te.run_tool_loop(user="u", plan=plan, ctx=_ctx(tmp_path), limits=te.ToolLimits(), generate=_gen(script),
                         on_call=audit.append, registry=reg)
    assert ran == [] and audit == []  # nada corre antes da decisão, nem a leitura do mesmo turno
    assert [p["name"] for p in exc.value.pending] == ["publicar"] and exc.value.pending[0]["args"] == {"texto": "ola"}
    json.dumps(exc.value.state)  # o estado vai para o disco


@pytest.mark.parametrize("verdict", ["approve", "reject"])
def test_loop_act_retoma_com_a_decisao(tmp_path, verdict):
    ran, audit = [], []
    reg = {**te.REGISTRY, "publicar": _publicar(ran)}
    plan = te.plan_tools(["read_repo_file", "publicar"], registry=reg)
    script = Script([_calls(("read_repo_file", {"path": "runner/requirements.txt"}, "c1"), ("publicar", {"texto": "ola"}, "c2")),
                     _text("fim")])
    kw = dict(user="u", plan=plan, ctx=_ctx(tmp_path), limits=te.ToolLimits(), generate=_gen(script),
              on_call=audit.append, registry=reg)
    with pytest.raises(te.ToolApprovalRequired) as exc:
        te.run_tool_loop(**kw)
    state = json.loads(json.dumps(exc.value.state))
    res = te.run_tool_loop(**kw, resume=state, approvals={exc.value.pending[0]["key"]: verdict})
    assert res.turns == 2 and [r["tool"] for r in res.calls] == ["read_repo_file", "publicar"]
    sent = script.bodies[-1]["contents"][-1]["parts"]
    publicar = sent[1]["functionResponse"]
    assert publicar["id"] == "c2" and audit[1]["approval"] == verdict
    if verdict == "approve":
        assert ran == [{"texto": "ola"}] and publicar["response"]["ok"]
    else:
        assert ran == [] and publicar["response"]["error"] == "rejected_by_human"


def test_loop_act_com_args_invalidos_nao_incomoda_o_humano(tmp_path):
    ran = []
    reg = {**te.REGISTRY, "publicar": _publicar(ran)}
    plan = te.plan_tools(["publicar"], registry=reg)
    script = Script([_call("publicar", {"texto": 7}), _text("fim")])
    res = te.run_tool_loop(user="u", plan=plan, ctx=_ctx(tmp_path), limits=te.ToolLimits(), generate=_gen(script), registry=reg)
    assert res.calls[0]["error"] == "invalid_args" and ran == []


def test_loop_cada_aprovacao_vale_para_uma_chamada(tmp_path):
    ran = []
    reg = {**te.REGISTRY, "publicar": _publicar(ran)}
    plan = te.plan_tools(["publicar"], registry=reg)
    script = Script([_call("publicar", {"texto": "ola"}), _call("publicar", {"texto": "ola"})])
    kw = dict(user="u", plan=plan, ctx=_ctx(tmp_path), limits=te.ToolLimits(), generate=_gen(script), registry=reg)
    with pytest.raises(te.ToolApprovalRequired) as first:
        te.run_tool_loop(**kw)
    with pytest.raises(te.ToolApprovalRequired) as second:  # a mesma chamada outra vez pede outra decisão
        te.run_tool_loop(**kw, resume=first.value.state, approvals={first.value.pending[0]["key"]: "approve"})
    assert ran == [{"texto": "ola"}] and second.value.state["turn"] == 2


def test_loop_resume_com_estado_invalido_falha(tmp_path):
    plan = te.plan_tools(["read_repo_file"])
    with pytest.raises(te.ToolLoopError, match="resume_invalido"):
        te.run_tool_loop(user="u", plan=plan, ctx=_ctx(tmp_path), limits=te.ToolLimits(), generate=_gen(Script([])),
                         resume={"contents": [{"role": "user", "parts": [{"text": "u"}]}], "turn": 1, "calls": []})


ACT_STEP = {"id": "s", "action": "research", "output_artifact": "artifacts/01.md", "tools_allowed": ["publicar"]}


def _requests(run_dir: Path) -> list[dict]:
    return [json.loads(x) for x in (run_dir / "hitl-requests.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def _paused_on_act(tmp_path, run_dir, monkeypatch, ran, extra: list[dict]) -> tuple[Script, dict]:
    monkeypatch.setenv(te.ENV_FLAG, "1")
    monkeypatch.setitem(te.REGISTRY, "publicar", _publicar(ran))
    script = Script([_call("publicar", {"texto": "ola mundo"}, id_="p1"), *extra])
    monkeypatch.setattr(ew, "httpx_transport", script)
    st = run_plan(_plan(tmp_path, [ACT_STEP]), mode="external", out_dir=run_dir, worker="gemini")
    return script, st


def test_com_flag_tool_act_pausa_no_hitl(tmp_path, run_dir, monkeypatch):
    ran: list = []
    script, st = _paused_on_act(tmp_path, run_dir, monkeypatch, ran, [])
    assert st["state"] == "paused_human_gate" and st["paused_at_step"] == "s" and ran == []
    assert len(script.bodies) == 1 and "s" not in st["completed"]
    req = _requests(run_dir)[-1]
    assert st["tool_approval"]["request_id"] == req["id"] and req["allow"] == ["approve", "reject"]
    assert req["context"]["tool_calls"] == [{"name": "publicar", "args": {"texto": "ola mundo"},
                                            "args_sha256": te._canonical_sha256({"texto": "ola mundo"})}]
    assert req["metadata"]["kind"] == "tool_approval" and req["status"] == "pending"
    contract = json.loads((REPO_ROOT / "docs/architecture/hitl/hitl-request-v1.json").read_text(encoding="utf-8"))
    import jsonschema

    jsonschema.validate(req, contract)  # o lado Node (HitlManager) lê o mesmo contrato
    pending = run_dir / "pending_steps/s"
    assert (pending / ew.TOOL_APPROVAL_FILE).is_file() and not (pending / ew.ERROR_FILE).exists()
    assert not (pending / "result.json").exists() and "publicar" in (run_dir / "HITL.md").read_text(encoding="utf-8")
    ev = _events(run_dir, "tool_approval_requested")
    assert ev[0]["payload"]["tools"] == ["publicar"] and "ola mundo" not in json.dumps(_events(run_dir, "tool_approval_requested"))
    assert _events(run_dir, "human_gate_requested")[0]["payload"]["kind"] == "tool_approval"
    # o worker sozinho (ex.: external_worker.main) não passa a pausa sem decisão
    with pytest.raises(ew.HumanGateBlocked):
        ew.GeminiWorker(transport=script).process(run_dir, "s")
    assert ran == []


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_com_flag_tool_act_retoma_com_a_decisao(tmp_path, run_dir, monkeypatch, decision):
    from plan_runner.engine import resume_run

    ran: list = []
    script, st = _paused_on_act(tmp_path, run_dir, monkeypatch, ran, [_text("# feito\n")])
    st = resume_run(run_dir, decision=decision, worker="gemini")
    assert st["state"] == "done" and "tool_approval" not in st  # reject recusa a chamada, não o run
    assert ran == ([{"texto": "ola mundo"}] if decision == "approve" else [])
    decisions = (run_dir / "hitl-decisions.jsonl").read_text(encoding="utf-8")
    assert json.loads(decisions.splitlines()[-1])["response"] == decision
    result = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))
    call = result["meta"]["tools"]["calls"][0]
    assert call["approval"] == decision and call["ok"] == (decision == "approve")
    assert result["meta"]["tools"]["needs_approval"] == ["publicar"]
    assert result["meta"]["tokens_total"] == 2 * USAGE["totalTokenCount"]  # os 2 turnos, antes e depois da pausa
    assert not (run_dir / "pending_steps/s" / ew.TOOL_APPROVAL_FILE).exists()
    assert _events(run_dir, "tool_approval_resolved")[0]["payload"]["decision"] == decision
    fr = script.bodies[-1]["contents"][-1]["parts"][0]["functionResponse"]
    assert fr["id"] == "p1" and (fr["response"]["ok"] if decision == "approve" else fr["response"]["error"] == "rejected_by_human")
    assert len((run_dir / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()) == 2


def test_com_flag_decisao_do_lado_node_manda(tmp_path, run_dir, monkeypatch):
    """O contrato HITL: se o lado Node já respondeu a este pedido, é essa a decisão que conta."""
    from plan_runner import hitl
    from plan_runner.engine import resume_run

    ran: list = []
    _, st = _paused_on_act(tmp_path, run_dir, monkeypatch, ran, [_text("# feito\n")])
    hitl.write_decision(run_dir, st["tool_approval"]["request_id"], response="reject", responder_id="node")
    assert resume_run(run_dir, decision="approve", worker="gemini")["state"] == "done"
    assert ran == []  # o approve do CLI não se sobrepõe ao reject já gravado para este pedido
    assert len((run_dir / "hitl-decisions.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_com_flag_uma_aprovacao_antiga_nao_aprova_um_pedido_novo(tmp_path, run_dir, monkeypatch):
    """2 pedidos no mesmo passo: a decisão do 1.º não pode valer para o 2.º (cada pedido tem o seu id)."""
    from plan_runner.engine import resume_run

    ran: list = []
    _, st = _paused_on_act(tmp_path, run_dir, monkeypatch, ran,
                           [_call("publicar", {"texto": "segundo"}, id_="p2"), _text("# feito\n")])
    first = st["tool_approval"]["request_id"]
    st = resume_run(run_dir, decision="approve", worker="gemini")
    assert st["state"] == "paused_human_gate" and st["tool_approval"]["request_id"] != first
    assert ran == [{"texto": "ola mundo"}]  # o 2.º espera pela sua própria decisão
    assert [r["context"]["tool_calls"][0]["args"] for r in _requests(run_dir)] == [{"texto": "ola mundo"}, {"texto": "segundo"}]
    # defesa em profundidade: mesmo com o run fora do paused_human_gate (ex.: recuperação de crash),
    # o worker só aceita a decisão deste pedido, nunca a do anterior
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    (run_dir / "status.json").write_text(json.dumps({**status, "state": "running"}), encoding="utf-8")
    with pytest.raises(ew.ToolApprovalPending):
        ew.GeminiWorker(transport=Script([])).process(run_dir, "s")
    assert ran == [{"texto": "ola mundo"}]
    (run_dir / "status.json").write_text(json.dumps(status), encoding="utf-8")
    assert resume_run(run_dir, decision="reject", worker="gemini")["state"] == "done"
    assert ran == [{"texto": "ola mundo"}]


def test_cli_aprovar_tool_act_nunca_e_o_default(tmp_path, run_dir, monkeypatch, capsys):
    """`plan_runner resume` sem --decision aprovava por omissão; numa tool act tem de ser explícito,
    e uma decisão antiga de OUTRO pedido no hitl-decisions.jsonl não pode valer para esta."""
    from plan_runner import hitl
    from plan_runner.cli import main

    ran: list = []
    _paused_on_act(tmp_path, run_dir, monkeypatch, ran, [_text("# feito\n")])
    assert main(["resume", str(run_dir)]) == 1 and "--decision approve|reject" in capsys.readouterr().out
    assert ran == [] and json.loads((run_dir / "status.json").read_text(encoding="utf-8"))["state"] == "paused_human_gate"
    hitl.write_decision(run_dir, "hitl_outro_pedido_antigo", response="approve", responder_id="node")
    assert main(["resume", str(run_dir), "--decision", "reject"]) == 0
    assert ran == []  # o approve antigo (de outro pedido) não aprovou esta chamada


def test_com_flag_tool_act_edit_nao_e_aceite(tmp_path, run_dir, monkeypatch):
    from plan_runner.engine import PlanError, resume_run

    _paused_on_act(tmp_path, run_dir, monkeypatch, [], [])
    with pytest.raises(PlanError, match="approve.reject"):
        resume_run(run_dir, decision="edit", worker="gemini")


def test_com_flag_langgraph_tambem_pausa_e_retoma(tmp_path, run_dir, monkeypatch):
    pytest.importorskip("langgraph")
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph

    ran: list = []
    monkeypatch.setenv(te.ENV_FLAG, "1")
    monkeypatch.setitem(te.REGISTRY, "publicar", _publicar(ran))
    script = Script([_call("publicar", {"texto": "ola"}, id_="p1"), _text("# feito\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    st = run_plan_langgraph(_plan(tmp_path, [ACT_STEP]), mode="external", out_dir=run_dir, worker="gemini")
    assert st["state"] == "paused_human_gate" and st["tool_approval"]["tools"] == ["publicar"] and ran == []
    st = resume_plan_langgraph(run_dir, decision="reject", worker="gemini")
    assert st["state"] == "done" and ran == []  # reject recusa a chamada; o grafo continua


# --------------------------------------------------------------------------- kb permitido ao passo (integração)


class _FakeMcp(FakeKnowledge):
    instances: list = []

    def __init__(self, *a, **k):
        super().__init__()
        _FakeMcp.instances.append(self)


def test_com_flag_retrieve_knowledge_so_nos_kb_do_passo(tmp_path, run_dir, monkeypatch):
    from plan_runner import mcp_knowledge

    monkeypatch.setenv(te.ENV_FLAG, "1")
    _FakeMcp.instances = []
    monkeypatch.setattr(mcp_knowledge, "McpKnowledge", _FakeMcp)
    step = {**STEP, "tools_allowed": ["retrieve_knowledge"], "tool_kbs": ["legal"]}
    script = Script([_call("retrieve_knowledge", {"kb": "security", "query": "x"}),
                     _call("retrieve_knowledge", {"kb": "legal", "query": "prazo"}), _text("# ok\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    decl = script.bodies[0]["tools"][0]["functionDeclarations"][0]
    assert decl["parameters"]["properties"]["kb"]["enum"] == ["legal"]
    assert "legal" in script.bodies[0]["systemInstruction"]["parts"][0]["text"]
    tools = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))["meta"]["tools"]
    assert [c.get("error") for c in tools["calls"]] == ["kb_not_allowed", None] and tools["kbs"] == ["legal"]
    assert [c[0] for i in _FakeMcp.instances for c in i.calls] == ["legal"]  # o kb recusado nunca chegou ao L5


def test_com_flag_retrieve_knowledge_sem_kb_fica_de_fora(tmp_path, run_dir, monkeypatch):
    monkeypatch.setenv(te.ENV_FLAG, "1")
    step = {**STEP, "tools_allowed": ["retrieve_knowledge"]}
    script = Script([_text("# ok\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    assert "tools" not in script.bodies[0]
    tools = json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))["meta"]["tools"]
    assert tools["enabled"] is False and tools["refused_policy"] == ["retrieve_knowledge"]


def test_schema_dos_planos_aceita_tool_limits_e_tool_kbs():
    """Um plano real com `tool_limits:`/`tool_kbs:` tem de passar no W-006 (step com additionalProperties false)."""
    from plan_runner.plan_schema import plan_errors

    step = {"id": "s", "action": "a", "tools_allowed": ["retrieve_knowledge"],
            "tool_kbs": ["legal"], "tool_limits": {"max_turns": 3, "max_tool_calls": 5}}
    assert plan_errors({"id": "x", "version": 1, "objective": "o", "steps": [step]}) == []
    bad = {**step, "tool_kbs": ["a b"], "tool_limits": {"max_turns": 0, "outro": 1}}
    assert len(plan_errors({"id": "x", "version": 1, "objective": "o", "steps": [bad]})) == 3


# --------------------------------------------------------------------------- plano de prova do run real (AU-20)

FORCE_READ = REPO_ROOT / "docs/orchestration/au20/au20-force-read.plan.yaml"
BUDGET_FACT = "13 130 tokens"  # só existe em docs/ops/BUDGET.md


def test_plano_force_read_obriga_a_tool_e_mostra_meta_tools(run_dir, monkeypatch):
    """O plano do run real: sem repo_files, o BUDGET.md não está no prompt; com a flag, a tool corre
    e o result.json tem meta.tools. É o que o DEV confirma no run com o Gemini real."""
    monkeypatch.setenv(te.ENV_FLAG, "1")
    script = Script([_call("read_repo_file", {"path": "docs/ops/BUDGET.md"}, id_="b1"),
                     _text("1) 13 130 tokens\n\nFonte: docs/ops/BUDGET.md\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(FORCE_READ, mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    first, second = script.bodies
    assert BUDGET_FACT not in json.dumps(first, ensure_ascii=False)  # o conteúdo não vai no prompt
    assert "docs/ops/BUDGET.md" in first["contents"][0]["parts"][0]["text"]  # a tarefa chega ao modelo
    assert [d["name"] for d in first["tools"][0]["functionDeclarations"]] == ["read_repo_file"]
    assert BUDGET_FACT in json.dumps(second, ensure_ascii=False)  # só chega pela tool
    tools = json.loads((run_dir / "pending_steps/read_budget/result.json").read_text(encoding="utf-8"))["meta"]["tools"]
    assert tools["enabled"] and tools["limits"] == {"max_turns": 3, "max_tool_calls": 2}
    assert tools["calls"][0]["tool"] == "read_repo_file" and tools["calls"][0]["ok"]
    assert tools["calls"][0]["sources"] == ["docs/ops/BUDGET.md"]
    assert len(_events(run_dir, "tool_called")) == 1


def test_plano_force_read_sem_flag_nao_tem_meta_tools(run_dir, monkeypatch):
    """Sem PLAN_RUNNER_TOOLS no processo: chamada única, e o result.json diz que a flag estava desligada
    (antes do AU-20b, o 1.º run do DEV só o mostrava pela ausência de meta.tools)."""
    script = Script([_text("Não consigo ler o ficheiro.\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(FORCE_READ, mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    assert len(script.bodies) == 1 and "tools" not in script.bodies[0]
    meta = json.loads((run_dir / "pending_steps/read_budget/result.json").read_text(encoding="utf-8"))["meta"]
    assert meta["worker"] == "gemini" and meta["tools"]["enabled"] is False
    assert meta["tools"]["reason"] == "PLAN_RUNNER_TOOLS desligada" and meta["tools"]["tools_allowed"] == ["read_repo_file"]


def test_sem_flag_passo_sem_tools_allowed_nao_ganha_meta_tools(tmp_path, run_dir, monkeypatch):
    """O AU-20b só marca os passos que declaram tools; os outros ficam como sempre."""
    step = {**STEP, "tools_allowed": []}
    script = Script([_text("# ok\n")])
    monkeypatch.setattr(ew, "httpx_transport", script)
    assert run_plan(_plan(tmp_path, [step]), mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    assert "tools" not in json.loads((run_dir / "pending_steps/s/result.json").read_text(encoding="utf-8"))["meta"]
