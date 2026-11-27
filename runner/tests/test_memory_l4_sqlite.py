"""L4 em SQLite (perfil de pouca capacidade): mesmo contrato do Postgres, sem servidor."""
from __future__ import annotations

import sqlite3

import pytest

from plan_runner import memory_l4 as l4
from plan_runner import memory_wiring as mw

P = l4.Scope("project", "site-x")
G = l4.Scope("global", "global")
H = "human:luiz"
A = "agent:marketing.copy"


@pytest.fixture
def conn(tmp_path):
    with l4.connect(f"sqlite:///{tmp_path / 'm.db'}") as c:
        yield c


def test_url_e_env_escolhem_sqlite(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("L4_SQLITE", str(tmp_path / "e.db"))
    assert l4.sqlite_path() == str(tmp_path / "e.db")
    assert mw.store_from_env() is not None
    monkeypatch.delenv("L4_SQLITE")
    assert mw.store_from_env() is None
    assert l4.sqlite_path("postgresql://x/y") is None
    assert l4.sqlite_path("sqlite:////abs/x.db") == "/abs/x.db"
    assert l4.sqlite_path("sqlite:///rel.db") == "rel.db"


def test_agente_escreve_candidate_e_so_humano_promove(conn):
    m = l4.remember(conn, scope=P, statement="O cliente prefere tom formal", actor=A)
    assert m["status"] == "candidate" and m["tags"] == [] and m["metadata"] == {}
    assert l4.recall(conn, scopes=[P]) == []                       # candidate não aparece por omissão
    assert len(l4.recall(conn, scopes=[P], include_candidates=True)) == 1
    with pytest.raises(l4.L4Error):
        l4.promote(conn, m["id"], actor=A)                         # agente não promove
    assert l4.promote(conn, m["id"], actor=H)["status"] == "active"
    assert [r["statement"] for r in l4.recall(conn, scopes=[P])] == ["O cliente prefere tom formal"]


def test_regras_de_ambito(conn):
    with pytest.raises(l4.ScopeError):
        l4.remember(conn, scope=G, statement="x", actor=A)         # agente não escreve em global
    with pytest.raises(l4.ScopeError):
        l4.remember(conn, scope=P, statement="x", actor=A, allowed=[l4.Scope("project", "outro")])
    with pytest.raises(l4.L4Error):
        l4.remember(conn, scope=P, statement="x", actor=A, status="active")
    with pytest.raises(l4.ScopeError):
        l4.recall(conn, scopes=[])


def test_recall_so_da_cadeia_e_filtra_tags(conn):
    l4.remember(conn, scope=P, statement="a", actor=H, status="active", tags=["seo", "pt"])
    l4.remember(conn, scope=l4.Scope("project", "outro"), statement="b", actor=H, status="active")
    assert [r["statement"] for r in l4.recall(conn, scopes=[P])] == ["a"]
    assert len(l4.recall(conn, scopes=[P], tags=["seo"])) == 1
    assert l4.recall(conn, scopes=[P], tags=["seo", "en"]) == []


def test_supersedes_e_forget_sem_apagar(conn):
    velho = l4.remember(conn, scope=P, statement="v1", actor=H, status="active")
    novo = l4.remember(conn, scope=P, statement="v2", actor=H, status="active", supersedes=velho["id"])
    assert l4.get(conn, velho["id"])["status"] == "superseded"
    assert l4.get(conn, velho["id"])["superseded_by"] == novo["id"]
    f = l4.forget(conn, novo["id"], actor=H, reason="errado")
    assert f["status"] == "archived" and f["archived_reason"] == "errado"
    assert l4.forget(conn, novo["id"], actor=H)["status"] == "archived"   # idempotente
    assert l4.recall(conn, scopes=[P]) == []
    with pytest.raises(l4.L4Error):
        l4.forget(conn, "nao-existe", actor=H)


def test_a_bd_recusa_editar_e_apagar(conn):
    m = l4.remember(conn, scope=P, statement="fixo", actor=H, status="active")
    with pytest.raises(sqlite3.IntegrityError, match="imutaveis"):
        conn.execute("UPDATE memory_l4 SET statement = 'outro' WHERE id = ?", (m["id"],))
    with pytest.raises(sqlite3.IntegrityError, match="DELETE proibido"):
        conn.execute("DELETE FROM memory_l4 WHERE id = ?", (m["id"],))


def test_expiradas_nao_saem(conn):
    from datetime import UTC, datetime, timedelta
    l4.remember(conn, scope=P, statement="velha", actor=H, status="active", expires_at=datetime.now(UTC) - timedelta(days=1))
    l4.remember(conn, scope=P, statement="viva", actor=H, status="active", expires_at=datetime.now(UTC) + timedelta(days=1))
    assert [r["statement"] for r in l4.recall(conn, scopes=[P])] == ["viva"]


def test_recall_por_similaridade_com_embedding_falso(conn):
    def emb(t: str) -> list[float]:
        return [1.0, 0.0] if "gato" in t else [0.0, 1.0]
    l4.remember(conn, scope=P, statement="fala de cão", actor=H, status="active", embed=emb)
    l4.remember(conn, scope=P, statement="fala de gato", actor=H, status="active", embed=emb)
    l4.remember(conn, scope=P, statement="sem embedding", actor=H, status="active")
    r = l4.recall(conn, scopes=[P], query="gato", embed=emb)
    assert r[0]["statement"] == "fala de gato" and r[0]["similarity"] == pytest.approx(1.0)
    assert r[-1]["statement"] == "sem embedding" and r[-1]["similarity"] is None   # sem embedding vai para o fim


def test_candidates_e_decisao_hitl(conn, tmp_path):
    a = l4.remember(conn, scope=P, statement="aprovar", actor=A)
    b = l4.remember(conn, scope=P, statement="rejeitar", actor=A)
    assert {c["id"] for c in l4.candidates(conn, scopes=[P])} == {a["id"], b["id"]}
    req = l4.request_promotion(tmp_path, [a], run_id="r", plan_id="p", step_id="s", agent_id="x")
    assert l4.decide(conn, tmp_path, req["id"], response="approve", actor=H)["results"][0]["status"] == "active"
    req2 = l4.request_promotion(tmp_path, [b], run_id="r", plan_id="p", step_id="s", agent_id="x")
    assert l4.decide(conn, tmp_path, req2["id"], response="reject", actor=H)["results"][0]["status"] == "archived"


def test_persiste_entre_ligacoes(tmp_path):
    url = f"sqlite:///{tmp_path / 'p.db'}"
    with l4.connect(url) as c:
        l4.remember(c, scope=P, statement="fica", actor=H, status="active")
    with l4.connect(url) as c:
        assert [r["statement"] for r in l4.recall(c, scopes=[P])] == ["fica"]
