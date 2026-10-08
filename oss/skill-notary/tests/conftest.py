"""Fixtures. The helpers (synthetic skills, local git "GitHub") are in helpers.py."""

from __future__ import annotations

import os
import shutil

import pytest

from skill_notary import approval

from .helpers import AGENT_VARS, LocalGitHub


@pytest.fixture
def no_agent(monkeypatch):
    """This test suite itself may run inside an AI agent; tests that approve must not."""
    for var in AGENT_VARS:
        monkeypatch.delenv(var, raising=False)
    assert approval.detect_agent(os.environ) is None


@pytest.fixture
def github(tmp_path) -> LocalGitHub:
    if shutil.which("git") is None:
        pytest.skip("git not installed")
    return LocalGitHub(tmp_path / "github")
