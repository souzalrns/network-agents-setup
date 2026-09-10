"""Testes de skills.py: resolucao de paths e leitura tolerante."""
from __future__ import annotations

from pathlib import Path

import pytest

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
