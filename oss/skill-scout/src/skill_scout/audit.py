"""Tamper-evident audit log: append-only JSON Lines, each record chained to the previous one.

Each record: `seq` (1, 2, …), `ts`, `event`, `actor`, `data`, `prev` (hash of the previous
record, 64 zeros for the first) and `hash` = sha256 of the record's canonical JSON without
`hash`. Editing, deleting or reordering a record breaks the chain and `verify` reports it.
Cutting the tail cannot be seen from the log alone, so every lock entry also stores the
`seq` and `hash` of its `installed` record: `skill-scout verify` checks they are still there.

Events: `scan`, `blocked`, `approval_rejected`, `installed`, `uninstalled`, `waiver_added`.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

from .errors import VerifyError
from .report import now

GENESIS = "0" * 64
EVENTS = ("scan", "blocked", "approval_rejected", "installed", "uninstalled", "waiver_added")

try:  # POSIX: serialise concurrent appends
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_hash(record: dict) -> str:
    return hashlib.sha256(canonical({k: v for k, v in record.items() if k != "hash"})).hexdigest()


def actor() -> str:
    """Who ran the command: SKILL_SCOUT_ACTOR, else the OS user. Never e-mail or host name."""
    value = os.environ.get("SKILL_SCOUT_ACTOR") or ""
    if not value:
        try:
            value = getpass.getuser()
        except (KeyError, OSError):
            value = "unknown"
    return value.strip()[:100] or "unknown"


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        if fcntl is not None:
            fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield fh
        finally:
            if fcntl is not None:
                fcntl.flock(fh, fcntl.LOCK_UN)


def read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            raise VerifyError(f"audit line {n} is not JSON") from None
        if not isinstance(rec, dict):
            raise VerifyError(f"audit line {n} is not an object")
        out.append(rec)
    return out


def append(path: Path, event: str, data: dict, who: str | None = None) -> dict:
    if event not in EVENTS:
        raise ValueError(f"unknown audit event {event}")
    path = Path(path)
    with _locked(path) as fh:
        fh.seek(0)
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        last = json.loads(lines[-1]) if lines else None
        rec = {
            "seq": (last["seq"] + 1) if last else 1,
            "ts": now(),
            "event": event,
            "actor": who or actor(),
            "data": data,
            "prev": last["hash"] if last else GENESIS,
        }
        rec["hash"] = record_hash(rec)
        fh.seek(0, os.SEEK_END)
        fh.write(canonical(rec).decode("utf-8") + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return rec


def verify(path: Path) -> list[str]:
    """Problems in the chain ([] if intact). A missing file is an empty, valid log."""
    try:
        records = read(Path(path))
    except VerifyError as e:
        return [str(e)]
    problems: list[str] = []
    prev, expected_seq = GENESIS, 1
    for rec in records:
        seq = rec.get("seq")
        if seq != expected_seq:
            problems.append(f"audit seq {seq}: expected {expected_seq} (record deleted or reordered)")
        if rec.get("prev") != prev:
            problems.append(f"audit seq {seq}: `prev` does not match the previous record (chain broken)")
        if rec.get("hash") != record_hash(rec):
            problems.append(f"audit seq {seq}: hash does not match its content (record edited)")
        prev = rec.get("hash", "")
        expected_seq = (seq if isinstance(seq, int) else expected_seq) + 1
    return problems
