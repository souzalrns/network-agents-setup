"""M-006, fase 2: os 9 agentes de execução.

Cada agente tem ficha completa (com fronteiras), capability `implemented`, lugar no escritório, linha na
tabela do líder da área e é usado de facto num template de área. A verificação de compliance corre em
todas as áreas antes da aprovação humana. Nenhum destes agentes publica ou gasta: preparam a execução.
Sem rede: worker Gemini falso.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import office
from plan_runner.engine import run_plan
from tests.test_external_worker import FakeGemini

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = REPO_ROOT / "docs/orchestration/marketing/templates/areas"
OFFICE = yaml.safe_load((REPO_ROOT / "config/office.yaml").read_text(encoding="utf-8"))
AREAS = yaml.safe_load((REPO_ROOT / "config/areas.yaml").read_text(encoding="utf-8"))["areas"]
MARKETING = next(a for a in AREAS if a["id"] == "marketing")
CAPS = {c["action"]: c for c in yaml.safe_load(
    (REPO_ROOT / "config/marketing-capabilities.yaml").read_text(encoding="utf-8"))["capabilities"]}

# action -> (agente, lugar, líder da área ou None, template de área que o usa)
EXEC = {
    "video_production": ("marketing.produtor_video", "marketing-video", "video", "video"),
    "audio_voice": ("marketing.audio_voz", "marketing-video", "video", "video"),
    "repurposing": ("marketing.repurposing", "marketing-video", "video", "video"),
    "editorial_calendar": ("marketing.calendario", "marketing-social", "social", "social"),
    "publish_package": ("marketing.publicador", "marketing-social", "social", "social"),
    "social_intelligence": ("marketing.social_intelligence", "marketing-pesquisa", "inteligencia", "inteligencia"),
    "social_performance": ("marketing.performance_social", "marketing-pesquisa", "inteligencia", "inteligencia"),
    "brand_guardian": ("marketing.guardiao_marca", "marketing-estrategia", "estrategia", "estrategia"),
    "compliance_check": ("marketing.compliance", "marketing-qualidade", None, None),
}
FICHA = ("## Missão", "## Recebe / entrega", "## Funções", "## Fronteiras (não confundir com)",
         "## Decide sozinho / pede aprovação", "## Regras que não quebra", "## Saída", "## Está pronto quando")
AREA_TEMPLATES = sorted(TEMPLATES.glob("*.plan.yaml"))


def _fm(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def _seat(seat_id: str) -> dict:
    return next(s for d in OFFICE["departments"] for s in d["seats"] if s["id"] == seat_id)


def _plan(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------------------- definição


@pytest.mark.parametrize("action", EXEC)
def test_agente_tem_skill_com_ficha_completa_e_regras_de_execucao(action):
    aid, *_ = EXEC[action]
    fm = _fm(REPO_ROOT / "agents/marketing" / f"{aid.split('.', 1)[1]}.agent.md")
    assert (fm["id"], fm["action"], fm["skill"]) == (aid, action, f"skills/marketing/{action}/SKILL.md")
    skill = (REPO_ROOT / fm["skill"]).read_text(encoding="utf-8")
    pos = [skill.index(h) for h in FICHA]
    assert pos == sorted(pos), "a ficha tem as secções por esta ordem"
    rules = skill.split("## Regras que não quebra", 1)[1].split("\n## ", 1)[0]
    assert "art. 50" in rules, "identificação de conteúdo gerado por IA (AI Act)"
    assert aid in MARKETING["agents"]


@pytest.mark.parametrize("action", EXEC)
def test_capability_lugar_e_tabela_do_lider(action):
    aid, seat, leader, _ = EXEC[action]
    cap = CAPS[action]
    assert (cap["agent"], cap["status"]) == (aid, "implemented")
    assert aid in _seat(seat)["agents"]
    if leader:
        table = (REPO_ROOT / f"skills/marketing/lider_{leader}/SKILL.md").read_text(encoding="utf-8")
        table = table.split("## Especialistas da área (só estes)", 1)[1].split("\n## ", 1)[0]
        assert f"| `{aid}` | `{action}` |" in table


def test_escritorio_e_capabilities_validos():
    assert office.validate_office(REPO_ROOT) == []
    from plan_runner.areas import agent_ids
    from plan_runner.capabilities import validate_capabilities

    known, _ = agent_ids(REPO_ROOT)
    assert validate_capabilities(REPO_ROOT, known, AREAS) == []


# --------------------------------------------------------------------------- uso nos templates


@pytest.mark.parametrize("action", [a for a, v in EXEC.items() if v[3]])
def test_cada_agente_e_usado_no_template_da_sua_area_depois_do_brief(action):
    *_, area = EXEC[action]
    plan = _plan(TEMPLATES / f"{area.replace('_', '-')}.plan.yaml")
    step = next(s for s in plan["steps"] if s["action"] == action)
    assert plan["steps"][0]["output_artifact"] in step["inputs"]
    assert step["depends_on"]


def test_cadeia_do_video_e_do_social():
    video = {s["id"]: s for s in _plan(TEMPLATES / "video.plan.yaml")["steps"]}
    assert set(video["edicao"]["depends_on"]) == {"producao", "imagem", "audio"}
    assert video["versoes"]["depends_on"] == ["edicao"]
    social = {s["id"]: s for s in _plan(TEMPLATES / "social.plan.yaml")["steps"]}
    assert social["publicacao"]["depends_on"] == ["calendario"]
    assert social["publicacao"]["output_artifact"].endswith(".json")


@pytest.mark.parametrize("path", AREA_TEMPLATES, ids=lambda p: p.stem)
def test_compliance_corre_em_todas_as_areas_antes_do_humano(path):
    plan = _plan(path)
    steps = {s["id"]: s for s in plan["steps"]}
    comp = [s for s in plan["steps"] if s["action"] == "compliance_check"]
    assert len(comp) == 1 and comp[0]["output_artifact"].endswith(".json")
    produced = {s["output_artifact"] for s in plan["steps"] if s["action"] not in
                {"critic", "compliance_check", "plan_approve"}}
    assert produced <= set(comp[0]["inputs"]), "a compliance vê todas as peças da área"
    hitl = plan["steps"][-1]
    assert hitl["action"] == "plan_approve" and comp[0]["id"] in hitl["depends_on"]
    assert "critic" in steps and set(steps["critic"]["depends_on"]) == set(comp[0]["depends_on"])
    assert plan["budget"]["max_steps"] >= len(plan["steps"])


# --------------------------------------------------------------------------- execução


@pytest.mark.parametrize("area", ["video", "social", "inteligencia", "estrategia"])
def test_template_corre_ate_ao_humano_com_os_agentes_de_execucao(area, tmp_path, tmp_run_dir, monkeypatch):
    fake = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    plan = _plan(TEMPLATES / f"{area}.plan.yaml")
    plan["objective"] = "Uma loja de bicicletas fictícia quer mais clientes no inverno."
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    status = run_plan(path, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate" and status.get("paused_at_step") == "hitl", status
    systems = [c["body"]["systemInstruction"]["parts"][0]["text"] for c in fake.calls]
    for action in (a for a, v in EXEC.items() if v[3] == area or a == "compliance_check"):
        skill = (REPO_ROOT / f"skills/marketing/{action}/SKILL.md").read_text(encoding="utf-8")
        mission = skill.split("## Missão\n\n", 1)[1].split("\n", 1)[0]
        assert any(mission in s for s in systems), action  # a skill do agente foi carregada no seu passo
    for s in plan["steps"]:
        if s["action"] != "plan_approve":
            assert (tmp_run_dir / s["output_artifact"]).is_file(), s["id"]
    comp = next(s for s in plan["steps"] if s["action"] == "compliance_check")
    json.loads((tmp_run_dir / comp["output_artifact"]).read_text(encoding="utf-8"))
