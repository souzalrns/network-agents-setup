"""GOV-LOCAL-1: política, grafo de delegação, recibos encadeados e ligação ao motor."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from plan_runner import governance_local as g

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
FUT = (NOW + timedelta(days=1)).isoformat()
PAST = (NOW - timedelta(days=1)).isoformat()


def pol(rules=None, default="deny", mode="enforce"):
    return g.Policy(mode=mode, default=default, rules=rules or [], max_depth=3)


def graph(tmp_path, depth=3):
    return g.DelegationGraph(tmp_path, max_depth=depth)


# -- política ---------------------------------------------------------------
def test_config_do_repo_e_valida():
    p = g.load_policy()
    assert p.mode in g.MODES and p.default in g.EFFECTS


def test_politica_ausente_ou_invalida_falha_fechado(tmp_path):
    with pytest.raises(g.GovernanceError):
        g.load_policy(tmp_path / "nao-existe.yaml")
    bad = tmp_path / "b.yaml"
    bad.write_text("version: 1\nmode: x\ndefault: allow\nrules: []\n", encoding="utf-8")
    with pytest.raises(g.GovernanceError):
        g.load_policy(bad)


def test_deny_ganha_a_approve_que_ganha_a_allow():
    rules = [{"agent": "*", "capability": "tool:*", "effect": "allow"},
             {"agent": "*", "capability": "tool:send_*", "effect": "approve"},
             {"agent": "x", "capability": "tool:send_mail", "effect": "deny"}]
    p = pol(rules)
    assert p.match("y", "tool:read") == "allow"
    assert p.match("y", "tool:send_mail") == "approve"
    assert p.match("x", "tool:send_mail") == "deny"


def test_sem_regra_decide_o_default():
    assert g.authorize(pol(default="deny"), None, "a", "tool:x").effect == "deny"
    assert g.authorize(pol(default="allow"), None, "a", "tool:x").effect == "allow"


# -- delegação ----------------------------------------------------------------
def test_delegacao_valida_da_allow_e_deny_da_politica_vence(tmp_path):
    gr = graph(tmp_path)
    gr.grant(from_="human:luiz", to="agent:a", scope=["tool:read*"], granted_by="human:luiz", now=NOW)
    d = g.authorize(pol(), gr, "agent:a", "tool:read_file", now=NOW)
    assert d.allowed and len(d.chain) == 1
    deny = pol([{"agent": "agent:a", "capability": "tool:read_file", "effect": "deny"}])
    assert g.authorize(deny, gr, "agent:a", "tool:read_file", now=NOW).effect == "deny"


def test_so_se_delega_o_que_se_tem(tmp_path):
    gr = graph(tmp_path)
    e1 = gr.grant(from_="human:luiz", to="agent:a", scope=["tool:read*"], granted_by="human:luiz", now=NOW)
    with pytest.raises(g.GovernanceError, match="só se delega"):
        gr.grant(from_="agent:a", to="agent:b", scope=["tool:write"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    e2 = gr.grant(from_="agent:a", to="agent:b", scope=["tool:read_file"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    assert e2["depth"] == 1
    assert g.authorize(pol(), gr, "agent:b", "tool:read_file", now=NOW).chain == [e1["id"], e2["id"]]


def test_raiz_tem_de_ser_humana(tmp_path):
    with pytest.raises(g.GovernanceError):
        graph(tmp_path).grant(from_="agent:a", to="agent:b", scope=["*"], granted_by="human:luiz", now=NOW)
    with pytest.raises(g.GovernanceError):
        graph(tmp_path).grant(from_="human:luiz", to="agent:b", scope=["*"], granted_by="agent:a", now=NOW)


def test_ciclo_profundidade_e_auto_delegacao(tmp_path):
    gr = graph(tmp_path, depth=2)
    e1 = gr.grant(from_="human:luiz", to="agent:a", scope=["*"], granted_by="human:luiz", now=NOW)
    with pytest.raises(g.GovernanceError, match="ciclo"):
        gr.grant(from_="agent:a", to="human:luiz", scope=["x"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    e2 = gr.grant(from_="agent:a", to="agent:b", scope=["x"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    with pytest.raises(g.GovernanceError, match="profundidade"):
        gr.grant(from_="agent:b", to="agent:c", scope=["x"], granted_by="human:luiz", parent=e2["id"], now=NOW)
    with pytest.raises(g.GovernanceError):
        gr.grant(from_="human:luiz", to="human:luiz", scope=["x"], granted_by="human:luiz", now=NOW)


def test_expiracao_e_filha_nao_dura_mais_que_mae(tmp_path):
    gr = graph(tmp_path)
    with pytest.raises(g.GovernanceError, match="expirada"):
        gr.grant(from_="human:luiz", to="agent:a", scope=["*"], granted_by="human:luiz", expires_at=PAST, now=NOW)
    e1 = gr.grant(from_="human:luiz", to="agent:a", scope=["*"], granted_by="human:luiz", expires_at=FUT, now=NOW)
    with pytest.raises(g.GovernanceError, match="durar mais"):
        gr.grant(from_="agent:a", to="agent:b", scope=["x"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    later = NOW + timedelta(days=2)
    assert g.authorize(pol(), gr, "agent:a", "x", now=later).effect == "deny"


def test_revogar_a_mae_corta_as_filhas(tmp_path):
    gr = graph(tmp_path)
    e1 = gr.grant(from_="human:luiz", to="agent:a", scope=["*"], granted_by="human:luiz", now=NOW)
    gr.grant(from_="agent:a", to="agent:b", scope=["x"], granted_by="human:luiz", parent=e1["id"], now=NOW)
    assert g.authorize(pol(), gr, "agent:b", "x", now=NOW).allowed
    with pytest.raises(g.GovernanceError):
        gr.revoke(e1["id"], by="agent:a")
    gr.revoke(e1["id"], by="human:luiz")
    assert g.authorize(pol(), gr, "agent:b", "x", now=NOW).effect == "deny"


# -- recibos ------------------------------------------------------------------
def _receipts(tmp_path, n=3):
    log = g.ReceiptLog(tmp_path)
    for i in range(n):
        log.append(run_id="r1", step_id=f"s{i}", agent="a", capability="step:run", decision="allow", inputs={"i": i})
    return log


def test_cadeia_integra_verifica(tmp_path):
    log = _receipts(tmp_path)
    assert log.verify() == []
    recs = log.records()
    assert [r["seq"] for r in recs] == [1, 2, 3] and recs[0]["prev"] == g.GENESIS and recs[1]["prev"] == recs[0]["hash"]


def test_edicao_remocao_meio_e_reordenacao_sao_detetadas(tmp_path):
    log = _receipts(tmp_path)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    edit = json.loads(lines[1])
    edit["decision"] = "deny"
    log.path.write_text("\n".join([lines[0], json.dumps(edit), lines[2]]) + "\n", encoding="utf-8")
    assert any("adulterado" in p for p in log.verify())
    log.path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    assert log.verify()
    log.path.write_text("\n".join([lines[0], lines[2], lines[1]]) + "\n", encoding="utf-8")
    assert log.verify()


def test_corte_do_fim_so_se_ve_com_o_head(tmp_path):
    log = _receipts(tmp_path)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    log.path.write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
    assert any("cortado" in p for p in log.verify())
    log.head.unlink()
    assert any("falta" in p for p in log.verify())


def test_hmac_assina_e_deteta_chave_errada(tmp_path, monkeypatch):
    monkeypatch.setenv(g.HMAC_ENV, "chave-um")
    log = _receipts(tmp_path, 2)
    assert log.records()[0]["sig"] and log.verify() == []
    monkeypatch.setenv(g.HMAC_ENV, "chave-dois")
    assert any("assinatura inválida" in p for p in log.verify())
    monkeypatch.delenv(g.HMAC_ENV)
    assert any("por verificar" in p for p in log.verify())


def test_recibo_nao_guarda_o_conteudo_dos_inputs(tmp_path):
    log = g.ReceiptLog(tmp_path)
    log.append(run_id="r", step_id="s", agent="a", capability="c", decision="allow", inputs={"segredo": "abc123"})
    assert "abc123" not in log.path.read_text(encoding="utf-8")


def test_aprovador_tem_de_ser_humano(tmp_path):
    with pytest.raises(g.GovernanceError):
        g.ReceiptLog(tmp_path).append(run_id="r", step_id="s", agent="a", capability="c", decision="approve", approver="agent:x")


def test_fim_de_linha_corrompido_nao_rebenta_verify(tmp_path):
    log = _receipts(tmp_path, 1)
    log.path.write_text("isto não é json\n", encoding="utf-8")
    assert log.verify()


# -- ligação ao motor ----------------------------------------------------------
def _step(action="a", tools=None, gate=None):
    return SimpleNamespace(id="s1", action=action, tools_allowed=tools or [], human_gate=gate, inputs=[])


def test_gate_record_nunca_bloqueia_mas_regista_a_decisao(tmp_path):
    ok, d = g.governance_gate(tmp_path, _step(), policy=pol(default="deny", mode="record"))
    assert ok and d.effect == "deny"


def test_gate_enforce_bloqueia_deny_e_approve_sem_gate_humano(tmp_path):
    rules = [{"agent": "*", "capability": "step:run", "effect": "allow"},
             {"agent": "*", "capability": "tool:send_*", "effect": "approve"}]
    p = pol(rules)
    assert g.governance_gate(tmp_path, _step(), policy=p)[0] is True
    assert g.governance_gate(tmp_path, _step(tools=["send_mail"]), policy=p)[0] is False
    assert g.governance_gate(tmp_path, _step(tools=["send_mail"], gate=object()), policy=p)[0] is True
    assert g.governance_gate(tmp_path, _step(), policy=pol())[0] is False


def test_engine_escreve_recibos_verificaveis(run_cli, plan_path, tmp_run_dir):
    out = tmp_run_dir
    proc = run_cli(["run", str(plan_path), "--engine", "native", "--mode", "stub", "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    log = g.ReceiptLog(out)
    recs = log.records()
    assert recs and all(r["capability"] == g.STEP_CAPABILITY for r in recs)
    assert log.verify() == []


def test_cli_verify(tmp_path, capsys):
    _receipts(tmp_path, 2)
    assert g.main(["verify", str(tmp_path)]) == 0
    p = tmp_path / g.RECEIPTS
    p.write_text(p.read_text(encoding="utf-8").replace('"allow"', '"deny"', 1), encoding="utf-8")
    assert g.main(["verify", str(tmp_path)]) == 1


# -- GOV-LOCAL-1 fecho: LangGraph, enforce e M-010 -------------------------------
def _plano(tmp_path, steps):
    import yaml

    from tests.politica import politica_dict
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump(politica_dict({"id": "gov", "objective": "x", "steps": steps})), encoding="utf-8")
    return p


GATE = {"level": "step", "kind": "output_review", "allow": ["approve", "reject", "edit"]}


@pytest.fixture
def _skills_offline(monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")


def _cfg(tmp_path, monkeypatch, mode="enforce", default="deny"):
    f = tmp_path / "gov.yaml"
    f.write_text(f"version: 1\nmode: {mode}\ndefault: {default}\nrules: []\n", encoding="utf-8")
    monkeypatch.setattr(g, "CONFIG_FILE", f)


def test_langgraph_escreve_recibos_e_o_gate_leva_aprovador(tmp_path, tmp_run_dir, _skills_offline):
    pytest.importorskip("langgraph.graph")
    from plan_runner.engine import resume_run  # noqa: F401
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph
    plan = _plano(tmp_path, [{"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
                             {"id": "hitl", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE}])
    assert run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    assert resume_plan_langgraph(tmp_run_dir, decision="approve")["state"] == "done"
    log = g.ReceiptLog(tmp_run_dir)
    recs = {r["step_id"]: r for r in log.records()}
    assert set(recs) == {"copy", "hitl"} and recs["hitl"]["approver"] == "human:cli" and recs["copy"]["approver"] is None
    assert log.verify() == []


@pytest.mark.parametrize("engine", ["native", "langgraph"])
def test_enforce_recusa_o_passo_e_deixa_recibo_deny(tmp_path, tmp_run_dir, monkeypatch, engine, _skills_offline):
    _cfg(tmp_path, monkeypatch)
    plan = _plano(tmp_path, [{"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"}])
    if engine == "native":
        from plan_runner.engine import run_plan
        st = run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    else:
        pytest.importorskip("langgraph.graph")
        from plan_runner.langgraph_engine import run_plan_langgraph
        st = run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)
    assert st["state"] == "failed" and "governança" in st["detail"]
    assert not (tmp_run_dir / "artifacts/01-copy.md").exists()
    recs = g.ReceiptLog(tmp_run_dir).records()
    assert [r["decision"] for r in recs] == ["deny"] and g.ReceiptLog(tmp_run_dir).verify() == []


def test_m010_decisao_responde_a_um_gate_e_deixa_o_outro_pendente(tmp_path, tmp_run_dir, _skills_offline):
    pytest.importorskip("langgraph.graph")
    from plan_runner import approval
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph
    plan = _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "g2", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE}])
    st = run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)
    assert st["state"] == "paused_human_gate"
    assert sorted(approval.pending_gates(tmp_run_dir, st["run_id"])) == ["g1", "g2"]
    st = resume_plan_langgraph(tmp_run_dir, decision="approve")
    assert len(approval.pending_gates(tmp_run_dir, st["run_id"])) == 1 and st["state"] == "paused_human_gate"
    st = resume_plan_langgraph(tmp_run_dir, decision="approve")
    assert st["state"] == "done" and approval.pending_gates(tmp_run_dir, st["run_id"]) == []
    assert g.ReceiptLog(tmp_run_dir).verify() == []


def test_nativo_tambem_deixa_recibo_do_gate_aprovado(tmp_path, tmp_run_dir, _skills_offline):
    from plan_runner.engine import resume_run, run_plan
    plan = _plano(tmp_path, [{"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
                             {"id": "hitl", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE}])
    assert run_plan(plan, mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"
    recs = {r["step_id"]: r for r in g.ReceiptLog(tmp_run_dir).records()}
    assert set(recs) == {"copy", "hitl"} and recs["hitl"]["approver"] == "human:cli"
    assert g.ReceiptLog(tmp_run_dir).verify() == []
