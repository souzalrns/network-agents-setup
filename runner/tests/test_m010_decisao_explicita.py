"""M-010 e M-011: a decisão de um gate humano é sempre explícita, dirigida ao pedido certo e pedida no momento certo.

Antes, no motor LangGraph, um `resume` dado para outra coisa (um passo externo à espera, um orçamento,
a aprovação de uma tool) respondia também a um gate humano pendente em paralelo, com `approve`. Havia
mais três caminhos de aprovação por omissão: `--decision` omitido na CLI, a "última decisão" do
ficheiro do contrato HITL reaproveitada para outro gate, e `decision="approve"` por omissão na tool MCP.

Cada teste prova que a situação NÃO aprova nada (não aparece `human_gate_resolved` com approve/edit
para o gate), nos dois motores quando se aplica.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from plan_runner import approval, hitl
from plan_runner.approval import ApprovalError
from plan_runner.cli import main
from plan_runner.engine import PlanError, load_status, resume_run, run_plan
from tests.politica import politica_dict

pytest.importorskip("langgraph.graph")
from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph  # noqa: E402

GATE = {"level": "step", "kind": "output_review", "allow": ["approve", "reject", "edit"]}
GATE_SEM_EDIT = {"level": "step", "kind": "output_review", "allow": ["approve", "reject"]}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


def _events(run: Path, type_: str | None = None) -> list[dict]:
    rows = [json.loads(x) for x in (run / "events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if type_ is None or r["type"] == type_]


def _aprovados(run: Path) -> list[str]:
    """Gates com uma decisão approve/edit gravada."""
    return [e["payload"]["step_id"] for e in _events(run, "human_gate_resolved")
            if e["payload"].get("decision") in ("approve", "edit") and e["payload"].get("kind") != "tool_approval"]


def _decididos(run: Path) -> list[str]:
    return [e["payload"]["step_id"] for e in _events(run, "human_gate_resolved")]


def _plano(tmp_path: Path, steps: list[dict], **top) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump(politica_dict({"id": "m010", "objective": "x", **top, "steps": steps})), encoding="utf-8")
    return p


def _um_gate(tmp_path: Path, gate: dict = GATE) -> Path:
    return _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": gate},
        {"id": "fim", "action": "storytelling", "depends_on": ["g1"], "output_artifact": "artifacts/03-fim.md"},
    ])


def _gate_e_externo(tmp_path: Path) -> Path:
    """O cenário do M-010: um gate e um passo externo em paralelo, depois de `copy`."""
    return _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "img", "action": "image", "depends_on": ["copy"], "output_artifact": "artifacts/02-img.md"},
    ])


def _dois_gates(tmp_path: Path) -> Path:
    return _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "g2", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "fim", "action": "storytelling", "depends_on": ["g1", "g2"], "output_artifact": "artifacts/03-fim.md"},
    ])


def _resultado(run: Path, step: str, texto: str) -> None:
    (run / "pending_steps" / step / "result.json").write_text(
        json.dumps({"ok": True, "artifact_content": texto}), encoding="utf-8")


def _ate_gate_e_externo(tmp_path: Path, run: Path) -> dict:
    """Run LangGraph parado com `img` à espera de um worker e `g1` pedido em paralelo."""
    assert run_plan_langgraph(_gate_e_externo(tmp_path), mode="external", out_dir=run)["state"] == "waiting_external"
    _resultado(run, "copy", "texto\n")
    st = resume_plan_langgraph(run)  # continua o passo externo; sem decisão
    assert st["state"] == "waiting_external" and st["paused_at_step"] == "img"
    assert approval.pending_gates(run, st["run_id"]) == ["g1"]
    return st


# ============================================================== o cenário do M-010 (LangGraph)

@pytest.mark.parametrize("decisao", [None, "approve", "edit"])
def test_resume_de_um_passo_externo_nao_decide_o_gate_em_paralelo(tmp_path, tmp_run_dir, decisao):
    """Retomar o passo externo, com ou sem `decision`, deixa o gate à espera (era aqui o approve implícito)."""
    _ate_gate_e_externo(tmp_path, tmp_run_dir)
    _resultado(tmp_run_dir, "img", "imagem\n")
    st = resume_plan_langgraph(tmp_run_dir, decision=decisao)
    assert st["state"] == "paused_human_gate" and st["paused_at_step"] == "g1" and st["pending_gates"] == ["g1"]
    assert "img" in st["completed"] and "g1" not in st["completed"]
    assert _decididos(tmp_run_dir) == []
    deixado = _events(tmp_run_dir, "human_gate_left_pending")[-1]["payload"]
    assert deixado == {"gates": ["g1"], "resume_for": "waiting_external"}


def test_gate_decide_se_a_parte_com_o_passo_externo_ainda_a_espera(tmp_path, tmp_run_dir):
    """Com `gate` a decisão vai só para esse gate; o passo externo continua à espera do worker."""
    _ate_gate_e_externo(tmp_path, tmp_run_dir)
    st = resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g1")
    assert st["state"] == "waiting_external" and st["paused_at_step"] == "img"
    assert _aprovados(tmp_run_dir) == ["g1"] and "g1" in st["completed"]
    _resultado(tmp_run_dir, "img", "imagem\n")
    assert resume_plan_langgraph(tmp_run_dir)["state"] == "done"
    assert _aprovados(tmp_run_dir) == ["g1"]  # decidido uma vez só; o nó do gate não volta a correr


def test_resume_de_orcamento_nao_decide_o_gate(tmp_path, tmp_run_dir):
    """Um run em paused_budget com um gate pedido: subir o tecto não é aprovar o gate."""
    st = _ate_gate_e_externo(tmp_path, tmp_run_dir)
    st = load_status(tmp_run_dir)
    st.update({"state": "paused_budget", "budget_spent": 10, "budget_unit": "tokens", "max_tokens": 5})
    (tmp_run_dir / "status.json").write_text(json.dumps(st), encoding="utf-8")
    _resultado(tmp_run_dir, "img", "imagem\n")
    out = resume_plan_langgraph(tmp_run_dir, decision="approve", max_tokens=5000)
    assert out["state"] == "paused_human_gate" and _decididos(tmp_run_dir) == []
    assert _events(tmp_run_dir, "budget_resumed")


# ============================================================== os cenários pedidos, nos dois motores

def _parar_no_gate(motor: str, tmp_path: Path, run: Path, gate: dict = GATE) -> None:
    plan = _um_gate(tmp_path, gate)
    st = run_plan_langgraph(plan, mode="stub", out_dir=run) if motor == "langgraph" else run_plan(plan, mode="stub", out_dir=run)
    assert st["state"] == "paused_human_gate" and st["paused_at_step"] == "g1"


def _resume(motor: str, run: Path, **kw):
    return resume_plan_langgraph(run, **kw) if motor == "langgraph" else resume_run(run, **kw)


MOTORES = pytest.mark.parametrize("motor", ["native", "langgraph"])


@MOTORES
def test_aprovacao_explicita_aprova_so_esse_gate(tmp_path, tmp_run_dir, motor):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    st = _resume(motor, tmp_run_dir, decision="approve", gate="g1")
    assert st["state"] == "done" and _aprovados(tmp_run_dir) == ["g1"]
    evt = _events(tmp_run_dir, "human_gate_resolved")[-1]
    assert evt["actor"] == {"kind": "human", "id": "cli"} and "fingerprint" in evt["payload"]


@MOTORES
def test_rejeicao_explicita_para_o_run(tmp_path, tmp_run_dir, motor):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    st = _resume(motor, tmp_run_dir, decision="reject", gate="g1")
    assert st["state"] == "rejected" and _aprovados(tmp_run_dir) == []
    assert [e["payload"]["decision"] for e in _events(tmp_run_dir, "human_gate_resolved")] == ["reject"]
    assert not (tmp_run_dir / "artifacts/03-fim.md").exists()
    with pytest.raises(PlanError, match="cannot resume from state 'rejected'"):
        _resume(motor, tmp_run_dir, decision="approve", gate="g1")  # um reject não se desfaz
    assert _aprovados(tmp_run_dir) == []


@MOTORES
def test_resume_sem_decisao_nao_aprova(tmp_path, tmp_run_dir, motor):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    with pytest.raises(ApprovalError, match="nunca é aprovado por omissão"):
        _resume(motor, tmp_run_dir)
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"
    assert not (tmp_run_dir / "artifacts/03-fim.md").exists()


@MOTORES
@pytest.mark.parametrize("invalida", ["", "yes", "APPROVE", "aprovar", "approve ", "true", "ok"])
def test_resposta_invalida_nao_aprova(tmp_path, tmp_run_dir, motor, invalida):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    with pytest.raises(PlanError):
        _resume(motor, tmp_run_dir, decision=invalida)
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"


@MOTORES
@pytest.mark.parametrize("errado", ["g2", "copy", "fim", "hitl_00000000", ""])
def test_identificador_de_aprovacao_incorrecto_nao_decide_nada(tmp_path, tmp_run_dir, motor, errado):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    with pytest.raises(ApprovalError, match="não há pedido de aprovação à espera"):
        _resume(motor, tmp_run_dir, decision="approve", gate=errado)
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"


@MOTORES
def test_aprovacao_sem_autorizacao_do_gate_e_recusada(tmp_path, tmp_run_dir, motor):
    """O `allow` do gate não prevê `edit`: a decisão é recusada (e um reject continua a ser aceite)."""
    _parar_no_gate(motor, tmp_path, tmp_run_dir, GATE_SEM_EDIT)
    with pytest.raises(ApprovalError, match="não é permitida no gate `g1`"):
        _resume(motor, tmp_run_dir, decision="edit", gate="g1")
    assert _decididos(tmp_run_dir) == []
    assert _resume(motor, tmp_run_dir, decision="reject", gate="g1")["state"] == "rejected"


@MOTORES
def test_resume_repetido_nao_aprova_duas_vezes(tmp_path, tmp_run_dir, motor):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    assert _resume(motor, tmp_run_dir, decision="approve", gate="g1")["state"] == "done"
    with pytest.raises(PlanError, match="cannot resume from state 'done'"):
        _resume(motor, tmp_run_dir, decision="approve", gate="g1")
    assert _aprovados(tmp_run_dir) == ["g1"]


@MOTORES
def test_timeout_o_gate_fica_a_espera_o_tempo_que_for(tmp_path, tmp_run_dir, motor, monkeypatch):
    """Não há prazo que aprove: retomas sem decisão, mesmo muito depois do pedido, deixam o gate como estava."""
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    pedido = hitl.latest_request(tmp_run_dir)
    assert pedido["expires_at"] is None and pedido["status"] == "pending"
    import plan_runner.events as ev
    monkeypatch.setattr(ev, "_now", lambda: "2099-01-01T00:00:00+00:00")  # "anos depois"
    for _ in range(3):
        with pytest.raises(ApprovalError, match="nunca é aprovado por omissão"):
            _resume(motor, tmp_run_dir)
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"


@MOTORES
def test_recuperacao_apos_interrupcao_nao_aprova(tmp_path, tmp_run_dir, motor):
    """O processo morreu com o estado `running` e um gate pedido: retomar (até com `approve`) não o aprova."""
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    st = load_status(tmp_run_dir)
    st["state"] = "running"
    (tmp_run_dir / "status.json").write_text(json.dumps(st), encoding="utf-8")
    out = _resume(motor, tmp_run_dir, decision="approve")
    assert out["state"] == "paused_human_gate" and out["paused_at_step"] == "g1"
    assert _decididos(tmp_run_dir) == [] and _events(tmp_run_dir, "resume_after_interrupt")
    assert _resume(motor, tmp_run_dir, decision="approve", gate="g1")["state"] == "done"  # e depois decide-se, à parte


# ============================================================== vários gates à espera (LangGraph)

def test_dois_gates_a_espera_exigem_o_nome_do_gate(tmp_path, tmp_run_dir):
    st = run_plan_langgraph(_dois_gates(tmp_path), mode="stub", out_dir=tmp_run_dir)
    # os dois nós correm em paralelo: a ordem dos pedidos não é fixa
    assert st["state"] == "paused_human_gate" and sorted(st["pending_gates"]) == ["g1", "g2"]
    with pytest.raises(ApprovalError, match=r"há 2 pedidos de aprovação à espera \(g[12], g[12]\)"):
        resume_plan_langgraph(tmp_run_dir, decision="approve")
    assert _decididos(tmp_run_dir) == []


def test_aprovar_um_gate_nao_aprova_o_outro(tmp_path, tmp_run_dir):
    run_plan_langgraph(_dois_gates(tmp_path), mode="stub", out_dir=tmp_run_dir)
    st = resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g2")
    assert st["state"] == "paused_human_gate" and st["pending_gates"] == ["g1"] and _aprovados(tmp_run_dir) == ["g2"]
    assert st["paused_at_step"] == "g1"
    assert not (tmp_run_dir / "artifacts/03-fim.md").exists()
    # repetir a mesma aprovação não passa para o gate que sobra
    with pytest.raises(ApprovalError, match="não há pedido de aprovação à espera para `g2`"):
        resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g2")
    assert _aprovados(tmp_run_dir) == ["g2"]
    assert resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g1")["state"] == "done"
    assert sorted(_aprovados(tmp_run_dir)) == ["g1", "g2"]


def test_rejeitar_um_gate_com_outro_a_espera_para_o_run_sem_aprovar_nenhum(tmp_path, tmp_run_dir):
    run_plan_langgraph(_dois_gates(tmp_path), mode="stub", out_dir=tmp_run_dir)
    assert resume_plan_langgraph(tmp_run_dir, decision="reject", gate="g1")["state"] == "rejected"
    assert _aprovados(tmp_run_dir) == [] and _decididos(tmp_run_dir) == ["g1"]


@pytest.mark.parametrize("solto", [
    "approve", {"decision": "approve"}, {"decision": "approve", "gate": "outro"}, {"gate": "g1"},
    {"decision": "yes", "gate": "g1"}, True,
])
def test_valor_sem_destinatario_entregue_ao_no_nao_aprova(tmp_path, tmp_run_dir, monkeypatch, solto):
    """Defesa em profundidade: mesmo que um valor solto chegasse à interrupção, o nó não o aceita."""
    import langgraph.types as lt

    run_plan_langgraph(_um_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    original = lt.Command

    def falso(resume=None, **kw):  # troca o valor dirigido por um valor solto
        return original(resume={next(iter(resume)): solto}, **kw)

    monkeypatch.setattr(lt, "Command", falso)
    with pytest.raises(PlanError):
        resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g1")
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"
    assert not (tmp_run_dir / "artifacts/03-fim.md").exists()
    monkeypatch.setattr(lt, "Command", original)
    assert resume_plan_langgraph(tmp_run_dir, decision="reject", gate="g1")["state"] == "rejected"  # parar é sempre possível


# ============================================================== CLI e contrato HITL

@MOTORES
def test_cli_sem_decision_num_gate_falha_e_nao_aprova(tmp_path, tmp_run_dir, motor, capsys):
    _parar_no_gate(motor, tmp_path, tmp_run_dir)
    assert main(["resume", str(tmp_run_dir)]) == 1
    assert "nunca e aprovado por omissao" in capsys.readouterr().out
    assert _decididos(tmp_run_dir) == [] and load_status(tmp_run_dir)["state"] == "paused_human_gate"
    assert main(["resume", str(tmp_run_dir), "--gate", "g1", "--decision", "approve"]) == 0
    assert _aprovados(tmp_run_dir) == ["g1"]


@MOTORES
def test_cli_decisao_antiga_do_ficheiro_nao_vale_para_outro_gate(tmp_path, tmp_run_dir, motor, capsys):
    """Dois gates em série: a aprovação escrita para o 1.º não pode decidir o 2.º (era `read_decision`: a última ganha)."""
    plan = _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "meio", "action": "storytelling", "depends_on": ["g1"], "output_artifact": "artifacts/02-meio.md"},
        {"id": "g2", "action": "plan_approve", "depends_on": ["meio"], "human_gate": GATE},
    ])
    st = run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir) if motor == "langgraph" else run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    pedido1 = next(r for r in hitl._read_jsonl(tmp_run_dir / hitl.REQUESTS_FILE) if r["step_id"] == "g1")
    hitl.write_decision(tmp_run_dir, pedido1["id"], response="approve", responder_id="cli:maria")
    assert main(["resume", str(tmp_run_dir)]) == 0  # a decisão escrita para o g1 decide o g1
    assert _aprovados(tmp_run_dir) == ["g1"] and load_status(tmp_run_dir)["paused_at_step"] == "g2"
    capsys.readouterr()
    assert main(["resume", str(tmp_run_dir)]) == 1  # ...e não o g2
    assert "aprovacao humana pendente em `g2`" in capsys.readouterr().out
    assert _aprovados(tmp_run_dir) == ["g1"]
    # um reject explícito do g2 não é trocado pela aprovação antiga do ficheiro
    assert main(["resume", str(tmp_run_dir), "--gate", "g2", "--decision", "reject"]) == 0
    assert load_status(tmp_run_dir)["state"] == "rejected" and _aprovados(tmp_run_dir) == ["g1"]
    assert st["run_id"] == load_status(tmp_run_dir)["run_id"]


def test_decisao_escrita_antes_de_um_pedido_renovado_nao_conta(tmp_path, tmp_run_dir, capsys):
    """M-009 renova o pedido quando o conteúdo muda: a decisão antiga do ficheiro não serve para o pedido novo."""
    run_plan(_um_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    pedido = hitl.latest_request(tmp_run_dir)
    hitl.write_decision(tmp_run_dir, pedido["id"], response="approve", responder_id="cli:maria")
    (tmp_run_dir / "artifacts/01-copy.md").write_text("mudado depois de a pessoa ver\n", encoding="utf-8")
    assert main(["resume", str(tmp_run_dir)]) == 1 and "mudou desde o pedido" in capsys.readouterr().out
    assert main(["resume", str(tmp_run_dir)]) == 1  # a decisão antiga já não vale: é preciso decidir outra vez
    assert "aprovacao humana pendente em `g1`" in capsys.readouterr().out
    assert _decididos(tmp_run_dir) == []
    hitl.write_decision(tmp_run_dir, pedido["id"], response="approve", responder_id="cli:maria")
    assert main(["resume", str(tmp_run_dir)]) == 0 and _aprovados(tmp_run_dir) == ["g1"]


def test_cli_decisoes_em_conflito_nao_decidem(tmp_path, tmp_run_dir, capsys):
    run_plan(_um_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    hitl.write_decision(tmp_run_dir, hitl.latest_request(tmp_run_dir)["id"], response="reject", responder_id="cli:maria")
    assert main(["resume", str(tmp_run_dir), "--decision", "approve"]) == 1
    assert "decisoes em conflito" in capsys.readouterr().out and _decididos(tmp_run_dir) == []


def test_cli_continuar_um_passo_externo_dispensa_decision(tmp_path, tmp_run_dir):
    """Compatibilidade: fora de um gate, `resume` sem --decision continua o run (motor nativo)."""
    plan = _plano(tmp_path, [{"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"}])
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir)["state"] == "waiting_external"
    _resultado(tmp_run_dir, "copy", "texto\n")
    assert main(["resume", str(tmp_run_dir)]) == 0 and load_status(tmp_run_dir)["state"] == "done"


# ============================================================== tool MCP

def test_mcp_resume_plan_nao_aprova_por_omissao(tmp_path, tmp_run_dir, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp" / "plan_runner"))
    try:
        from mcp_plan_runner import tools_impl
    finally:
        sys.path.pop(0)
    import inspect

    assert inspect.signature(tools_impl.resume_plan).parameters["decision"].default is None
    run_plan(_um_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)

    class _Auth:
        authorized = True
        caller = "teste"
        reason = "ok"

    monkeypatch.setattr(tools_impl, "authorize", lambda tool: _Auth())
    monkeypatch.setattr(tools_impl, "rate_limit", lambda caller: None)
    monkeypatch.setattr(tools_impl, "audit", lambda rec: None)
    monkeypatch.setattr(tools_impl, "sanitize_repo_path", lambda p, must_exist=False: Path(p))
    res = tools_impl.resume_plan(str(tmp_run_dir))
    assert res["ok"] is False and "nunca é aprovado por omissão" in res["error"]
    assert _decididos(tmp_run_dir) == []
    assert tools_impl.resume_plan(str(tmp_run_dir), decision="approve", gate="g1")["ok"] is True
    assert _aprovados(tmp_run_dir) == ["g1"]


# ============================================================== M-011: o gate espera por todas as dependências

def _eventos_por_passo(run: Path) -> dict[tuple[str, str], int]:
    return {(e["type"], e["payload"].get("step_id")): i for i, e in enumerate(_events(run))}


def _atrasar(monkeypatch, lentos: set[str], segundos: float = 0.3) -> None:
    """Torna a corrida determinística: os passos `lentos` demoram, como um passo real demoraria."""
    import time

    from plan_runner import langgraph_engine as lg

    real = lg.execute_stub

    def lento(out, step):
        if step.id in lentos:
            time.sleep(segundos)
        return real(out, step)

    monkeypatch.setattr(lg, "execute_stub", lento)


def test_gate_so_e_pedido_depois_de_todas_as_dependencias(tmp_path, tmp_run_dir, monkeypatch):
    """M-011: com uma aresta por dependência o gate era pedido quando a primeira acabava, antes da
    revisão e da compliance, e a impressão digital do pedido não as incluía."""
    _atrasar(monkeypatch, {"revisao", "compliance"})
    plan = _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "revisao", "action": "storytelling", "depends_on": ["copy"], "output_artifact": "artifacts/02-revisao.md"},
        {"id": "compliance", "action": "image", "depends_on": ["copy"], "output_artifact": "artifacts/03-compliance.md"},
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy", "revisao", "compliance"], "human_gate": GATE},
        {"id": "fim", "action": "storytelling", "depends_on": ["g1"], "output_artifact": "artifacts/04-fim.md"},
    ])
    st = run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)
    assert st["state"] == "paused_human_gate" and st["pending_gates"] == ["g1"]
    idx = _eventos_por_passo(tmp_run_dir)
    pedido = idx[("human_gate_requested", "g1")]
    assert pedido > idx[("step_finished", "revisao")] and pedido > idx[("step_finished", "compliance")]
    fp = _events(tmp_run_dir, "human_gate_requested")[-1]["payload"]["fingerprint"]["artifacts"]
    assert {"artifacts/01-copy.md", "artifacts/02-revisao.md", "artifacts/03-compliance.md"} <= set(fp)
    assert len(_events(tmp_run_dir, "human_gate_requested")) == 1
    assert resume_plan_langgraph(tmp_run_dir, decision="approve", gate="g1")["state"] == "done"


def test_passo_com_varias_dependencias_corre_uma_vez_e_no_fim(tmp_path, tmp_run_dir, monkeypatch):
    _atrasar(monkeypatch, {"b", "c"})
    plan = _plano(tmp_path, [
        {"id": "a", "action": "copy_social", "output_artifact": "artifacts/01-a.md"},
        {"id": "b", "action": "storytelling", "depends_on": ["a"], "output_artifact": "artifacts/02-b.md"},
        {"id": "c", "action": "image", "depends_on": ["a"], "output_artifact": "artifacts/03-c.md"},
        {"id": "d", "action": "storytelling", "depends_on": ["a", "b", "c"], "output_artifact": "artifacts/04-d.md"},
    ])
    assert run_plan_langgraph(plan, mode="stub", out_dir=tmp_run_dir)["state"] == "done"
    inicios = [e["payload"]["step_id"] for e in _events(tmp_run_dir, "step_started")]
    assert inicios.count("d") == 1
    idx = _eventos_por_passo(tmp_run_dir)
    assert idx[("step_started", "d")] > idx[("step_finished", "b")] and idx[("step_started", "d")] > idx[("step_finished", "c")]
