"""Fixtures e ajudas dos testes do auditron."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# Código Python com um problema que o bandit apanha em média+ (B602: subprocess com shell=True).
BAD_PY = """import subprocess


def run(cmd):
    subprocess.call(cmd, shell=True)  # o alvo do teste (shell=True)
"""

# Workflow do GitHub Actions com injecção por template (zizmor: template-injection, high).
BAD_WORKFLOW = """on: [pull_request]
jobs:
  x:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "${{ github.event.pull_request.title }}"
"""


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def requires(tool: str):
    return pytest.mark.skipif(not have(tool), reason=f"{tool} não instalado")


@pytest.fixture
def clean_repo(tmp_path: Path) -> Path:
    """Um repo sem nada para apanhar: código inócuo, sem requirements, sem workflows."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "ok.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def bad_repo(tmp_path: Path) -> Path:
    """Um repo com um problema para cada engine."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "bad.py").write_text(BAD_PY, encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("requests==2.19.0\n", encoding="utf-8")
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "bad.yml").write_text(BAD_WORKFLOW, encoding="utf-8")
    return tmp_path
