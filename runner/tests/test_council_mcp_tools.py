"""M-011: as 3 ferramentas MCP do conselho (mcp/plan_runner), de ponta a ponta com o motor real.

Ficam em runner/tests para correrem no CI (runner-tests.yml). Nao precisam do SDK `mcp`: testam tools_impl,
que e o que o servidor expoe. A sessao do conselho e real; so o cadastro de IAs e falso.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from plan_runner import council_providers as prov
from plan_runner import council_session as cs

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "mcp" / "plan_runner"))

from mcp_plan_runner import policy, tools_impl  # noqa: E402

TOPIC = "Estrutura do projeto novo: monorepo ou repositorios separados?"
POSITION = {"vote": "approve", "confidence": 0.8, "position": "Monorepo, com CI unica.", "arguments": ["menos atrito"],
            "risks": ["acoplamento"], "conditions": [], "kill_criteria": ["CI > 15 min"], "veto": False, "veto_reason": None}


@pytest.fixture
def session(tmp_path, monkeypatch):
    """Raiz do MCP = tmp_path; uma sessao `structural` real la dentro, a espera de 3 IAs."""
    monkeypatch.setenv("PLAN_RUNNER_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("PLAN_RUNNER_MCP_PROFILE", "strict")
    monkeypatch.setenv("PLAN_RUNNER_MCP_KEY", "chave-do-servidor")
    monkeypatch.setattr(policy, "audit_path", lambda: tmp_path / "audit.jsonl")
    monkeypatch.setattr(policy, "rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(tools_impl, "rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(prov, "load_providers",
                        lambda repo_root=REPO_ROOT: [{"id": "claude", "kind": "mcp"}, {"id": "gpt", "kind": "mcp"},
                                                     {"id": "grok", "kind": "mcp"}])
    monkeypatch.setattr(tools_impl, "_ensure_runner_on_path", lambda: tmp_path)
    s = cs.CouncilSession(tmp_path / "pilots" / "council-structural-t1", deps=cs.CouncilDeps())
    s.start("structural", TOPIC, context="contexto de negocio XYZ")
    return s


def test_scopes_e_mutacao_declarados():
    assert policy.SCOPES["council_get_request"] == "runner:council:read"
    assert policy.SCOPES["council_status"] == "runner:council:read"
    assert policy.SCOPES["council_submit_position"] == "runner:council:submit"
    assert "council_submit_position" in policy.MUTATING and "council_get_request" not in policy.MUTATING


def test_status_pelo_mcp(session):
    st = tools_impl.council_status("pilots/council-structural-t1")
    assert st["ok"] and st["status"]["status"] == "awaiting_external" and st["status"]["waiting_for"] == ["claude", "gpt", "grok"]


def test_leitura_nao_precisa_de_chave_do_servidor_e_entrega_sim_em_strict(session, monkeypatch):
    rel = "pilots/council-structural-t1"
    # leitura: autorizada em strict sem chave do servidor
    req = tools_impl.council_get_request(rel, "gpt")
    assert req["ok"] and req["round"] == 1 and TOPIC in req["request"] and "vote" in req["answer_format"]
    # entrega: em strict exige PLAN_RUNNER_MCP_KEY no servidor (configurada no fixture)
    out = tools_impl.council_submit_position(rel, "gpt", json.dumps(POSITION))
    assert out["ok"] and out["waiting_for"] == ["claude", "grok"]
    # segunda entrega recusada, erro estruturado (sem traceback)
    again = tools_impl.council_submit_position(rel, "gpt", json.dumps(POSITION))
    assert again["ok"] is False and "já entregou" in again["error"]
    # sem chave configurada no servidor, o strict recusa a entrega (mutacao) mas deixa ler
    monkeypatch.delenv("PLAN_RUNNER_MCP_KEY", raising=False)
    blocked = tools_impl.council_submit_position(rel, "grok", json.dumps(POSITION))
    assert blocked["ok"] is False and "PLAN_RUNNER_MCP_KEY" in blocked["error"]
    assert tools_impl.council_status(rel)["ok"]


def test_caminho_fora_do_repo_e_recusado(session, tmp_path):
    outside = tmp_path.parent / "fora-do-repo"
    outside.mkdir(exist_ok=True)
    r = tools_impl.council_status(str(outside))
    assert r["ok"] is False and "outside repo root" in r["error"]
    r = tools_impl.council_submit_position("../fora-do-repo", "claude", json.dumps(POSITION))
    assert r["ok"] is False


def test_dir_sem_sessao_de_conselho_e_recusado(session, tmp_path):
    (tmp_path / "pilots" / "vazio").mkdir(parents=True)
    r = tools_impl.council_status("pilots/vazio")
    assert r["ok"] is False and "sem sessão de conselho" in r["error"]


def test_auditoria_nao_guarda_tema_posicao_nem_chaves(session, tmp_path):
    rel = "pilots/council-structural-t1"
    tools_impl.council_get_request(rel, "claude")
    tools_impl.council_submit_position(rel, "claude", json.dumps(POSITION), key="chave-secreta-da-ia")
    log = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "council_submit_position" in log and "claude" in log
    for forbidden in ("Monorepo", "XYZ", TOPIC, "chave-secreta-da-ia"):
        assert forbidden not in log


def test_end_to_end_do_mcp_ate_ao_motor(session, monkeypatch):
    """As 3 entregas pelo MCP chegam ao motor: com as 3 posicoes a sessao deixa de esperar."""
    rel = "pilots/council-structural-t1"
    for pid, vote in (("claude", "approve"), ("gpt", "approve"), ("grok", "reject")):
        assert tools_impl.council_submit_position(rel, pid, json.dumps({**POSITION, "vote": vote}))["ok"]
    assert tools_impl.council_status(rel)["status"]["waiting_for"] == []
    loaded = cs.CouncilSession.load(session.out, deps=cs.CouncilDeps())
    rnd = loaded.state["rounds"][0]
    loaded._collect_external(rnd)
    assert {m: p["vote"] for m, p in rnd["positions"].items()} == {"ext:claude": "approve", "ext:gpt": "approve", "ext:grok": "reject"}
