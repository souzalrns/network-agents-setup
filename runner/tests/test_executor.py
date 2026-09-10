"""Testes de executor.py: ramos de erro do external + stub artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner.executor import execute_external_request, execute_stub
from plan_runner.models import HumanGate, Step


def test_execute_stub_with_human_gate(tmp_path):
    step = Step(id="hitl", action="approve", human_gate=HumanGate())
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.detail == "awaiting_human_gate"
    assert result.artifact is None


def test_execute_stub_writes_json_artifact(tmp_path):
    step = Step(id="a", action="do", output_artifact="artifacts/a.json")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.detail == "stub_ok"
    # Normalizar separadores (Windows devolve \, POSIX devolve /)
    assert result.artifact.replace("\\", "/") == "artifacts/a.json"
    body = json.loads((tmp_path / "artifacts/a.json").read_text(encoding="utf-8"))
    assert body["_stub"] is True
    assert body["step_id"] == "a"


def test_execute_stub_writes_md_artifact(tmp_path):
    step = Step(id="a", action="do", output_artifact="artifacts/note.md")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    text = (tmp_path / "artifacts/note.md").read_text(encoding="utf-8")
    assert "Stub: a" in text


def test_execute_stub_no_artifact(tmp_path):
    step = Step(id="a", action="do")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.artifact is None


def test_external_waits_when_no_result_json(tmp_path):
    step = Step(id="prep", action="prep")
    result = execute_external_request(tmp_path, step)
    assert result.ok is False
    assert result.detail == "waiting_external"
    req = tmp_path / "pending_steps" / "prep" / "request.json"
    assert req.exists()


def test_external_ok_with_artifact_content_dict(tmp_path):
    step = Step(id="prep", action="prep", output_artifact="artifacts/prep.json")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True, "artifact_content": {"k": "v"}}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert result.detail == "external_ok"
    assert result.artifact == "artifacts/prep.json"
    body = json.loads((tmp_path / "artifacts/prep.json").read_text(encoding="utf-8"))
    assert body == {"k": "v"}


def test_external_ok_with_artifact_content_str(tmp_path):
    step = Step(id="prep", action="prep", output_artifact="artifacts/prep.md")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True, "artifact_content": "# hello"}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert (tmp_path / "artifacts/prep.md").read_text(encoding="utf-8") == "# hello"


def test_external_fails_when_ok_false(tmp_path):
    step = Step(id="prep", action="prep")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": False, "detail": "boom"}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is False
    assert result.detail == "boom"


def test_external_ok_no_artifact(tmp_path):
    step = Step(id="prep", action="prep")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert result.detail == "external_ok_no_artifact"
