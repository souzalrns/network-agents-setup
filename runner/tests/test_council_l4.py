"""Bloco C + L4 real: o veredicto do conselho entra na memory_l4 como candidate e o HITL promove-o.

Postgres descartavel com pgvector (RAG_TEST_DATABASE_URL; no CI o job test-rag) e
Gemini falso. E o criterio de DONE do Bloco C: conselho architecture de ponta a
ponta, veredicto estruturado, HITL aprovado, L4 candidate -> active.
"""
from __future__ import annotations

from contextlib import contextmanager

import pytest

psycopg = pytest.importorskip("psycopg")

from psycopg.rows import dict_row  # noqa: E402

from plan_runner import council_session as cs  # noqa: E402
from plan_runner import hitl  # noqa: E402
from plan_runner import memory_l4 as l4  # noqa: E402
from plan_runner import memory_wiring as mw  # noqa: E402
from tests.test_council import TOPIC, CouncilGemini, default_position  # noqa: E402
from tests.test_memory_l4 import DB_URL, fake_embed  # noqa: E402

pytestmark = pytest.mark.skipif(not DB_URL, reason="RAG_TEST_DATABASE_URL nao definida (ver test_memory_l4.py)")

SCOPE = l4.Scope("project", "network-agents-setup")


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def store(l4_opts):
    @contextmanager
    def connect():
        conn = psycopg.connect(DB_URL, autocommit=False, row_factory=dict_row, options=l4_opts)
        try:
            yield conn
        finally:
            conn.close()

    return mw.MemoryStore(connect=connect, embed=fake_embed)


def _session(tmp_path, store, gemini=None):
    return cs.CouncilSession(tmp_path / "council", deps=cs.CouncilDeps(transport=gemini or CouncilGemini(), memory=store))


def test_done_bloco_c_architecture_candidate_para_active(tmp_path, store, db):
    s = _session(tmp_path, store)
    out = s.start("architecture", TOPIC, context="Hoje: langgraph-checkpoint-sqlite (runner/requirements-langgraph.txt).")
    assert out["status"] == "awaiting_human" and out["gate"]["result"] == "pass"
    mid = out["memory"]["id"]
    row = l4.get(db, mid)
    assert row["status"] == "candidate" and row["created_by"] == "agent:meta.chairman"
    assert (row["scope_kind"], row["scope_id"]) == (SCOPE.kind, SCOPE.id) and row["subject"] == "council:architecture"
    assert row["source_run_id"] == s.state["session_id"] and "decision:approve" in row["tags"]
    assert row["metadata"]["verdict"]["decision"] == "approve" and row["metadata"]["gate"]["result"] == "pass"
    assert float(row["confidence"]) == 0.85
    # candidate nao sai no recall normal
    assert l4.recall(db, scopes=[SCOPE]) == []

    s.decide("approve", actor="maestro")
    row = l4.get(db, mid)
    assert row["status"] == "active" and row["promoted_by"] == "human:maestro"
    hits = l4.recall(db, scopes=[SCOPE], query="checkpoints postgres")
    assert [str(h["id"]) for h in hits] == [mid]
    assert hitl.read_decision(s.out)["response"] == "approve"
    assert (s.out / mw.TRACE_FILE).is_file()


def test_reject_arquiva_o_candidate(tmp_path, store, db):
    s = _session(tmp_path, store)
    mid = s.start("architecture", TOPIC)["memory"]["id"]
    s.decide("reject", actor="maestro", comment="nao agora")
    row = l4.get(db, mid)
    assert row["status"] == "archived" and row["archived_by"] == "human:maestro" and "nao agora" in row["archived_reason"]


def test_revise_arquiva_e_a_nova_ronda_grava_outro_candidate(tmp_path, store, db):
    s = _session(tmp_path, store)
    first = s.start("architecture", TOPIC)["memory"]["id"]
    out = s.decide("revise", actor="maestro", comment="mede o custo")
    second = out["memory"]["id"]
    assert second != first and l4.get(db, first)["status"] == "archived" and l4.get(db, second)["status"] == "candidate"


def test_veto_nunca_chega_a_active(tmp_path, store, db):
    pos = {"meta.arquitetura-agentes": {**default_position("x"), "vote": "reject", "veto": True}}
    s = _session(tmp_path, store, CouncilGemini(positions=pos))
    mid = s.start("architecture", TOPIC)["memory"]["id"]
    with pytest.raises(cs.CouncilError):
        s.decide("approve", actor="maestro")
    assert l4.get(db, mid)["status"] == "candidate" and "gate:veto" in l4.get(db, mid)["tags"]


def test_ambito_acima_do_permitido_e_recusado(tmp_path, store):
    with pytest.raises(cs.CouncilError, match="so escreve candidate"):
        _session(tmp_path, store).start("architecture", TOPIC, scope="org:lrns")
