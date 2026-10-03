"""J3: ingest -> retrieve na tabela canonica (knowledge_chunks).

Escreve 1 documento com supabase_writer.replace_chunks (o caminho real do
ingest) e le-o com match_knowledge chamado como o agent-network-mcp o chama
(lib/knowledge.js:54: 3 argumentos com nome). Embeddings sinteticos de 768
dims, sem Gemini.

Corre so contra um Postgres DESCARTAVEL com pgvector, indicado em
RAG_TEST_DATABASE_URL (no CI: o servico pgvector/pgvector do job test-rag do
runner-tests.yml). Nunca usa DATABASE_URL: esse e o Supabase de producao. Cria
e apaga um schema proprio. Com RAG_TEST_REQUIRED=1 (o CI), a falta da BD e um
erro e nao um skip -- o job nunca fica verde sem ter corrido nada.

PLANO item 10 (ingest -> retrieve no CI): os testes `test_e2e_*` partem de
ficheiros markdown e passam pelo ingest real (scripts/ingest_apply.py::
apply_one: chunk_markdown -> embed -> replace_chunks), com o embedder trocado
por um falso deterministico (sem Gemini) e o connect() apontado a esta BD.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import os
import re
import unicodedata
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from plan_runner import supabase_writer as sw  # noqa: E402

DB_URL = os.environ.get("RAG_TEST_DATABASE_URL", "").strip()
if os.environ.get("RAG_TEST_REQUIRED") == "1" and not DB_URL:
    raise RuntimeError("RAG_TEST_REQUIRED=1 mas RAG_TEST_DATABASE_URL nao esta definida")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida (Postgres descartavel com pgvector; "
    "nunca o Supabase de producao)",
)

# AU-11: o schema vem do DDL canónico versionado (scripts/rag_schema.sql), o
# mesmo que serve de referência para produção; não há uma cópia aqui.
SCHEMA_SQL = (Path(__file__).resolve().parents[2] / "scripts" / "rag_schema.sql").read_text(encoding="utf-8")


def _vec(i: int) -> list[float]:
    return [1.0 if d == i else 0.001 for d in range(768)]


@pytest.fixture
def connect():
    """Devolve uma fabrica de ligacoes ao schema de teste. Uma ligacao por
    operacao, como o ingest real (scripts/ingest_apply.py:183): no psycopg 3,
    `with conn:` (usado em replace_chunks) faz commit E fecha a ligacao."""
    schema = f"rag_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        admin.execute(f"CREATE SCHEMA {schema}")

    def _open():
        return psycopg.connect(DB_URL, autocommit=False, options=f"-c search_path={schema},public")

    try:
        with _open() as c:
            c.execute(SCHEMA_SQL)
        yield _open
    finally:
        with psycopg.connect(DB_URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA {schema} CASCADE")


def _retrieve(connect, agent_id: str, query: list[float], k: int = 3) -> list[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT source FROM match_knowledge("
            "query_embedding => %s::vector, match_agent_id => %s, match_count => %s)",
            (query, agent_id, k),
        )
        return [r[0] for r in cur.fetchall()]


def _ingest(connect, source: str, agent_id: str, dim: int) -> dict[str, int]:
    return sw.replace_chunks(
        connect(),
        source_path=source,
        content_hash="h",
        agent_id=agent_id,
        kb="marketing",
        chunks=[{"content": f"conteudo {source}", "content_hash": "c0",
                 "chunk_index": 0, "embedding": _vec(dim)}],
    )


def test_schema_canonico_e_idempotente(connect):
    """AU-11: scripts/rag_schema.sql corre por cima do que existe sem erro nem perda
    (e o que permite usa-lo como referencia de producao)."""
    _ingest(connect, "docs/knowledge/geo-agent.md", "marketing", 7)
    with connect() as c:
        c.execute(SCHEMA_SQL)  # 2.a vez
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks")
        assert cur.fetchone()[0] == 1
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'knowledge_chunks' ORDER BY ordinal_position"
        )
        assert [r[0] for r in cur.fetchall()] == [
            "id", "agent_id", "source", "content", "embedding", "created_at",
            "project", "content_hash", "chunk_index", "kb", "updated_at",
        ]


def test_ingested_doc_is_retrieved(connect):
    assert _ingest(connect, "docs/knowledge/geo-agent.md", "marketing", 7)["inserted"] == 1
    assert _retrieve(connect, "marketing", _vec(7))[0] == "docs/knowledge/geo-agent.md"


def test_composite_agent_retrieved_by_each_agent(connect):
    _ingest(connect, "docs/item-13-ai-findability.md", "marketing+produto-tech-transversal", 9)
    for agent in ("marketing", "produto-tech-transversal"):
        assert _retrieve(connect, agent, _vec(9))[0] == "docs/item-13-ai-findability.md"


def test_reingest_does_not_touch_mcp_rows_with_same_source(connect):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO knowledge_chunks (agent_id, source, content, embedding) "
            "VALUES ('marketing', 'docs/x.md', 'linha do MCP', %s::vector)",
            (_vec(3),),
        )
    _ingest(connect, "docs/x.md", "marketing", 3)
    out = _ingest(connect, "docs/x.md", "marketing", 3)
    assert out == {"deleted": 1, "inserted": 1}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks WHERE project IS NULL")
        assert cur.fetchone()[0] == 1


# --------------------------------------------------------------------------
# Ponta a ponta: ficheiro -> ingest_apply.apply_one -> match_knowledge
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fake_embed(text: str) -> list[float]:
    """Embedder falso: bag-of-words com hash em 768 dims, normalizado (sem rede).

    Textos com as mesmas palavras ficam proximos, como num embedding real, e o
    resultado e sempre o mesmo para o mesmo texto.
    """
    norm = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    vec = [0.0] * 768
    for word in re.findall(r"[a-z0-9]{3,}", norm):
        vec[int(hashlib.sha256(word.encode()).hexdigest(), 16) % 768] += 1.0
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


@pytest.fixture
def ingest(connect, monkeypatch, tmp_path):
    """apply_one real com o embedder falso e o connect() desta BD descartavel."""
    # O ingest_apply carrega o .env do repo para os.environ ao ser importado: num PC
    # com o .env de producao isso deixaria chaves no ambiente dos testes seguintes.
    # Copia isolada durante este teste; o monkeypatch repoe o os.environ no fim.
    monkeypatch.setattr(os, "environ", dict(os.environ))
    spec = importlib.util.spec_from_file_location("ingest_apply_e2e", REPO_ROOT / "scripts" / "ingest_apply.py")
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)

    @contextmanager
    def test_connect():
        with connect() as conn:
            yield conn

    monkeypatch.setattr(ia, "connect", test_connect)  # nunca o DATABASE_URL de producao
    monkeypatch.setattr(ia, "embed_text", _fake_embed)  # nunca o Gemini
    monkeypatch.setattr(ia, "ROOT", tmp_path)

    def _apply(rel: str, body: str, agent_id: str) -> dict:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return ia.apply_one(rel, agent_id, "P1", dry_run=False, budget=ia.ChunkBudget(100))

    return _apply


def _ask(connect, agent_id: str, question: str, k: int = 10) -> list[str]:
    return _retrieve(connect, agent_id, _fake_embed(question), k)


DOC_SOCIAL = """# Instagram

## Campanha de lancamento

Reels curtos, hashtags da colecao e calendario de posts para a campanha de verao.
"""
DOC_CONTAS = """# Contabilidade

## Fecho trimestral

Balancete, declaracao de IVA e reconciliacao das faturas de fornecedores do trimestre.
"""


def test_e2e_ingest_de_um_doc_e_retrieve_devolve_esse_doc(connect, ingest):
    out = ingest("docs/knowledge/instagram.md", DOC_SOCIAL, "marketing")
    assert out["action"] == "OK" and out["chunks"] >= 1

    hits = _ask(connect, "marketing", "calendario de posts e reels para a campanha")
    assert hits and set(hits) == {"docs/knowledge/instagram.md"}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT agent_id, chunk_count FROM knowledge_sources WHERE source_path = %s",
                    ("docs/knowledge/instagram.md",))
        assert cur.fetchone() == ("marketing", out["chunks"])
        cur.execute("SELECT DISTINCT agent_id, kb FROM knowledge_chunks WHERE source = %s", ("docs/knowledge/instagram.md",))
        assert cur.fetchall() == [("marketing", "marketing")]


def test_e2e_dois_docs_com_agent_ids_diferentes_cada_um_so_devolve_o_seu(connect, ingest):
    ingest("docs/knowledge/instagram.md", DOC_SOCIAL, "marketing")
    ingest("docs/knowledge/fecho-trimestral.md", DOC_CONTAS, "contabilidade")

    assert set(_ask(connect, "marketing", "campanha de reels")) == {"docs/knowledge/instagram.md"}
    assert set(_ask(connect, "contabilidade", "balancete e IVA")) == {"docs/knowledge/fecho-trimestral.md"}
    # Isolamento mesmo quando a pergunta se parece mais com o doc do outro agente
    assert set(_ask(connect, "marketing", "balancete declaracao de IVA faturas")) == {"docs/knowledge/instagram.md"}
    assert set(_ask(connect, "contabilidade", "reels hashtags instagram")) == {"docs/knowledge/fecho-trimestral.md"}
    assert _ask(connect, "outro-agente", "campanha balancete") == []


def test_e2e_reingest_do_mesmo_ficheiro_nao_duplica(connect, ingest):
    first = ingest("docs/knowledge/instagram.md", DOC_SOCIAL, "marketing")
    second = ingest("docs/knowledge/instagram.md", DOC_SOCIAL + "\nNota: rever na segunda.\n", "marketing")
    assert second["deleted"] == first["chunks"]
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks WHERE source = %s", ("docs/knowledge/instagram.md",))
        assert cur.fetchone()[0] == second["chunks"]

