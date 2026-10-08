"""`verify`: is what is installed still exactly what a human approved?

Checks, all reported (not just the first):
- the audit chain is intact (audit.verify);
- every lock entry: the install folder exists, holds no symlink or special file, and hashes to
  `content_sha256` (drift: a file added, removed, edited or made executable after approval);
- every lock entry points at an `installed` audit record (`audit.seq` + `audit.hash`) for the
  same name and content: an entry added to the lock by hand, or a cut audit log, fails;
- skill folders in the destination that are not in the lock (`--dest`) are reported as
  unmanaged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import audit, lock
from .errors import UsageError, VerifyError
from .locate import SKILL_FILE
from .treehash import tree_hash


@dataclass
class VerifyResult:
    checked: int = 0
    problems: list[str] = field(default_factory=list)
    unmanaged: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_json(self) -> dict:
        return {"ok": self.ok, "checked": self.checked, "problems": self.problems, "unmanaged": self.unmanaged}


def verify(lock_path: Path, audit_path: Path, dest: Path | None = None) -> VerifyResult:
    lock_path, audit_path = Path(lock_path), Path(audit_path)
    result = VerifyResult()
    try:
        data = lock.load(lock_path)
    except VerifyError as e:
        result.problems.append(str(e))
        return result
    result.problems += audit.verify(audit_path)
    try:
        records = {r.get("seq"): r for r in audit.read(audit_path)}
    except VerifyError:
        records = {}
    base = lock_path.parent
    installed_paths = set()
    for name, entry in sorted(data["skills"].items()):
        result.checked += 1
        if not isinstance(entry, dict):
            result.problems.append(f"{name}: lock entry is not an object")
            continue
        path = (base / str(entry.get("install_path", ""))).resolve()
        installed_paths.add(path)
        if not path.is_dir():
            result.problems.append(f"{name}: not installed at {entry.get('install_path')}")
        else:
            try:
                tree = tree_hash(path)
            except UsageError as e:
                result.problems.append(f"{name}: {e}")
            else:
                if tree.unsupported:
                    result.problems.append(f"{name}: unpinnable entries appeared: {', '.join(tree.unsupported[:5])}")
                if tree.digest != entry.get("content_sha256"):
                    result.problems.append(
                        f"{name}: content drifted from the approved hash "
                        f"({str(entry.get('content_sha256'))[:12]}… → {tree.digest[:12]}…)"
                    )
        ref = entry.get("audit") if isinstance(entry.get("audit"), dict) else {}
        rec = records.get(ref.get("seq"))
        if (
            rec is None
            or rec.get("hash") != ref.get("hash")
            or rec.get("event") != "installed"
            or (rec.get("data") or {}).get("name") != name
            or (rec.get("data") or {}).get("content_sha256") != entry.get("content_sha256")
        ):
            result.problems.append(
                f"{name}: no matching `installed` record in the audit log (lock edited by hand, or audit log cut)"
            )
    if dest is not None and Path(dest).is_dir():
        for child in sorted(Path(dest).iterdir()):
            if child.name.startswith(".") or not (child / SKILL_FILE).is_file():
                continue
            if child.resolve() not in installed_paths:
                result.unmanaged.append(child.name)
    return result
