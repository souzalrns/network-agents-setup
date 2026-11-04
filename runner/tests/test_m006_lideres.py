"""M-006 (P-90 = B): líderes de área que orquestram de facto.

Cada líder (marketing.lider_<área>) coordena como o marketing.marketing, mas só com os especialistas
da sua área: decide e entrega o brief; os especialistas recebem-no como input num template de área.
O escritório só aceita um `lead` que orquestra de facto num plano real (plan_runner/office.py).
Sem rede: worker Gemini falso.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import office
from plan_runner.capabilities import validate_capabilities
from plan_runner.engine import run_plan
from plan_runner.plan_schema import file_errors
from plan_runner.skills import list_modes, resolve_skill_path
from tests.test_external_worker import FakeGemini

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = REPO_ROOT / "docs/orchestration/marketing/templates/areas"
OFFICE = yaml.safe_load((REPO_ROOT / "config/office.yaml").read_text(encoding="utf-8"))
AREAS = yaml.safe_load((REPO_ROOT / "config/areas.yaml").read_text(encoding="utf-8"))["areas"]
MARKETING = next(a for a in AREAS if a["id"] == "marketing")
CAPS = {c["id"]: c for c in yaml.safe_load((REPO_ROOT / "config/marketing-capabilities.yaml").read_text(encoding="utf-8"))["capabilities"]}
LEADERS = ["estrategia", "inteligencia", "conteudo", "video", "social", "site_seo", "anuncios", "crm"]
QUALITY_ACTIONS = {"critic", "critic_item13", "compliance_check", "plan_approve"}  # a camada de Qualidade revê tudo; não é especialista da área
FICHA = ("## Missão", "## Recebe / entrega", "## Funções", "## Especialistas da área (só estes)",
         "## Decide sozinho / pede aprovação", "## Regras que não quebra", "## Saída: brief da área", "## Está pronto quando")


def _fm(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def _members(slug: str) -> set[str]:
    """Lugar (marketing) ou departamento (Comercial, para o CRM) que o líder coordena."""
    lead = f"marketing.lider_{slug}"
    for dept in OFFICE["departments"]:
        if dept.get("lead") == lead:
            return {a for s in dept["seats"] for a in s["agents"]}
        for seat in dept["seats"]:
            if seat.get("lead") == lead:
                return set(seat["agents"])
    raise AssertionError(f"{lead} não é lead de nenhum lugar ou departamento")


def _actions() -> dict[str, str]:
    index, errors = office.action_index(REPO_ROOT)
    assert errors == []
    return index


def _template(slug: str) -> dict:
    return yaml.safe_load((TEMPLATES / f"{slug.replace('_', '-')}.plan.yaml").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------------------- definição do líder


@pytest.mark.parametrize("slug", LEADERS)
def test_lider_tem_agente_skill_ficha_e_capability(slug):
    aid = f"marketing.lider_{slug}"
    agent = REPO_ROOT / "agents/marketing" / f"lider_{slug}.agent.md"
    fm = _fm(agent)
    assert (fm["id"], fm["action"], fm["skill"]) == (aid, f"lider_{slug}", f"skills/marketing/lider_{slug}/SKILL.md")
    skill = (REPO_ROOT / fm["skill"]).read_text(encoding="utf-8")
    pos = [skill.index(h) for h in FICHA]
    assert pos == sorted(pos), "a ficha-padrão tem as secções por esta ordem"
    assert aid in MARKETING["agents"]
    cap = CAPS[f"area_lead_{slug}"]
    assert (cap["agent"], cap["action"], cap["status"]) == (aid, f"lider_{slug}", "implemented")


@pytest.mark.parametrize("slug", LEADERS)
def test_tabela_de_especialistas_bate_com_o_lugar_e_os_modos_existem(slug):
    """A skill lista exactamente os especialistas do lugar/departamento, com as actions e os modos reais."""
    skill = (REPO_ROOT / f"skills/marketing/lider_{slug}/SKILL.md").read_text(encoding="utf-8")
    table = skill.split("## Especialistas da área (só estes)", 1)[1].split("\n## ", 1)[0]
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in table.splitlines() if line.startswith("| `")]
    listed = {r[0].strip("`"): (r[1].strip("`"), r[2]) for r in rows}
    assert set(listed) == _members(slug) - {f"marketing.lider_{slug}"}
    by_agent = {aid: act for act, aid in _actions().items()}
    for aid, (action, modes) in listed.items():
        assert by_agent[aid] == action, aid
        declared = {m.strip(" `") for m in modes.split(",")} - {"—"}
        real = set(list_modes(resolve_skill_path(REPO_ROOT, action, "design" if aid.startswith("design.") else "marketing")))
        assert declared <= real, (aid, declared, real)


def test_capabilities_reais_validas():
    from plan_runner.areas import agent_ids

    known, _ = agent_ids(REPO_ROOT)
    assert validate_capabilities(REPO_ROOT, known, AREAS) == []


# --------------------------------------------------------------------------- template de área = orquestração de facto


@pytest.mark.parametrize("slug", LEADERS)
def test_template_comeca_no_lider_e_so_usa_especialistas_da_area(slug):
    path = TEMPLATES / f"{slug.replace('_', '-')}.plan.yaml"
    assert file_errors(path) == []
    plan = _template(slug)
    steps = {s["id"]: s for s in plan["steps"]}
    first = plan["steps"][0]
    assert first["action"] == f"lider_{slug}" and not first.get("depends_on")
    brief = first["output_artifact"]
    actions = _actions()
    members = _members(slug)

    def reaches_leader(sid: str) -> bool:
        deps = steps[sid].get("depends_on") or []
        return "lider" in deps or any(reaches_leader(d) for d in deps)

    specialists = [s for s in plan["steps"][1:] if s["action"] not in QUALITY_ACTIONS]
    assert specialists, "um líder sem especialistas não orquestra nada"
    for s in specialists:
        assert actions[s["action"]] in members, (s["id"], actions[s["action"]])
        assert brief in s["inputs"] and reaches_leader(s["id"]), s["id"]
    assert plan["steps"][-1]["action"] == "plan_approve"  # nada sai sem aprovação humana
    assert f"{brief} exists" in plan["done_when"]


def test_escritorio_aceita_os_leads_reais_com_evidencia():
    assert office.validate_office(REPO_ROOT) == []
    for slug in LEADERS:
        rel = office.orchestration_evidence(REPO_ROOT, f"marketing.lider_{slug}", _members(slug))
        assert rel == f"docs/orchestration/marketing/templates/areas/{slug.replace('_', '-')}.plan.yaml", slug


def test_lead_que_nao_orquestra_e_recusado(monkeypatch):
    """Sem dependências no plano, o lead deixa de ter evidência e o escritório recusa-o."""
    real = office._plans

    def no_deps(repo_root):
        return [(rel, [{**s, "depends_on": []} for s in steps]) for rel, steps in real(repo_root)]

    monkeypatch.setattr(office, "_plans", no_deps)
    errors = office.validate_office(REPO_ROOT)
    for slug in LEADERS:
        assert any(f"marketing.lider_{slug}` não orquestra de facto" in e for e in errors), slug


def test_coordenador_sem_skill_mantem_a_regra_antiga():
    """O marketing.marketing (dispatch pelo router, skill null) continua lead do departamento sem plano."""
    mk = next(d for d in OFFICE["departments"] if d["id"] == "marketing")
    assert mk["lead"] == "marketing.marketing" and not office._lead_has_skill(REPO_ROOT, "marketing.marketing")


def test_projeccao_e_html_mostram_o_lead_do_lugar():
    from plan_runner.office_html import render

    snap = office.snapshot(REPO_ROOT, [])
    seat = next(s for d in snap["departments"] for s in d["seats"] if s["id"] == "marketing-video")
    assert seat["lead"] == "marketing.lider_video"
    assert "lead: lider_video" in render(snap)


# --------------------------------------------------------------------------- execução de ponta a ponta


@pytest.mark.parametrize("slug", LEADERS)
def test_template_corre_brief_chega_aos_especialistas_e_para_no_humano(slug, tmp_path, tmp_run_dir, monkeypatch):
    fake = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    plan = _template(slug)
    plan["objective"] = "Uma loja de bicicletas fictícia quer mais clientes no inverno."
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    status = run_plan(path, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate" and status.get("paused_at_step") == "hitl", status
    brief = plan["steps"][0]["output_artifact"]
    assert (tmp_run_dir / brief).is_file()
    first_system = fake.calls[0]["body"]["systemInstruction"]["parts"][0]["text"]
    skill = (REPO_ROOT / f"skills/marketing/lider_{slug}/SKILL.md").read_text(encoding="utf-8")
    mission = skill.split("## Missão\n\n", 1)[1].split("\n", 1)[0]
    assert mission in first_system  # o primeiro passo carregou a skill do líder
    specialists = [s for s in plan["steps"][1:] if s["action"] not in QUALITY_ACTIONS]
    for call in fake.calls[1:1 + len(specialists)]:
        user = call["body"]["contents"][0]["parts"][0]["text"]
        assert f"Input: {brief}" in user  # o brief do líder entrou no prompt de cada especialista
