"""The command line: exit codes (README, "Exit codes"), output formats, `python -m skill_scout`."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from skill_scout import __version__, cli
from skill_scout import install as inst
from skill_scout.errors import (
    EXIT_APPROVAL,
    EXIT_BLOCKED,
    EXIT_ENGINE,
    EXIT_FINDINGS,
    EXIT_OK,
    EXIT_USAGE,
    EXIT_VERIFY,
)
from skill_scout.treehash import tree_hash

from .helpers import make_dangerous, make_risky, make_safe, monorepo


@pytest.mark.parametrize(
    "maker, fail_on, code",
    [
        (make_safe, "high", EXIT_OK),
        (make_risky, "high", EXIT_OK),
        (make_risky, "medium", EXIT_FINDINGS),
        (make_dangerous, "high", EXIT_FINDINGS),
        (make_dangerous, "none", EXIT_OK),
    ],
)
def test_scan_exit_codes(tmp_path, capsys, maker, fail_on, code):
    d = maker(tmp_path / "s")
    assert cli.main(["scan", str(d), "--fail-on", fail_on]) == code
    out = capsys.readouterr().out
    assert tree_hash(d).digest in out and "verdict:" in out


def test_scan_json_and_sarif_files(tmp_path, monkeypatch):
    monorepo(tmp_path / "repo" / "skills")
    monkeypatch.chdir(tmp_path / "repo")
    assert cli.main(["scan", "./skills", "--format", "json", "-o", "r.json", "--fail-on", "none"]) == EXIT_OK
    doc = json.loads((tmp_path / "repo" / "r.json").read_text())
    assert doc["verdict"] == "dangerous" and doc["source"]["spec"] == "./skills" and len(doc["skills"]) == 3
    assert (
        cli.main(
            ["scan", "./skills", "--format", "sarif", "-o", "r.sarif", "--fail-on", "none", "--category", "skills"]
        )
        == EXIT_OK
    )
    sarif = json.loads((tmp_path / "repo" / "r.sarif").read_text())
    run = sarif["runs"][0]
    assert run["automationDetails"]["id"] == "skills/"
    assert all(
        r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"].startswith("skills/skills/")
        for r in run["results"]
    )


def test_scan_github_source_selects_the_skill(tmp_path, github, monkeypatch, capsys):
    github.repo("acme", "skills", monorepo)
    real_fetch = cli.fetch
    monkeypatch.setattr(cli, "fetch", lambda src, dest: real_fetch(src, dest, base_url=github.base_url))
    assert cli.main(["scan", "acme/skills@good", "--format", "json"]) == EXIT_OK
    doc = json.loads(capsys.readouterr().out)
    assert doc["source"]["skill_path"] == "skills/good" and len(doc["source"]["commit"]) == 40
    assert cli.main(["scan", "acme/skills@ghost"]) == EXIT_USAGE


def test_engine_failure_exit_code(tmp_path, monkeypatch):
    from skill_scout import engines

    monkeypatch.setattr(engines, "_run_json", lambda cmd, name: ({}, 2))
    assert cli.main(["scan", str(make_safe(tmp_path / "s"))]) == EXIT_ENGINE


def test_usage_errors(tmp_path, capsys):
    assert cli.main(["scan", "not a source"]) == EXIT_USAGE
    assert cli.main(["scan", str(tmp_path), "--engine", "nope"]) == EXIT_ENGINE
    assert "skill-scout:" in capsys.readouterr().err


def test_install_and_verify_through_the_cli(tmp_path, monkeypatch, no_agent, capsys):
    src = make_safe(tmp_path / "src", name="good")
    monkeypatch.chdir(tmp_path)
    digest = tree_hash(src).digest
    assert cli.main(["install", "./src"]) == EXIT_APPROVAL  # no TTY, no flag
    assert cli.main(["install", "./src", "--approve-sha256", digest]) == EXIT_OK
    assert "installed good" in capsys.readouterr().out
    assert cli.main(["verify", "--dest", ".claude/skills"]) == EXIT_OK
    capsys.readouterr()
    assert cli.main(["verify", "--format", "json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {"ok": True, "checked": 1, "problems": [], "unmanaged": []}
    (tmp_path / ".claude" / "skills" / "good" / "SKILL.md").write_text("tampered")
    assert cli.main(["verify"]) == EXIT_VERIFY
    assert "drifted" in capsys.readouterr().out


def test_install_blocked_exit_code(tmp_path, monkeypatch, no_agent):
    src = make_dangerous(tmp_path / "src")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install", "./src", "--approve-sha256", tree_hash(src).digest]) == EXIT_BLOCKED


def test_install_refused_in_this_agent_environment(tmp_path, monkeypatch):
    """Not mocked: when this suite runs inside an AI agent, the real environment must refuse."""
    import os

    from skill_scout.approval import detect_agent

    if detect_agent(os.environ) is None:
        monkeypatch.setenv("AI_AGENT", "test-agent")
    src = make_safe(tmp_path / "src", name="good")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install", "./src", "--approve-sha256", tree_hash(src).digest]) == EXIT_APPROVAL
    assert not (tmp_path / ".claude" / "skills" / "good").exists()


def test_version_and_python_dash_m(tmp_path):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    out = subprocess.run([sys.executable, "-m", "skill_scout", "--version"], capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == f"skill-scout {__version__}"
    d = make_risky(tmp_path / "s")
    run = subprocess.run(
        [sys.executable, "-m", "skill_scout", "scan", str(d), "--fail-on", "medium"], capture_output=True, text=True
    )
    assert run.returncode == EXIT_FINDINGS and "RISKY" in run.stdout


def test_default_destination_is_claude_project_skills():
    assert inst.DEFAULT_DEST == ".claude/skills"
