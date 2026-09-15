"""Testes do contrato HITL v1 (lado Python).

Valida que o que hitl.py escreve cumpre docs/architecture/hitl/hitl-request-v1.json
e que read_decision tolera o ficheiro ausente, linhas invalidas e varios registos.

Estilo alinhado com test_events.py (tmp_path + import absoluto de plan_runner).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from plan_runner.hitl import (
    DECISIONS_FILE,
    REQUESTS_FILE,
    SCHEMA_ID,
    build_decision,
    build_request,
    latest_request,
    read_decision,
    write_decision,
    write_request,
)

# -- Schema loading -----------------------------------------------------------

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "architecture"
    / "hitl"
    / "hitl-request-v1.json"
)


def _load_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema nao encontrado: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# -- Step/gate fakes (nao dependemos de models.py) ----------------------------

@dataclass
class _Gate:
    allow: list[str] = field(default_factory=lambda: ["approve", "reject"])
    level: str = "step"
    kind: str = "approval"


@dataclass
class _Step:
    id: str = "hitl"
    action: str = "approve"
    human_gate: _Gate = field(default_factory=_Gate)


# -- Shape --------------------------------------------------------------------

def test_build_request_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    record = build_request(
        step=_Step(),
        run_id="run_abc",
        plan_id="example-design-flow-demo",
        completed=["a", "b"],
        mode="stub",
    )
    jsonschema.validate(instance=record, schema=schema)


def test_build_request_id_format():
    record = build_request(
        step=_Step(),
        run_id="run_abc",
        plan_id="p",
        completed=[],
    )
    assert record["id"].startswith("hitl_")
    uuid_part = record["id"][len("hitl_"):]
    assert len(uuid_part) == 36
    assert uuid_part.count("-") == 4


def test_build_request_python_defaults():
    """Campos que o README diz serem 'Python-specific' ou nunca usados."""
    record = build_request(
        step=_Step(),
        run_id="r",
        plan_id="p",
        completed=[],
    )
    assert record["schema"] == SCHEMA_ID
    assert record["source"] == "plan_runner"
    assert record["status"] == "pending"
    assert record["priority"] == "medium"
    assert record["category"] is None
    assert record["expires_at"] is None
    assert record["responded_at"] is None
    assert record["response"] is None
    assert record["alternatives"] == []
    assert record["risks"] == []
    assert record["impacts"] == []


def test_build_request_context():
    record = build_request(
        step=_Step(id="s1", action="publish"),
        run_id="r",
        plan_id="p",
        completed=["x", "y"],
        mode="external",
    )
    assert record["context"]["paused_at_step"] == "s1"
    assert record["context"]["completed"] == ["x", "y"]
    assert record["context"]["mode"] == "external"
    assert record["proposed_action"] == "publish"


def test_build_request_allow_filtered_to_enum():
    record = build_request(
        step=_Step(human_gate=_Gate(allow=["approve", "edit"])),
        run_id="r",
        plan_id="p",
        completed=[],
    )
    assert record["allow"] == ["approve", "edit"]


def test_build_request_allow_fallback_when_empty():
    record = build_request(
        step=_Step(human_gate=_Gate(allow=[])),
        run_id="r",
        plan_id="p",
        completed=[],
    )
    assert record["allow"] == ["approve", "reject"]


# -- Write / read -------------------------------------------------------------

def test_write_request_creates_files(tmp_path: Path):
    hitl_id = write_request(
        tmp_path,
        step=_Step(),
        run_id="r",
        plan_id="p",
        completed=[],
    )
    assert hitl_id.startswith("hitl_")
    assert (tmp_path / REQUESTS_FILE).exists()
    assert not (tmp_path / DECISIONS_FILE).exists()


def test_write_request_appends(tmp_path: Path):
    ids = [
        write_request(tmp_path, step=_Step(id=f"s{i}"), run_id="r", plan_id="p", completed=[])
        for i in range(3)
    ]
    lines = (tmp_path / REQUESTS_FILE).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert [json.loads(line)["id"] for line in lines] == ids


def test_latest_request(tmp_path: Path):
    assert latest_request(tmp_path) is None
    write_request(tmp_path, step=_Step(id="first"), run_id="r", plan_id="p", completed=[])
    write_request(tmp_path, step=_Step(id="second"), run_id="r", plan_id="p", completed=[])
    last = latest_request(tmp_path)
    assert last is not None
    assert last["context"]["paused_at_step"] == "second"


# -- read_decision ------------------------------------------------------------

def test_read_decision_missing_file(tmp_path: Path):
    assert read_decision(tmp_path) is None


def test_read_decision_skips_blank_and_invalid(tmp_path: Path):
    path = tmp_path / DECISIONS_FILE
    path.write_text(
        "\n"
        + "not json\n"
        + json.dumps({"id": "hitl_x", "response": "approve"}) + "\n"
        + "\n",
        encoding="utf-8",
    )
    decision = read_decision(tmp_path)
    assert decision is not None
    assert decision["response"] == "approve"


def test_read_decision_last_wins(tmp_path: Path):
    write_decision(tmp_path, "hitl_a", response="reject")
    write_decision(tmp_path, "hitl_b", response="approve", comment="ok")
    decision = read_decision(tmp_path)
    assert decision is not None
    assert decision["id"] == "hitl_b"
    assert decision["response"] == "approve"
    assert decision["response_comment"] == "ok"


def test_read_decision_ignores_unknown_response(tmp_path: Path):
    path = tmp_path / DECISIONS_FILE
    path.write_text(
        json.dumps({"id": "hitl_a", "response": "maybe"}) + "\n"
        + json.dumps({"id": "hitl_b", "response": "reject"}) + "\n",
        encoding="utf-8",
    )
    decision = read_decision(tmp_path)
    assert decision is not None
    assert decision["id"] == "hitl_b"


# -- build_decision / write_decision ------------------------------------------

def test_build_decision_rejects_invalid_response():
    with pytest.raises(ValueError):
        build_decision("hitl_x", response="maybe")


def test_write_decision_roundtrip(tmp_path: Path):
    write_decision(
        tmp_path,
        "hitl_x",
        response="edit",
        responder_id="cli",
        comment="tweak",
    )
    decision = read_decision(tmp_path)
    assert decision is not None
    assert decision["id"] == "hitl_x"
    assert decision["response"] == "edit"
    assert decision["responder_id"] == "cli"
    assert decision["response_comment"] == "tweak"
    assert decision["responded_at"] is not None
