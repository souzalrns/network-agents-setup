"""Append-only, hash-chained decision journal (JSONL).

Every proposal, assessment, gate decision, order and fill is one line. Each line carries the
SHA-256 of the previous line, so an edited or deleted line breaks ``verify``. It answers the
question a trading agent must always be able to answer: *why did it do that, and on what?*
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import now_iso

GENESIS = "0" * 64


class Journal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last = self._tail_hash()

    def _tail_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = GENESIS
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = hashlib.sha256(line.rstrip("\n").encode()).hexdigest()
        return last

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        entry = {"ts": now_iso(), "kind": kind, "prev": self._last, "payload": payload}
        line = json.dumps(entry, sort_keys=True, ensure_ascii=False, default=str)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        self._last = hashlib.sha256(line.encode()).hexdigest()
        return entry

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]


def verify(path: str | Path) -> list[str]:
    """Return the chain breaks (empty = intact)."""
    errors, prev = [], GENESIS
    lines = [x for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    for i, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {i}: not JSON")
            prev = hashlib.sha256(line.encode()).hexdigest()
            continue
        if entry.get("prev") != prev:
            errors.append(f"line {i}: chain broken (prev hash mismatch)")
        prev = hashlib.sha256(line.encode()).hexdigest()
    return errors
