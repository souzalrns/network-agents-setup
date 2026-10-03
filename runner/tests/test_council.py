"""Bloco C: CouncilSession (Fase 1 do ADR-META-AGENTS) com Gemini falso e L4 falsa.

A L4 real (Postgres + pgvector) esta em test_council_l4.py (job test-rag).
"""
from __future__ import annotations

import json
import re
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest
import yaml

from plan_runner import council_session as cs
from plan_runner import external_worker as ew
from plan_runner import hitl
from plan_runner import memory_wiring as mw
from plan_runner.areas import validate_areas
from plan_runner.router import Router

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCH = ["meta.arquitetura-agentes", "engenharia.desenvolvimento", "engenharia.revisor-codigo"]
TOPIC = "Decisao de arquitetura: passar os checkpoints do LangGraph de SQLite para Postgres?"


# ---------------------------------------------------------------------------
# Gemini falso: responde por estagio (o prompt diz qual e quem e)
# ---------------------------------------------------------------------------

def default_position(mid: str) -> dict[str, Any]:
    return {"vote": "approve", "confidence": 0.8, "position": f"Concordo; {mid} ve beneficio claro.",
            "arguments": ["checkpoints duraveis partilhados"], "risks": ["custo do Supabase"],
            "conditions": [], "kill_criteria": ["latencia de resume > 2s"], "veto": False, "veto_reason": None}


DEFAULT_VERDICT = {
    "decision": "approve", "summary": "Migrar quando houver multi-instancia.", "rationale": "Posicoes A e B convergem.",
    "conditions": [], "dissent": [], "kill_criteria": ["resume > 2s em p95"],
    "next_actions": [{"action": "spike langgraph-checkpoint-postgres", "owner": "dev"}], "risks": ["lock-in"],
    "confidence": 0.85,
}


class CouncilGemini:
    def __init__(self, positions: dict[str, Any] | None = None, verdict: Any = None, ballots: dict[str, Any] | None = None):
        self.positions = positions or {}
        self.verdict = DEFAULT_VERDICT if verdict is None else verdict
        self.ballots = ballots or {}
        self.calls: list[dict[str, Any]] = []

    def __call__(self, url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        stage = re.search(r"Estagio do conselho: (\w+)", system).group(1)
        who = re.search(r"Es o (?:membro|revisor) `([^`]+)`", system)
        who = who.group(1) if who else "chairman"
        if stage == "INDEPENDENT":
            out = self.positions.get(who, default_position(who))
        elif stage == "PEER_RANK":
            labels = re.search(r"letras ([A-Z, ]+), sem repetir", system).group(1).split(", ")
            out = self.ballots.get(who, {"ranking": labels, "critiques": {lab: f"falta medir ({who})" for lab in labels}})
        else:
            out = self.verdict
        text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
        self.calls.append({"stage": stage, "who": who, "system": system, "user": user, "model": url})
        p, c = (len(system) + len(user)) // 4, len(text) // 4
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": p, "candidatesTokenCount": c, "totalTokenCount": p + c},
                     "modelVersion": "gemini-3.5-flash-lite"}

    def stages(self) -> list[str]:
        return [c["stage"] for c in self.calls]


class FakeL4:
    """remember/promote/forget em memoria (as regras reais sao testadas em test_council_l4.py)."""

    def __init__(self):
        self.rows: dict[str, dict[str, Any]] = {}

    def remember(self, conn, **kw):
        assert kw["actor"].startswith("agent:") and "status" not in kw  # agente escreve sempre candidate
        rid = f"mem-{len(self.rows) + 1}"
        self.rows[rid] = {"id": rid, "status": "candidate", **{k: kw[k] for k in ("statement", "subject", "tags", "metadata", "confidence")},
                          "scope": str(kw["scope"]), "created_by": kw["actor"]}
        return self.rows[rid]

    def promote(self, conn, mid, *, actor):
        assert actor.startswith("human:")
        self.rows[mid].update(status="active", promoted_by=actor)
        return self.rows[mid]

    def forget(self, conn, mid, *, actor, reason=None):
        self.rows[mid].update(status="archived", archived_by=actor, archived_reason=reason)
        return self.rows[mid]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_l4(monkeypatch):
    f = FakeL4()
    for name in ("remember", "promote", "forget"):
        monkeypatch.setattr(cs.l4, name, getattr(f, name))
    return f


def deps(gemini, l4store: bool = True, sink=None) -> cs.CouncilDeps:
    store = mw.MemoryStore(connect=lambda: nullcontext(object())) if l4store else None
    return cs.CouncilDeps(transport=gemini, memory=store, remote_ledger=sink)


def start(tmp_path, gemini, council="architecture", **kw) -> cs.CouncilSession:
    s = cs.CouncilSession(tmp_path / "council", deps=deps(gemini, l4store=kw.pop("l4store", True), sink=kw.pop("sink", None)))
    s.start(council, kw.pop("topic", TOPIC), **kw)
    return s


# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

def test_councils_yaml_real_e_valido():
    assert cs.validate_councils(REPO_ROOT) == []
    assert validate_areas(REPO_ROOT) == []
    data = cs.load_councils(REPO_ROOT)
    assert [c["id"] for c in data["councils"]] == ["architecture", "security", "product"]
    for c in data["councils"]:
        assert 2 <= len(c["members"]) <= 3 and c["chairman"] == "meta.chairman"
        assert c["chairman"] not in cs._member_ids(c)


def _mini_repo(tmp_path: Path, councils: dict, chair_kind: str = "meta", chair_in_area: bool = False) -> Path:
    agents = {"eng/a.agent.md": ("eng.a", "internal"), "eng/b.agent.md": ("eng.b", "internal"),
              "eng/c.agent.md": ("eng.c", "internal"), "eng/d.agent.md": ("eng.d", "internal"),
              "eng/x.agent.md": ("eng.x", "external_ai"), "meta/chair.agent.md": ("meta.chair", chair_kind)}
    for rel, (aid, kind) in agents.items():
        p = tmp_path / "agents" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\nid: {aid}\nkind: {kind}\naction: {aid.split('.')[1]}\n---\n# {aid}\n", encoding="utf-8")
    eng = ["eng.a", "eng.b", "eng.c", "eng.d", "eng.x"] + (["meta.chair"] if chair_in_area or chair_kind != "meta" else [])
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "areas.yaml").write_text(yaml.safe_dump({"routing": {"fallback_area": "software"}, "areas": [
        {"id": "software", "description": "S.", "agents": eng, "horizontals": []}]}), encoding="utf-8")
    (tmp_path / "config" / "councils.yaml").write_text(yaml.safe_dump(councils), encoding="utf-8")
    return tmp_path


def _council(**over) -> dict:
    c = {"id": "architecture", "description": "D.", "hitl_category": "architectural", "area": "software",
         "chairman": "meta.chair", "members": [{"id": "eng.a", "role": "member"}, {"id": "eng.b", "role": "critic"}],
         "required": ["eng.a"], "max_rounds": 2, "confidence_threshold": 0.7,
         "escalation": {"areas": ["software"], "keywords": ["decisao de arquitetura"]}}
    c.update(over)
    return {"version": 1, "memory_scope": "project:x", "councils": [c]}


def test_mini_repo_valido(tmp_path):
    assert validate_areas(_mini_repo(tmp_path, _council())) == []


@pytest.mark.parametrize("over,expect", [
    ({"members": [{"id": f"eng.{x}"} for x in "abcd"]}, "2 a 3 entradas"),
    ({"members": [{"id": "eng.a"}]}, "2 a 3 entradas"),
    ({"required": ["eng.c"]}, "required"),
    ({"confidence_threshold": 7}, "AU-13"),
    ({"max_rounds": None}, "max_rounds obrigatorio"),
    ({"members": [{"id": "eng.a"}, {"id": "eng.x"}]}, "Fase 2"),
    ({"members": [{"id": "eng.a"}, {"id": "meta.chair"}]}, "chairman nao pode ser membro"),
    ({"members": [{"id": "eng.a"}, {"id": "eng.b", "role": "boss"}]}, "role"),
    ({"area": "nao-existe"}, "area `nao-existe`"),
    ({"escalation": {"areas": ["software"], "keywords": ["Decisão"]}}, "sem acentos"),
])
def test_validador_recusa(tmp_path, over, expect):
    errors = validate_areas(_mini_repo(tmp_path, _council(**over)))
    assert any(expect in e for e in errors), errors


def test_chairman_tem_de_ser_meta_e_fora_das_areas(tmp_path):
    errors = validate_areas(_mini_repo(tmp_path, _council(), chair_kind="internal"))
    assert any("kind: meta" in e for e in errors), errors
    errors = validate_areas(_mini_repo(tmp_path / "b", _council(), chair_in_area=True))
    assert any("não pertence a áreas" in e for e in errors), errors


def test_agente_meta_sem_conselho_e_orfao(tmp_path):
    cfg = _council()
    cfg["councils"][0]["chairman"] = "eng.d"  # deixa meta.chair sem conselho (e eng.d nao e meta)
    errors = validate_areas(_mini_repo(tmp_path, cfg))
    assert any("agente meta órfão `meta.chair`" in e for e in errors), errors


# ---------------------------------------------------------------------------
# Ponta a ponta (mock): INDEPENDENT -> PEER_RANK -> SYNTHESIZE -> GATE -> HITL -> L4
# ---------------------------------------------------------------------------

def test_conselho_architecture_ponta_a_ponta(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g)
    st = s.state
    # 3 membros + 3 peers + 1 chairman = 2N+1
    assert g.stages() == ["INDEPENDENT"] * 3 + ["PEER_RANK"] * 3 + ["SYNTHESIZE"]
    assert st["status"] == "awaiting_human" and st["stage"] == "hitl"
    rnd = st["rounds"][0]
    assert set(rnd["positions"]) == set(ARCH) and all(p["vote"] == "approve" for p in rnd["positions"].values())
    assert rnd["positions"]["engenharia.revisor-codigo"]["role"] == "critic"
    assert len(rnd["ballots"]) == 3 and set(rnd["peer_scores"]) == set(rnd["labels"])
    v = st["verdict"]
    assert v["decision"] == "approve" and v["confidence"] == 0.85 and v["kill_criteria"] and v["next_actions"]
    assert st["gate_ok"] is True and rnd["gate"]["allow"] == ["approve", "reject", "edit"]
    # L4: candidate gravado pelo chairman, com o veredicto em metadata
    mem = rnd["memory"]
    row = fake_l4.rows[mem["id"]]
    assert mem["status"] == "candidate" and row["created_by"] == "agent:meta.chairman"
    assert row["scope"] == "project:network-agents-setup" and "council:architecture" in row["tags"]
    assert row["metadata"]["verdict"]["decision"] == "approve" and "APPROVE" in row["statement"]
    # HITL pedido duravel, com o id da memoria
    req = hitl.latest_request(s.out)
    assert req["proposed_action"] == "council_verdict" and req["metadata"]["memory_id"] == mem["id"]
    assert json.loads((s.out / "status.json").read_text())["state"] == "paused_human_gate"

    out = s.decide("approve", actor="maestro", comment="ok")
    assert out["status"] == "done" and st["hitl_decision"] == "approve"
    assert fake_l4.rows[mem["id"]]["status"] == "active" and fake_l4.rows[mem["id"]]["promoted_by"] == "human:maestro"
    final = json.loads((s.out / cs.VERDICT_FILE).read_text())
    assert final["decision"] == "approve" and final["memory"]["status"] == "active"
    assert hitl.read_decision(s.out)["response"] == "approve"
    assert len(g.calls) == 7  # decidir nao chama o LLM


@pytest.mark.parametrize("decision", cs.VOTES)
def test_veredicto_estruturado_nos_4_valores(tmp_path, fake_l4, decision):
    v = {**DEFAULT_VERDICT, "decision": decision, "conditions": ["so com flag"] if decision == "conditional" else []}
    s = start(tmp_path, CouncilGemini(verdict=v))
    verdict = s.state["verdict"]
    assert verdict["decision"] == decision
    assert set(verdict) >= {"decision", "summary", "rationale", "conditions", "dissent", "kill_criteria",
                            "next_actions", "risks", "confidence", "participants"}
    # quem votou diferente da decisao aparece no dissent (approve x3 contra reject/defer/conditional)
    if decision != "approve":
        assert {d["member_id"] for d in verdict["dissent"]} == set(ARCH)


def test_dissent_deterministico_mesmo_que_o_chairman_o_omita(tmp_path, fake_l4):
    pos = {"engenharia.revisor-codigo": {**default_position("x"), "vote": "reject", "position": "Risco de lock-in."}}
    s = start(tmp_path, CouncilGemini(positions=pos))  # chairman devolve dissent: []
    d = s.state["verdict"]["dissent"]
    assert [x["member_id"] for x in d] == ["engenharia.revisor-codigo"] and d[0]["source"] == "gate"
    assert "lock-in" in d[0]["point"]


def test_gate_veto_de_membro_obrigatorio_bloqueia_approve(tmp_path, fake_l4):
    pos = {"meta.arquitetura-agentes": {**default_position("x"), "vote": "reject", "veto": True, "veto_reason": "parte o HITL"}}
    s = start(tmp_path, CouncilGemini(positions=pos))  # o chairman diz approve na mesma
    g = s.state["rounds"][0]["gate"]
    assert g["result"] == "veto" and g["vetoes"] == ["meta.arquitetura-agentes"] and g["allow"] == ["reject", "edit"]
    assert hitl.latest_request(s.out)["priority"] == "high"
    with pytest.raises(cs.CouncilError, match="nao permitida"):
        s.decide("approve", actor="maestro")
    # o chairman viu o veto (sem saber de quem)
    chair = next(c for c in s.deps.transport.calls if c["stage"] == "SYNTHESIZE")
    assert "veto_de_membro_obrigatorio" in chair["user"]


def test_veto_de_membro_nao_obrigatorio_nao_bloqueia(tmp_path, fake_l4):
    pos = {"engenharia.desenvolvimento": {**default_position("x"), "vote": "reject", "veto": True}}
    s = start(tmp_path, CouncilGemini(positions=pos))
    assert s.state["rounds"][0]["gate"]["result"] == "pass"


def test_veto_com_decisao_reject_passa(tmp_path, fake_l4):
    pos = {"meta.arquitetura-agentes": {**default_position("x"), "vote": "reject"}}
    s = start(tmp_path, CouncilGemini(positions=pos, verdict={**DEFAULT_VERDICT, "decision": "reject"}))
    assert s.state["rounds"][0]["gate"]["result"] == "pass"  # aprovar = aceitar o veredicto "reject"


def test_gate_low_confidence(tmp_path, fake_l4):
    s = start(tmp_path, CouncilGemini(verdict={**DEFAULT_VERDICT, "confidence": 0.5}))
    g = s.state["rounds"][0]["gate"]
    assert g["result"] == "low_confidence" and g["tau"] == 0.7 and "approve" not in g["allow"]


def test_confidence_fora_de_escala_e_invalida_nao_reescalada(tmp_path, fake_l4):
    s = start(tmp_path, CouncilGemini(verdict={**DEFAULT_VERDICT, "confidence": 8}))
    g = s.state["rounds"][0]["gate"]
    assert g["result"] == "invalid" and any("AU-13" in r for r in g["reasons"])
    assert s.state["verdict"]["confidence"] is None


def test_gate_incompleto_sem_kill_criteria(tmp_path, fake_l4):
    s = start(tmp_path, CouncilGemini(verdict={**DEFAULT_VERDICT, "kill_criteria": [], "next_actions": []}))
    g = s.state["rounds"][0]["gate"]
    assert g["result"] == "incomplete" and set(g["reasons"]) == {"sem kill criteria", "sem proximos passos"}


def test_hitl_para_e_resume_sem_decisao_nao_chama_o_llm(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g)
    again = cs.CouncilSession.load(s.out, deps=deps(g))
    out = again.resume()
    assert out["status"] == "awaiting_human" and "espera" in out["message"] and len(g.calls) == 7


def test_pedido_hitl_cumpre_o_contrato_v1(tmp_path, fake_l4):
    jsonschema = pytest.importorskip("jsonschema")
    s = start(tmp_path, CouncilGemini())
    schema = json.loads((REPO_ROOT / "docs/architecture/hitl/hitl-request-v1.json").read_text())
    jsonschema.validate(instance=hitl.latest_request(s.out), schema=schema)


def test_decisao_escrita_pelo_lado_node(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g)
    req = s.state["rounds"][0]["hitl"]["request_id"]
    hitl.write_decision(s.out, req, response="reject", responder_id="user:luiz", comment="nao agora")
    out = cs.CouncilSession.load(s.out, deps=deps(g)).resume()
    assert out["status"] == "rejected"
    mem = out["memory"]
    assert fake_l4.rows[mem["id"]]["status"] == "archived" and fake_l4.rows[mem["id"]]["archived_by"] == "human:user:luiz"
    assert "nao agora" in fake_l4.rows[mem["id"]]["archived_reason"]


def test_revise_abre_nova_ronda_com_o_comentario_humano(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g)
    first = s.state["rounds"][0]["memory"]["id"]
    out = s.decide("revise", actor="maestro", comment="considera o custo do Supabase free")
    assert out["round"] == 2 and out["status"] == "awaiting_human" and len(g.calls) == 14
    assert fake_l4.rows[first]["status"] == "archived"
    r2 = [c for c in g.calls[7:] if c["stage"] == "INDEPENDENT"]
    assert all("considera o custo do Supabase free" in c["user"] for c in r2)
    # max_rounds = 2: na ronda 2 ja nao ha revisao
    assert out["gate"]["allow"] == ["approve", "reject"]
    s.decide("approve", actor="maestro")
    assert fake_l4.rows[s.state["rounds"][1]["memory"]["id"]]["status"] == "active"


# ---------------------------------------------------------------------------
# Anonimato e anti-bajulacao
# ---------------------------------------------------------------------------

def test_chairman_nunca_ve_ids_dos_membros(tmp_path, fake_l4):
    pos = {mid: {**default_position(mid), "position": f"Eu, {mid}, acho que sim."} for mid in ARCH}
    g = CouncilGemini(positions=pos)
    start(tmp_path, g)
    chair = next(c for c in g.calls if c["stage"] == "SYNTHESIZE")
    for mid in ARCH:
        assert mid not in chair["system"] + chair["user"]
    assert "[membro]" in chair["user"]


def test_peer_nao_ve_a_propria_posicao_e_letras_sao_coerentes(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g)
    labels = s.state["rounds"][0]["labels"]
    own = {mid: lab for lab, mid in labels.items()}
    for c in (c for c in g.calls if c["stage"] == "PEER_RANK"):
        shown = re.search(r"letras ([A-Z, ]+), sem repetir", c["system"]).group(1).split(", ")
        assert own[c["who"]] not in shown and len(shown) == 2


def test_ballot_invalido_nao_bloqueia(tmp_path, fake_l4):
    g = CouncilGemini(ballots={"engenharia.desenvolvimento": {"ranking": ["Z"]}})
    s = start(tmp_path, g)
    rnd = s.state["rounds"][0]
    assert "engenharia.desenvolvimento" in rnd["ballot_errors"] and len(rnd["ballots"]) == 2
    assert s.state["status"] == "awaiting_human"


def test_borda():
    assert cs.borda({"x": {"ranking": ["A", "B", "C"]}, "y": {"ranking": ["B", "A", "C"]}}) == {"A": 0.75, "B": 0.75, "C": 0.0}
    assert cs.borda({"x": {"ranking": ["A"]}}) == {}  # 1 posicao nao ordena nada


# ---------------------------------------------------------------------------
# Falhas, quorum, orcamento
# ---------------------------------------------------------------------------

def test_membro_obrigatorio_falha_quorum_e_resume_so_repete_esse(tmp_path, fake_l4):
    g = CouncilGemini(positions={"meta.arquitetura-agentes": "isto nao e json"})
    s = start(tmp_path, g)
    assert s.state["status"] == "error" and "quorum" in s.state["error"] and len(g.calls) == 3
    g.positions = {}
    out = cs.CouncilSession.load(s.out, deps=deps(g)).resume()
    assert out["status"] == "awaiting_human"
    indep = [c["who"] for c in g.calls if c["stage"] == "INDEPENDENT"]
    assert indep.count("meta.arquitetura-agentes") == 2 and indep.count("engenharia.desenvolvimento") == 1


def test_orcamento_pausa_e_retoma_sem_repagar(tmp_path, fake_l4):
    g = CouncilGemini()
    s = start(tmp_path, g, max_tokens=2500)
    assert s.state["status"] == "paused_budget" and "orcamento" in s.state["error"]
    n = len(g.calls)
    assert 0 < n < 7
    out = cs.CouncilSession.load(s.out, deps=deps(g)).resume(max_tokens=10**6)
    assert out["status"] == "awaiting_human" and len(g.calls) == 7  # so as que faltavam


def test_tecto_por_omissao_e_o_da_area_do_conselho(tmp_path, fake_l4):
    s = start(tmp_path, CouncilGemini())
    assert s.state["max_tokens"] == 80000  # area software (areas.yaml)
    s2 = start(tmp_path / "sec", CouncilGemini(positions={}), council="security")
    assert s2.state["max_tokens"] == 40000


# ---------------------------------------------------------------------------
# Ledger: tokens por ronda e call_kind
# ---------------------------------------------------------------------------

def test_tokens_registados_por_ronda_e_call_kind(tmp_path, fake_l4):
    sent: list[dict] = []
    g = CouncilGemini()
    s = start(tmp_path, g, sink=sent.append)
    s.decide("revise", actor="maestro", comment="mais dados")
    rows = [json.loads(x) for x in (s.out / ew.LEDGER_FILE).read_text().splitlines()]
    assert len(rows) == 14 and len(sent) == 14
    kinds = [r["call_kind"] for r in rows[:7]]
    assert kinds == ["council_member"] * 3 + ["council_peer"] * 3 + ["council_chairman"]
    assert {r["step_id"].split("/")[1] for r in rows} == {"r1", "r2"}
    assert all(r["run_id"] == ew.ledger_run_uuid(s.state["session_id"]) and r["remote"] == "ok" for r in rows)
    summ = s.summary()["tokens_by_round"]
    assert summ["r1"]["calls"] == 7 and summ["r2"]["calls"] == 7
    assert summ["r1"]["tokens_total"] == sum(r["tokens_total"] for r in rows[:7])
    assert s.state["tokens_total"] == sum(r["tokens_total"] for r in rows)
    assert all(e["prompt_chars"] > 0 for e in s.state["ledger"])


def test_sem_database_url_a_l4_fica_desligada_mas_o_conselho_fecha(tmp_path):
    s = start(tmp_path, CouncilGemini(), l4store=False)
    assert s.state["rounds"][0]["memory"]["status"] == "disabled"
    out = s.decide("approve", actor="maestro")
    assert out["status"] == "done" and out["memory"]["skipped"]
    assert json.loads((s.out / cs.VERDICT_FILE).read_text())["decision"] == "approve"


def test_chairman_model_opcional(tmp_path, fake_l4, monkeypatch):
    orig = cs.get_council

    def with_model(root, cid):
        return {**orig(root, cid), "chairman_model": "gemini-outro"}

    monkeypatch.setattr(cs, "get_council", with_model)
    g = CouncilGemini()
    start(tmp_path, g)
    assert "gemini-outro" in g.calls[-1]["model"] and "gemini-outro" not in g.calls[0]["model"]


# ---------------------------------------------------------------------------
# Router: um pedido estrutural escala para conselho
# ---------------------------------------------------------------------------

def test_router_escala_pedido_estrutural_para_conselho(tmp_path, fake_l4):
    def no_llm(*a, **k):  # o router nao chama o LLM para escalar (keywords)
        raise AssertionError("o router nao devia chamar o LLM")

    router = Router(transport=no_llm)
    d = router.route("Decisao de arquitetura: o backend deve passar a API para filas?")
    assert d.outcome == "council" and d.council == "architecture" and d.area == "software" and d.hitl_required
    g = CouncilGemini()
    res = router.execute(d, out_dir=tmp_path / "r", council_deps=deps(g))
    assert res["executed"] and res["council"]["status"] == "awaiting_human" and len(g.calls) == 7
    assert json.loads((tmp_path / "r" / "route.json").read_text())["council"] == "architecture"


def test_router_sem_keyword_estrutural_nao_escala_e_no_council_desliga():
    calls = []

    def llm(url, headers, body, timeout):
        calls.append(1)
        text = json.dumps({"mode": "agent", "agent": "engenharia.desenvolvimento", "confidence": 0.9, "reason": "x"})
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}}], "usageMetadata": {"totalTokenCount": 3}}

    assert Router(transport=llm).route("corrige o bug no backend da api").outcome == "agent"
    d = Router(transport=llm, councils=False).route("Decisao de arquitetura: o backend deve usar filas?")
    assert d.outcome == "agent" and d.council is None and len(calls) == 2


def test_escalada_so_nas_areas_do_conselho():
    assert cs.match_escalation(REPO_ROOT, "decisao de arquitetura do post", "marketing") is None
    assert cs.match_escalation(REPO_ROOT, "Uma decisão de segurança sobre segredos", "security")[0] == "security"


# ---------------------------------------------------------------------------
# CLI e custo (countTokens)
# ---------------------------------------------------------------------------

def test_cli_run_decide_status(tmp_path, monkeypatch, capsys):
    from plan_runner.cli import main

    g = CouncilGemini()
    monkeypatch.setattr(ew, "httpx_transport", g)
    out = tmp_path / "c"
    assert main(["council", "run", "architecture", TOPIC, "--out", str(out)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "awaiting_human" and first["memory"]["status"] == "disabled"
    assert main(["council", "decide", str(out), "approve", "--by", "maestro"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "done"
    assert main(["council", "status", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["hitl"]["responder"] == "human:maestro"
    assert main(["council", "decide", str(out), "reject"]) == 1  # ja fechado
    assert main(["council", "validate"]) == 0


def test_cost_com_count_tokens(tmp_path):
    seen = []

    def counter(url, headers, body, timeout):
        assert url.endswith(":countTokens") and headers["x-goog-api-key"] == "chave-de-teste"
        req = body["generateContentRequest"]
        n = len(req["systemInstruction"]["parts"][0]["text"] + req["contents"][0]["parts"][0]["text"]) // 4
        seen.append(n)
        return 200, {"totalTokens": n}

    r = cs.estimate_cost("architecture", TOPIC, transport=counter)
    assert r["calls_per_round"] == 7 and len(r["calls"]) == 7 and len(seen) == 7
    assert r["round_floor_tokens"] == sum(seen) < r["round_ceiling_tokens"]
    assert [c["stage"] for c in r["calls"]] == ["independent"] * 3 + ["peer_rank"] * 3 + ["synthesize"]
