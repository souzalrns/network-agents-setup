"""Lock file (`skill-notary.lock.json`): what is installed, pinned to the approved content.

```json
{
  "version": 1,
  "skills": {
    "<name>": {
      "source": "owner/repo@skill", "source_type": "github", "repo_url": "https://github.com/owner/repo",
      "ref": null, "commit": "<40 hex>", "skill_path": "skills/<name>",
      "content_sha256": "<skill-notary-tree-v1>", "files": 3, "bytes": 1024,
      "verdict": "safe", "counts": {"info": 0, "low": 0, "medium": 0, "high": 0, "critical": 0},
      "engines": [{"name": "asm", "version": "1.0.4"}],
      "install_path": ".claude/skills/<name>",
      "approval": {"mode": "tty", "actor": "alice", "at": "…"},
      "audit": {"seq": 3, "hash": "<sha256 of the `installed` audit record>"}
    }
  }
}
```

Written atomically (temporary file + rename), keys sorted, so a PR diff shows exactly what a
human approved. `install_path` is relative to the lock file's folder.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .errors import VerifyError

LOCK_VERSION = 1
DEFAULT_LOCK = "skill-notary.lock.json"
DEFAULT_AUDIT = "skill-notary.audit.jsonl"


def empty() -> dict:
    return {"version": LOCK_VERSION, "skills": {}}


def load(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        return empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise VerifyError(f"lock file unreadable: {type(e).__name__}") from None
    if not isinstance(data, dict) or data.get("version") != LOCK_VERSION or not isinstance(data.get("skills"), dict):
        raise VerifyError(f"lock file is not skill-notary lock version {LOCK_VERSION}")
    return data


def save(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        json.dumps(
            {"version": data["version"], "skills": dict(sorted(data["skills"].items()))},
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )
    fd, tmp = tempfile.mkstemp(prefix=".skill-notary-lock-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def rel_to(path: Path, base: Path) -> str:
    try:
        return Path(os.path.relpath(Path(path).resolve(), Path(base).resolve())).as_posix()
    except ValueError:  # pragma: no cover - other drive on Windows
        return Path(path).resolve().as_posix()
