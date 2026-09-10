"""Testes de events.py: has_event tolera ficheiro ausente e linhas invalidas."""
from __future__ import annotations

import json
from pathlib import Path

from plan_runner.events import EventLog


def test_has_event_returns_false_when_file_missing(tmp_path):
    log = EventLog(tmp_path / "nao-existe.jsonl")
    assert log.has_event("x", "run-1") is False


def test_has_event_skips_blank_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n\n"
        + json.dumps({"type": "foo", "run_id": "run-1", "payload": {}}) + "\n"
        + "\n",
        encoding="utf-8",
    )
    log = EventLog(path)
    assert log.has_event("foo", "run-1") is True


def test_has_event_with_match(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps({"type": "step_started", "run_id": "r1", "payload": {"step_id": "a"}}) + "\n",
        encoding="utf-8",
    )
    log = EventLog(path)
    assert log.has_event("step_started", "r1", step_id="a") is True
    assert log.has_event("step_started", "r1", step_id="b") is False
    assert log.has_event("other", "r1", step_id="a") is False
