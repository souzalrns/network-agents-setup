import json
import subprocess
import sys
from pathlib import Path

HOOK = str(Path(__file__).resolve().parent.parent / "scripts" / "planwright_hook.py")

GOOD = "| ID | Title | Status | Est | Depends |\n|--|--|--|--|--|\n| A | a | done | 1d | - |\n"
CYCLE = "| ID | Title | Depends |\n|--|--|--|\n| A | a | B |\n| B | b | A |\n"


def run_hook(file_path: str):
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    return subprocess.run(
        [sys.executable, HOOK],
        input=payload,
        capture_output=True,
        text=True,
    )


def test_hook_passes_on_good_plan(tmp_path):
    p = tmp_path / "PLAN.md"
    p.write_text(GOOD, encoding="utf-8")
    r = run_hook(str(p))
    assert r.returncode == 0, r.stderr


def test_hook_blocks_on_cycle(tmp_path):
    p = tmp_path / "PLAN.md"
    p.write_text(CYCLE, encoding="utf-8")
    r = run_hook(str(p))
    assert r.returncode == 2
    assert "cycle" in r.stderr.lower()


def test_hook_ignores_non_plan_files(tmp_path):
    p = tmp_path / "notes.md"
    p.write_text(CYCLE, encoding="utf-8")  # broken, but not a plan file
    r = run_hook(str(p))
    assert r.returncode == 0


def test_hook_matches_dot_plan_suffix(tmp_path):
    p = tmp_path / "roadmap.plan.md"
    p.write_text(CYCLE, encoding="utf-8")
    r = run_hook(str(p))
    assert r.returncode == 2


def test_hook_survives_garbage_stdin():
    r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
    assert r.returncode == 0
