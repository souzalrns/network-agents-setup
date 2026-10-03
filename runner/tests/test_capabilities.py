"""Capability First: config/*-capabilities.yaml validado no E7 + inventário agente <-> skill."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from plan_runner.areas import main as areas_main
from plan_runner.areas import validate_areas
from plan_runner.capabilities import capability_files, inventory, validate_capabilities

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _cap(**over) -> dict:
    c = {"id": "triage", "description": "Classificar.", "levels": ["read"], "action": "sec_triage",
         "agent": "sec.triage", "skill": "skills/sec/triage/SKILL.md", "status": "implemented"}
    c.update(over)
    return c


def _repo(tmp_path: Path, caps: list[dict] | None = None, policy: dict | None = None, *, hitl="required",
          fname="sec-capabilities.yaml", domain="sec", agent_skill="skills/sec/triage/SKILL.md",
          skill_action="sec_triage", extra_area_agents=()) -> Path:
    _write(tmp_path / "agents/sec/sec_triage.agent.md",
           f"---\nid: sec.triage\nkind: internal\naction: sec_triage\nskill: {agent_skill}\nvertical: sec\n---\n# T\n")
    _write(tmp_path / "agents/eng/dev.agent.md", "---\nid: eng.dev\nkind: internal\naction: dev\n---\n# D\n")
    _write(tmp_path / "skills/sec/triage/SKILL.md", f"---\nname: t\naction: {skill_action}\n---\n# S\n")
    areas = {"routing": {"fallback_area": "sec"}, "areas": [
        {"id": "sec", "description": "S.", "agents": ["sec.triage", *extra_area_agents], "horizontals": [], "hitl": hitl},
        {"id": "eng", "description": "E.", "agents": ["eng.dev"], "horizontals": []}]}
    _write(tmp_path / "config/areas.yaml", yaml.safe_dump(areas))
    data = {"version": 1, "domain": domain,
            "policy": policy or {"offensive": "forbidden", "act_in_production": "forbidden", "default_level": "read", "hitl": "required"},
            "capabilities": caps if caps is not None else [_cap()]}
    _write(tmp_path / "config" / fname, yaml.safe_dump(data, allow_unicode=True))
    return tmp_path


def test_ficheiro_real_de_security_e_valido():
    assert [p.name for p in capability_files(REPO_ROOT)] == ["security-capabilities.yaml"]
    assert validate_areas(REPO_ROOT) == []


def test_mini_repo_valido(tmp_path):
    assert validate_areas(_repo(tmp_path)) == []


@pytest.mark.parametrize("kw,expect", [
    ({"policy": {"offensive": "allowed", "act_in_production": "forbidden", "default_level": "read", "hitl": "required"}}, "policy.offensive"),
    ({"policy": {"offensive": "forbidden", "act_in_production": "allowed", "default_level": "read", "hitl": "required"}}, "policy.act_in_production"),
    ({"policy": {"offensive": "forbidden", "act_in_production": "forbidden", "default_level": "read", "hitl": None}}, "policy.hitl"),
    ({"policy": {"offensive": "forbidden", "act_in_production": "forbidden", "default_level": "root", "hitl": "required"}}, "default_level"),
    ({"caps": [_cap(levels=["act"])]}, "nível `act` proibido"),
    ({"caps": [_cap(levels=["lab"])]}, "nível `lab` só em capabilities `deferred`"),
    ({"caps": [_cap(levels=["write"])]}, "levels tem de ser"),
    ({"caps": [_cap(status="done")]}, "status tem de ser"),
    ({"caps": [_cap(), _cap()]}, "id repetido"),
    ({"caps": [_cap(agent=None)]}, "`agent` obrigatório"),
    ({"caps": [_cap(agent="nao.existe")]}, "não existe em agents"),
    ({"caps": [_cap(agent="eng.dev", action="dev", skill=None)]}, "não está em agents[] da área `sec`"),
    ({"caps": [_cap(action="outra")]}, "tem action `sec_triage`, não `outra`"),
    ({"caps": [_cap(skill="skills/sec/nada/SKILL.md")]}, "não existe no repo"),
    ({"caps": [_cap(skill="../fora.md")]}, "não existe no repo"),
    ({"skill_action": "outra"}, "a skill `skills/sec/triage/SKILL.md` tem action `outra`"),
    ({"caps": [_cap(tools_guidance="gitleaks")]}, "tools_guidance"),
    ({"fname": "outro-capabilities.yaml"}, "chama-se `sec-capabilities.yaml`"),
    ({"domain": "nao-existe", "fname": "nao-existe-capabilities.yaml"}, "não é uma área"),
    ({"caps": []}, "falta a lista `capabilities`"),
])
def test_validador_recusa(tmp_path, kw, expect):
    errors = validate_areas(_repo(tmp_path, **kw))
    assert any(expect in e for e in errors), errors


def test_deferred_pode_ficar_sem_executor(tmp_path):
    caps = [_cap(), _cap(id="lab", levels=["lab"], action=None, agent=None, skill=None, status="deferred")]
    assert validate_areas(_repo(tmp_path, caps=caps)) == []


def test_skill_declarada_pelo_agente_tem_de_existir(tmp_path):
    errors = validate_areas(_repo(tmp_path, agent_skill="skills/sec/nao-existe/SKILL.md"))
    assert any("agente `sec.triage`" in e and "não existe no repo" in e for e in errors), errors


def test_agente_declara_outra_skill_que_a_capability(tmp_path):
    _write(tmp_path / "skills/sec/outra/SKILL.md", "---\naction: sec_triage\n---\n")
    errors = validate_areas(_repo(tmp_path, agent_skill="skills/sec/outra/SKILL.md"))
    assert any("declara a skill `skills/sec/outra/SKILL.md`" in e for e in errors), errors


def test_sem_ficheiros_de_capabilities_nada_muda(tmp_path):
    repo = _repo(tmp_path)
    (repo / "config/sec-capabilities.yaml").unlink()
    from plan_runner.areas import agent_ids, load_areas

    known, _ = agent_ids(repo)
    assert validate_capabilities(repo, known, load_areas(repo)) == []


def test_inventario(tmp_path):
    repo = _repo(tmp_path)
    _write(repo / "skills/meta/orfa/SKILL.md", "---\naction: orfa\n---\n")
    _write(repo / "skills/claude/pack/SKILL.md", "---\naction: pack\n---\n")
    from plan_runner.areas import agent_ids

    known, _ = agent_ids(repo)
    inv = inventory(repo, known)
    assert inv["agents_without_skill"] == ["eng.dev"]
    assert inv["skills_without_agent"] == ["skills/meta/orfa/SKILL.md"]  # o pack Claude fica de fora
    assert inv["agents_using_claude_pack"] == [] and inv["shared_skill_action_differs"] == []


def test_inventario_real_e_cli(capsys):
    assert areas_main([str(REPO_ROOT), "--inventory"]) == 0
    out = capsys.readouterr().out
    assert "1 ficheiro(s) de capabilities válido(s)" in out
    for key in ("agents_without_skill", "skills_without_agent", "agents_using_claude_pack", "shared_skill_action_differs"):
        assert key in out
    assert "security.triage" not in out.split("agents_without_skill")[1].split("skills_without_agent")[0]
