#!/usr/bin/env python3
"""Aplica o delta de ingestao T6: chunking + embedding + write no Supabase.

Aditivo: nao altera o scripts/ingest_delta.py (que continua a correr em
dry-run no CI). Este modulo usa o MANIFEST e o sha256_file desse modulo,
e chama os modulos novos em runner/plan_runner/:

    chunking.chunk_markdown          -- divide markdown em chunks
    embedder.embed_text              -- Gemini, 768 dims
    supabase_writer.replace_chunks   -- delete + insert idempotente
    supabase_writer.purge_source     -- remove fonte + chunks

Uso:
    python scripts/ingest_apply.py                # aplica tudo
    python scripts/ingest_apply.py --only docs/knowledge/ai-findability.md
    python scripts/ingest_apply.py --dry-run      # so mostra o que faria
    python scripts/ingest_apply.py --max-chunks 20  # limita o orcamento de embeddings

Le .env da raiz do repo (sem python-dotenv): GEMINI_API_KEY, DATABASE_URL.

Rate limit do Gemini (HTTP 429, "quota exceeded" no tier gratuito):
ver docs/architecture/RATE-LIMITS.md para o achado original e a
estrategia de retry usada aqui.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# --- sys.path + .env (antes de qualquer import do runner) -------------------

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # scripts/ (para scripts.ingest_delta)
sys.path.insert(0, str(ROOT / "runner"))  # plan_runner/


def _load_env(path: Path) -> None:
    """Le .env (KEY="VALUE" ou KEY=VALUE) e exporta para os.environ.

    Nao sobrepoe variaveis ja definidas (respeita o ambiente).
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env(ROOT / ".env")


# --- imports do runner (depois do sys.path) ---------------------------------

from plan_runner.chunking import chunk_markdown  # noqa: E402
from plan_runner.embedder import EmbedderError, embed_text  # noqa: E402
from plan_runner.supabase_writer import (  # noqa: E402
    connect,
    purge_source,
    replace_chunks,
)

# Importa o manifesto e helpers do ingest_delta (sem correr o main).
from scripts.ingest_delta import MANIFEST, sha256_file  # noqa: E402


# --- retry com backoff exponencial para o rate limit do Gemini --------------

MAX_RETRIES_429 = 3
BACKOFF_BASE_SECONDS = 2.0  # 2s, 4s, 8s


class QuotaExhaustedError(RuntimeError):
    """As 3 tentativas de retry ao HTTP 429 esgotaram-se sem sucesso."""


def embed_with_retry(text: str) -> list[float]:
    """Chama embed_text() com retry+backoff exponencial só para HTTP 429.

    Outros erros (auth, timeout, dimensao errada) propagam-se de imediato --
    não faz sentido repetir um erro que não é de quota. Segue o mesmo padrão
    de exceção que embedder.py já usa (EmbedderError), sem tocar nesse
    ficheiro.
    """
    last_error: EmbedderError | None = None
    for attempt in range(1, MAX_RETRIES_429 + 1):
        try:
            return embed_text(text)
        except EmbedderError as e:
            is_429 = "HTTP 429" in str(e)
            if not is_429:
                raise  # erro diferente de quota -- não vale a pena repetir
            last_error = e
            if attempt < MAX_RETRIES_429:
                wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                print(
                    f"  [429] quota Gemini excedida (tentativa {attempt}/"
                    f"{MAX_RETRIES_429}) -- a aguardar {wait:.0f}s antes de repetir",
                    file=sys.stderr,
                )
                time.sleep(wait)
    raise QuotaExhaustedError(
        f"Quota do Gemini esgotada após {MAX_RETRIES_429} tentativas: {last_error}"
    )


def _kb_for(agent_id: str) -> str:
    """Deriva o id da base de conhecimento a partir do agent_id."""
    if "marketing" in agent_id:
        return "marketing"
    if "design" in agent_id:
        return "design"
    if "produto-tech" in agent_id:
        return "produto-tech"
    return "global"


class ChunkBudget:
    """Orçamento global de chunks a embeddar nesta corrida (protege a quota)."""

    def __init__(self, max_chunks: int):
        self.max_chunks = max_chunks
        self.used = 0

    def remaining(self) -> int:
        return max(0, self.max_chunks - self.used)

    def exhausted(self) -> bool:
        return self.used >= self.max_chunks


def apply_one(
    rel: str, agent_id: str, priority: str, *, dry_run: bool, budget: ChunkBudget
) -> dict:
    """Processa um ficheiro: chunk + embed + write. Devolve contagens."""
    full = ROOT / rel
    if not full.is_file():
        return {"action": "MISSING", "chunks": 0, "deleted": 0}

    text = full.read_text(encoding="utf-8")
    content_hash, size = sha256_file(full)
    kb = _kb_for(agent_id)

    chunks = chunk_markdown(
        text,
        source_path=rel,
        agent_id=agent_id,
        kb=kb,
    )
    if not chunks:
        return {"action": "EMPTY", "chunks": 0, "deleted": 0}

    if dry_run:
        return {"action": "DRY", "chunks": len(chunks), "deleted": 0}

    if budget.exhausted():
        return {"action": "SKIPPED_QUOTA", "chunks": 0, "deleted": 0}

    if len(chunks) > budget.remaining():
        # Orçamento não chega para este ficheiro inteiro -- salta-o por
        # completo em vez de o ingerir parcialmente (parcial seria pior:
        # deixaria a fonte com metade dos chunks antigos, metade novos).
        return {
            "action": "SKIPPED_QUOTA",
            "chunks": 0,
            "deleted": 0,
            "note": f"precisa de {len(chunks)} chunks, restam {budget.remaining()}",
        }

    # Gera embeddings (768 dims) para cada chunk, com retry a 429.
    for c in chunks:
        c["embedding"] = embed_with_retry(c["content"])
        c["content_hash"] = content_hash
    budget.used += len(chunks)

    with connect() as conn:
        out = replace_chunks(
            conn,
            source_path=rel,
            content_hash=content_hash,
            agent_id=agent_id,
            kb=kb,
            chunks=chunks,
            priority=priority,
            git_sha=os.environ.get("GITHUB_SHA") or os.environ.get("GIT_SHA"),
            size_bytes=size,
        )
    return {"action": "OK", "chunks": len(chunks), "deleted": out["deleted"]}


def purge_one(rel: str, *, dry_run: bool) -> dict:
    """Remove uma fonte do Supabase."""
    if dry_run:
        return {"action": "PURGE_DRY", "chunks": 0, "deleted": 0}
    with connect() as conn:
        deleted = purge_source(conn, rel)
    return {"action": "PURGE", "chunks": 0, "deleted": deleted}


def main() -> int:
    parser = argparse.ArgumentParser(description="T6 ingest apply")
    parser.add_argument(
        "--only",
        default=None,
        help="Aplica so a este path (relativo a raiz).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que faria, sem escrever.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=50,
        help="Orcamento maximo de chunks a embeddar nesta corrida (protege a quota do Gemini). Default: 50.",
    )
    args = parser.parse_args()

    targets = MANIFEST
    if args.only:
        targets = [t for t in MANIFEST if t[0] == args.only]
        if not targets:
            print(f"ERROR: {args.only} nao esta no MANIFEST", file=sys.stderr)
            return 2

    print("=== T6 ingest_apply ===")
    print(f"root: {ROOT}")
    print(f"mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"targets: {len(targets)}")
    print(f"max_chunks (orcamento desta corrida): {args.max_chunks}")
    print()

    budget = ChunkBudget(args.max_chunks)
    total_chunks = 0
    total_deleted = 0
    failures: list[tuple[str, str]] = []  # (path, motivo) -- para o resumo final

    for rel, agent_id, priority in targets:
        try:
            out = apply_one(rel, agent_id, priority, dry_run=args.dry_run, budget=budget)
        except QuotaExhaustedError as e:
            # Esgotou o retry a 429: para este ficheiro, reporta, e CONTINUA
            # para o proximo -- nao aborta a corrida inteira (pedido explicito).
            print(f"ERROR  {rel}: {e}", file=sys.stderr)
            failures.append((rel, str(e)))
            continue
        except Exception as e:
            # Qualquer outro erro (auth, ligacao, etc.) tambem nao aborta a
            # corrida -- regista e segue para o proximo ficheiro.
            print(f"ERROR  {rel}: {e}", file=sys.stderr)
            failures.append((rel, str(e)))
            continue

        note = f"  ({out['note']})" if out.get("note") else ""
        print(
            f"{out['action']:14}  {priority:3}  {rel}  "
            f"chunks={out['chunks']} deleted={out['deleted']}{note}"
        )
        total_chunks += out["chunks"]
        total_deleted += out["deleted"]

    print()
    print(f"TOTAL: chunks={total_chunks} deleted={total_deleted} orcamento_usado={budget.used}/{budget.max_chunks}")

    if failures:
        print()
        print(f"=== {len(failures)} FICHEIRO(S) COM ERRO (ver acima para detalhe) ===")
        for rel, motivo in failures:
            print(f"  FALHOU  {rel}: {motivo[:150]}")
        # Reporta falha (exit != 0) mas só depois de ter tentado todos os
        # ficheiros -- não abortou o workflow a meio.
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
