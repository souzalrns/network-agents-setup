"""Testes de skills.py: resolucao de paths e leitura tolerante."""
from __future__ import annotations

from pathlib import Path

from plan_runner.skills import (
    read_text_if_exists,
    repo_root_from_out,
    resolve_agent_path,
    resolve_skill_path,
)


def test_repo_root_from_out_with_pilots():
    out = Path("/repo/pilots/run-1")
    assert repo_root_from_out(out) == Path("/repo")


def test_repo_root_from_out_without_pilots():
    out = Path("/repo/other/run-1")
    assert repo_root_from_out(out) == Path("/repo/other")
    assert repo_root_from_out(out) == Path("/repo/other")


def test_resolve_skill_path_exists(tmp_path):
    skill = tmp_path / "skills" / "marketing" / "review" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# skill", encoding="utf-8")

    result = resolve_skill_path(tmp_path, "review")
    assert result == skill


def test_resolve_skill_path_missing(tmp_path):
    result = resolve_skill_path(tmp_path, "nao-existe")
    assert result is None


def test_resolve_skill_path_non_marketing_vertical(tmp_path):
    """S34: resolve_skill_path ja aceitava `vertical`, mas executor.py nunca
    o passava (sempre "marketing", hardcoded) -- partindo planos fora desse
    vertical (ex. design-flow-demo.plan.yaml). Este teste cobre o parametro
    em si; o teste de regressao do caller real esta em test_executor.py.
    """
    skill = tmp_path / "skills" / "design" / "ux_flow" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# skill design", encoding="utf-8")

    assert resolve_skill_path(tmp_path, "ux_flow", "design") == skill
    # Mesma action, vertical errado (omissao "marketing") continua a nao achar --
    # confirma que o parametro discrimina de facto, nao e um no-op.
    assert resolve_skill_path(tmp_path, "ux_flow") is None


def test_resolve_agent_path_exists(tmp_path):
    agent = tmp_path / "agents" / "marketing" / "review.agent.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("# agent", encoding="utf-8")

    result = resolve_agent_path(tmp_path, "review")
    assert result == agent


def test_read_text_if_exists_none():
    assert read_text_if_exists(None) is None


def test_read_text_if_exists_missing(tmp_path):
    assert read_text_if_exists(tmp_path / "nada.txt") is None


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_planos_fora_de_marketing_declaram_vertical_em_cada_passo_de_dominio():
    """AU-32 / S34: sem `vertical:`, o executor resolve contra "marketing"
    (executor.py:88). Fora de docs/orchestration/marketing/ isso so funciona por
    fallback; cada passo de dominio (sem human_gate) tem de declarar o seu."""
    import yaml

    faltam = []
    for plan in sorted((REPO_ROOT / "docs" / "orchestration").glob("**/*.plan.yaml")):
        if plan.relative_to(REPO_ROOT / "docs" / "orchestration").parts[0] == "marketing":
            continue
        for step in (yaml.safe_load(plan.read_text(encoding="utf-8")) or {}).get("steps") or []:
            if not step.get("human_gate") and "vertical" not in step:
                faltam.append(f"{plan.relative_to(REPO_ROOT).as_posix()}:{step.get('id')}")
    assert faltam == []


def test_design_flow_resolve_skills_e_agentes_de_design():
    """AU-32: com `vertical: design`, cada passo resolve no proprio vertical."""
    import yaml

    plan = REPO_ROOT / "docs/orchestration/design/templates/design-flow.plan.yaml"
    for step in yaml.safe_load(plan.read_text(encoding="utf-8"))["steps"]:
        if step.get("human_gate"):
            continue
        assert step["vertical"] == "design"
        skill = resolve_skill_path(REPO_ROOT, step["action"], step["vertical"])
        agent = resolve_agent_path(REPO_ROOT, step["action"], step["vertical"])
        assert skill is not None and skill.relative_to(REPO_ROOT).parts[:2] == ("skills", "design")
        assert agent is not None and agent.relative_to(REPO_ROOT).parts[:2] == ("agents", "design")
