"""Day-two commands: `list`, `update`, `uninstall` and `waive`.

`update` is where other tools re-install silently. Here:
- a lock entry pinned to a commit (`--ref <sha>`) is never moved;
- nothing changes unless the fetched content hash differs from the approved one;
- the installed copy must still match the lock (no local edits are overwritten);
- the human approves the NEW hash, after seeing what changed since the approved version
  (files added, changed, removed) and the new scan. `--check` only reports (exit 1 when there
  are updates, for CI);
- the audit record of the update carries the previous hash and the change list.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from . import audit, lock
from . import waivers as waivers_mod
from .approval import Approval, approve, confirm
from .engines import Engine
from .errors import ApprovalError, BlockedError, UsageError, VerifyError
from .install import audit_data, block_if_unsafe, prepared, record, stage_and_swap
from .report import render_text
from .source import GITHUB, Source, parse_source
from .treehash import TreeHash, tree_hash

_SHA1 = re.compile(r"^[0-9a-f]{40}$")
MAX_LISTED = 20


# --------------------------------------------------------------------------- helpers


def select_entries(data: dict, lock_dir: Path, name: str | None = None, dest: Path | None = None) -> list[tuple]:
    prefix = lock.rel_to(dest, lock_dir).rstrip("/") + "/" if dest is not None else None
    out = []
    for key, entry in sorted(data["skills"].items()):
        if not isinstance(entry, dict):
            continue
        if name is not None and entry.get("name") != name:
            continue
        if prefix is not None and not key.startswith(prefix):
            continue
        out.append((key, entry))
    return out


def entry_status(lock_dir: Path, key: str, entry: dict) -> str:
    path = lock_dir / key
    if not path.is_dir():
        return "missing"
    try:
        tree = tree_hash(path)
    except UsageError:
        return "unreadable"
    if tree.unsupported:
        return "unpinnable"
    return "ok" if tree.digest == entry.get("content_sha256") else "drifted"


def source_of(entry: dict, lock_dir: Path) -> Source:
    spec = str(entry.get("spec") or "")
    ref = entry.get("ref") or None
    if entry.get("source_type") == "local":
        path = (lock_dir / spec).resolve()
        if not path.is_dir():
            raise UsageError(f"local source {spec} no longer exists")
        return Source("local", spec, path=path)
    return parse_source(spec, ref)


def tree_diff(old: TreeHash, new: TreeHash) -> dict[str, list[str]]:
    o = {e.path: e for e in old.entries}
    n = {e.path: e for e in new.entries}
    return {
        "added": sorted(set(n) - set(o)),
        "removed": sorted(set(o) - set(n)),
        "changed": sorted(
            p for p in set(o) & set(n) if (o[p].sha256, o[p].executable) != (n[p].sha256, n[p].executable)
        ),
    }


def render_diff(diff: dict[str, list[str]]) -> str:
    lines = ["Changes since the approved version:"]
    for label, mark in (("added", "+"), ("changed", "~"), ("removed", "-")):
        paths = diff[label]
        lines += [f"  {mark} {p}" for p in paths[:MAX_LISTED]]
        if len(paths) > MAX_LISTED:
            lines.append(f"  {mark} … {len(paths) - MAX_LISTED} more {label}")
    if len(lines) == 1:
        lines.append("  (only file modes or metadata)")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- list


def list_skills(lock_path: Path) -> list[dict]:
    lock_path = Path(lock_path)
    data = lock.load(lock_path)
    live = {w.id: w for w in waivers_mod.load(data)}
    out = []
    for key, entry in select_entries(data, lock_path.parent):
        expired = [w for w in entry.get("waivers") or [] if w not in live or not live[w].active()]
        out.append(
            {
                "install_path": key,
                "name": entry.get("name"),
                "source": entry.get("source"),
                "commit": entry.get("commit"),
                "content_sha256": entry.get("content_sha256"),
                "verdict": entry.get("verdict"),
                "waivers": entry.get("waivers") or [],
                "approved_by": (entry.get("approval") or {}).get("actor"),
                "approved_at": (entry.get("approval") or {}).get("at"),
                "status": entry_status(lock_path.parent, key, entry) if not expired else "waiver-expired",
            }
        )
    return out


# --------------------------------------------------------------------------- update


@dataclass
class UpdateInfo:
    install_path: str
    name: str
    status: str  # up_to_date | pinned | available | updated | blocked | drifted | skipped
    old: str = ""
    new: str = ""
    commit: str | None = None
    changes: dict[str, list[str]] = field(default_factory=dict)
    message: str = ""

    def to_json(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def update(
    *,
    engines: list[Engine],
    lock_path: Path = Path(lock.DEFAULT_LOCK),
    audit_path: Path = Path(lock.DEFAULT_AUDIT),
    name: str | None = None,
    check: bool = False,
    approve_sha256: str | None = None,
    env: Mapping[str, str] | None = None,
    interactive: bool | None = None,
    ask: Callable[[str], str] = input,
    base_url: str = GITHUB,
) -> list[UpdateInfo]:
    env = os.environ if env is None else env
    interactive = sys.stdin.isatty() and sys.stderr.isatty() if interactive is None else interactive
    lock_path, audit_path = Path(lock_path), Path(audit_path)
    lock_dir = lock_path.parent
    data = lock.load(lock_path)
    entries = select_entries(data, lock_dir, name)
    if name is not None and not entries:
        raise UsageError(f"{name} is not in {lock_path}")
    results: list[UpdateInfo] = []
    for key, entry in entries:
        info = UpdateInfo(key, str(entry.get("name")), "up_to_date", old=str(entry.get("content_sha256")))
        results.append(info)
        if _SHA1.match(str(entry.get("ref") or "")):
            info.status, info.message = "pinned", "pinned to a commit (--ref); never moved"
            continue
        src = source_of(entry, lock_dir)
        with prepared(
            src, engines, waivers_mod.trusted(data, audit_path), base_url=base_url, skill_name=info.name
        ) as p:
            info.new, info.commit = p.report.tree.digest, p.report.commit
            if info.new == info.old:
                continue
            installed = lock_dir / key
            if entry_status(lock_dir, key, entry) != "ok":
                info.status, info.message = "drifted", "installed copy differs from the lock; run `verify`"
                continue
            info.changes = tree_diff(tree_hash(installed), p.report.tree)
            info.status = "available"
            if check:
                continue
            audit.append(audit_path, "scan", audit_data(p.report, p.name))
            try:
                block_if_unsafe(p, audit_path)
            except BlockedError as e:
                info.status, info.message = "blocked", str(e)
                continue
            if approve_sha256 is not None and approve_sha256.strip().lower() != info.new:
                info.status, info.message = "skipped", "--approve-sha256 is for other content"
                continue
            try:
                approval: Approval = approve(
                    p.report,
                    approve_sha256=approve_sha256,
                    env=env,
                    interactive=interactive,
                    ask=ask,
                    extra=render_diff(info.changes),
                )
            except ApprovalError as e:
                audit.append(audit_path, "approval_rejected", {**audit_data(p.report, p.name), "reason": str(e)[:300]})
                raise
            stage_and_swap(p.skill.path, p.report.tree, installed)
            record(data, key, p, approval, audit_path, lock_path, {"update_from": info.old, "changes": info.changes})
            lock.save(lock_path, data)
            info.status = "updated"
    return results


# --------------------------------------------------------------------------- uninstall


def uninstall(
    name: str,
    *,
    lock_path: Path = Path(lock.DEFAULT_LOCK),
    audit_path: Path = Path(lock.DEFAULT_AUDIT),
    dest: Path | None = None,
    discard_changes: bool = False,
) -> list[str]:
    lock_path, audit_path = Path(lock_path), Path(audit_path)
    lock_dir = lock_path.parent
    data = lock.load(lock_path)
    matches = select_entries(data, lock_dir, name, dest)
    if not matches:
        raise UsageError(f"{name} is not installed (per {lock_path})")
    if len(matches) > 1:
        where = ", ".join(k for k, _ in matches)
        raise UsageError(f"{name} is installed in {len(matches)} places ({where}); pick one with --agent or --dest")
    key, entry = matches[0]
    path = lock_dir / key
    status = entry_status(lock_dir, key, entry)
    if status in ("drifted", "unpinnable") and not discard_changes:
        raise VerifyError(f"{path} has local changes; re-run with --discard-local-changes to remove it anyway")
    if path.is_dir():
        shutil.rmtree(path)
    del data["skills"][key]
    audit.append(
        audit_path,
        "uninstalled",
        {
            "name": name,
            "install_path": key,
            "content_sha256": entry.get("content_sha256"),
            "discarded_local_changes": status != "ok" and status != "missing",
        },
    )
    lock.save(lock_path, data)
    return [key]


# --------------------------------------------------------------------------- waive


def waive(
    source_spec: str,
    *,
    engines: list[Engine],
    rule: str,
    path: str,
    reason: str | None,
    expires: str | None = None,
    ref: str | None = None,
    lock_path: Path = Path(lock.DEFAULT_LOCK),
    audit_path: Path = Path(lock.DEFAULT_AUDIT),
    approve_sha256: str | None = None,
    env: Mapping[str, str] | None = None,
    interactive: bool | None = None,
    ask: Callable[[str], str] = input,
    base_url: str = GITHUB,
) -> waivers_mod.Waiver:
    env = os.environ if env is None else env
    interactive = sys.stdin.isatty() and sys.stderr.isatty() if interactive is None else interactive
    reason = waivers_mod.check_reason(reason)
    expiry = waivers_mod.parse_expiry(expires)
    lock_path, audit_path = Path(lock_path), Path(audit_path)
    data = lock.load(lock_path)
    src = parse_source(source_spec, ref)
    with prepared(src, engines, [], base_url=base_url) as p:
        if not p.report.engines_ok:
            raise BlockedError("an engine failed: there is no verdict to waive a finding of")
        finding = next((f for f in p.report.findings if f.rule_id == rule and f.path == path), None)
        if finding is None:
            known = ", ".join(f"{f.rule_id} @ {f.path}" for f in p.report.findings[:10]) or "none"
            raise UsageError(f"no finding {rule} on {path} in this content (findings: {known})")
        waivers_mod.check_waivable(finding)
        digest = p.report.tree.digest
        approval = confirm(
            digest,
            what=f"waiving {rule} on {path} for this exact content until {expiry}",
            summary=render_text(p.report) + f"\nWaiver: {rule} on {path} — {reason} (until {expiry})\n",
            approve_sha256=approve_sha256,
            env=env,
            interactive=interactive,
            ask=ask,
        )
        wid = waivers_mod.waiver_id(digest, rule, path)
        w = waivers_mod.Waiver(wid, digest, rule, path, reason, expiry, p.report.source, approval.actor, approval.at)
        rec = audit.append(
            audit_path, "waiver_added", {**w.to_json(), "severity": finding.severity, "approval": approval.to_json()}
        )
        data["waivers"] = [x for x in data["waivers"] if x.get("id") != wid] + [
            {**w.to_json(), "audit": {"seq": rec["seq"], "hash": rec["hash"]}}
        ]
        lock.save(lock_path, data)
        return w
