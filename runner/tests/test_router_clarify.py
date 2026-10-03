"""W-002 (R3): clarificacao com estado no router."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import router as rt
from tests.test_router import FakeRouterLLM, _mini_repo


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.delenv("AGENT_MODEL", raising=False)


def _combined(prev: rt.RouteDecision, answer: str) -> str:
    return f"{prev.request}\n\nEsclarecimento (pergunta: {prev.question}): {answer}"


def _two_areas(tmp_path: Path) -> Path:
    """Duas areas sem risco que empatam em 'codigo do post'."""
    repo = _mini_repo(tmp_path)
    (repo / "agents/mkt/post.agent.md").parent.mkdir(parents=True, exist_ok=True)
    (repo / "agents/mkt/post.agent.md").write_text("---\nid: mkt.post\naction: post\ndescription: \"Posts.\"\n---\n",
                                                   encoding="utf-8")
    (repo / "config/areas.yaml").write_text(
        "routing: {area_min_confidence: 0.6, agent_min_confidence: 0.6, fallback_area: horizontal}\n"
        "areas:\n"
        "  - {id: software, description: Software., keywords: [codigo], agents: [eng.dev], horizontals: []}\n"
        "  - {id: marketing, description: Marketing., keywords: [post, campanha], agents: [mkt.post], horizontals: []}\n"
        "  - {id: horizontal, description: Transversal., agents: [meta.plan], horizontals: []}\n",
        encoding="utf-8",
    )
    return repo


def test_clarificacao_do_agente_mantem_a_area_e_usa_o_pedido_original(tmp_path):
    llm = FakeRouterLLM(replies={"pedido de codigo": {"mode": "clarify", "confidence": 0.3, "question": "Escrever ou rever?"}})
    router = rt.Router(_mini_repo(tmp_path), transport=llm)
    first = router.route("pedido de codigo")
    assert first.outcome == "clarify" and first.area == "software"

    llm.replies[_combined(first, "rever o PR")] = {"mode": "agent", "agent": "eng.rev", "confidence": 0.9}
    d = router.clarify(first, "rever o PR")

    assert d.outcome == "agent" and d.agent == "eng.rev"
    assert d.area == "software" and d.area_method == "clarification"
    assert "pedido de codigo" in d.request and "rever o PR" in d.request  # o plano leva o contexto todo
    assert d.clarification == {"original_request": "pedido de codigo", "question": "Escrever ou rever?",
                               "answer": "rever o PR", "rounds": 1}


def test_clarificacao_da_area_pelo_id_ou_pelas_keywords_da_resposta(tmp_path):
    router = rt.Router(_two_areas(tmp_path), transport=FakeRouterLLM(replies={}))  # sem LLM: 1 agente por area
    first = router.route("codigo do post")
    assert first.outcome == "clarify" and first.area is None and set(first.candidates) == {"software", "marketing"}

    by_id = router.clarify(first, "e de marketing")
    assert by_id.outcome == "agent" and by_id.area == "marketing" and by_id.agent == "mkt.post"

    by_kw = router.clarify(first, "o importante e o codigo")
    assert by_kw.area == "software" and by_kw.agent == "eng.dev"


def test_aceita_o_json_impresso_pelo_route(tmp_path):
    router = rt.Router(_two_areas(tmp_path), transport=FakeRouterLLM(replies={}))
    printed = {"executed": False, "decision": router.route("codigo do post").to_dict()}
    assert router.clarify(json.loads(json.dumps(printed)), "marketing").area == "marketing"


def test_sem_convergencia_passa_a_hitl(tmp_path):
    router = rt.Router(_two_areas(tmp_path), transport=FakeRouterLLM(replies={}))
    d1 = router.clarify(router.route("codigo do post"), "nao sei")  # nada decide: reclassifica e volta a empatar
    assert d1.outcome == "clarify" and d1.clarification["rounds"] == 1
    d2 = router.clarify(d1, "tanto faz")
    assert d2.outcome == "hitl" and d2.hitl_required and d2.clarification["rounds"] == rt.MAX_CLARIFY_ROUNDS
    assert d2.clarification["original_request"] == "codigo do post"


@pytest.mark.parametrize("prev, answer, msg", [
    ({"outcome": "agent", "request": "x"}, "y", "so se responde a uma decisao `clarify`"),
    ({"outcome": "clarify", "request": "x", "question": "q"}, "   ", "resposta vazia"),
])
def test_erros(tmp_path, prev, answer, msg):
    d = rt.Router(_mini_repo(tmp_path), transport=FakeRouterLLM(replies={})).clarify(prev, answer)
    assert d.outcome == "error" and msg in d.reason


def test_cli_route_com_clarify_from(tmp_path, capsys):
    """Repo real: o golden 'Cria um jogo para a nossa campanha' acaba em clarify (marketing x gamedev)."""
    from plan_runner.cli import main

    log = tmp_path / "decisions.jsonl"
    assert main(["route", "Cria um jogo para a nossa campanha", "--log", str(log)]) == 0
    first = capsys.readouterr().out
    assert json.loads(first)["decision"]["outcome"] == "clarify"
    prev = tmp_path / "prev.json"
    prev.write_text(first, encoding="utf-8")

    assert main(["route", "--clarify-from", str(prev), "e sobretudo o jogo", "--log", str(log)]) == 0
    d = json.loads(capsys.readouterr().out)["decision"]
    assert d["area"] == "gamedev" and d["area_method"] == "clarification"
    assert d["clarification"]["original_request"] == "Cria um jogo para a nossa campanha"


def test_cli_clarify_from_ficheiro_invalido(tmp_path, capsys):
    from plan_runner.cli import main

    assert main(["route", "--clarify-from", str(tmp_path / "nao-existe.json"), "x"]) == 1
    assert "--clarify-from" in capsys.readouterr().out
