"""done-when: acceptance by evidence (the two verifiable forms + unverifiable)."""

from __future__ import annotations

import json

import pytest

from done_when import evaluate, is_satisfied
from done_when.cli import main

# ---- form 1: "<path> exists"


def test_exists_passes_when_file_present(tmp_path):
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "r.md").write_text("x", encoding="utf-8")
    r = evaluate(tmp_path, ["artifacts/r.md exists"])
    assert r == {"passed": [{"kind": "file_exists", "target": "artifacts/r.md"}], "failed": [], "unverifiable": []}
    assert is_satisfied(r)


def test_exists_fails_with_reason_when_missing(tmp_path):
    r = evaluate(tmp_path, ["artifacts/zz.md exists"])
    assert r["passed"] == [] and r["unverifiable"] == []
    assert r["failed"] == [
        {
            "kind": "file_exists",
            "target": "artifacts/zz.md",
            "condition": "artifacts/zz.md exists",
            "reason": "file missing",
        }
    ]
    assert not is_satisfied(r)


def test_exists_outside_root_fails(tmp_path):
    r = evaluate(tmp_path, ["../secret.md exists"])
    assert r["failed"][0]["reason"] == "path outside the run directory"
    assert not is_satisfied(r)


def test_directory_is_not_a_file(tmp_path):
    (tmp_path / "artifacts").mkdir()
    r = evaluate(tmp_path, ["artifacts exists"])
    assert r["failed"][0]["reason"] == "file missing"


# ---- form 2: "human_gate_resolved on <step>"


def test_gate_passes_when_resolver_says_so(tmp_path):
    r = evaluate(tmp_path, ["human_gate_resolved on hitl"], gate_resolved=lambda step: step == "hitl")
    assert r["passed"] == [{"kind": "gate_resolved", "target": "hitl"}]
    assert is_satisfied(r)


def test_gate_fails_closed_by_default(tmp_path):
    r = evaluate(tmp_path, ["human_gate_resolved on hitl"])
    assert r["failed"] == [
        {
            "kind": "gate_resolved",
            "target": "hitl",
            "condition": "human_gate_resolved on hitl",
            "reason": "gate not resolved",
        }
    ]


def test_passed_items_drop_the_literal_gate_text(tmp_path):
    """A reader scanning for 'human_gate_resolved' must not match an accepted condition."""
    r = evaluate(tmp_path, ["human_gate_resolved on hitl"], gate_resolved=lambda _s: True)
    assert "human_gate_resolved" not in json.dumps(r["passed"])


# ---- form 3: unverifiable — reported, never failed


def test_unknown_shape_is_unverifiable_not_failed(tmp_path):
    cond = "no ad_account_mutation without approve"
    r = evaluate(tmp_path, [cond, "x.md exists"])
    assert r["unverifiable"] == [cond]
    # the free-text condition does not fail the set; only the missing file does
    assert [f["kind"] for f in r["failed"]] == ["file_exists"]


def test_empty_conditions_is_satisfied(tmp_path):
    assert evaluate(tmp_path, []) == {"passed": [], "failed": [], "unverifiable": []}
    assert is_satisfied(evaluate(tmp_path, []))


# ---- autonomy test: no event store, no external deps


def test_runs_with_no_gate_resolver_and_pure_stdlib(tmp_path):
    (tmp_path / "a").write_text("1", encoding="utf-8")
    r = evaluate(tmp_path, ["a exists", "human_gate_resolved on g", "free text"])
    assert r["passed"] == [{"kind": "file_exists", "target": "a"}]
    assert r["failed"][0]["kind"] == "gate_resolved"
    assert r["unverifiable"] == ["free text"]


# ---- CLI


def test_cli_exit_0_when_satisfied(tmp_path, capsys):
    (tmp_path / "a").write_text("1", encoding="utf-8")
    assert main(["check", str(tmp_path), "a exists"]) == 0
    assert "satisfied" in capsys.readouterr().out


def test_cli_exit_1_when_failed(tmp_path, capsys):
    assert main(["check", str(tmp_path), "missing exists"]) == 1
    assert "FAILED" in capsys.readouterr().out


def test_cli_resolved_flag(tmp_path):
    assert main(["check", str(tmp_path), "human_gate_resolved on hitl", "--resolved", "hitl"]) == 0


def test_cli_unverifiable_does_not_fail(tmp_path):
    assert main(["check", str(tmp_path), "something free"]) == 0


def test_cli_json_output(tmp_path, capsys):
    main(["check", str(tmp_path), "missing exists", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["failed"][0]["target"] == "missing"


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "done-when" in capsys.readouterr().out
