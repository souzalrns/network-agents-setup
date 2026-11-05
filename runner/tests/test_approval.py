"""M-009 (fase 2): o conhecimento tem de chegar ao passo, e a aprovação humana fica presa ao conteúdo."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import knowledge_wiring
from plan_runner.approval import ApprovalError
from plan_runner.engine import resume_run, run_plan
from plan_runner.mcp_knowledge import McpKnowledgeError
from tests.politica import politica_dict
from tests.test_external_worker import FakeGemini

REPO = Path(__file__).resolve().parents[2]
ROUNDS = REPO / "docs/orchestration/marketing/templates/approval-rounds.plan.yaml"
GATE = {"level": "step", "kind": "output_review", "allow": ["approve", "reject", "edit"]}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


def _events(run: Path, type_: str) -> list[dict]:
    rows = [json.loads(x) for x in (run / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    return [r for r in rows if r["type"] == type_]


def _plano(tmp_path: Path, steps: list[dict], **top) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump(politica_dict({"id": "m009", "objective": "x", **top, "steps": steps})), encoding="utf-8")
    return p


def _com_gate(tmp_path: Path) -> Path:
    return _plano(tmp_path, [
        {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01-copy.md"},
        {"id": "hitl", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
    ])


# ------------------------------------------------------------------ (a) o conhecimento tem de chegar

class _Falha:
    def retrieve(self, *a, **kw):
        raise McpKnowledgeError("quota excedida")


class _Vazio:
    def retrieve(self, *a, **kw):
        return []


@pytest.mark.parametrize("backend, motivo", [(_Falha, "quota excedida"), (_Vazio, "L5 CONTEXT: EMPTY|Contexto vazio")])
def test_passo_de_marketing_sem_contexto_nao_chama_o_modelo(tmp_path, tmp_run_dir, monkeypatch, backend, motivo):
    monkeypatch.setattr(knowledge_wiring, "McpKnowledge", backend)
    fake = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    plan = _plano(tmp_path, [{"id": "r", "action": "research", "output_artifact": "artifacts/r.md"}])
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "failed"
    failed = _events(tmp_run_dir, "step_failed")[0]["payload"]
    assert failed["step_id"] == "r" and failed["detail"].startswith("knowledge_missing: o passo `r` exige")
    assert fake.calls == []  # nem um token gasto
    assert not (tmp_run_dir / "pending_steps/r/request.json").exists()  # nem pedido para um worker de fora


def test_com_contexto_o_passo_corre_e_cita_a_fonte(tmp_path, tmp_run_dir, monkeypatch, fake_knowledge):
    fake = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    plan = _plano(tmp_path, [{"id": "r", "action": "research", "output_artifact": "artifacts/r.md"}])
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")["state"] == "done"
    assert fake_knowledge.calls == [("marketing", "research: plano de teste")]
    assert "docs/knowledge/teste.md" in json.dumps(fake.calls[0]["body"], ensure_ascii=False)


def test_vertical_sem_a_regra_segue_sem_contexto(tmp_path, tmp_run_dir, monkeypatch):
    """O design não tem R6: a falha do L5 fica registada e o passo corre, como antes."""
    monkeypatch.setattr(knowledge_wiring, "McpKnowledge", _Falha)
    monkeypatch.setattr(ew, "httpx_transport", FakeGemini())
    plan = _plano(tmp_path, [{"id": "ui", "action": "ui_spec", "vertical": "design", "output_artifact": "artifacts/ui.md",
                              "knowledge": {"kb": "design", "query": "componentes de interface"}}])
    assert run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")["state"] == "done"
    assert _events(tmp_run_dir, "knowledge_context_failed")


# ------------------------------------------------------------------ (b) a aprovação fica presa ao conteúdo

def test_pedido_e_decisao_levam_a_impressao_digital(tmp_path, tmp_run_dir):
    run_plan(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    req = _events(tmp_run_dir, "human_gate_requested")[0]["payload"]["fingerprint"]
    assert set(req["artifacts"]) == {"artifacts/01-copy.md"} and len(req["plan_sha256"]) == 64
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"
    assert _events(tmp_run_dir, "human_gate_resolved")[0]["payload"]["fingerprint"] == req


def test_aprovar_conteudo_que_mudou_depois_do_pedido_e_recusado(tmp_path, tmp_run_dir):
    run_plan(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    (tmp_run_dir / "artifacts/01-copy.md").write_text("outro texto\n", encoding="utf-8")
    with pytest.raises(ApprovalError, match=r"mudou desde o pedido \(artifacts/01-copy.md\)"):
        resume_run(tmp_run_dir, decision="approve")
    assert _events(tmp_run_dir, "human_gate_resolved") == []  # a decisão não ficou registada
    renewed = _events(tmp_run_dir, "human_gate_requested")[-1]["payload"]
    assert renewed["renewed"] is True and renewed["changed"] == ["artifacts/01-copy.md"]
    assert "foi renovado" in (tmp_run_dir / "HITL.md").read_text(encoding="utf-8")
    # revisto o conteúdo novo, a 2.ª aprovação vale e fica presa a ele
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"
    assert _events(tmp_run_dir, "human_gate_resolved")[0]["payload"]["fingerprint"] == renewed["fingerprint"]


def test_edit_aceita_a_mudanca_porque_e_a_pessoa_a_mudar(tmp_path, tmp_run_dir):
    run_plan(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    (tmp_run_dir / "artifacts/01-copy.md").write_text("texto corrigido pela pessoa\n", encoding="utf-8")
    assert resume_run(tmp_run_dir, decision="edit")["state"] == "done"
    fp = _events(tmp_run_dir, "human_gate_resolved")[0]["payload"]["fingerprint"]
    import hashlib
    assert fp["artifacts"]["artifacts/01-copy.md"] == hashlib.sha256(b"texto corrigido pela pessoa\n").hexdigest()


def test_reject_nao_precisa_de_prova(tmp_path, tmp_run_dir):
    run_plan(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    (tmp_run_dir / "artifacts/01-copy.md").write_text("mudou\n", encoding="utf-8")
    assert resume_run(tmp_run_dir, decision="reject")["state"] == "rejected"


def test_mudar_o_plano_depois_de_aprovado_invalida_a_aprovacao(tmp_run_dir):
    assert run_plan(ROUNDS, mode="stub", out_dir=tmp_run_dir)["paused_at_step"] == "hitl_r1"
    assert resume_run(tmp_run_dir, decision="approve")["paused_at_step"] == "hitl_r2"
    plan = tmp_run_dir / "plan.yaml"
    plan.write_text(plan.read_text(encoding="utf-8").replace("max_steps: 12", "max_steps: 11"), encoding="utf-8")
    with pytest.raises(ApprovalError, match=r"aprovação de `hitl_r1` deixou de valer: .*\(plan.yaml\)"):
        resume_run(tmp_run_dir, decision="approve")
    assert _events(tmp_run_dir, "approval_invalidated")[0]["payload"] == {"step_id": "hitl_r1", "changed": ["plan.yaml"]}


def test_mudar_um_artefacto_ja_aprovado_invalida_a_aprovacao(tmp_run_dir):
    run_plan(ROUNDS, mode="stub", out_dir=tmp_run_dir)
    resume_run(tmp_run_dir, decision="approve")  # hitl_r1 aprovou o 01-review-r1.json
    (tmp_run_dir / "artifacts/01-review-r1.json").write_text('{"mudado": true}\n', encoding="utf-8")
    with pytest.raises(ApprovalError, match=r"`hitl_r1` deixou de valer: .*artifacts/01-review-r1.json"):
        resume_run(tmp_run_dir, decision="approve")


def test_pedido_sem_impressao_digital_conta_como_mudado(tmp_path, tmp_run_dir):
    """Fail-closed: um run de antes do M-009 não aprova às cegas; o pedido é renovado."""
    run_plan(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)
    ev = tmp_run_dir / "events.jsonl"
    rows = [json.loads(x) for x in ev.read_text(encoding="utf-8").splitlines()]
    for r in rows:
        r["payload"].pop("fingerprint", None)
    ev.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    with pytest.raises(ApprovalError, match="pedido sem impressão digital"):
        resume_run(tmp_run_dir, decision="approve")
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"


def test_langgraph_tambem_recusa_aprovar_conteudo_mudado(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph.graph")
    from plan_runner.langgraph_engine import resume_plan_langgraph, run_plan_langgraph

    assert run_plan_langgraph(_com_gate(tmp_path), mode="stub", out_dir=tmp_run_dir)["state"] == "paused_human_gate"
    (tmp_run_dir / "artifacts/01-copy.md").write_text("outro texto\n", encoding="utf-8")
    with pytest.raises(ApprovalError, match="mudou desde o pedido"):
        resume_plan_langgraph(tmp_run_dir, decision="approve")
    assert resume_plan_langgraph(tmp_run_dir, decision="approve")["state"] == "done"
    fp = _events(tmp_run_dir, "human_gate_resolved")[-1]["payload"]["fingerprint"]
    assert "artifacts/01-copy.md" in fp["artifacts"]
