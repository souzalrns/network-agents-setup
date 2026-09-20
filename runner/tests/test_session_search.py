"""Testes do indice FTS5 sobre events.jsonl (B11/M1)."""
from __future__ import annotations

from pathlib import Path

from plan_runner.events import EventLog
from plan_runner.session_search import build_index, search


def _make_events(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run_1"
    log = EventLog(run_dir / "events.jsonl")
    log.append("step_started", "run_1", {"step_id": "seo_brief", "action": "seo_brief"})
    log.append("step_finished", "run_1", {"step_id": "seo_brief", "detail": "ok", "artifact": "artifacts/02-seo-brief.json"})
    log.append("human_gate_requested", "run_1", {"step_id": "hitl", "kind": "output_review"})
    log.append("step_failed", "run_1", {"step_id": "critic", "detail": "timeout ao chamar MCP"})
    return run_dir


def test_build_index_creates_db_file(tmp_path):
    run_dir = _make_events(tmp_path)
    index_path = build_index(run_dir)
    assert index_path.exists()
    assert index_path.name == "events_fts.db"


def test_search_finds_only_matching_event_no_false_positives(tmp_path):
    run_dir = _make_events(tmp_path)
    build_index(run_dir)

    hits = search(run_dir, "timeout")
    assert len(hits) == 1
    assert hits[0]["type"] == "step_failed"
    assert "timeout" in hits[0]["payload"]["detail"]


def test_search_by_step_id_finds_multiple_real_hits(tmp_path):
    run_dir = _make_events(tmp_path)
    build_index(run_dir)

    hits = search(run_dir, "seo_brief")
    assert len(hits) == 2
    assert {h["type"] for h in hits} == {"step_started", "step_finished"}


def test_search_term_absent_from_all_events_returns_empty(tmp_path):
    run_dir = _make_events(tmp_path)
    build_index(run_dir)

    assert search(run_dir, "termo_que_nao_existe_em_nenhum_evento") == []


def test_search_auto_builds_index_if_missing(tmp_path):
    run_dir = _make_events(tmp_path)
    # Sem chamar build_index() primeiro -- search() deve indexar sozinho.
    hits = search(run_dir, "hitl")
    assert len(hits) == 1
    assert hits[0]["type"] == "human_gate_requested"


def test_rebuild_index_is_idempotent_after_new_events(tmp_path):
    run_dir = _make_events(tmp_path)
    build_index(run_dir)
    assert search(run_dir, "critic") == [] or len(search(run_dir, "critic")) == 1

    log = EventLog(run_dir / "events.jsonl")
    log.append("step_started", "run_1", {"step_id": "critic", "action": "critic_item13"})
    build_index(run_dir)  # reindexa do zero

    hits = search(run_dir, "critic")
    assert len(hits) == 2


def test_missing_events_jsonl_yields_empty_index(tmp_path):
    run_dir = tmp_path / "run_empty"
    run_dir.mkdir()
    build_index(run_dir)
    assert search(run_dir, "qualquer") == []
