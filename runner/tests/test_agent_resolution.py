"""A8/D8: resolucao de agentes e skills pelo frontmatter dos .agent.md.

Antes, o runner so encontrava agents/<vertical>/<action>.agent.md e
skills/<vertical>/<action>/SKILL.md -- 23/35 agentes tinham `action:` diferente
do nome do ficheiro e ficavam com agent_path null (AUDIT-3 A7/A8).
"""
from __future__ import annotations

import pytest

from plan_runner.skills import resolve_agent_path, resolve_skill_path
from tests.conftest import REPO_ROOT

# (action, vertical do plano, agente esperado, skill esperada) -- os 7 casos A7.
A7_CASES = [
    ("ui_spec", "design", "agents/design/ui.agent.md", "skills/design/ui_spec/SKILL.md"),
    ("ux_flow", "design", "agents/design/ux.agent.md", "skills/design/ux_flow/SKILL.md"),
    ("ux_writing", "design", "agents/design/ux_writer.agent.md", "skills/design/ux_writing/SKILL.md"),
    ("influencer_brief", "marketing", "agents/marketing/influencer.agent.md", "skills/marketing/influencer_brief/SKILL.md"),
    ("media_plan", "marketing", "agents/marketing/media_buyer.agent.md", "skills/marketing/media_plan/SKILL.md"),
    ("ugc_brief", "marketing", "agents/marketing/ugc.agent.md", "skills/marketing/ugc_brief/SKILL.md"),
    ("video_edit_plan", "marketing", "agents/marketing/editor_video.agent.md", "skills/marketing/video_edit_plan/SKILL.md"),
]


def _rel(p):
    return p.relative_to(REPO_ROOT).as_posix() if p else None


def test_security_auditor_found_by_action_and_skill_field():
    assert _rel(resolve_agent_path(REPO_ROOT, "security_audit", "meta")) == "agents/meta/security_auditor.agent.md"
    # A pasta da skill tem hifen (security-audit): so o `skill:` do frontmatter a encontra.
    assert _rel(resolve_skill_path(REPO_ROOT, "security_audit", "meta")) == "skills/meta/security-audit/SKILL.md"


@pytest.mark.parametrize("action,vertical,agent,skill", A7_CASES)
def test_a7_agents_resolved(action, vertical, agent, skill):
    assert _rel(resolve_agent_path(REPO_ROOT, action, vertical)) == agent
    assert _rel(resolve_skill_path(REPO_ROOT, action, vertical)) == skill


def test_convention_still_wins(tmp_path):
    """Regressao: o caminho por convencao continua a ser o primeiro a ser usado."""
    agent = tmp_path / "agents" / "marketing" / "review.agent.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("---\nid: marketing.review\naction: review\n---\n# agent", encoding="utf-8")
    skill = tmp_path / "skills" / "marketing" / "review" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# skill", encoding="utf-8")

    assert resolve_agent_path(tmp_path, "review") == agent
    assert resolve_skill_path(tmp_path, "review") == skill


def test_skill_field_outside_repo_is_ignored(tmp_path):
    agent = tmp_path / "agents" / "meta" / "x.agent.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("---\naction: y\nskill: ../fora/SKILL.md\n---\n", encoding="utf-8")
    (tmp_path.parent / "fora").mkdir(exist_ok=True)
    (tmp_path.parent / "fora" / "SKILL.md").write_text("# fora", encoding="utf-8")

    assert resolve_agent_path(tmp_path, "y", "meta") == agent
    assert resolve_skill_path(tmp_path, "y", "meta") is None


def test_unknown_action_and_bad_frontmatter(tmp_path):
    bad = tmp_path / "agents" / "marketing" / "bad.agent.md"
    bad.parent.mkdir(parents=True)
    bad.write_text("---\n: [nao e yaml\n---\n", encoding="utf-8")

    assert resolve_agent_path(tmp_path, "nao_existe") is None
    assert resolve_skill_path(tmp_path, "nao_existe") is None


def test_every_agent_resolvable_by_its_action():
    """Os 35 .agent.md sao encontrados a partir do proprio `action:`."""
    import yaml

    for path in sorted((REPO_ROOT / "agents").glob("**/*.agent.md")):
        fm = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
        vertical = fm.get("vertical") or path.parent.name
        assert resolve_agent_path(REPO_ROOT, fm["action"], vertical) == path, path
