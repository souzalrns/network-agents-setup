"""Unit tests for policy — no MCP SDK required."""

from __future__ import annotations

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
    outside = tmp_path.parent / "other_secret.txt"
    outside.write_text("no", encoding="utf-8")
    with pytest.raises(PermissionError):
        policy.sanitize_repo_path(str(outside))


def test_moderate_allows_mutate_without_key(monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_MCP_PROFILE", "moderate")
    monkeypatch.delenv("PLAN_RUNNER_MCP_KEY", raising=False)
    monkeypatch.delenv("PLAN_RUNNER_MCP_ALLOW_MUTATE", raising=False)
    ctx = policy.authorize("run_plan")
    assert ctx.authorized is True


def test_strict_blocks_mutate_without_key(monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_MCP_PROFILE", "strict")
    monkeypatch.delenv("PLAN_RUNNER_MCP_KEY", raising=False)
    monkeypatch.delenv("PLAN_RUNNER_MCP_ALLOW_MUTATE", raising=False)
    ctx = policy.authorize("run_plan")
    assert ctx.authorized is False


def test_scopes_defined():
    assert policy.SCOPES["run_plan"] == "runner:plan:execute"


def test_moderate_lab_open_warns(monkeypatch):
    """SECURITY-AUDIT.md 2026-09-17 (LLM03/Excessive Agency): o caminho
    moderate-sem-chave continua autorizado (ver test_moderate_allows_mutate_without_key,
    que fixa esse comportamento), mas agora tem de emitir um aviso explicito --
    mitigacao parcial, nao o fecho completo do achado.
    """
    monkeypatch.setenv("PLAN_RUNNER_MCP_PROFILE", "moderate")
    monkeypatch.delenv("PLAN_RUNNER_MCP_KEY", raising=False)
    monkeypatch.delenv("PLAN_RUNNER_MCP_ALLOW_MUTATE", raising=False)
    with pytest.warns(UserWarning, match="moderate"):
        ctx = policy.authorize("run_plan")
    assert ctx.authorized is True
    assert ctx.reason == "moderate_lab_open"
