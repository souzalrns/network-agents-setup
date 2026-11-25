"""M-011: conselho `structural` com IAs externas opcionais (P-91 = A, P-92 = B).

O Gemini (chairman) e a L4 sao falsos, como em test_council.py. As IAs externas "entregam" posicoes pelas mesmas
funcoes que o MCP expoe (council_providers.get_request / submit_position / session_status).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from plan_runner import council_providers as prov
from plan_runner import council_session as cs
from plan_runner.plan_schema import plan_errors
from tests.test_council import (  # noqa: F401  (_env e fixture autouse partilhada)
    CouncilGemini,
    _env,
    default_position,
    deps,
    fake_l4,  # noqa: F401
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPIC = "Estrutura do projeto novo: monorepo ou repositorios separados?"

PLAN = {
    "id": "projeto-base",
    "objective": "Monorepo com tres pacotes e CI unica.",
    "done_when": ["out/estrutura.md exists"],
    "steps": [
        {"id": "s1", "action": "research", "task": "Levantar o que ja existe"},
        {"id": "s2", "action": "planejador", "task": "Escrever a estrutura", "depends_on": ["s1"]},
    ],
}
VERDICT = {
    "decision": "approve", "summary": "Monorepo.", "rationale": "As posicoes convergem.", "conditions": [],
    "dissent": [], "kill_criteria": ["CI > 15 min"], "next_actions": [{"action": "criar o esqueleto", "owner": "dev"}],
    "risks": ["acoplamento"], "confidence": 0.85, "plan": PLAN,
}


def register(monkeypatch, ids: list[str], key_env: dict[str, str] | None = None) -> None:
    providers = [{"id": i, "kind": "mcp", **({"key_env": key_env[i]} if key_env and i in key_env else {})} for i in ids]
    monkeypatch.setattr(prov, "load_providers", lambda repo_root=REPO_ROOT: providers)


def open_session(tmp_path, gemini, **kw) -> cs.CouncilSession:
    s = cs.CouncilSession(tmp_path / "council", deps=deps(gemini, l4store=False))
    s.start("structural", kw.pop("topic", TOPIC), **kw)
    return s


def pos(vote: str = "approve", **over) -> dict:
    return {**default_position("x"), "vote": vote, **over}


def submit_all(s: cs.CouncilSession, votes: dict[str, str]) -> None:
    for pid, vote in votes.items():
        prov.submit_position(s.out, pid, pos(vote, position=f"{pid} diz {vote} e argumenta."))


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------

def test_cadastro_real_vem_vazio_e_valido():
    assert prov.load_providers(REPO_ROOT) == []
    assert prov.validate_providers(REPO_ROOT) == []
    assert cs.validate_councils(REPO_ROOT) == []


@pytest.mark.parametrize("n,mode", [(0, "none"), (1, "simple"), (2, "even"), (3, "full"), (4, "even"), (5, "full")])
def test_modo_pelo_numero_de_ias(n, mode):
    assert prov.panel_mode(n) == mode


@pytest.mark.parametrize("entry,expect", [
    ({"id": "Claude"}, "minúsculas"),
    ({"id": "gpt", "kind": "api"}, "não suportado"),
    ({"id": "gpt", "key_env": "sk-abc123"}, "NOME de uma variável"),
    ({"id": "gpt", "api_key": "x"}, "campos desconhecidos"),
])
def test_cadastro_recusa(tmp_path, entry, expect):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "council-providers.yaml").write_text(yaml.safe_dump({"providers": [entry]}), encoding="utf-8")
    assert any(expect in e for e in prov.validate_providers(tmp_path))


def test_cadastro_recusa_repetidas_e_excesso(tmp_path):
    (tmp_path / "config").mkdir()
    ids = [{"id": f"ia{i}"} for i in range(6)] + [{"id": "ia1"}]
    (tmp_path / "config" / "council-providers.yaml").write_text(yaml.safe_dump({"providers": ids}), encoding="utf-8")
    errors = prov.validate_providers(tmp_path)
    assert any("repetido" in e for e in errors) and any("no máximo" in e for e in errors)


def test_sem_ias_registadas_o_structural_recusa_e_aponta_o_interno(tmp_path):
    g = CouncilGemini()
    with pytest.raises(cs.CouncilError, match="conselho interno"):
        open_session(tmp_path, g)
    assert g.calls == []  # nem uma chamada paga


# ---------------------------------------------------------------------------
# Conselho completo (3 IAs)
# ---------------------------------------------------------------------------

def test_tres_ias_ponta_a_ponta_ate_ao_plano_aprovado(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)

    # espera as 3 IAs, sem gastar nenhuma chamada
    assert s.state["status"] == "awaiting_external" and g.calls == []
    assert s.state["panel"] == {"mode": "full", "providers": ["claude", "gpt", "grok"]}
    assert prov.session_status(s.out)["waiting_for"] == ["claude", "gpt", "grok"]

    # a IA le o pedido: so tema/contexto e formato, nada das outras
    req = prov.get_request(s.out, "gpt")
    assert TOPIC in req["request"] and "vote" in req["answer_format"] and "claude" not in json.dumps(req["request"])

    submit_all(s, {"claude": "approve", "gpt": "approve", "grok": "reject"})
    assert prov.session_status(s.out)["waiting_for"] == []

    s = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False))
    out = s.resume()
    # so o chairman gasta uma chamada: critica entre pares e dele (P-92 = B), os membros nao sao chamados
    assert g.stages() == ["SYNTHESIZE"]
    assert out["status"] == "awaiting_human" and out["gate"]["result"] == "pass"
    assert out["gate"]["warnings"] == []
    # o chairman nao ve nomes de IAs (anonimizado)
    chairman_user = g.calls[0]["user"]
    assert "ext:claude" not in chairman_user and "ext:grok" not in chairman_user
    # o dissidente nunca se perde
    assert any(d["member_id"] == "ext:grok" for d in out["verdict"]["dissent"])

    s.decide("approve", actor="luiz")
    assert s.state["status"] == "done"
    plan = yaml.safe_load((s.out / "plan.yaml").read_text(encoding="utf-8"))
    assert plan_errors(plan) == [] and plan["id"] == "projeto-base"
    final = json.loads((s.out / "verdict.json").read_text(encoding="utf-8"))
    assert final["plan_file"] == "plan.yaml"


def test_resume_sem_entregas_continua_a_esperar(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "approve"})
    s = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False))
    out = s.resume()
    assert out["status"] == "awaiting_external" and out["waiting_for"] == ["gpt", "grok"] and g.calls == []


def test_partial_prossegue_com_quorum_e_recusa_sem_ele(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "approve", "gpt": "approve"})
    s = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False))
    out = s.resume(partial=True)
    assert out["status"] == "awaiting_human" and set(out["verdict"]["participants"]["members"]) == {"ext:claude", "ext:gpt"}

    # so uma posicao num painel completo: sem quorum
    s2 = cs.CouncilSession(tmp_path / "outro", deps=deps(g, l4store=False))
    s2.start("structural", TOPIC)
    submit_all(s2, {"claude": "approve"})
    s2 = cs.CouncilSession.load(s2.out, deps=deps(g, l4store=False))
    out2 = s2.resume(partial=True)
    assert out2["status"] == "error" and "quorum" in out2["error"]


# ---------------------------------------------------------------------------
# Modos simples e par
# ---------------------------------------------------------------------------

def test_modo_simples_uma_ia(tmp_path, monkeypatch):
    register(monkeypatch, ["claude"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)
    assert s.state["panel"]["mode"] == "simple"
    submit_all(s, {"claude": "approve"})
    out = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False)).resume()
    assert g.stages() == ["SYNTHESIZE"] and out["status"] == "awaiting_human"
    assert any("modo simples" in w for w in out["gate"]["warnings"])
    assert "approve" in out["gate"]["allow"]  # o gate humano e o plano mantem-se


def test_modo_par_avisa_que_nao_ha_desempate(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)
    assert s.state["panel"]["mode"] == "even"
    submit_all(s, {"claude": "approve", "gpt": "reject"})
    out = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False)).resume()
    assert any("sem desempate" in w for w in out["gate"]["warnings"])


# ---------------------------------------------------------------------------
# Plano executavel
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_plan", [
    None,
    {"id": "x", "steps": [{"id": "s1"}]},                       # passo sem action
    {"id": "x", "steps": [{"id": "s1", "action": "a"}], "campo_inventado": 1},  # raiz com campo fora do schema
])
def test_plano_invalido_bloqueia_o_approve(tmp_path, monkeypatch, bad_plan):
    register(monkeypatch, ["claude"])
    g = CouncilGemini(verdict={**VERDICT, "plan": bad_plan})
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "approve"})
    out = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False)).resume()
    assert out["gate"]["result"] == "invalid" and "approve" not in out["gate"]["allow"]
    assert any("plano" in r for r in out["gate"]["reasons"])


def test_reject_nao_exige_plano(tmp_path, monkeypatch):
    register(monkeypatch, ["claude"])
    g = CouncilGemini(verdict={**VERDICT, "decision": "reject", "plan": None})
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "reject"})
    out = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False)).resume()
    assert out["verdict"]["invalid"] == []


def test_conselho_interno_nao_exige_plano(tmp_path, fake_l4):  # noqa: F811
    """Regressao: os conselhos internos continuam sem `plan` (emits_plan so existe no structural)."""
    g = CouncilGemini()
    s = cs.CouncilSession(tmp_path / "c", deps=deps(g))
    s.start("architecture", "Decisao de arquitetura: mudar o checkpointer?")
    assert s.state["rounds"][0]["gate"]["result"] == "pass"
    assert s.state["council"]["emits_plan"] is False and s.state["rounds"][0]["verdict"]["plan"] is None


# ---------------------------------------------------------------------------
# Entregas: regras e seguranca
# ---------------------------------------------------------------------------

def test_entrega_unica_por_ronda_e_validada(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT))
    prov.submit_position(s.out, "claude", pos())
    with pytest.raises(prov.ProviderError, match="já entregou"):
        prov.submit_position(s.out, "claude", pos("reject"))
    with pytest.raises(prov.ProviderError, match="posição inválida"):
        prov.submit_position(s.out, "gpt", pos(confidence=7))           # fora de [0, 1]: nunca reescalado (AU-13)
    with pytest.raises(prov.ProviderError, match="posição inválida"):
        prov.submit_position(s.out, "gpt", {"vote": "talvez", "confidence": 0.5, "position": "x"})
    with pytest.raises(prov.ProviderError, match="não é JSON válido"):
        prov.submit_position(s.out, "gpt", "isto nao e json")
    with pytest.raises(prov.ProviderError, match="não está registada"):
        prov.submit_position(s.out, "intruso", pos())
    # a primeira entrega ficou intacta
    assert prov.read_submission(s.out, 1, "claude")["vote"] == "approve"
    # aceita JSON em texto (e o que um cliente MCP envia)
    prov.submit_position(s.out, "gpt", json.dumps(pos("conditional", conditions=["medir primeiro"])))
    assert prov.read_submission(s.out, 1, "gpt")["vote"] == "conditional"


def test_chave_por_ia_impede_personificacao(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt"], key_env={"claude": "COUNCIL_KEY_CLAUDE", "gpt": "COUNCIL_KEY_GPT"})
    monkeypatch.setenv("COUNCIL_KEY_CLAUDE", "segredo-claude")
    monkeypatch.delenv("COUNCIL_KEY_GPT", raising=False)
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT))
    with pytest.raises(prov.ProviderError, match="chave inválida"):
        prov.submit_position(s.out, "claude", pos())
    with pytest.raises(prov.ProviderError, match="chave inválida"):
        prov.get_request(s.out, "claude", key="segredo-gpt")
    # a chave certa passa
    assert prov.get_request(s.out, "claude", key="segredo-claude")["round"] == 1
    assert prov.submit_position(s.out, "claude", pos(), key="segredo-claude")["ok"]
    # key_env declarada mas sem variavel no servidor: falha fechada
    with pytest.raises(prov.ProviderError, match="variável não está definida"):
        prov.submit_position(s.out, "gpt", pos(), key="qualquer")


def test_nao_se_entrega_fora_de_hora(tmp_path, monkeypatch):
    register(monkeypatch, ["claude"])
    g = CouncilGemini(verdict=VERDICT)
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "approve"})
    s = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False))
    s.resume()  # agora esta em awaiting_human
    with pytest.raises(prov.ProviderError, match="não a espera de posições"):
        prov.submit_position(s.out, "claude", pos())
    with pytest.raises(prov.ProviderError, match="não a espera de posições"):
        prov.get_request(s.out, "claude")


def test_status_nao_expoe_tema_nem_posicoes(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT), context="segredo de negocio XYZ")
    submit_all(s, {"claude": "approve"})
    dump = json.dumps(prov.session_status(s.out))
    assert "XYZ" not in dump and TOPIC not in dump and "approve" not in dump


def test_revisao_humana_abre_nova_ronda_e_pede_novas_posicoes(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    g = CouncilGemini(verdict={**VERDICT, "confidence": 0.3})  # abaixo de tau: o humano so pode rejeitar/editar
    s = open_session(tmp_path, g)
    submit_all(s, {"claude": "approve", "gpt": "approve", "grok": "approve"})
    s = cs.CouncilSession.load(s.out, deps=deps(g, l4store=False))
    out = s.resume()
    assert out["gate"]["result"] == "low_confidence"
    out = s.decide("revise", actor="luiz", comment="detalha os custos")
    assert out["status"] == "awaiting_external" and out["round"] == 2
    assert out["waiting_for"] == ["claude", "gpt", "grok"]  # ronda nova: as IAs voltam a ser pedidas
    assert "detalha os custos" in prov.get_request(s.out, "claude")["request"]  # e vêem o comentario do humano


# ---------------------------------------------------------------------------
# Ponte manual: colar o pedido numa IA e colar a resposta de volta (sem MCP)
# ---------------------------------------------------------------------------

def test_ponte_manual_pedido_para_colar_e_resposta_suja(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt", "grok"])
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT))
    text = prov.paste_ready(s.out, "gpt")
    assert TOPIC in text and "APENAS" in text and "ext:" not in text and "claude" not in text
    # resposta como as IAs de chat costumam dar: conversa + cerca de codigo + conversa
    reply = "Claro! Aqui vai:\n```json\n" + json.dumps(pos("conditional", conditions=["medir"])) + "\n```\nEspero que ajude."
    assert prov.submit_position(s.out, "gpt", reply)["ok"]
    assert prov.read_submission(s.out, 1, "gpt")["vote"] == "conditional"
    with pytest.raises(prov.ProviderError, match="não é JSON válido"):
        prov.submit_position(s.out, "grok", "so conversa, sem objecto nenhum")


def test_cli_prompt_e_submit_de_texto_colado(tmp_path, monkeypatch, capsys):
    register(monkeypatch, ["claude"])
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT))
    assert cs.main(["prompt", str(s.out), "claude"]) == 0
    assert TOPIC in capsys.readouterr().out
    f = tmp_path / "resposta.txt"
    f.write_text("Resposta:\n" + json.dumps(pos("approve")) + "\nfim", encoding="utf-8")
    assert cs.main(["submit", str(s.out), "claude", "--file", str(f)]) == 0
    assert prov.read_submission(s.out, 1, "claude")["vote"] == "approve"


def test_status_da_cli_reflete_as_entregas_ao_vivo(tmp_path, monkeypatch):
    register(monkeypatch, ["claude", "gpt"])
    s = open_session(tmp_path, CouncilGemini(verdict=VERDICT))
    submit_all(s, {"gpt": "approve"})
    summary = cs.CouncilSession.load(s.out, deps=deps(CouncilGemini(), l4store=False)).summary()
    assert summary["waiting_for"] == ["claude"]
