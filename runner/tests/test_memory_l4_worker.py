"""L4 no worker (memory_wiring.py): recall antes da chamada, remember opt-in, HITL de promocao.

Postgres descartavel com pgvector (RAG_TEST_DATABASE_URL; no CI o job test-rag)
e Gemini falso. Prova tambem o ciclo entre runs: o run 1 propoe um facto, um
humano aprova-o, o run 2 recebe-o no prompt.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from psycopg.rows import dict_row  # noqa: E402

from plan_runner import external_worker as ew  # noqa: E402
from plan_runner import memory_l4 as l4  # noqa: E402
from plan_runner import memory_wiring as mw  # noqa: E402
from plan_runner.engine import run_plan  # noqa: E402
from plan_runner.memory_l4 import Scope  # noqa: E402
from tests.test_memory_l4 import DB_URL, fake_embed  # noqa: E402

pytestmark = pytest.mark.skipif(not DB_URL, reason="RAG_TEST_DATABASE_URL nao definida (ver test_memory_l4.py)")

HUMAN = "human:maestro"
P_A, P_B = Scope("project", "site-a"), Scope("project", "site-b")


class MemoryGemini:
    """Responde com um artefacto e, se o prompt pedir memoria, com factos propostos."""

    def __init__(self, facts: list[str] | None = None):
        self.facts = facts if facts is not None else ["O cliente quer tom formal [Fonte: pedido]"]
        self.calls: list[dict] = []

    def __call__(self, url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        self.calls.append({"system": system, "user": user})
        items = [{"statement": f, "subject": "tom", "confidence": 0.7} for f in self.facts]
        if body["generationConfig"].get("responseMimeType") == "application/json":
            art = {"titulo": "brief"}
            text = json.dumps({"artifact": art, "memoria": items} if "`memoria`" in system else art)
        else:
            text = "# Post\n\nTexto do post.\n"
            if mw.MEMORY_MARKER in system:
                text += mw.MEMORY_MARKER + "\n" + "\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n"
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
                     "modelVersion": "gemini-3.5-flash-lite"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def store(l4_opts, monkeypatch):
    """A L4 do worker aponta para o schema de teste (nunca o DATABASE_URL de producao)."""
    calls = {"n": 0}

    @contextmanager
    def connect():
        calls["n"] += 1
        conn = psycopg.connect(DB_URL, autocommit=False, row_factory=dict_row, options=l4_opts)
        try:
            yield conn
        finally:
            conn.close()

    s = mw.MemoryStore(connect=connect, embed=fake_embed)
    s.calls = calls
    monkeypatch.setattr(mw, "store_from_env", lambda: s)
    return s


@pytest.fixture
def fake(monkeypatch):
    f = MemoryGemini()
    monkeypatch.setattr(ew, "httpx_transport", f)
    return f


def _plan(tmp_path: Path, step_extra: str = "", memory: str = "memory: {project: site-a}\n", art: str = "artifacts/01.md") -> Path:
    p = tmp_path / "p.yaml"
    p.write_text(f"id: mem\nobjective: Post de lancamento\n{memory}steps:\n"
                 f"  - {{id: post, action: copy_social, output_artifact: {art}{step_extra}}}\n", encoding="utf-8")
    return p


def _result(out: Path) -> dict:
    return json.loads((out / "pending_steps/post/result.json").read_text(encoding="utf-8"))


def _rows(db) -> list[dict]:
    with db.cursor() as cur:
        cur.execute("SELECT * FROM memory_l4 ORDER BY created_at")
        rows = [dict(r) for r in cur.fetchall()]
    db.commit()
    return rows


# --------------------------------------------------------------------------
# remember: so com `remember: true`; candidate; pedido HITL
# --------------------------------------------------------------------------

def test_passo_com_remember_grava_candidate_e_abre_hitl(tmp_path, tmp_run_dir, db, store, fake):
    status = run_plan(_plan(tmp_path, ", remember: true"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    assert mw.MEMORY_MARKER in fake.calls[0]["system"]  # o pedido de factos so aparece com remember

    [row] = _rows(db)
    assert (row["scope_kind"], row["scope_id"], row["status"]) == ("project", "site-a", "candidate")
    assert row["created_by"] == "agent:marketing.copy_social" and row["source_run_id"] == status["run_id"]
    assert "step:post" in row["tags"] and row["embedding"] is not None

    art = (tmp_run_dir / "artifacts/01.md").read_text(encoding="utf-8")
    assert mw.MEMORY_MARKER not in art and art.startswith("# Post")  # o artefacto fica limpo
    meta = _result(tmp_run_dir)["meta"]["memory"]
    assert meta["remember"]["written"] == [str(row["id"])]
    [req] = l4.pending_requests(tmp_run_dir)
    assert req["metadata"]["memory_ids"] == [str(row["id"])] and req["id"] == meta["remember"]["hitl_request"]
    trace = [json.loads(line) for line in (tmp_run_dir / mw.TRACE_FILE).read_text().splitlines()]
    assert trace[0]["op"] == "remember" and trace[0]["status"] == "candidate"


def test_passo_sem_remember_nao_grava_nem_pede_factos(tmp_path, tmp_run_dir, db, store, fake):
    run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert mw.MEMORY_MARKER not in fake.calls[0]["system"]
    assert _rows(db) == []
    assert l4.pending_requests(tmp_run_dir) == []
    assert "remember" not in _result(tmp_run_dir)["meta"]["memory"]


def test_passo_json_com_remember(tmp_path, tmp_run_dir, db, store, fake):
    run_plan(_plan(tmp_path, ", remember: {scope: agent, max: 1, tags: [brand]}", art="artifacts/01.json"),
             mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert json.loads((tmp_run_dir / "artifacts/01.json").read_text()) == {"titulo": "brief"}
    [row] = _rows(db)
    assert (row["scope_kind"], row["scope_id"]) == ("agent", "marketing.copy_social") and "brand" in row["tags"]


def test_remember_nao_eleva_o_ambito(tmp_path, tmp_run_dir, db, store, fake):
    status = run_plan(_plan(tmp_path, ", remember: {scope: org}"), mode="external", out_dir=tmp_run_dir,
                      worker="gemini")
    assert status["state"] == "waiting_external" and "memory:" in status["worker_error"]
    assert fake.calls == [] and _rows(db) == []


def test_max_de_factos_por_passo(tmp_path, tmp_run_dir, db, store, monkeypatch):
    many = MemoryGemini(facts=[f"facto {i}" for i in range(4)])
    monkeypatch.setattr(ew, "httpx_transport", many)
    run_plan(_plan(tmp_path, ", remember: {max: 2}"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert len(_rows(db)) == 2
    assert "acima do max 2" in _result(tmp_run_dir)["meta"]["memory"]["remember"]["rejected"][0]


# --------------------------------------------------------------------------
# recall: so active, so a cadeia do passo
# --------------------------------------------------------------------------

def test_recall_injecta_so_active_da_cadeia_do_passo(tmp_path, tmp_run_dir, db, store, fake):
    mine = l4.remember(db, scope=P_A, statement="Marca escreve-se sempre ACME", actor=HUMAN, status="active",
                       embed=fake_embed)
    l4.remember(db, scope=P_B, statement="Facto do outro projecto", actor=HUMAN, status="active")
    l4.remember(db, scope=P_A, statement="Candidato ainda por aprovar", actor="agent:x", allowed=[P_A])
    l4.remember(db, scope=Scope("agent", "marketing.copy_social"), statement="Max 3 hashtags", actor=HUMAN,
                status="active")

    run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    user = fake.calls[0]["user"]
    assert "## Memoria L4 (factos entre runs)" in user
    assert "Marca escreve-se sempre ACME" in user and "Max 3 hashtags" in user
    assert "outro projecto" not in user and "Candidato" not in user
    recall = _result(tmp_run_dir)["meta"]["memory"]["recall"]
    assert str(mine["id"]) in recall["recalled"] and len(recall["recalled"]) == 2
    assert recall["scopes"] == ["global:global", "project:site-a", "agent:marketing.copy_social"]


def test_recall_false_no_passo_desliga(tmp_path, tmp_run_dir, db, store, fake):
    l4.remember(db, scope=P_A, statement="facto", actor=HUMAN, status="active")
    run_plan(_plan(tmp_path, ", recall: false"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert "Memoria L4" not in fake.calls[0]["user"]


# --------------------------------------------------------------------------
# Sem `memory:` nada muda; falha da L4 nunca parte o passo
# --------------------------------------------------------------------------

def test_plano_sem_memory_nao_toca_na_l4(tmp_path, tmp_run_dir, store, fake):
    status = run_plan(_plan(tmp_path, ", remember: true", memory=""), mode="external", out_dir=tmp_run_dir,
                      worker="gemini")
    assert status["state"] == "done" and store.calls["n"] == 0
    assert "memory" not in _result(tmp_run_dir)["meta"]


def test_falha_da_l4_nao_parte_o_passo(tmp_path, tmp_run_dir, fake, monkeypatch):
    @contextmanager
    def down():
        raise psycopg.OperationalError("ligacao recusada")
        yield  # pragma: no cover

    monkeypatch.setattr(mw, "store_from_env", lambda: mw.MemoryStore(connect=down))
    status = run_plan(_plan(tmp_path, ", remember: true"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    meta = _result(tmp_run_dir)["meta"]["memory"]
    assert "ligacao recusada" in meta["recall"]["error"] and "ligacao recusada" in meta["remember"]["error"]


def test_plano_com_memory_mas_sem_database_url(tmp_path, tmp_run_dir, fake, monkeypatch):
    monkeypatch.setattr(mw, "store_from_env", lambda: None)
    status = run_plan(_plan(tmp_path, ", remember: true"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    assert "sem DATABASE_URL" in _result(tmp_run_dir)["meta"]["memory"]["error"]


# --------------------------------------------------------------------------
# DONE: entre runs -- o run 1 aprende, o humano aprova, o run 2 lembra
# --------------------------------------------------------------------------

def test_ciclo_entre_runs_com_gate_humano(tmp_path, tmp_run_dir, db, store, fake):
    run_plan(_plan(tmp_path, ", remember: true"), mode="external", out_dir=tmp_run_dir, worker="gemini")
    [req] = l4.pending_requests(tmp_run_dir)

    second = tmp_run_dir.parent / f"{tmp_run_dir.name}_r2"
    try:
        run_plan(_plan(tmp_path), mode="external", out_dir=second, worker="gemini")
        assert "tom formal" not in fake.calls[-1]["user"]  # candidate: ainda nao entra

        l4.decide(db, tmp_run_dir, req["id"], response="approve", actor=HUMAN)  # gate humano

        third = tmp_run_dir.parent / f"{tmp_run_dir.name}_r3"
        try:
            run_plan(_plan(tmp_path), mode="external", out_dir=third, worker="gemini")
            assert "O cliente quer tom formal" in fake.calls[-1]["user"]  # o run 3 lembra
        finally:
            import shutil

            shutil.rmtree(third, ignore_errors=True)
    finally:
        import shutil

        shutil.rmtree(second, ignore_errors=True)
