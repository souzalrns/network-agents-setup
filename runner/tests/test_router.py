"""Router hierarquico hibrido (D2): plan_runner/router.py.

A area e sempre calculada de verdade (keywords de config/areas.yaml). O LLM
do router e falso (responde o `llm_reply` do golden set) e o worker tambem:
nenhum teste sai para a rede nem escreve no Supabase.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import router as rt
from plan_runner.engine import resume_run
from tests.test_external_worker import USAGE, FakeGemini

GOLDEN = rt.load_golden()


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


class FakeRouterLLM:
    """generateContent falso: devolve o `llm_reply` do caso cujo pedido vem no prompt."""

    def __init__(self, replies: dict[str, dict] | None = None, status: int = 200):
        self.replies = replies if replies is not None else {c["request"]: c["llm_reply"] for c in GOLDEN if "llm_reply" in c}
        self.calls: list[dict] = []
        self.status = status

    def __call__(self, url, headers, body, timeout):
        self.calls.append(body)
        if self.status != 200:
            return self.status, {"error": {"message": "quota"}}
        user = body["contents"][0]["parts"][0]["text"]
        request = user.split("<<<\n", 1)[1].rsplit("\n>>>", 1)[0]
        reply = self.replies[request]  # KeyError = o router chamou o LLM quando nao devia
        return 200, {
            "candidates": [{"content": {"parts": [{"text": json.dumps(reply, ensure_ascii=False)}]}, "finishReason": "STOP"}],
            "usageMetadata": {**USAGE, "promptTokenCount": 640, "candidatesTokenCount": 40, "totalTokenCount": 680},
            "modelVersion": "gemini-3.5-flash-lite",
            "responseId": "router-1",
        }

    def candidates_in_last_prompt(self) -> list[str]:
        user = self.calls[-1]["contents"][0]["parts"][0]["text"]
        block = user.split("Candidatos:\n", 1)[1].split("\n\n", 1)[0]
        return [line[2:].split(":", 1)[0] for line in block.splitlines()]


@pytest.fixture
def llm():
    return FakeRouterLLM()


@pytest.fixture
def router(llm):
    return rt.Router(transport=llm)


# --------------------------------------------------------------------------
# Golden set: 10 pedidos + 3 ambiguos + regressao (fallback horizontal)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("case", GOLDEN, ids=[c["request"][:40] for c in GOLDEN])
def test_golden(router, llm, case):
    d = router.route(case["request"])
    assert rt.check_case(d, case) == [], d.to_dict()
    # So chama o LLM quando a decisao passa pelo andar do agente
    assert len(llm.calls) == (1 if "llm_reply" in case else 0)


def test_golden_tem_10_pedidos_3_ambiguos_e_a_regressao():
    clear = [c for c in GOLDEN if c.get("area") not in (None, "horizontal") and c["outcome"] in ("agent", "plan", "hitl")]
    ambiguous = [c for c in GOLDEN if c["outcome"] in ("clarify", "hitl") and (c.get("area") is None or "llm_reply" in c)]
    assert len(clear) == 10 and len(ambiguous) == 3
    assert {c["area"] for c in clear} == {"marketing", "legal", "gamedev", "software", "security", "finance", "ops", "research"}
    assert any(c["area"] == "horizontal" for c in GOLDEN)


def test_llm_so_ve_os_candidatos_da_area_mais_horizontais(router, llm):
    d = router.route("Faz um post de Instagram para o lançamento da nova coleção de verão")
    marketing = router.areas["marketing"]
    assert llm.candidates_in_last_prompt() == marketing["agents"] + marketing["horizontals"]
    assert d.candidates == marketing["agents"] + marketing["horizontals"]
    prompt = llm.calls[-1]["contents"][0]["parts"][0]["text"]
    assert "engenharia." not in prompt  # nada de outras areas (R5: lista curta)
    assert router.agents["marketing.copy_social"]["description"] in prompt  # J4
    assert llm.calls[-1]["generationConfig"]["responseMimeType"] == "application/json"


def test_decisao_regista_tokens_do_router(router):
    d = router.route("Revê o código deste pull request e aponta bugs")
    [row] = d.usage
    assert row["call_kind"] == "router" and row["agent_id"] is None
    assert row["tokens_total"] == 680 and row["model_version"] == "gemini-3.5-flash-lite"


def test_area_de_risco_ambigua_vai_para_hitl_e_nao_para_clarificacao(router):
    d = router.route("Analisa o contrato e o orçamento do fornecedor")
    assert d.outcome == "hitl" and d.hitl_required
    assert set(d.candidates) == {"legal", "finance", "ops"}
    assert "exige HITL" in d.reason and d.question


def test_clarificacao_de_area_pergunta_entre_as_areas_em_causa(router):
    d = router.route("Cria um jogo para a nossa campanha")
    assert d.outcome == "clarify" and set(d.candidates) == {"marketing", "gamedev"}
    assert "marketing" in d.question and "gamedev" in d.question


# --------------------------------------------------------------------------
# Regras do andar do agente (registo pequeno em tmp, para isolar cada regra)
# --------------------------------------------------------------------------

def _mini_repo(tmp_path: Path, areas_extra: str = "") -> Path:
    for rel, aid, action, desc in (
        ("eng/dev.agent.md", "eng.dev", "dev", "Escreve codigo."),
        ("eng/rev.agent.md", "eng.rev", "rev", "Reve codigo."),
        ("fin/conta.agent.md", "fin.conta", "conta", "Faz contabilidade."),
        ("meta/plan.agent.md", "meta.plan", "plan", "Planeia."),
    ):
        p = tmp_path / "agents" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\nid: {aid}\naction: {action}\ndescription: \"{desc}\"\n---\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config/areas.yaml").write_text(
        "routing: {area_min_confidence: 0.6, agent_min_confidence: 0.6, fallback_area: horizontal}\n"
        "areas:\n"
        "  - {id: software, description: Software., keywords: [codigo], agents: [eng.dev, eng.rev], horizontals: [meta.plan]"
        + areas_extra + "}\n"
        "  - {id: finance, description: Financas., keywords: [conta], agents: [fin.conta], horizontals: [], hitl: required}\n"
        "  - {id: horizontal, description: Transversal., agents: [meta.plan], horizontals: []}\n",
        encoding="utf-8",
    )
    return tmp_path


def _mini(tmp_path, reply: dict, areas_extra: str = "", **kw) -> tuple[rt.Router, FakeRouterLLM]:
    llm = FakeRouterLLM(replies={"pedido de codigo": reply, "pedido de conta": reply}, **kw)
    return rt.Router(_mini_repo(tmp_path, areas_extra), transport=llm), llm


def test_um_so_candidato_nao_chama_o_llm(tmp_path):
    router, llm = _mini(tmp_path, {})
    d = router.route("pedido de conta")
    assert (d.outcome, d.agent, d.agent_confidence) == ("agent", "fin.conta", 1.0)
    assert llm.calls == [] and d.hitl_required  # finance tem hitl: required


def test_confianca_baixa_do_llm_clarifica(tmp_path):
    router, _ = _mini(tmp_path, {"mode": "agent", "agent": "eng.dev", "confidence": 0.4, "question": "Que linguagem?"})
    d = router.route("pedido de codigo")
    assert d.outcome == "clarify" and d.question == "Que linguagem?" and "0.40 < 0.6" in d.reason


def test_confianca_baixa_em_area_de_risco_vai_para_hitl(tmp_path):
    router, _ = _mini(tmp_path, {"mode": "agent", "agent": "fin.conta", "confidence": 0.2}, )
    router.areas["finance"]["agents"].append("eng.dev")  # 2 candidatos -> passa pelo LLM
    d = router.route("pedido de conta")
    assert d.outcome == "hitl" and "exige HITL" in d.reason


@pytest.mark.parametrize("reply, erro", [
    ({"mode": "agent", "agent": "fin.conta", "confidence": 0.9}, "fora dos candidatos"),
    ({"mode": "plan", "confidence": 0.9, "steps": [{"agent": "eng.dev"}, {"agent": "eng.rev", "depends_on": [2]}]}, "depends_on invalido"),
    ({"mode": "plan", "confidence": 0.9, "steps": []}, "sem passos"),
    ({"mode": "talvez", "confidence": 0.9}, "mode desconhecido"),
])
def test_resposta_invalida_do_llm_e_erro_explicito_nunca_omissao(tmp_path, reply, erro):
    router, _ = _mini(tmp_path, reply)
    d = router.route("pedido de codigo")
    assert d.outcome == "error" and erro in d.reason and d.agent is None


def test_plano_sem_depends_on_fica_sequencial_e_respeita_o_budget(tmp_path):
    steps = [{"agent": "eng.dev", "task": "a"}, {"agent": "eng.rev", "task": "b"}, {"agent": "meta.plan", "task": "c"}]
    router, _ = _mini(tmp_path, {"mode": "plan", "confidence": 0.9, "steps": steps})
    d = router.route("pedido de codigo")
    assert d.outcome == "plan" and [s["depends_on"] for s in d.steps] == [[], [1], [2]]

    router, _ = _mini(tmp_path / "b", {"mode": "plan", "confidence": 0.9, "steps": steps}, areas_extra=", budget: {max_steps: 2}")
    assert "3 passos > max 2" in router.route("pedido de codigo").reason


def test_delegation_da_area(tmp_path):
    router, _ = _mini(tmp_path, {"mode": "agent", "agent": "eng.rev", "confidence": 0.9}, areas_extra=", delegation: plan")
    d = router.route("pedido de codigo")
    assert d.outcome == "plan" and [s["agent"] for s in d.steps] == ["eng.rev"]

    plan = {"mode": "plan", "confidence": 0.9, "steps": [{"agent": "eng.dev"}, {"agent": "eng.rev"}]}
    router, llm = _mini(tmp_path / "b", plan, areas_extra=", delegation: agent")
    assert router.route("pedido de codigo").outcome == "error"
    assert "SEMPRE num so agente" in llm.calls[0]["systemInstruction"]["parts"][0]["text"]


def test_falha_do_llm_e_erro_com_motivo(tmp_path):
    router, _ = _mini(tmp_path, {}, status=429)
    d = router.route("pedido de codigo")
    assert d.outcome == "error" and "HTTP 429" in d.reason


def test_embeddings_quando_nenhuma_keyword_casa(tmp_path):
    vectors = {"software": [1.0, 0.0], "finance": [0.0, 1.0], "horizontal": [0.1, 0.1]}

    def embed(text: str) -> list[float]:
        for aid, v in vectors.items():
            if text.startswith(f"{aid}:"):
                return v
        return [0.95, 0.05]  # o pedido parece-se com software

    router, llm = _mini(tmp_path, {"mode": "agent", "agent": "eng.dev", "confidence": 0.9})
    router.embed = embed
    llm.replies["programar um servico"] = {"mode": "agent", "agent": "eng.dev", "confidence": 0.9}
    d = router.route("programar um servico")
    assert (d.area, d.area_method, d.outcome) == ("software", "embeddings", "agent")
    assert [u["call_kind"] for u in d.usage] == ["embed_query", "router"]


# --------------------------------------------------------------------------
# Integracao com o plan_runner + worker external
# --------------------------------------------------------------------------

@pytest.fixture
def worker_llm(monkeypatch):
    f = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", f)
    return f


def _ledger(out: Path) -> list[dict]:
    return [json.loads(line) for line in (out / ew.LEDGER_FILE).read_text(encoding="utf-8").splitlines()]


def test_um_agente_corre_um_passo_no_worker_de_ponta_a_ponta(router, tmp_run_dir, worker_llm):
    d = router.route("Faz um post de Instagram para o lançamento da nova coleção de verão")
    result = router.execute(d, out_dir=tmp_run_dir, worker="gemini")

    status = result["status"]
    assert status["state"] == "done" and status["completed"] == ["p1_copy_social"]
    assert len(worker_llm.calls) == 1
    system = worker_llm.calls[0]["body"]["systemInstruction"]["parts"][0]["text"]
    assert "copy_social" in system  # AGENT.md/SKILL.md do agente escolhido
    assert (tmp_run_dir / "artifacts/01-copy_social.md").read_text(encoding="utf-8").startswith("# Saida 1")

    rows = _ledger(tmp_run_dir)
    assert [r["call_kind"] for r in rows] == ["agent", "router"]
    assert rows[0]["agent_id"] == "marketing.copy_social"
    assert rows[0]["run_id"] == rows[1]["run_id"] == ew.ledger_run_uuid(status["run_id"])  # router + agente no mesmo run
    route = json.loads((tmp_run_dir / "route.json").read_text(encoding="utf-8"))
    assert route["area"] == "marketing" and route["agent"] == "marketing.copy_social"


def test_plano_multi_passo_corre_no_plan_runner_com_a_tarefa_de_cada_passo(router, tmp_run_dir, worker_llm):
    d = router.route("Cria um artigo SEO sobre AI Findability, com pesquisa de base e revisão crítica no fim")
    status = router.execute(d, out_dir=tmp_run_dir)["status"]
    assert status["state"] == "done"
    assert status["completed"] == sorted(["p1_research", "p2_seo_brief", "p3_copy_answer_first", "p4_critic_item13"])
    assert len(worker_llm.calls) == 4
    user = worker_llm.calls[1]["body"]["contents"][0]["parts"][0]["text"]
    assert "## Tarefa deste passo\n\nBrief SEO a partir da pesquisa" in user
    assert "## Input: artifacts/01-research.md" in user  # depende do passo 1
    assert [r["step_id"] for r in _ledger(tmp_run_dir)] == [
        "p1_research", "p2_seo_brief", "p3_copy_answer_first", "p4_critic_item13", "router",
    ]


def test_area_com_hitl_required_ganha_gate_no_fim(router, tmp_run_dir, worker_llm):
    d = router.route("Prepara o balancete e a declaração de IVA deste trimestre")
    plan = router.build_plan(d)
    assert [s["id"] for s in plan["steps"]] == ["p1_contabilidade", "aprovacao"]
    assert plan["steps"][1]["depends_on"] == ["p1_contabilidade"]

    status = router.execute(d, out_dir=tmp_run_dir)["status"]
    assert status["state"] == "paused_human_gate" and status["paused_at_step"] == "aprovacao"
    assert len(worker_llm.calls) == 1  # o agente correu; a aprovacao e humana
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"


def test_sem_especialista_abre_hitl_duravel_sem_chamar_ninguem(router, llm, tmp_run_dir, worker_llm):
    d = router.route("Analisa este contrato de prestação de serviços e aponta riscos")
    status = router.execute(d, out_dir=tmp_run_dir)["status"]
    assert status["state"] == "paused_human_gate" and status["paused_at_step"] == "triagem"
    assert llm.calls == [] and worker_llm.calls == []
    req = json.loads((tmp_run_dir / "hitl-requests.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert req["step_id"] == "triagem"


def test_clarificacao_nao_executa(router, tmp_run_dir):
    d = router.route("Cria um jogo para a nossa campanha")
    assert router.execute(d, out_dir=tmp_run_dir) == {"executed": False, "decision": d.to_dict()}
    assert not (tmp_run_dir / "status.json").exists()


# --------------------------------------------------------------------------
# CLI + log de decisoes (R7)
# --------------------------------------------------------------------------

def test_cli_route_e_log_de_decisoes(tmp_path, capsys):
    from plan_runner.cli import main

    log = tmp_path / "decisions.jsonl"
    assert main(["route", "Escreve um jogo simples", "--log", str(log)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["executed"] is False and out["decision"]["outcome"] == "hitl"
    [entry] = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert (entry["area"], entry["outcome"], entry["tokens_total"]) == ("gamedev", "hitl", 0)


def test_embeddings_ambiguos_nao_escolhem_e_keywords_dispensam_embeddings(tmp_path):
    vectors = {"software": [1.0, 0.0], "finance": [0.0, 1.0], "horizontal": [-1.0, -1.0]}
    calls: list[str] = []

    def embed(text: str) -> list[float]:
        calls.append(text)
        for aid, v in vectors.items():
            if text.startswith(f"{aid}:"):
                return v
        return [0.7, 0.7]  # a meio caminho entre software e finance

    router, _ = _mini(tmp_path, {"mode": "agent", "agent": "eng.dev", "confidence": 0.9})
    router.embed = embed
    d = router.route("uma coisa qualquer")
    # empate software/finance; finance tem hitl: required -> HITL, nao clarificacao (D2:141)
    assert d.outcome == "hitl" and set(d.candidates) == {"software", "finance"}

    calls.clear()
    assert router.route("pedido de codigo").area_method == "keywords"
    assert calls == []  # houve keyword: nenhum embedding gasto
