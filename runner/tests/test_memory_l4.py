"""L4 (D3): memory_l4.py + scripts/create_memory_l4_table.sql + create_recall_l4_rpc.sql.

Corre contra um Postgres DESCARTAVEL com pgvector (RAG_TEST_DATABASE_URL; no CI,
o servico do job test-rag). Nunca o DATABASE_URL de producao. Cada teste aplica
o SQL versionado (duas vezes: idempotencia) num schema proprio e apaga-o no fim.
Com RAG_TEST_REQUIRED=1 (CI), a falta da BD e erro, nao skip.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from plan_runner import memory_l4 as l4  # noqa: E402
from plan_runner.memory_l4 import L4Error, Scope, ScopeError  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_FILES = [REPO_ROOT / "scripts/create_memory_l4_table.sql", REPO_ROOT / "scripts/create_recall_l4_rpc.sql"]
DB_URL = os.environ.get("RAG_TEST_DATABASE_URL", "").strip()
if os.environ.get("RAG_TEST_REQUIRED") == "1" and not DB_URL:
    raise RuntimeError("RAG_TEST_REQUIRED=1 mas RAG_TEST_DATABASE_URL nao esta definida")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida: a L4 precisa de um Postgres descartavel com pgvector "
    "(nunca o Supabase de producao). Ver docs/ops/MEMORY-L4.md",
)

AGENT = "agent:marketing.copy_social"
HUMAN = "human:maestro"
P_A, P_B = Scope("project", "site-a"), Scope("project", "site-b")
AG = Scope("agent", "marketing.copy_social")


def _vec(i: int) -> list[float]:
    return [1.0 if d == i else 0.001 for d in range(768)]


def fake_embed(text: str) -> list[float]:
    """Determinista: o primeiro digito do texto escolhe a direccao (sem Gemini)."""
    digits = [c for c in text if c.isdigit()]
    return _vec(int(digits[0]) if digits else 0)


def _count(conn, where: str = "true", params: tuple = ()) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS n FROM memory_l4 WHERE {where}", params)
        n = cur.fetchone()["n"]
    conn.commit()
    return n


# --------------------------------------------------------------------------
# Ciclo completo: remember -> recall -> promote -> forget
# --------------------------------------------------------------------------

def test_ciclo_remember_recall_promote_forget(db):
    row = l4.remember(db, scope=P_A, statement="O cliente prefere tom formal [Fonte: run_x]", actor=AGENT,
                      subject="tom", confidence=0.8, source_run_id="run_x", tags=["tom"], allowed=[P_A, AG])
    assert row["status"] == "candidate" and row["created_by"] == AGENT

    # recall devolve o mesmo facto (candidates so a pedido; o worker nao as injecta)
    assert l4.recall(db, scopes=[P_A]) == []
    [hit] = l4.recall(db, scopes=[P_A], include_candidates=True)
    assert (hit["id"], hit["statement"], hit["confidence"], hit["source_run_id"]) == (
        row["id"], row["statement"], pytest.approx(0.8), "run_x")

    # promote (gate humano): candidate -> active
    with pytest.raises(L4Error, match="gate humano"):
        l4.promote(db, row["id"], actor=AGENT)
    promoted = l4.promote(db, row["id"], actor=HUMAN)
    assert promoted["status"] == "active" and promoted["promoted_by"] == HUMAN
    assert [m["id"] for m in l4.recall(db, scopes=[P_A])] == [row["id"]]

    # forget: tombstone, nao apaga; idempotente
    gone = l4.forget(db, row["id"], actor=HUMAN, reason="corrigido pelo cliente")
    assert gone["status"] == "archived" and gone["archived_reason"] == "corrigido pelo cliente"
    assert l4.forget(db, row["id"], actor=HUMAN)["archived_at"] == gone["archived_at"]
    assert l4.recall(db, scopes=[P_A], include_candidates=True) == []
    assert _count(db, "id = %s", (row["id"],)) == 1  # a linha continua la


def test_delete_proibido_e_so_por_compliance_explicito(db):
    row = l4.remember(db, scope=P_A, statement="facto", actor=HUMAN, status="active")
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="DELETE proibido"):
        with db.cursor() as cur:
            cur.execute("DELETE FROM memory_l4 WHERE id = %s", (row["id"],))
    db.rollback()
    with db.cursor() as cur:
        cur.execute("SET LOCAL memory_l4.allow_delete = 'on'")
        cur.execute("DELETE FROM memory_l4 WHERE id = %s", (row["id"],))
    db.commit()
    assert _count(db) == 0


# --------------------------------------------------------------------------
# Ambitos: errado nao devolve; hierarquia; ninguem eleva
# --------------------------------------------------------------------------

def test_ambito_errado_nao_devolve(db):
    l4.remember(db, scope=P_A, statement="so do site A", actor=HUMAN, status="active")
    l4.remember(db, scope=AG, statement="so do copy_social", actor=HUMAN, status="active")
    assert l4.recall(db, scopes=[P_B]) == []
    assert l4.recall(db, scopes=[Scope("agent", "marketing.research")]) == []
    assert l4.recall(db, scopes=[Scope("project", "site-a ")]) == []  # ids exactos
    assert [m["statement"] for m in l4.recall(db, scopes=[P_A])] == ["so do site A"]


def test_cadeia_hierarquica_le_global_org_project_agent(db):
    for scope, text in ((Scope("global", "global"), "g"), (Scope("org", "acme"), "o"), (P_A, "p"), (AG, "a"),
                        (Scope("org", "outra"), "x"), (P_B, "y")):
        l4.remember(db, scope=scope, statement=text, actor=HUMAN, status="active")
    chain = [Scope("global", "global"), Scope("org", "acme"), P_A, AG]
    assert sorted(m["statement"] for m in l4.recall(db, scopes=chain)) == ["a", "g", "o", "p"]


@pytest.mark.parametrize("kwargs, erro", [
    (dict(scope=None), "ambito explicito"),
    (dict(scope=Scope("run", "run_1")), "o `run` e L2"),
    (dict(scope=Scope("org", "acme")), "nao escreve em 'org'"),
    (dict(scope=Scope("global", "global")), "nao escreve em 'global'"),
    (dict(scope=P_B, allowed=[P_A, AG]), "elevacao recusada"),
    (dict(scope=P_A, status="active"), "`active` so por gate humano"),
    (dict(scope=P_A, statement="x" * 2001), "2000"),
    (dict(scope=P_A, confidence=1.5), "confidence"),
])
def test_remember_recusa_o_que_o_contrato_proibe(db, kwargs, erro):
    args = dict(statement="facto", actor=AGENT, **kwargs) if "statement" not in kwargs else dict(actor=AGENT, **kwargs)
    with pytest.raises(L4Error, match=erro):
        l4.remember(db, **args)
    assert _count(db) == 0


def test_recall_exige_ambito_e_limit_do_contrato(db):
    with pytest.raises(ScopeError):
        l4.recall(db, scopes=[])
    with pytest.raises(L4Error, match="1..50"):
        l4.recall(db, scopes=[P_A], limit=51)


# --------------------------------------------------------------------------
# Nao editar em silencio: facto novo + invalidacao do antigo
# --------------------------------------------------------------------------

def test_update_do_statement_e_recusado_pela_bd(db):
    row = l4.remember(db, scope=P_A, statement="original", actor=HUMAN, status="active")
    with pytest.raises(psycopg.errors.CheckViolation, match="imutaveis"):
        with db.cursor() as cur:
            cur.execute("UPDATE memory_l4 SET statement = 'editado' WHERE id = %s", (row["id"],))
    db.rollback()
    assert l4.get(db, row["id"])["statement"] == "original"


def test_supersedes_so_invalida_o_antigo_quando_o_novo_e_promovido(db):
    old = l4.remember(db, scope=P_A, statement="tom informal", actor=HUMAN, status="active")
    new = l4.remember(db, scope=P_A, statement="tom formal", actor=AGENT, supersedes=old["id"], allowed=[P_A])
    assert l4.get(db, old["id"])["status"] == "active"  # o candidato ainda nao manda
    assert [m["statement"] for m in l4.recall(db, scopes=[P_A])] == ["tom informal"]

    l4.promote(db, new["id"], actor=HUMAN)
    old_now = l4.get(db, old["id"])
    assert old_now["status"] == "superseded" and old_now["superseded_by"] == new["id"]
    assert [m["statement"] for m in l4.recall(db, scopes=[P_A])] == ["tom formal"]
    assert _count(db) == 2  # o historico fica

    with pytest.raises(ScopeError, match="mesmo ambito"):
        l4.remember(db, scope=P_B, statement="x", actor=HUMAN, supersedes=new["id"])


# --------------------------------------------------------------------------
# Recall: similaridade, tags, expiracao
# --------------------------------------------------------------------------

def test_recall_por_similaridade_tags_e_expiracao(db):
    for i in (1, 2, 3):
        l4.remember(db, scope=P_A, statement=f"facto {i}", actor=HUMAN, status="active", tags=[f"t{i}", "comum"],
                    embed=fake_embed)
    past = datetime.now(UTC) - timedelta(days=1)
    l4.remember(db, scope=P_A, statement="facto 2 expirado", actor=HUMAN, status="active", expires_at=past,
                embed=fake_embed)

    hits = l4.recall(db, scopes=[P_A], query="pergunta 2", embed=fake_embed)
    assert hits[0]["statement"] == "facto 2" and hits[0]["similarity"] > 0.99
    assert "facto 2 expirado" not in [h["statement"] for h in hits]
    assert [h["statement"] for h in l4.recall(db, scopes=[P_A], tags=["t3"])] == ["facto 3"]
    assert len(l4.recall(db, scopes=[P_A], tags=["comum"], limit=2)) == 2


def test_falha_do_embedding_nao_impede_a_escrita(db):
    def broken(_):
        raise RuntimeError("quota")

    row = l4.remember(db, scope=P_A, statement="sem vector", actor=HUMAN, status="active", embed=broken)
    assert row["metadata"]["embedding_error"].startswith("RuntimeError")
    assert [m["statement"] for m in l4.recall(db, scopes=[P_A], query="x", embed=fake_embed)] == ["sem vector"]


# --------------------------------------------------------------------------
# Promocao por HITL (hitl-request-v1, ficheiros proprios)
# --------------------------------------------------------------------------

def test_hitl_de_promocao_approve_e_reject(db, tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    a = l4.remember(db, scope=P_A, statement="facto a", actor=AGENT, allowed=[P_A])
    b = l4.remember(db, scope=P_A, statement="facto b", actor=AGENT, allowed=[P_A])
    c = l4.remember(db, scope=P_A, statement="facto c", actor=AGENT, allowed=[P_A])

    req_ok = l4.request_promotion(tmp_path, [a, b], run_id="run_1", plan_id="p", step_id="s1", agent_id="marketing.x")
    req_no = l4.request_promotion(tmp_path, [c], run_id="run_1", plan_id="p", step_id="s2", agent_id="marketing.x")
    schema = json.loads((REPO_ROOT / "docs/architecture/hitl/hitl-request-v1.json").read_text(encoding="utf-8"))
    jsonschema.validate(req_ok, schema)  # o mesmo contrato do HITL duravel
    assert {r["id"] for r in l4.pending_requests(tmp_path)} == {req_ok["id"], req_no["id"]}

    with pytest.raises(L4Error, match="humana"):
        l4.decide(db, tmp_path, req_ok["id"], response="approve", actor=AGENT)
    out = l4.decide(db, tmp_path, req_ok["id"], response="approve", actor=HUMAN)
    assert [r["status"] for r in out["results"]] == ["active", "active"]
    l4.decide(db, tmp_path, req_no["id"], response="reject", actor=HUMAN, comment="nao confirmado")
    rejected = l4.get(db, c["id"])
    assert rejected["status"] == "archived" and "nao confirmado" in rejected["archived_reason"]

    assert l4.pending_requests(tmp_path) == []
    with pytest.raises(L4Error, match="ja foi decidido"):
        l4.decide(db, tmp_path, req_ok["id"], response="reject", actor=HUMAN)
    assert not (tmp_path / "hitl-decisions.jsonl").exists()  # nunca toca nas decisoes dos gates do run
