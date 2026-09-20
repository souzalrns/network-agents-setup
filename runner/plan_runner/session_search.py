"""B11/M1 -- indice de busca (FTS5) sobre events.jsonl de um run.

Aditivo: le `events.jsonl` (formato de EventLog.append() em events.py --
{id, type, run_id, at, payload, **extra}) e escreve um indice SQLite FTS5
ao lado, sem alterar o ficheiro original nem o EventLog.

Uso como script:
    python -m plan_runner.session_search <run_dir>          # reindexa
    python -m plan_runner.session_search <run_dir> --search "termo"
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

INDEX_FILENAME = "events_fts.db"


def _events_path(run_dir: Path) -> Path:
    return run_dir / "events.jsonl"


def _index_path(run_dir: Path) -> Path:
    return run_dir / INDEX_FILENAME


def _read_events(events_path: Path) -> list[dict[str, Any]]:
    if not events_path.exists():
        return []
    events: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def build_index(run_dir: Path) -> Path:
    """(Re)constroi o indice FTS5 a partir de events.jsonl. Devolve o path do indice.

    Idempotente: apaga e recria a tabela a cada chamada -- pensado para
    correr depois de cada alteracao ao events.jsonl (nao incremental).
    """
    events = _read_events(_events_path(run_dir))
    index_path = _index_path(run_dir)
    conn = sqlite3.connect(index_path)
    try:
        conn.execute("DROP TABLE IF EXISTS events_fts")
        conn.execute(
            """
            CREATE VIRTUAL TABLE events_fts USING fts5(
                payload,
                event_id UNINDEXED,
                run_id UNINDEXED,
                type UNINDEXED,
                at UNINDEXED
            )
            """
        )
        conn.executemany(
            "INSERT INTO events_fts (payload, event_id, run_id, type, at) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    json.dumps(evt.get("payload", {}), ensure_ascii=False),
                    evt.get("id"),
                    evt.get("run_id"),
                    evt.get("type"),
                    evt.get("at"),
                )
                for evt in events
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return index_path


def search(run_dir: Path, query: str) -> list[dict[str, Any]]:
    """Procura `query` (sintaxe de query do FTS5) no payload dos eventos.

    Reindexação automática se o índice ainda não existir. Devolve os
    eventos correspondentes (event_id/run_id/type/at/payload), sem
    falsos positivos/negativos face ao texto literal do payload.
    """
    index_path = _index_path(run_dir)
    if not index_path.exists():
        build_index(run_dir)
    conn = sqlite3.connect(index_path)
    try:
        rows = conn.execute(
            "SELECT event_id, run_id, type, at, payload FROM events_fts WHERE events_fts MATCH ? ORDER BY rank",
            (query,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {"id": r[0], "run_id": r[1], "type": r[2], "at": r[3], "payload": json.loads(r[4])}
        for r in rows
    ]


def _main() -> int:
    parser = argparse.ArgumentParser(description="Indice/busca FTS5 sobre events.jsonl (B11/M1)")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--search", default=None, help="Termo a procurar (sintaxe FTS5)")
    args = parser.parse_args()

    if args.search:
        for hit in search(args.run_dir, args.search):
            print(json.dumps(hit, ensure_ascii=False))
    else:
        path = build_index(args.run_dir)
        print(f"indexado: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
