import json
import subprocess
import sys
from pathlib import Path

PLAN = """\
| ID | Title | Status | Est | Depends |
|----|-------|--------|-----|---------|
| A1 | a | done | 1d | -  |
| A2 | b | todo | 2d | A1 |
| A3 | c | todo | 1d | A2 |
"""

CYCLE = "| ID | Title | Depends |\n|--|--|--|\n| A | a | B |\n| B | b | A |\n"

SRC = str(Path(__file__).resolve().parent.parent / "src")


def run(args, cwd):
    import os

    env = {**os.environ, "PYTHONPATH": SRC}
    return subprocess.run(
        [sys.executable, "-m", "planwright.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def write(tmp_path, text=PLAN) -> str:
    p = tmp_path / "PLAN.md"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_validate_ok(tmp_path):
    p = write(tmp_path)
    r = run(["validate", p], tmp_path)
    assert r.returncode == 0, r.stderr


def test_validate_cycle_fails(tmp_path):
    p = write(tmp_path, CYCLE)
    r = run(["validate", p], tmp_path)
    assert r.returncode == 1
    assert "cycle" in r.stdout.lower()


def test_graph_json(tmp_path):
    p = write(tmp_path)
    r = run(["graph", p, "--json"], tmp_path)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["ready"] == ["A2"]
    assert data["critical_path"]["ids"] == ["A1", "A2", "A3"]
    assert data["schedulable"] is True


def test_next(tmp_path):
    p = write(tmp_path)
    r = run(["next", p], tmp_path)
    assert r.returncode == 0
    assert r.stdout.strip() == "A2"


def test_status(tmp_path):
    p = write(tmp_path)
    r = run(["status", p], tmp_path)
    assert "3 items" in r.stdout
    assert "done 1" in r.stdout


def test_missing_file(tmp_path):
    r = run(["graph", str(tmp_path / "nope.md")], tmp_path)
    assert r.returncode == 2
