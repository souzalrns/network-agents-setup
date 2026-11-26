"""M-006 (P-89 = A): prova de que cada agente fundido passou a função para um herdeiro activo.

Para cada uma das 11 skills `MERGED` de scripts/vendor_marketingskills.py, os 4 pontos do §5 de
docs/orchestration/marketing/ESTRUTURA-AREAS.md:

1. capability re-apontada: mantém o id, aponta para o herdeiro + `mode`, e o agente antigo saiu;
2. conhecimento preservado: o modo tem o conhecimento upstream integral e o contrato do runner;
3. encaminhamento: um pedido típico cai na área marketing (keywords reais) e no herdeiro com o modo
   (LLM do router falso: prova a canalização, não a qualidade do Gemini);
4. execução: um plano com o herdeiro + modo corre de ponta a ponta (worker Gemini falso), o modo
   entra no prompt só nesse passo e o `done_when` passa.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import router as rt
from plan_runner.capabilities import validate_capabilities
from plan_runner.engine import run_plan
from plan_runner.plan_schema import plan_errors
from tests.politica import politica_dict
from tests.test_external_worker import FakeGemini
from tests.test_router import FakeRouterLLM

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = yaml.safe_load((REPO_ROOT / "config/router-golden.yaml").read_text(encoding="utf-8"))
TRANSFERS = GOLDEN["transfers"]


def _script():
    spec = importlib.util.spec_from_file_location("vendor_marketingskills", REPO_ROOT / "scripts" / "vendor_marketingskills.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _script()
MERGED = MOD.MERGED  # upstream -> (capability, níveis, descrição, herdeiro, modo)
CAPS = {c["id"]: c for c in yaml.safe_load((REPO_ROOT / "config/marketing-capabilities.yaml").read_text(encoding="utf-8"))["capabilities"]}
AREAS = yaml.safe_load((REPO_ROOT / "config/areas.yaml").read_text(encoding="utf-8"))["areas"]
MARKETING = next(a for a in AREAS if a["id"] == "marketing")


def _heir(agent_id: str) -> dict:
    fm = yaml.safe_load((REPO_ROOT / "agents/marketing" / f"{agent_id.split('.', 1)[1]}.agent.md").read_text(encoding="utf-8").split("---")[1])
    return fm


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)


def test_ha_11_fundidas_e_cada_uma_tem_caso_de_encaminhamento():
    assert len(MERGED) == 11 and not set(MERGED) & set(MOD.NEW)
    covered = {t["replaces"] for t in TRANSFERS}
    assert covered == {f"marketing.{n.replace('-', '_')}" for n in MERGED}


# --------------------------------------------------------------------------- 1. capability re-apontada


@pytest.mark.parametrize("name", sorted(MERGED))
def test_1_capability_mantem_o_id_e_aponta_para_o_herdeiro(name):
    cap_id, _levels, desc, heir, mode = MERGED[name]
    old = name.replace("-", "_")
    cap = CAPS[cap_id]
    fm = _heir(heir)
    assert (cap["agent"], cap["action"], cap["skill"], cap["mode"]) == (heir, fm["action"], fm["skill"], mode)
    assert cap["status"] in ("partial", "implemented") and cap["description"] == desc
    assert heir in MARKETING["agents"] and f"marketing.{old}" not in MARKETING["agents"]
    assert not (REPO_ROOT / "agents/marketing" / f"{old}.agent.md").exists()
    assert not (REPO_ROOT / "skills/marketing" / old).exists()


def test_1_validador_aceita_todas_as_capabilities_reais():
    from plan_runner.areas import agent_ids

    known, _ = agent_ids(REPO_ROOT)
    assert validate_capabilities(REPO_ROOT, known, AREAS) == []


# --------------------------------------------------------------------------- 2. conhecimento preservado


@pytest.mark.parametrize("name", sorted(MERGED))
def test_2_modo_tem_o_conhecimento_upstream_integral_e_o_contrato(name):
    _cap, _levels, desc, heir, mode = MERGED[name]
    skill = REPO_ROOT / _heir(heir)["skill"]
    text = (skill.parent / "modes" / f"{mode}.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["mode"] == mode and fm["description"] == desc and fm["replaces"] == f"marketing.{name.replace('-', '_')}"
    _vfm, body = MOD.split_frontmatter((REPO_ROOT / "vendor/marketingskills/skills" / name / "SKILL.md").read_text(encoding="utf-8"))
    knowledge = text.split("## Conhecimento (upstream)\n\n", 1)[1]
    assert knowledge == MOD.relink(body, name, depth=4).lstrip()  # nada se perdeu na passagem
    contract = text.split("## Contrato do runner (obrigatório)", 1)[1].split("## Conhecimento", 1)[0]
    for note in MOD._contract_notes(name):
        assert note in contract  # inclui as notas de conformidade (ex.: loops → aprovação humana)
    assert f"`{heir}` só no passo com `mode: {mode}`" in contract


# --------------------------------------------------------------------------- 3. encaminhamento


@pytest.mark.parametrize("case", TRANSFERS, ids=[t["replaces"] for t in TRANSFERS])
def test_3_pedido_tipico_cai_no_herdeiro_com_o_modo(case):
    reply = {"mode": "agent", "agent": case["agent"], "skill_mode": case["mode"], "confidence": 0.9, "reason": "funcao herdada"}
    llm = FakeRouterLLM(replies={case["request"]: reply})
    router = rt.Router(transport=llm)
    d = router.route(case["request"])
    assert rt.check_case(d, {"area": "marketing", "outcome": "agent", "agent": case["agent"], "mode": case["mode"]}) == [], d.to_dict()
    prompt = llm.calls[-1]["contents"][0]["parts"][0]["text"]
    assert f"`{case['mode']}` = " in prompt and case["replaces"] not in llm.candidates_in_last_prompt()
    plan = router.build_plan(d)
    assert plan["steps"][0]["mode"] == case["mode"] and plan_errors(plan) == []


# --------------------------------------------------------------------------- 4. execução de ponta a ponta


@pytest.mark.parametrize("name", sorted(MERGED))
def test_4_plano_com_o_herdeiro_e_o_modo_corre_e_cumpre_o_done_when(name, tmp_path, tmp_run_dir, monkeypatch):
    _cap, _levels, _desc, heir, mode = MERGED[name]
    action = _heir(heir)["action"]
    fake = FakeGemini()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    art = f"artifacts/01-{mode}.md"
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump(politica_dict({
        "id": f"m006-{mode}", "objective": f"Prova da transferencia de marketing.{name.replace('-', '_')}",
        "done_when": [f"{art} exists"],
        "steps": [
            {"id": "base", "action": action, "output_artifact": "artifacts/00-base.md"},
            {"id": "herdado", "action": action, "mode": mode, "depends_on": ["base"], "output_artifact": art},
        ],
    })), encoding="utf-8")
    status = run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done" and not status.get("done_when_failed"), status
    base_sys, mode_sys = (c["body"]["systemInstruction"]["parts"][0]["text"] for c in fake.calls)
    title = f"Modo da skill: {mode} (só neste passo)"
    assert title in mode_sys and title not in base_sys  # o modo só entra no passo que o pede
    mode_md = (tmp_run_dir / "pending_steps/herdado/MODE.md").read_text(encoding="utf-8")
    first_line = mode_md.split("## Conhecimento (upstream)\n\n", 1)[1].strip().splitlines()[0]
    assert first_line in mode_sys  # o conhecimento da função fundida chegou ao modelo
    activation = json.loads((tmp_run_dir / "pending_steps/herdado/skill_activation.json").read_text(encoding="utf-8"))
    assert activation["mode"]["error"] is None and activation["agent"]["path"].endswith(f"{heir.split('.', 1)[1]}.agent.md")
    assert (tmp_run_dir / art).is_file()
