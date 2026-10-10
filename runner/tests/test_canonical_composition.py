"""O cenário canónico: a prova de que planwright (plano) e plan_runner (execução)
compõem de ponta a ponta, com governação real.

Fecha a última linha da matriz de capacidades (CAPABILITY-MATRIX-PLANWRIGHT.md):
o contrato (PR #164) tornou a composição *viável*; este cenário torna-a *provada*.
Caminho e delta esqueleto→plano: docs/architecture/CANONICAL-SCENARIO.md.

Num único run, o plano executável exercita as três garantias do runner:

1. **porta humana (HITL)** — `decide` (autonomy=human na planwright) pausa o run;
2. **tecto de orçamento** — `budget.max_tokens: 1500` pausa antes de `finalize`;
3. **done_when por evidência** — ficheiros + o evento `human_gate_resolved`.

O Gemini é falso (FakeGemini): cada chamada gasta 955 tokens, nenhum teste sai
para a rede. O runner nunca importa a planwright — o contrato abaixo é o que
`planwright export` emite (guardado pelo lado da planwright em
oss/planwright/tests/test_export.py), copiado aqui como dict.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import model_tiers as mt
from plan_runner.engine import load_plan, resume_run, run_plan
from plan_runner.plan_import import import_contract
from plan_runner.plan_schema import plan_errors
from tests.test_external_worker import FakeGemini

PER_CALL = 955  # tokens por chamada falsa (USAGE de test_external_worker)

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_MD = REPO_ROOT / "oss/planwright/examples/composicao-canonica.PLAN.md"
PLAN_YAML = REPO_ROOT / "docs/architecture/plan-execute/examples/composicao-canonica.plan.yaml"

# O contrato que `planwright export composicao-canonica.PLAN.md` emite
# (planwright-plan/v1). Copiado aqui para o runner nunca importar a planwright;
# o lado da planwright prova que o export corresponde a isto (test_export.py).
CANON_CONTRACT = {
    "schema": "planwright-plan/v1",
    "items": [
        {"id": "research", "title": "Levantar requisitos e contexto", "status": "todo",
         "owner": "agent", "estimate_hours": 2.0, "depends": [], "track": "discovery",
         "autonomy": "auto", "complexity": "C2"},
        {"id": "decide", "title": "Aprovar o rumo antes de investir", "status": "todo",
         "owner": "maestro", "estimate_hours": 1.0, "depends": ["research"], "track": "governance",
         "autonomy": "human", "complexity": "C3"},
        {"id": "draft", "title": "Redigir a proposta", "status": "todo",
         "owner": "agent", "estimate_hours": 3.0, "depends": ["decide"], "track": "build",
         "autonomy": "auto", "complexity": "C2"},
        {"id": "finalize", "title": "Consolidar e publicar o resultado", "status": "todo",
         "owner": "agent", "estimate_hours": 1.0, "depends": ["draft"], "track": "build",
         "autonomy": "auto", "complexity": "C1"},
    ],
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake(monkeypatch):
    f = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", f)
    return f


def _events(out: Path) -> list[dict]:
    return [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]


# --------------------------------------------------------------------------
# A ligação: o plano executável é uma completação fiel do esqueleto do contrato
# --------------------------------------------------------------------------

def test_plano_executavel_e_completacao_do_esqueleto_do_contrato():
    """O esqueleto importado e o plano executável partilham o mesmo backbone:
    ids, dependências e a porta humana em `decide` (do autonomy=human)."""
    skeleton = import_contract(CANON_CONTRACT, plan_id="composicao-canonica")
    assert plan_errors(skeleton) == []  # o esqueleto já é schema-válido

    plan = load_plan(PLAN_YAML)
    assert plan.id == skeleton["id"]

    skel_steps = {s["id"]: s for s in skeleton["steps"]}
    exec_steps = {s.id: s for s in plan.steps}
    assert set(exec_steps) == set(skel_steps)  # mesmos passos

    for sid, skel in skel_steps.items():
        step = exec_steps[sid]
        assert step.depends_on == skel.get("depends_on", [])  # mesmas dependências
        # o human_gate do esqueleto (autonomy=human) está na mesma no plano executável
        assert bool(step.human_gate) == bool(skel.get("human_gate"))

    # só `decide` tem porta humana, como o contrato (autonomy=human) determinou
    assert [s.id for s in plan.steps if s.human_gate] == ["decide"]


def test_planwright_source_e_o_plano_existem_e_casam_nos_ids():
    """Os dois ficheiros do cenário existem e o contrato cobre exactamente os passos do plano."""
    assert PLAN_MD.is_file()
    assert PLAN_YAML.is_file()
    contract_ids = [it["id"] for it in CANON_CONTRACT["items"]]
    plan_ids = [s.id for s in load_plan(PLAN_YAML).steps]
    assert contract_ids == plan_ids


# --------------------------------------------------------------------------
# A prova: um run único exercita HITL + tecto de orçamento + done_when
# --------------------------------------------------------------------------

def test_run_canonico_hitl_depois_orcamento_depois_done(tmp_run_dir, fake):
    # 1) Arranca: research corre (0 < 1500); decide tem porta humana -> PAUSA (HITL).
    status = run_plan(PLAN_YAML, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate"
    assert status["paused_at_step"] == "decide"
    assert status["completed"] == ["research"]
    assert len(fake.calls) == 1  # só research chamou o Gemini; a porta não gasta tokens
    assert (tmp_run_dir / "HITL.md").is_file()

    # 2) Aprova a porta: decide fecha (grava a decisão), draft corre (955 < 1500),
    #    finalize bate no tecto (1910 >= 1500) -> PAUSA (orçamento).
    status = resume_run(tmp_run_dir, decision="approve")
    assert status["state"] == "paused_budget"
    assert status["paused_at_step"] == "finalize"
    assert sorted(status["completed"]) == ["decide", "draft", "research"]
    assert status["budget_spent"] == 2 * PER_CALL
    assert len(fake.calls) == 2  # research + draft; finalize nunca chegou ao Gemini
    assert (tmp_run_dir / "BUDGET.md").is_file()
    assert (tmp_run_dir / "artifacts/02-decision.json").is_file()  # artefacto da porta

    # 3) Sobe o tecto: finalize corre -> done. O done_when é verificado por evidência.
    status = resume_run(tmp_run_dir, decision="approve", max_tokens=5000)
    assert status["state"] == "done", status
    assert sorted(status["completed"]) == ["decide", "draft", "finalize", "research"]
    assert len(fake.calls) == 3

    # Evidência verificável de cada garantia, no events.jsonl e no disco:
    types = [e["type"] for e in _events(tmp_run_dir)]
    assert "human_gate_resolved" in types          # HITL resolvido
    assert "budget_exceeded" in types              # tecto atingido
    assert "budget_resumed" in types               # tecto subido no resume
    assert "plan_done" in types                    # done_when passou

    # done_when por evidência: os dois ficheiros e o gate resolvido
    done_checked = [e for e in _events(tmp_run_dir) if e["type"] == "done_when_checked"]
    assert done_checked, "faltou o evento done_when_checked"
    passed = {(i["kind"], i["target"]) for i in done_checked[-1]["payload"]["passed"]}
    assert ("file_exists", "artifacts/02-decision.json") in passed
    assert ("file_exists", "artifacts/04-final.md") in passed
    assert ("gate_resolved", "decide") in passed
    assert done_checked[-1]["payload"]["failed"] == []


def test_sinais_da_planwright_chegam_a_seleccao_do_runner(tmp_path, tmp_run_dir, fake, monkeypatch):
    """A ponte final: complexity do contrato -> router.signals (import --signals) -> o
    worker escolhe o modelo por complexidade quando o passo nao declara model_tier."""
    # import com sinais: o contrato da planwright leva complexity/autonomy para router.signals
    plan_dict = import_contract(CANON_CONTRACT, plan_id="composicao-canonica", with_signals=True)
    sig = plan_dict["router"]["signals"]
    assert sig["research"]["complexity"] == "C2"
    assert sig["finalize"]["complexity"] == "C1"
    assert sig["decide"]["autonomy"] == "human"  # o mesmo sinal que vira a porta humana

    # com uma config de complexidade, o run escolhe modelos cheap->expensive a partir do sinal.
    # (plano minimo, sem porta nem tecto: aqui o foco e so a seleccao de modelo pelo sinal)
    mtcfg = tmp_path / "mt.yaml"
    mtcfg.write_text('{"complexity": {"C1": "modelo-barato", "C2": "modelo-medio"}}', encoding="utf-8")
    monkeypatch.setattr(mt, "TIERS_PATH", mtcfg)
    plan_yaml = tmp_path / "plan.yaml"
    plan_yaml.write_text(
        '{"id": "sel", "objective": "x",'
        ' "router": {"signals": {"a": {"complexity": "C2"}, "b": {"complexity": "C1"}}},'
        ' "steps": [{"id": "a", "action": "research", "output_artifact": "artifacts/a.md"},'
        '           {"id": "b", "action": "research", "depends_on": ["a"], "output_artifact": "artifacts/b.md"}]}',
        encoding="utf-8",
    )
    status = run_plan(plan_yaml, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    models = [c["url"].split("/models/")[1].split(":")[0] for c in fake.calls]
    assert models == ["modelo-medio", "modelo-barato"]  # C2 -> medio, C1 -> barato


def test_done_when_falha_sem_a_evidencia(tmp_run_dir, fake):
    """Tirar um artefacto exigido pelo done_when faz o run terminar em `failed`,
    não em `done`: a conclusão é por evidência, não por 'os passos correram'."""
    run_plan(PLAN_YAML, mode="external", out_dir=tmp_run_dir, worker="gemini")
    resume_run(tmp_run_dir, decision="approve")  # -> paused_budget em finalize
    # apaga o artefacto da porta antes de deixar o run acabar
    (tmp_run_dir / "artifacts/02-decision.json").unlink()
    status = resume_run(tmp_run_dir, decision="approve", max_tokens=5000)

    assert status["state"] == "failed"
    assert status["detail"] == "done_when"
    failed = {(i["kind"], i["target"]) for i in status["done_when_failed"]}
    assert ("file_exists", "artifacts/02-decision.json") in failed
