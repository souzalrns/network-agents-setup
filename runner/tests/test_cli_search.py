"""S31 -- expoe session_search.py (B11/M1) via `plan_runner search`.

Ate esta correcao, session_search.py so tinha o seu proprio CLI standalone
(`python -m plan_runner.session_search`), nunca ligado ao resto do runner
(nem `engine.py`/`langgraph_engine.py`, nem uma tool MCP). Este teste cobre
o novo subcomando `search` do CLI principal (`python -m plan_runner search`),
Opcao A do brief do S31 -- a mais simples, sem tocar em `mcp_plan_runner/`.

Mesmo padrao de fixtures de test_session_search.py (EventLog.append() real,
tokens sem hifen para nao depender de detalhe do tokenizador FTS5).
search()/build_index() nao exigem run_dir dentro de pilots/ (sem
_validate_out_dir) -- por isso um tmp_path isolado chega, sem subprocess
a correr um plano real.
"""
from __future__ import annotations

import json
from pathlib import Path

from plan_runner.events import EventLog

from tests.conftest import RUNNER_DIR, _run_cli


def _make_events(run_dir: Path) -> None:
    log = EventLog(run_dir / "events.jsonl")
    log.append("step_finished", "r1", {"step_id": "ux", "artifact": "artifacts/01_ux_flow.md"})
    log.append("step_finished", "r1", {"step_id": "critic", "artifact": "artifacts/04_design_critic.json"})


def test_cli_search_finds_matching_event(tmp_path):
    _make_events(tmp_path)

    proc = _run_cli(["search", str(tmp_path), "ux_flow"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, proc.stderr

    hits = json.loads(proc.stdout)["hits"]
    assert len(hits) == 1
    assert hits[0]["payload"]["step_id"] == "ux"


def test_cli_search_no_match_returns_empty(tmp_path):
    _make_events(tmp_path)

    proc = _run_cli(["search", str(tmp_path), "termo_que_nao_existe"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["hits"] == []


def test_cli_search_auto_indexes_without_prior_build(tmp_path):
    """search() auto-indexa se events_fts.db ainda nao existir -- confirma
    que o subcomando novo nao exige correr `session_search.py` a parte primeiro."""
    _make_events(tmp_path)
    assert not (tmp_path / "events_fts.db").exists()

    proc = _run_cli(["search", str(tmp_path), "critic"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)["hits"]) == 1
    assert (tmp_path / "events_fts.db").exists()
