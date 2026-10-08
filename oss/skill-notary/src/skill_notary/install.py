"""`install`: fetch → pin → scan → (block | human approval) → atomic copy → lock + audit.

Time-of-check/time-of-use: the source is fetched once into a private workspace. The bytes that
are hashed, scanned and shown to the human are the ones copied: the copy writes only the files
of the pinned manifest, checks each file's sha256 while writing, and re-hashes the staged copy
before the rename. Anything that changes in between aborts the install with nothing installed.

Nothing from the skill runs: files are copied as data (mode 0644, or 0755 when the pinned
entry is executable; never setuid), symlinks and special files are refused.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from . import audit, lock
from .approval import Approval, approve
from .engines import Engine
from .errors import ApprovalError, BlockedError, UsageError, VerifyError
from .locate import install_name, select
from .report import ScanReport, scan_dir
from .source import GITHUB, Source, fetch, parse_source
from .treehash import TreeHash, tree_hash

DEFAULT_DEST = ".claude/skills"
_CHUNK = 1024 * 1024


@dataclass
class InstallResult:
    name: str
    path: Path
    report: ScanReport
    approval: Approval
    audit_seq: int


def _scan_meta(src: Source, commit: str | None, skill_rel: str) -> dict:
    return {"repo_url": src.repo_url, "ref": src.ref, "commit": commit, "skill_path": skill_rel}


def _audit_data(report: ScanReport, name: str | None = None) -> dict:
    data = {
        "source": report.source,
        "commit": report.commit,
        "skill_path": report.skill_path,
        "content_sha256": report.tree.digest,
        "verdict": report.verdict,
        "counts": report.counts,
        "engines": [{"name": e.name, "version": e.version, "ok": e.ok} for e in report.engines],
    }
    if name:
        data["name"] = name
    return data


def _copy_pinned(src_root: Path, tree: TreeHash, dest: Path) -> None:
    """Write exactly the pinned files into `dest`, verifying each sha256 as it is written."""
    for entry in tree.entries:
        src = src_root / entry.path
        out = dest / entry.path
        if src.is_symlink() or not src.is_file():
            raise VerifyError(f"{entry.path} changed type after it was scanned")
        out.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        with src.open("rb") as fi, out.open("xb") as fo:
            for chunk in iter(lambda: fi.read(_CHUNK), b""):
                h.update(chunk)
                fo.write(chunk)
        if h.hexdigest() != entry.sha256:
            raise VerifyError(f"{entry.path} changed after it was scanned (expected {entry.sha256[:12]}…)")
        os.chmod(out, 0o755 if entry.executable else 0o644)


def install(
    source_spec: str,
    *,
    engines: list[Engine],
    dest: Path = Path(DEFAULT_DEST),
    lock_path: Path = Path(lock.DEFAULT_LOCK),
    audit_path: Path = Path(lock.DEFAULT_AUDIT),
    ref: str | None = None,
    approve_sha256: str | None = None,
    replace: bool = False,
    env: Mapping[str, str] | None = None,
    interactive: bool | None = None,
    ask: Callable[[str], str] = input,
    base_url: str = GITHUB,
) -> InstallResult:
    env = os.environ if env is None else env
    interactive = sys.stdin.isatty() and sys.stderr.isatty() if interactive is None else interactive
    src = parse_source(source_spec, ref)
    dest, lock_path, audit_path = Path(dest), Path(lock_path), Path(audit_path)
    data = lock.load(lock_path)  # fail early on a broken lock file
    with tempfile.TemporaryDirectory(prefix="skill-notary-ws-") as ws:
        fetched = fetch(src, Path(ws) / "src", base_url=base_url)
        skill = select(fetched.root, src.skill)
        name = install_name(skill)
        report = scan_dir(
            skill.path, engines, source=src.display, source_type=src.kind, **_scan_meta(src, fetched.commit, skill.rel)
        )
        audit.append(audit_path, "scan", _audit_data(report, name))
        if report.verdict in ("dangerous", "not_scanned"):
            audit.append(audit_path, "blocked", _audit_data(report, name))
            raise BlockedError(
                f"blocked: {name} is {report.verdict.upper()} "
                f"({', '.join(f'{k} {v}' for k, v in report.counts.items() if v) or 'engine failure'}); "
                "nothing was installed"
            )

        target = dest / name
        if target.exists() or target.is_symlink():
            entry = data["skills"].get(name)
            if not replace:
                raise UsageError(f"{target} already exists; use --replace to update it")
            if entry is None or tree_hash(target).digest != entry.get("content_sha256"):
                raise VerifyError(f"{target} has changes that are not in the lock file; refusing to replace it")

        try:
            approval = approve(report, approve_sha256=approve_sha256, env=env, interactive=interactive, ask=ask)
        except ApprovalError as e:
            audit.append(audit_path, "approval_rejected", {**_audit_data(report, name), "reason": str(e)[:300]})
            raise

        dest.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".skill-notary-{name}-", dir=dest))
        try:
            staged = staging / name
            staged.mkdir()
            _copy_pinned(skill.path, report.tree, staged)
            if tree_hash(staged).digest != report.tree.digest:
                raise VerifyError("staged copy does not match the approved content; nothing was installed")
            backup = staging / ".previous"
            if target.exists():
                os.replace(target, backup)
            os.replace(staged, target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    record = audit.append(
        audit_path,
        "installed",
        {
            **_audit_data(report, name),
            "approval": approval.to_json(),
            "install_path": lock.rel_to(target, lock_path.parent),
        },
    )
    data["skills"][name] = {
        "source": report.source,
        "source_type": src.kind,
        "repo_url": src.repo_url,
        "ref": src.ref,
        "commit": report.commit,
        "skill_path": report.skill_path,
        "content_sha256": report.tree.digest,
        "files": report.tree.files,
        "bytes": report.tree.size,
        "verdict": report.verdict,
        "counts": report.counts,
        "engines": [{"name": e.name, "version": e.version} for e in report.engines],
        "install_path": lock.rel_to(target, lock_path.parent),
        "approval": approval.to_json(),
        "audit": {"seq": record["seq"], "hash": record["hash"]},
    }
    lock.save(lock_path, data)
    return InstallResult(name, target, report, approval, record["seq"])
