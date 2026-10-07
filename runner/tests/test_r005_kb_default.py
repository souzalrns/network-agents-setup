"""R-005 / P-20: o `kb` das linhas do MCP, contra Postgres + pgvector descartável.

Prova `scripts/migrations/r005_kb_default.sql` sobre uma cópia do estado de produção
de 2026-10-07 (coluna `kb` com DEFAULT 'marketing' e linhas do MCP gravadas sem kb):
- reclassifica: kb = agent_id; a fonte ECC de segurança do revisor-codigo vai para
  'security'; as linhas do T6 (project preenchido) não mudam, mesmo com kb = marketing;
- tira o DEFAULT e o trigger põe kb = agent_id quando o insert não traz kb, sem
  mexer num kb explícito;
- é idempotente e corre a reclassificação uma vez só: numa 2.ª execução não toca
  numa linha gravada depois com kb = 'marketing' de propósito, mesmo que o
  `rag_schema.sql` (que também tira o DEFAULT) tenha corrido entretanto;
- a pesquisa (que filtra por agent_id) devolve o mesmo antes e depois.

Nunca o Supabase. Com RAG_TEST_REQUIRED=1 (CI), a falta da BD é erro.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg import sql  # noqa: E402

DB_URL = os.environ.get("RAG_TEST_DATABASE_URL", "").strip()
if os.environ.get("RAG_TEST_REQUIRED") == "1" and not DB_URL:
    raise RuntimeError("RAG_TEST_REQUIRED=1 mas RAG_TEST_DATABASE_URL nao esta definida")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL nao definida (Postgres descartavel com pgvector; "
    "nunca o Supabase de producao)",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SQL = (REPO_ROOT / "scripts" / "rag_schema.sql").read_text(encoding="utf-8")
MIGRATION_SQL = (REPO_ROOT / "scripts" / "migrations" / "r005_kb_default.sql").read_text(
    encoding="utf-8"
)
ECC_SEC = "ECC security-reviewer + database-reviewer"

# (agent_id, source, project, kb explícito ou None = o DEFAULT de produção)
PROD_ROWS = [
    ("revisor-codigo", ECC_SEC, None, None),
    ("revisor-codigo", ECC_SEC, None, None),
    ("revisor-codigo", "ECC code-reviewer", None, None),
    ("design", "skills UI/UX", None, None),
    ("global", "regras gerais", None, None),
    ("marketing", "ECC marketing-agent", None, None),
    # T6: kb explícito, e o item-13 é marketing de propósito (agente composto)
    (
        "produto-tech-transversal",
        "docs/item-13-ai-findability.md",
        "network-agents-setup",
        "marketing",
    ),
    ("security", "docs/knowledge/security/x.md", "network-agents-setup", "security"),
]

# Sem kb, o insert fica com o DEFAULT da coluna (como o MCP antes do R-005).
INSERT_NO_KB = (
    "INSERT INTO knowledge_chunks (agent_id, source, content, embedding, project) "
    "VALUES (%s, %s, %s, %s::vector, %s)"
)
INSERT_KB = (
    "INSERT INTO knowledge_chunks (agent_id, source, content, embedding, project, kb) "
    "VALUES (%s, %s, %s, %s::vector, %s, %s)"
)


def _vec(i: int) -> list[float]:
    return [1.0 if d == i else 0.001 for d in range(768)]


@pytest.fixture
def prod_like():
    """O schema e os dados de produção de 2026-10-07 (antes do R-005)."""
    schema = f"r005_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # SEC-2d falso positivo: o nome do schema é gerado aqui (uuid) e vai como sql.Identifier.
        # nosemgrep: formatted-sql-query, sqlalchemy-execute-raw-query
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    def _open():
        return psycopg.connect(DB_URL, autocommit=False, options=f"-c search_path={schema},public")

    with _open() as c:
        c.execute(BASE_SQL)
        c.execute("ALTER TABLE knowledge_chunks ALTER COLUMN kb SET DEFAULT 'marketing'")
        for i, (agent, source, project, kb) in enumerate(PROD_ROWS):
            if kb is None:
                c.execute(INSERT_NO_KB, (agent, source, f"c{i}", str(_vec(i)), project))
            else:
                c.execute(INSERT_KB, (agent, source, f"c{i}", str(_vec(i)), project, kb))
    try:
        yield _open
    finally:
        with psycopg.connect(DB_URL, autocommit=True) as admin:
            # SEC-2d falso positivo: o nome do schema é gerado aqui (uuid) e vai como sql.Identifier.
            # nosemgrep: formatted-sql-query, sqlalchemy-execute-raw-query
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _q(opener, sql: str, params=()):
    with opener() as conn, conn.cursor() as cur:
        cur.execute(sql, params or None)
        return cur.fetchall()


def _kb_default(opener):
    return _q(
        opener,
        "SELECT column_default FROM information_schema.columns WHERE table_schema = current_schema() "
        "AND table_name = 'knowledge_chunks' AND column_name = 'kb'",
    )[0][0]


def _migrate(opener):
    with opener() as c:
        c.execute(MIGRATION_SQL)


def _insert(opener, agent: str, source: str, kb: str | None = None):
    with opener() as c:
        if kb is None:
            c.execute(INSERT_NO_KB, (agent, source, "x", None, None))
        else:
            c.execute(INSERT_KB, (agent, source, "x", None, None, kb))


def test_estado_de_producao_reproduzido(prod_like):
    assert _kb_default(prod_like) == "'marketing'::text"
    rows = _q(prod_like, "SELECT DISTINCT kb FROM knowledge_chunks WHERE project IS NULL")
    assert rows == [("marketing",)]


def test_reclassifica_as_linhas_do_mcp(prod_like):
    _migrate(prod_like)
    got = dict(
        _q(
            prod_like,
            "SELECT agent_id || ' | ' || source, kb FROM knowledge_chunks WHERE project IS NULL",
        )
    )
    assert got == {
        f"revisor-codigo | {ECC_SEC}": "security",
        "revisor-codigo | ECC code-reviewer": "revisor-codigo",
        "design | skills UI/UX": "design",
        "global | regras gerais": "global",
        "marketing | ECC marketing-agent": "marketing",
    }
    assert _q(
        prod_like, "SELECT count(*) FROM knowledge_chunks WHERE project IS NULL AND kb = 'security'"
    ) == [(2,)]


def test_linhas_do_t6_nao_mudam(prod_like):
    before = _q(
        prod_like,
        "SELECT id, kb, agent_id FROM knowledge_chunks WHERE project IS NOT NULL ORDER BY id",
    )
    _migrate(prod_like)
    after = _q(
        prod_like,
        "SELECT id, kb, agent_id FROM knowledge_chunks WHERE project IS NOT NULL ORDER BY id",
    )
    assert after == before
    assert ("marketing",) in [(r[1],) for r in after]  # o item-13 continua marketing


def test_sem_default_e_trigger_poe_kb_igual_ao_agent_id(prod_like):
    _migrate(prod_like)
    assert _kb_default(prod_like) is None
    _insert(prod_like, "design", "novo sem kb")
    _insert(prod_like, "revisor-codigo", "novo com kb", kb="security")
    got = dict(_q(prod_like, "SELECT source, kb FROM knowledge_chunks WHERE source LIKE 'novo%'"))
    assert got == {"novo sem kb": "design", "novo com kb": "security"}


def test_idempotente_e_reclassifica_uma_vez_so(prod_like):
    _migrate(prod_like)
    # depois do R-005 alguém grava kb = marketing de propósito e o rag_schema volta a correr
    _insert(prod_like, "design", "campanha", kb="marketing")
    with prod_like() as c:
        c.execute(BASE_SQL)
    _migrate(prod_like)  # 2.ª vez
    assert _q(prod_like, "SELECT kb FROM knowledge_chunks WHERE source = 'campanha'") == [
        ("marketing",)
    ]
    assert _kb_default(prod_like) is None
    assert _q(prod_like, "SELECT count(*) FROM knowledge_chunks") == [(len(PROD_ROWS) + 1,)]


def test_a_pesquisa_por_agent_id_nao_muda(prod_like):
    def search(agent):
        # O que volta, sem a ordem: com distâncias iguais, a ordem dos empates depende
        # da posição física das linhas, que o UPDATE muda (visto no CI com pgvector:pg16).
        return sorted(
            _q(
                prod_like,
                "SELECT source FROM match_knowledge(query_embedding => %s::vector, "
                "match_agent_id => %s, match_count => 10)",
                (str(_vec(0)), agent),
            )
        )

    agents = ("revisor-codigo", "design", "marketing", "security")
    before = {a: search(a) for a in agents}
    _migrate(prod_like)
    assert {a: search(a) for a in agents} == before
