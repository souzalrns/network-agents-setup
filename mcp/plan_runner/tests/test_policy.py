"""Unit tests for policy — no MCP SDK required."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_plan_runner import policy  # noqa: E402


def test_sanitize_blocks_outside(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_REPO_ROOT", str(tmp_path))
    (tmp_path / "ok.txt").write_text("x", encoding="utf-8")
    p = policy.sanitize_repo_path("ok.txt")
    assert p == (tmp_path / "ok.txt").resolve()
    with pytest.raises(PermissionError):
        policy.sanitize_repo_path(str(Path.cwd() / ".." / ".." / "etc" / "passwd"))


def test_scopes_defined():
    assert "run_plan" in policy.SCOPES
    assert policy.SCOPES["run_plan"] == "runner:plan:execute"
