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

Le .env da raiz do repo (sem python-dotenv): GEMINI_API_KEY, DATABASE_URL.
"""
from __future__ import annotations

import argparse
import os
import sys
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
from plan_runner.embedder import embed_text  # noqa: E402
from plan_runner.supabase_writer import (  # noqa: E402
    connect,
    purge_source,
    replace_chunks,
)

# Importa o manifesto e helpers do ingest_delta (sem correr o main).
from scripts.ingest_delta import MANIFEST, sha256_file  # noqa: E402


def _kb_for(agent_id: str) -> str:
    """Deriva o id da base de conhecimento a partir do agent_id."""
    if "marketing" in agent_id:
        return "marketing"
    if "design" in agent_id:
        return "design"
    if "produto-tech" in agent_id:
        return "produto-tech"
    return "global"


def apply_one(rel: str, agent_id: str, priority: str, *, dry_run: bool) -> dict:
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

    # Gera embeddings (768 dims) para cada chunk.
    for c in chunks:
        c["embedding"] = embed_text(c["content"])
        c["content_hash"] = content_hash

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
    print()

    total_chunks = 0
    total_deleted = 0
    for rel, agent_id, priority in targets:
        try:
            out = apply_one(rel, agent_id, priority, dry_run=args.dry_run)
        except Exception as e:
            print(f"ERROR  {rel}: {e}", file=sys.stderr)
            return 1
        print(
            f"{out['action']:8}  {priority:3}  {rel}  "
            f"chunks={out['chunks']} deleted={out['deleted']}"
        )
        total_chunks += out["chunks"]
        total_deleted += out["deleted"]

    print()
    print(f"TOTAL: chunks={total_chunks} deleted={total_deleted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())