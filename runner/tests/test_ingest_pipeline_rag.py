"""F1 / T6e: documento convertido → T6 real → retrieve, contra Postgres + pgvector descartável.

O caminho é o de produção, sem pipeline paralela (ADR §2, regra 2):

    fixture (PDF/DOCX/XLSX) → ingest_document (processo filho, MarkItDown)
      → write_ingested (.md + .meta.yaml) → scripts/ingest_apply.py::apply_one
        (chunk_markdown → embed → replace_chunks) → match_knowledge

Reutiliza as fixtures do `test_rag_canonical.py`: BD descartável (`RAG_TEST_DATABASE_URL`, nunca
o Supabase), embedder falso determinístico (nunca o Gemini) e o `apply_one` real. Prova:
- o `content_hash` gravado pelo T6 em `knowledge_sources` é o `source_meta.content_hash`;
- o retrieve devolve o documento convertido, com o texto da tabela;
- a 2.ª corrida é UNCHANGED (incremental por hash, sem gastar embeddings);
- o orçamento de embeddings (`--max-chunks`) é respeitado: sem orçamento, SKIPPED_QUOTA e
  nada escrito.

O gate humano deste caminho é o merge do PR que põe o `.md` no MANIFEST (escrita em
produção, decisão do maestro); o T6 não tem HITL próprio.

Precisa do `markitdown` (INGEST_TEST_REQUIRED) e da BD (RAG_TEST_REQUIRED): no CI, os 2 no
job `test-ingest`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from tests.optional_deps import require
from tests.test_rag_canonical import (  # noqa: F401  (fixtures do pytest)
    DB_URL,
    _ask,
    connect,
    ingest,
)

pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="RAG_TEST_DATABASE_URL não definida (Postgres descartável com pgvector; "
    "nunca o Supabase de produção)",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ing = _load("ingest_document", "scripts/ingest_document.py")

# Pergunta → linha da tabela que tem de vir no excerto devolvido.
CASES = {
    "pdf": ("conversor PdfConverter formato estado testado", "PdfConverter"),
    "docx": ("conversor DocxConverter formato estado testado", "DocxConverter"),
    "xlsx": ("fornecedor Supabase custo mensal anual", "Supabase"),
}


def _convert_and_write(fmt: str, root: Path) -> tuple[str, dict]:
    require("markitdown")
    result = ing.ingest_document(FIXTURES / fmt / f"simple_synthetic.{fmt}")
    rel = f"{ing.INGESTED_DIR}/simple-{fmt}.md"
    ing.write_ingested(result, root / ing.INGESTED_DIR, f"simple-{fmt}")
    return rel, result


@pytest.mark.parametrize("fmt", ["pdf", "docx", "xlsx"])
def test_convertido_entra_no_t6_e_volta_no_retrieve(connect, ingest, tmp_path, fmt) -> None:  # noqa: F811
    rel, result = _convert_and_write(fmt, tmp_path)  # tmp_path é a ROOT do apply_one
    ia = ingest.ia

    out = ia.apply_one(rel, "global", "P2", dry_run=False, budget=ia.ChunkBudget(100))
    assert out["action"] == "OK" and out["chunks"] >= 1

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT content_hash, chunk_count FROM knowledge_sources WHERE source_path = %s",
            (rel,),
        )
        content_hash, chunk_count = cur.fetchone()
    assert content_hash == result["source_meta"]["content_hash"]  # o hash do T6 = o do ADR
    assert chunk_count == out["chunks"]

    question, expected = CASES[fmt]
    hits = _ask(connect, "global", question)
    assert hits and set(hits) == {rel}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT content FROM knowledge_chunks WHERE source = %s", (rel,))
        stored = "\n".join(row[0] for row in cur.fetchall())
    assert expected in stored

    again = ia.apply_one(rel, "global", "P2", dry_run=False, budget=ia.ChunkBudget(100))
    assert again == {"action": "UNCHANGED", "chunks": 0, "deleted": 0}


def test_orcamento_de_embeddings_e_respeitado(connect, ingest, tmp_path) -> None:  # noqa: F811
    rel, _ = _convert_and_write("docx", tmp_path)
    ia = ingest.ia
    n_embeds = len(ingest.embedded)

    out = ia.apply_one(rel, "global", "P2", dry_run=False, budget=ia.ChunkBudget(0))
    assert out["action"] == "SKIPPED_QUOTA"
    assert len(ingest.embedded) == n_embeds  # nenhum embedding gasto
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_chunks WHERE source = %s", (rel,))
        assert cur.fetchone()[0] == 0  # nada escrito, nem parcial
