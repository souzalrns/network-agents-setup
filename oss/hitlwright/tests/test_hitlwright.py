"""hitlwright: the typed HITL contract (build/write/read + schema validity)."""

from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator

from hitlwright import (
    SCHEMA_ID,
    VALID_DECISIONS,
    build_decision,
    build_request,
    latest_request,
    pending_request,
    read_decision,
    schema_path,
    write_decision,
    write_request,
)


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# ---- build_request ----


def test_build_request_matches_schema(validator):
    rec = build_request(step_id="publish", action="publish", run_id="run_1", completed=["a", "b"])
    validator.validate(rec)
    assert rec["schema"] == SCHEMA_ID
    assert rec["id"].startswith("hitl_")
    assert rec["status"] == "pending"
    assert rec["allow"] == ["approve", "reject"]
    assert rec["context"] == {"paused_at_step": "publish", "completed": ["a", "b"]}


def test_build_request_filters_allow_and_keeps_edit():
    rec = build_request(step_id="s", allow=["approve", "edit", "bogus"])
    assert rec["allow"] == ["approve", "edit"]


def test_build_request_empty_allow_falls_back():
    rec = build_request(step_id="s", allow=["bogus"])
    assert rec["allow"] == ["approve", "reject"]


def test_build_request_bad_priority():
    with pytest.raises(ValueError):
        build_request(step_id="s", priority="urgent")


def test_build_request_title_and_mode(validator):
    rec = build_request(step_id="s", action="spend", mode="opt", title="Approve spend")
    validator.validate(rec)
    assert rec["title"] == "Approve spend"
    assert rec["context"]["mode"] == "opt"


def test_build_request_default_title():
    assert build_request(step_id="s", action="go")["title"] == "Approve step 's' (go)"
    assert build_request(step_id="s")["title"] == "Approve step 's'"
    assert build_request(step_id=None)["title"] == "Approve HITL gate"


# ---- write/read round trip ----


def test_write_then_read_decision(tmp_path):
    rid = write_request(tmp_path, step_id="publish", action="publish")
    assert read_decision(tmp_path) is None  # nothing decided yet
    write_decision(tmp_path, rid, response="approve", responder_id="user:ana", comment="ok")
    dec = read_decision(tmp_path)
    assert dec["id"] == rid and dec["response"] == "approve" and dec["responder_id"] == "user:ana"


def test_last_decision_wins(tmp_path):
    rid = write_request(tmp_path, step_id="s")
    write_decision(tmp_path, rid, response="reject")
    write_decision(tmp_path, rid, response="approve")
    assert read_decision(tmp_path)["response"] == "approve"


def test_append_only_keeps_history(tmp_path):
    write_request(tmp_path, step_id="a")
    write_request(tmp_path, step_id="b")
    lines = (tmp_path / "hitl-requests.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # nothing overwritten


def test_read_tolerates_blank_and_bad_lines(tmp_path):
    rid = write_request(tmp_path, step_id="s")
    path = tmp_path / "hitl-decisions.jsonl"
    path.write_text("\n{bad json\n" + json.dumps({"id": rid, "response": "approve"}) + "\n", encoding="utf-8")
    assert read_decision(tmp_path)["response"] == "approve"


def test_latest_and_pending(tmp_path):
    r1 = write_request(tmp_path, step_id="s1")
    r2 = write_request(tmp_path, step_id="s2")
    assert latest_request(tmp_path)["id"] == r2
    assert pending_request(tmp_path)["id"] == r2  # newest undecided
    write_decision(tmp_path, r2, response="approve")
    assert pending_request(tmp_path)["id"] == r1  # r2 decided, r1 still pending
    write_decision(tmp_path, r1, response="reject")
    assert pending_request(tmp_path) is None  # all decided


# ---- build_decision ----


def test_build_decision_rejects_bad_response():
    with pytest.raises(ValueError):
        build_decision("hitl_x", response="maybe")


def test_build_decision_shape():
    d = build_decision("hitl_x", response="edit", responder_id="cli", comment="tweak")
    assert d == {
        "id": "hitl_x",
        "response": "edit",
        "responder_id": "cli",
        "response_comment": "tweak",
        "responded_at": d["responded_at"],
    }
    assert "edit" in VALID_DECISIONS


# ---- CLI ----


def test_cli_request_decide_pending_decision(tmp_path, capsys):
    from hitlwright.cli import main

    assert main(["request", str(tmp_path), "--step", "publish", "--action", "publish"]) == 0
    rid = capsys.readouterr().out.strip()
    assert rid.startswith("hitl_")

    assert main(["pending", str(tmp_path)]) == 0  # something pending
    capsys.readouterr()

    assert main(["decide", str(tmp_path), rid, "--response", "approve", "--by", "user:ana"]) == 0
    capsys.readouterr()

    assert main(["decision", str(tmp_path)]) == 0
    assert "approve" in capsys.readouterr().out
    assert main(["pending", str(tmp_path)]) == 1  # nothing pending now


def test_cli_decision_none(tmp_path):
    from hitlwright.cli import main

    assert main(["decision", str(tmp_path)]) == 1


def test_cli_version(capsys):
    from hitlwright.cli import main

    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "hitlwright" in capsys.readouterr().out
