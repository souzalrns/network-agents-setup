"""M-008 (fase 1): o motor recusa, antes de arrancar, um plano que falhe as regras de
config/plan-policy.yaml. Testes negativos e positivos, com planos feitos aqui (fora dos templates).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from plan_runner import policy
from plan_runner.engine import load_plan, resume_run, run_plan
from plan_runner.models import Plan
from plan_runner.policy import PolicyError, check_plan

REPO = Path(__file__).resolve().parents[2]
GATE = {"level": "step", "kind": "output_review", "allow": ["approve", "reject", "edit"]}


def k(q: str = "regras de marca e conformidade") -> dict:
    return {"kb": "marketing", "query": q}


def externo() -> dict:
    """Plano de marketing externo que cumpre todas as regras."""
    return {
        "id": "pol-externo", "version": 1, "objective": "x", "delivery": "external",
        "deliverable_type": "social_pack", "budget": {"max_steps": 5},
        "steps": [
            {"id": "copy", "action": "copy_social", "output_artifact": "artifacts/01.md", "knowledge": k()},
            {"id": "critic", "action": "critic", "depends_on": ["copy"], "output_artifact": "artifacts/02.json",
             "knowledge": k()},
            {"id": "compliance", "action": "compliance_check", "depends_on": ["copy"],
             "output_artifact": "artifacts/03.json", "knowledge": k()},
            {"id": "hitl", "action": "plan_approve", "depends_on": ["critic", "compliance"], "human_gate": GATE},
        ],
        "done_when": ["human_gate_resolved on hitl"],
    }


def violacoes(data: dict) -> list[str]:
    try:
        check_plan(Plan.from_dict(data))
    except PolicyError as e:
        return e.violations
    return []


def sem(data: dict, step_id: str) -> dict:
    """O plano sem um passo (e sem as dependências para ele)."""
    out = copy.deepcopy(data)
    out["steps"] = [s for s in out["steps"] if s["id"] != step_id]
    for s in out["steps"]:
        s["depends_on"] = [d for d in s.get("depends_on", []) if d != step_id]
    return out


# ------------------------------------------------------------------ positivos

def test_plano_externo_completo_e_aceite():
    assert violacoes(externo()) == []


def test_plano_interno_sem_gate_de_entrega_e_aceite():
    data = {"id": "pol-interno", "objective": "x", "delivery": "internal", "budget": {"max_steps": 1},
            "steps": [{"id": "r", "action": "research", "output_artifact": "artifacts/r.md", "knowledge": k()}]}
    assert violacoes(data) == []


def test_outra_vertical_e_avaliada_so_pelas_regras_dela():
    """O design não tem perfil: sem delivery, sem knowledge e sem budget explícito, passa nas regras gerais."""
    data = {"id": "pol-design", "objective": "x",
            "steps": [{"id": "ui", "action": "ui_spec", "vertical": "design", "output_artifact": "artifacts/ui.md"}]}
    assert violacoes(data) == []
    data["steps"][0]["tools_allowed"] = ["web_search"]  # mas as regras gerais valem para todas
    assert violacoes(data) == ["R1: o passo `ui` declara ferramentas que o motor não tem: web_search"]


# ------------------------------------------------------------------ negativos (marketing)

def test_sem_critic_e_recusado():
    assert violacoes(sem(externo(), "critic")) == [
        "R4 [marketing]: a aprovação `hitl` tem de depender directamente de: critic"]


def test_sem_compliance_e_recusado():
    assert violacoes(sem(externo(), "compliance")) == [
        "R4 [marketing]: a aprovação `hitl` tem de depender directamente de: compliance_check"]


def test_revisao_que_nao_e_dependencia_directa_do_gate_nao_conta():
    data = externo()
    data["steps"][3]["depends_on"] = ["critic"]  # a compliance corre, mas o gate não espera por ela
    data["steps"][1]["depends_on"] = ["compliance"]
    data["steps"][2]["depends_on"] = ["copy"]
    assert violacoes(data) == ["R4 [marketing]: a aprovação `hitl` tem de depender directamente de: compliance_check"]


def test_site_ou_artigo_sem_citabilidade_e_recusado():
    data = externo()
    data["deliverable_type"] = "seo_article"
    assert violacoes(data) == ["R5 [marketing]: a aprovação `hitl` tem de depender directamente de: critic_item13"]


def test_sem_consulta_ao_conhecimento_e_recusado():
    data = externo()
    del data["steps"][0]["knowledge"]
    assert violacoes(data) == [
        "R6 [marketing]: o passo `copy` (`copy_social`) não consulta a base de conhecimento (falta `knowledge:`)"]


@pytest.mark.parametrize("bloco, msg", [
    ({"kb": "marketing"}, "`knowledge.query` vazia"),
    ({"kb": "marketing", "query": "curta"}, "`knowledge.query` vazia ou com menos de 12"),
    ({"kb": "seguranca", "query": "uma pergunta comprida"}, "usa `knowledge.kb: 'seguranca'`"),
    ("marketing", "não consulta a base de conhecimento"),
])
def test_conhecimento_declarado_mal_e_recusado(bloco, msg):
    data = externo()
    data["steps"][0]["knowledge"] = bloco
    v = violacoes(data)
    assert len(v) == 1 and msg in v[0], v


def test_publicacao_sem_aprovacao_e_recusada():
    data = sem(externo(), "hitl")
    data["done_when"] = []
    assert violacoes(data) == [
        "R2: entrega externa sem aprovação humana em `done_when` (`human_gate_resolved on <id do passo>`)"]


def test_passo_fora_da_aprovacao_numa_entrega_externa_e_recusado():
    data = externo()
    data["steps"].insert(0, {"id": "solto", "action": "research", "output_artifact": "artifacts/s.md", "knowledge": k()})
    assert violacoes(data) == ["R2: entrega externa com passos fora da aprovação humana final: solto"]


def test_passo_depois_da_aprovacao_final_e_recusado():
    """Revisão externa (2026-11-05): conteúdo novo depois da aprovação final ficava sem revisão."""
    data = externo()
    data["budget"]["max_steps"] = 6
    data["steps"].append({"id": "publicar", "action": "publish_package", "depends_on": ["hitl"],
                          "output_artifact": "artifacts/p.md", "knowledge": k()})
    assert violacoes(data) == ["R2: entrega externa com passos fora da aprovação humana final: publicar"]


def test_ramo_depois_de_um_gate_intermedio_que_nao_chega_ao_final_e_recusado():
    data = externo()
    data["budget"]["max_steps"] = 7
    data["steps"] += [
        {"id": "g1", "action": "plan_approve", "depends_on": ["copy"], "human_gate": GATE},
        {"id": "lado", "action": "copy_social", "depends_on": ["g1"], "output_artifact": "artifacts/l.md",
         "knowledge": k()},
    ]
    assert violacoes(data) == ["R2: entrega externa com passos fora da aprovação humana final: lado"]


def test_declarar_internal_com_um_passo_que_prepara_publicacao_e_recusado():
    data = {"id": "pol-falso-interno", "objective": "x", "delivery": "internal", "budget": {"max_steps": 1},
            "steps": [{"id": "pub", "action": "publish_package", "output_artifact": "artifacts/p.md", "knowledge": k()}]}
    v = violacoes(data)
    assert v[0] == ("R2: o passo `pub` (`publish_package`) prepara uma publicação: "
                    "o plano tem de declarar `delivery: external`")
    assert any(x.startswith("R2: entrega externa sem aprovação humana") for x in v)  # e é avaliado como externo


def test_revisor_que_nao_ve_o_trabalho_nao_conta():
    data = externo()
    data["steps"][1]["depends_on"] = []  # o critic corre, mas sem receber o copy
    assert violacoes(data) == ["R4 [marketing]: o revisor `critic` (`critic`) não recebe o trabalho de: copy"]


def test_plano_sem_passos_e_recusado():
    assert violacoes({"id": "vazio", "objective": "x", "steps": []}) == ["R9: o plano não tem passos"]


def test_marketing_sem_delivery_nem_budget_e_recusado():
    data = externo()
    del data["delivery"], data["budget"]
    assert violacoes(data) == ["R3 [marketing]: o plano tem de declarar `budget.max_steps`",
                               "R2 [marketing]: o plano tem de declarar `delivery: internal` ou `delivery: external`"]


@pytest.mark.parametrize("valor", [0, 41, 1_000_000, "10", True])
def test_orcamento_fora_do_tecto_global_e_recusado(valor):
    data = externo()
    data["budget"]["max_steps"] = valor
    v = violacoes(data)
    assert len(v) == 1 and v[0].startswith("R3: `budget.max_steps` tem de ser um inteiro entre 1 e 40"), v


def test_delivery_desconhecido_e_recusado():
    data = externo()
    data["delivery"] = "publico"
    assert "R2: `delivery` tem de ser internal ou external (veio 'publico')" in violacoes(data)


def test_especialista_antes_do_lider_e_recusado():
    data = externo()
    data["deliverable_type"] = "area_conteudo"
    data["budget"]["max_steps"] = 6
    data["steps"].insert(0, {"id": "lider", "action": "lider_conteudo", "output_artifact": "artifacts/00.md",
                             "knowledge": k()})
    assert violacoes(data) == ["R2: entrega externa com passos fora da aprovação humana final: lider",
                               "R7 [marketing]: estes passos não dependem do líder `lider`: copy, critic, compliance, hitl"]
    data["steps"][1]["depends_on"] = ["lider"]
    assert violacoes(data) == []


def test_plano_de_area_sem_lider_e_recusado():
    data = externo()
    data["deliverable_type"] = "area_conteudo"
    assert violacoes(data) == [
        "R7 [marketing]: um plano de área (`area_conteudo`) tem de ter o passo do líder (`lider_*`)"]


def test_dois_lideres_sao_recusados():
    data = externo()
    data["budget"]["max_steps"] = 7
    data["steps"][:0] = [
        {"id": "l1", "action": "lider_conteudo", "output_artifact": "artifacts/a.md", "knowledge": k()},
        {"id": "l2", "action": "lider_social", "depends_on": ["l1"], "output_artifact": "artifacts/b.md",
         "knowledge": k()},
    ]
    data["steps"][2]["depends_on"] = ["l2"]
    assert violacoes(data) == ["R7 [marketing]: só pode haver um líder no plano (há l1, l2)"]


# ------------------------------------------------------------------ fail-closed (R9)

def test_accao_sem_agente_e_recusada():
    data = externo()
    data["steps"][0]["action"] = "acao_inventada"
    assert violacoes(data) == [
        "R9: o passo `copy` usa a acção `acao_inventada`, que nenhum agente tem (agents/**/*.agent.md)"]


def test_aprovacao_sem_human_gate_e_recusada():
    data = externo()
    del data["steps"][3]["human_gate"]
    v = violacoes(data)
    assert "R9: o passo `hitl` (`plan_approve`) é uma aprovação mas não tem `human_gate`" in v


def test_sem_ficheiro_de_regras_nada_arranca(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "POLICY_FILE", tmp_path / "nao-existe.yaml")
    with pytest.raises(PolicyError, match="R9: não foi possível ler as regras do motor"):
        check_plan(Plan.from_dict(externo()))


@pytest.mark.parametrize("conteudo", [
    "version: 2\nglobal: {}\nverticals: {}\n", "global: x\n", "- lista\n", "a: [\n",
    # perfis com valores estranhos (revisão externa): recusam tudo, não ficam a meio
    "version: 1\nglobal: {max_steps_cap: 9, gate_actions: [g], delivery_values: [a]}\n"
    "verticals: {m: {knowledge: {allowed_kbs: [x], min_query_chars: muitos}}}\n",
    "version: 1\nglobal: {max_steps_cap: 9, gate_actions: [g], delivery_values: [a]}\n"
    "verticals: {m: {review_before_gate: critic}}\n",
    "version: 1\nglobal: {max_steps_cap: 9, gate_actions: [g], delivery_values: [a]}\nverticals: {m: lista}\n",
])
def test_ficheiro_de_regras_invalido_nada_arranca(tmp_path, monkeypatch, conteudo):
    p = tmp_path / "plan-policy.yaml"
    p.write_text(conteudo, encoding="utf-8")
    monkeypatch.setattr(policy, "POLICY_FILE", p)
    with pytest.raises(PolicyError, match="R9"):
        check_plan(Plan.from_dict(externo()))


# ------------------------------------------------------------------ o motor aplica-as em todos os caminhos

def _escreve(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return p


def test_run_recusado_nao_cria_o_run(tmp_path, tmp_run_dir):
    with pytest.raises(PolicyError):
        run_plan(_escreve(tmp_path, sem(externo(), "critic")), mode="stub", out_dir=tmp_run_dir)
    assert not tmp_run_dir.exists() or not any(tmp_run_dir.iterdir())


def test_dry_run_tambem_e_recusado(tmp_path):
    with pytest.raises(PolicyError):
        run_plan(_escreve(tmp_path, sem(externo(), "critic")), mode="dry-run")


def test_langgraph_tambem_e_recusado(tmp_path, tmp_run_dir):
    pytest.importorskip("langgraph.graph")
    from plan_runner.langgraph_engine import run_plan_langgraph

    with pytest.raises(PolicyError):
        run_plan_langgraph(_escreve(tmp_path, sem(externo(), "critic")), mode="stub", out_dir=tmp_run_dir)


def test_resume_de_um_plano_alterado_para_fora_das_regras_e_recusado(tmp_path, tmp_run_dir):
    status = run_plan(_escreve(tmp_path, externo()), mode="stub", out_dir=tmp_run_dir)
    assert status["state"] == "paused_human_gate"
    (tmp_run_dir / "plan.yaml").write_text(yaml.safe_dump(sem(externo(), "compliance")), encoding="utf-8")
    with pytest.raises(PolicyError, match="R4"):
        resume_run(tmp_run_dir, decision="approve")


def test_cli_recusa_com_a_lista_das_regras(tmp_path, run_cli, tmp_run_dir):
    proc = run_cli(["run", str(_escreve(tmp_path, sem(externo(), "critic"))), "--mode", "stub",
                    "--out", str(tmp_run_dir)])
    assert proc.returncode != 0
    assert "R4 [marketing]: a aprovação `hitl` tem de depender directamente de: critic" in proc.stdout + proc.stderr


# ------------------------------------------------------------------ planos do repo e do router

# Registo de um piloto de 2026-09 (formato antigo, não é template): o motor recusa-o, como deve.
HISTORICO = {"docs/architecture/plan-execute/examples/piloto-netos.plan.yaml"}
PLANOS = sorted(p.relative_to(REPO).as_posix() for p in REPO.glob("docs/**/*.plan.yaml"))


@pytest.mark.parametrize("rel", [p for p in PLANOS if p not in HISTORICO])
def test_cada_plano_do_repo_cumpre_as_regras(rel):
    load_plan(REPO / rel)


def test_o_registo_historico_e_recusado():
    for rel in HISTORICO:
        with pytest.raises(PolicyError):
            load_plan(REPO / rel)


def test_os_templates_de_marketing_que_saem_para_fora_tem_revisao_e_compliance():
    externos = [p for p in PLANOS if "/marketing/" in p
                and yaml.safe_load((REPO / p).read_text(encoding="utf-8")).get("delivery") == "external"]
    assert len(externos) >= 12, externos  # 6 áreas, os packs e os exemplos que publicam ou enviam


@pytest.mark.parametrize("outcome, agentes, hitl", [
    ("agent", ["marketing.research"], False),
    ("plan", ["marketing.seo_brief", "marketing.copy_answer_first"], False),
    ("agent", ["marketing.copy_social"], True),
    ("hitl", [], True),
])
def test_plano_do_router_cumpre_as_regras(monkeypatch, outcome, agentes, hitl):
    """Um plano feito na hora pelo router (fora dos templates) passa pelas mesmas regras."""
    from plan_runner import router as rt
    from tests.test_router import FakeRouterLLM

    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    router = rt.Router(transport=FakeRouterLLM())
    d = rt.RouteDecision(request="Escreve um post sobre a nova lei", outcome=outcome, area="marketing",
                         agent=agentes[0] if outcome == "agent" else None, hitl_required=hitl, reason="teste",
                         steps=[{"agent": a, "task": "", "depends_on": [n] if n else []} for n, a in enumerate(agentes)]
                         if outcome == "plan" else [])
    plan = router.build_plan(d)
    assert plan["delivery"] == "internal"
    if outcome != "hitl":  # a triagem é só o gate humano: não tem passos de marketing
        assert plan["budget"]["max_steps"] >= len(plan["steps"])
    check_plan(Plan.from_dict(plan))


def test_tecto_do_schema_e_o_das_regras():
    schema = json.loads((REPO / "runner/plan_runner/plan.schema.json").read_text(encoding="utf-8"))
    cap = yaml.safe_load((REPO / "config/plan-policy.yaml").read_text(encoding="utf-8"))["global"]["max_steps_cap"]
    assert schema["properties"]["budget"]["properties"]["max_steps"]["maximum"] == cap


def test_nao_ha_forma_de_desligar_as_regras_no_plano(tmp_path, tmp_run_dir):
    """Nem um campo no plano, nem uma variável de ambiente: o plano vai na mesma às regras."""
    data = sem(externo(), "critic")
    data["policy"] = "off"
    with pytest.raises(PolicyError):
        check_plan(Plan.from_dict(data))
    src = Path(policy.__file__).read_text(encoding="utf-8")
    assert "os.environ" not in src and "getenv" not in src


def test_os_testes_usam_as_regras_reais():
    """Nenhum teste troca as regras por uma cópia permissiva (só os testes de fail-closed, acima)."""
    assert policy.POLICY_FILE == REPO / "config/plan-policy.yaml"
    outros = [p.name for p in Path(__file__).parent.glob("test_*.py")
              if p.name != Path(__file__).name and "POLICY_FILE" in p.read_text(encoding="utf-8")]
    assert outros == []


def test_router_nao_corre_um_plano_que_as_regras_recusam(monkeypatch, tmp_run_dir):
    """Revisão externa: o LLM do router pode propor o líder depois de um especialista; não corre."""
    from plan_runner import router as rt
    from tests.test_router import FakeRouterLLM

    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    router = rt.Router(transport=FakeRouterLLM())
    d = rt.RouteDecision(request="Plano de redes para o inverno", outcome="plan", area="marketing", reason="teste",
                         steps=[{"agent": "marketing.research", "task": "", "depends_on": []},
                                {"agent": "marketing.lider_social", "task": "", "depends_on": [1]}])
    out = router.execute(d, out_dir=tmp_run_dir, worker=None)
    assert out["executed"] is False and out["decision"]["outcome"] == "error"
    assert any(v.startswith("R7 [marketing]: estes passos não dependem do líder") for v in out["violations"])
    assert not (tmp_run_dir / "status.json").exists()
