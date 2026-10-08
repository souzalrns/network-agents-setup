"""Deterministic content hash of a skill directory (`skill-notary-tree-v1`).

The hash is what a human approves and what the lock file pins, so it must be the same on
every machine for the same bytes:

- every regular file below the root, with its POSIX relative path, its sha256 and whether
  it is executable (the only mode bit that changes behaviour);
- sorted by code point (Python `str` order), never by locale. The `skills` CLI hashes with
  JavaScript `localeCompare`, whose order depends on the ICU locale, so the same folder can
  hash differently on two machines;
- each entry is a JSON array on its own line, so no file name (even one with a newline) can
  forge another entry;
- symlinks and special files (devices, FIFOs, sockets) are not hashed: they are listed as
  `unsupported` and an install refuses them. The root `.git` is skipped (fetch metadata).
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from .errors import UsageError

TREE_ALGO = "skill-notary-tree-v1"
MAX_FILES = 5000
MAX_BYTES = 50 * 1024 * 1024
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class TreeEntry:
    path: str
    sha256: str
    size: int
    executable: bool


@dataclass(frozen=True)
class TreeHash:
    digest: str
    entries: tuple[TreeEntry, ...] = ()
    unsupported: tuple[str, ...] = field(default_factory=tuple)

    @property
    def files(self) -> int:
        return len(self.entries)

    @property
    def size(self) -> int:
        return sum(e.size for e in self.entries)

    def to_json(self) -> dict:
        return {
            "algorithm": TREE_ALGO,
            "sha256": self.digest,
            "files": self.files,
            "bytes": self.size,
            "unsupported": list(self.unsupported),
        }


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_of(entries: list[TreeEntry] | tuple[TreeEntry, ...]) -> str:
    h = hashlib.sha256(f"{TREE_ALGO}\n".encode())
    for e in sorted(entries, key=lambda x: x.path):
        line = json.dumps([e.path, e.executable, e.sha256], ensure_ascii=True, separators=(",", ":"))
        h.update(line.encode("ascii") + b"\n")
    return h.hexdigest()


def tree_hash(root: Path) -> TreeHash:
    """Hash `root`. Raises UsageError above MAX_FILES files or MAX_BYTES bytes."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise UsageError(f"not a directory: {root}")
    entries: list[TreeEntry] = []
    unsupported: list[str] = []
    total = 0
    stack: list[tuple[Path, str]] = [(root, "")]
    while stack:
        current, prefix = stack.pop()
        with os.scandir(current) as it:
            for de in sorted(it, key=lambda d: d.name):
                rel = f"{prefix}{de.name}"
                if not prefix and de.name == ".git":
                    continue
                st = os.lstat(de.path)
                if stat.S_ISLNK(st.st_mode):
                    unsupported.append(f"{rel} (symlink)")
                elif stat.S_ISDIR(st.st_mode):
                    stack.append((Path(de.path), f"{rel}/"))
                elif stat.S_ISREG(st.st_mode):
                    total += st.st_size
                    if len(entries) >= MAX_FILES or total > MAX_BYTES:
                        raise UsageError(f"skill too large to pin (max {MAX_FILES} files, {MAX_BYTES} bytes)")
                    entries.append(
                        TreeEntry(
                            rel,
                            file_sha256(Path(de.path)),
                            st.st_size,
                            bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)),
                        )
                    )
                else:
                    unsupported.append(f"{rel} (special file)")
    entries.sort(key=lambda e: e.path)
    return TreeHash(digest_of(entries), tuple(entries), tuple(sorted(unsupported)))
