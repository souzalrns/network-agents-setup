#!/usr/bin/env python3
"""
T6 — Delta ingest of knowledge packs (dry-run by default).

Git = source of truth. Computes per-file SHA-256 and reports:
  SKIP | REINGEST | MISSING | PURGE candidates.

Real embed/Supabase only when --apply is wired (stubs for now).

  python scripts/ingest_delta.py
  python scripts/ingest_delta.py --apply
  python scripts/ingest_delta.py --state .ingest-state.json

See docs/T6-INGEST-PIPELINE.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# path, agent_id (network), priority
MANIFEST: list[tuple[str, str, str]] = [
    ("docs/item-13-ai-findability.md", "marketing+produto-tech-transversal", "P0"),
    ("docs/knowledge/item-13-ai-findability.md", "marketing", "P0"),
    ("docs/knowledge/ai-findability.md", "marketing", "P0"),
    ("docs/knowledge/seo-specialist.md", "produto-tech-transversal", "P0"),
    ("docs/knowledge/ai-visibility.md", "marketing", "P1"),
    ("docs/knowledge/geo-agent.md", "marketing", "P1"),
    ("docs/knowledge/copywriter.md", "marketing", "P1"),
    ("docs/knowledge/content-strategist.md", "marketing", "P1"),
    ("docs/knowledge/research-marketing.md", "marketing", "P1"),
    ("docs/knowledge/critic-criativo.md", "marketing", "P1"),
    ("docs/knowledge/media-buyer.md", "marketing", "P1"),
    ("docs/knowledge/performance-analyst.md", "marketing", "P1"),
    ("docs/knowledge/social-media-manager.md", "marketing", "P1"),
    ("docs/knowledge/storytelling.md", "marketing", "P1"),
    ("docs/knowledge/ugc-specialist.md", "marketing", "P1"),
    ("docs/knowledge/influencer-strategist.md", "marketing", "P1"),
    ("docs/knowledge/trend-hunter.md", "marketing", "P1"),
    ("docs/knowledge/editor-video.md", "marketing", "P1"),
    ("docs/knowledge/diretor-arte.md", "marketing", "P1"),
    ("docs/knowledge/ux.md", "marketing", "P1"),
    ("docs/knowledge/ui.md", "marketing", "P1"),
    ("docs/knowledge/marketing-orquestrador.md", "marketing", "P1"),
    ("docs/knowledge/orquestrador-playbook.md", "marketing", "P1"),
    ("docs/knowledge/vertical-client-context.md", "marketing", "P1"),
    ("docs/knowledge/estrategista-marca.md", "marketing", "P1"),
    ("docs/knowledge/brand-guard-cliente.md", "marketing", "P1"),
    ("docs/knowledge/social-instagram-cliente.md", "marketing", "P1"),
    ("docs/knowledge/social-tiktok-cliente.md", "marketing", "P1"),
    ("docs/knowledge/trafego-pago-cliente.md", "marketing", "P1"),
    ("docs/knowledge/conteudo-calendario-cliente.md", "marketing", "P1"),
    ("docs/knowledge/producao-audiovisual-cliente.md", "marketing", "P1"),
    ("docs/knowledge/tiktok-shop-cliente.md", "marketing", "P1"),
    ("docs/T6-INGEST-PIPELINE.md", "produto-tech-transversal", "P2"),
]


@dataclass
class FileResult:
    path: str
    agent_id: str
    priority: str
    action: str
    content_hash: str | None
    previous_hash: str | None
    size_bytes: int | None


def sha256_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.is_file():
        return {"sources": {}, "updated_at": None}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state_path: Path, sources: dict[str, Any]) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": os.environ.get("GITHUB_SHA") or os.environ.get("GIT_SHA"),
        "sources": sources,
    }
    state_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def discover_orphan_paths(prev_sources: dict[str, Any], manifest_paths: set[str]) -> list[str]:
    return sorted(set(prev_sources.keys()) - manifest_paths)


def apply_reingest_stub(path: str, agent_id: str, content_hash: str, full: Path) -> None:
    _ = (path, agent_id, content_hash, full)
    print(f"  [stub] reingest {path} → agent={agent_id}")


def apply_purge_stub(path: str) -> None:
    print(f"  [stub] purge chunks for {path}")


def run_delta(state_path: Path, apply: bool) -> int:
    state = load_state(state_path)
    prev_sources: dict[str, Any] = state.get("sources") or {}
    manifest_paths = {p for p, _, _ in MANIFEST}
    results: list[FileResult] = []
    new_sources: dict[str, Any] = dict(prev_sources)

    for rel, agent_id, priority in MANIFEST:
        full = ROOT / rel
        previous = (prev_sources.get(rel) or {}).get("content_hash")
        if not full.is_file():
            results.append(
                FileResult(rel, agent_id, priority, "MISSING", None, previous, None)
            )
            new_sources.pop(rel, None)
            continue

        digest, size = sha256_file(full)
        if previous == digest:
            action = "SKIP"
        else:
            action = "REINGEST"
            if apply:
                apply_reingest_stub(rel, agent_id, digest, full)
            new_sources[rel] = {
                "content_hash": digest,
                "agent_id": agent_id,
                "priority": priority,
                "size_bytes": size,
            }
        results.append(
            FileResult(rel, agent_id, priority, action, digest, previous, size)
        )

    orphans = discover_orphan_paths(prev_sources, manifest_paths)
    for r in results:
        if r.action == "MISSING" and r.previous_hash:
            orphans.append(r.path)
    orphans = sorted(set(orphans))

    if apply and orphans:
        for path in orphans:
            apply_purge_stub(path)
            new_sources.pop(path, None)

    counts = {"SKIP": 0, "REINGEST": 0, "MISSING": 0, "PURGE": len(orphans)}
    for r in results:
        if r.action in counts:
            counts[r.action] += 1

    print("=== T6 ingest_delta ===")
    print(f"root: {ROOT}")
    print(f"mode: {'APPLY (stubs)' if apply else 'DRY-RUN'}")
    print(f"state: {state_path}")
    print()
    for r in results:
        prev = (r.previous_hash or "-")[:12]
        cur = (r.content_hash or "-")[:12]
        print(f"{r.action:8}  {r.priority:3}  {r.path}")
        if r.action == "REINGEST":
            print(f"         hash {prev} → {cur}  agent={r.agent_id}")
        if r.action == "MISSING":
            print(f"         was {prev}  agent={r.agent_id}")
    if orphans:
        print()
        print("PURGE candidates:")
        for p in orphans:
            print(f"PURGE     {p}")
    print()
    print(
        f"summary: SKIP={counts['SKIP']} REINGEST={counts['REINGEST']} "
        f"MISSING={counts['MISSING']} PURGE={counts['PURGE']}"
    )

    if apply:
        save_state(state_path, new_sources)
        print(f"state written: {state_path}")
    else:
        print("dry-run: state file not modified")
        would = sum(1 for r in results if r.action == "REINGEST")
        if would:
            print(f"would update {would} source hash(es)")

    p0_missing = [r for r in results if r.action == "MISSING" and r.priority == "P0"]
    if p0_missing:
        print(
            "ERROR: P0 sources missing:",
            ", ".join(r.path for r in p0_missing),
            file=sys.stderr,
        )
        return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="T6 knowledge delta ingest")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument(
        "--apply", action="store_true", help="Write local state + stubs"
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=ROOT / ".ingest-state.json",
        help="Hash state file",
    )
    args = parser.parse_args()
    sys.exit(run_delta(args.state, apply=bool(args.apply)))


if __name__ == "__main__":
    main()
