"""`verify`: is what is installed still exactly what a human approved?

Checks, all reported (not just the first):
- the audit chain is intact (audit.verify);
- every lock entry: the install folder exists, holds no symlink or special file, and hashes to
  `content_sha256` (drift: a file added, removed, edited or made executable after approval);
- every lock entry points at an `installed` audit record (`audit.seq` + `audit.hash`) for the
  same install path and content: an entry added to the lock by hand, or a cut audit log, fails;
- every waiver in the lock points at its `waiver_added` audit record (a waiver added by hand
  fails), and every waiver an installed skill relies on still exists and has not expired;
- skill folders in the destination that are not in the lock (`--dest`) are reported as
  unmanaged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import audit, lock
from . import waivers as waivers_mod
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


def _matches(rec: dict | None, ref: dict, event: str, **fields) -> bool:
    if rec is None or rec.get("hash") != ref.get("hash") or rec.get("event") != event:
        return False
    data = rec.get("data") or {}
    return all(data.get(k) == v for k, v in fields.items())


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

    waivers = {}
    for raw in data.get("waivers") or []:
        if not isinstance(raw, dict):
            result.problems.append("waiver entry is not an object")
            continue
        w = waivers_mod.Waiver.from_json(raw)
        waivers[w.id] = w
        ref = raw.get("audit") if isinstance(raw.get("audit"), dict) else {}
        if not _matches(
            records.get(ref.get("seq")),
            ref,
            "waiver_added",
            id=w.id,
            content_sha256=w.content_sha256,
            rule=w.rule,
            path=w.path,
            expires=w.expires,
        ):
            result.problems.append(
                f"waiver {w.id}: no matching `waiver_added` record in the audit log (added to the lock by hand?)"
            )

    base = lock_path.parent
    installed_paths = set()
    for key, entry in sorted(data["skills"].items()):
        result.checked += 1
        if not isinstance(entry, dict):
            result.problems.append(f"{key}: lock entry is not an object")
            continue
        path = (base / key).resolve()
        installed_paths.add(path)
        if not path.is_dir():
            result.problems.append(f"{key}: not installed")
        else:
            try:
                tree = tree_hash(path)
            except UsageError as e:
                result.problems.append(f"{key}: {e}")
            else:
                if tree.unsupported:
                    result.problems.append(f"{key}: unpinnable entries appeared: {', '.join(tree.unsupported[:5])}")
                if tree.digest != entry.get("content_sha256"):
                    result.problems.append(
                        f"{key}: content drifted from the approved hash "
                        f"({str(entry.get('content_sha256'))[:12]}… → {tree.digest[:12]}…)"
                    )
        ref = entry.get("audit") if isinstance(entry.get("audit"), dict) else {}
        if not _matches(
            records.get(ref.get("seq")), ref, "installed", install_path=key, content_sha256=entry.get("content_sha256")
        ):
            result.problems.append(
                f"{key}: no matching `installed` record in the audit log (lock edited by hand, or audit log cut)"
            )
        for wid in entry.get("waivers") or []:
            w = waivers.get(wid)
            if w is None:
                result.problems.append(f"{key}: relies on waiver {wid}, which is not in the lock")
            elif not w.active():
                result.problems.append(
                    f"{key}: waiver {wid} ({w.rule} on {w.path}) expired on {w.expires}; "
                    "review the finding again (`skill-scout waive` or `uninstall`)"
                )
    if dest is not None and Path(dest).is_dir():
        for child in sorted(Path(dest).iterdir()):
            if child.name.startswith(".") or not (child / SKILL_FILE).is_file():
                continue
            if child.resolve() not in installed_paths:
                result.unmanaged.append(child.name)
    return result
