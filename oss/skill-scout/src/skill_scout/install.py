"""`install`: fetch → pin → scan → (block | human approval) → atomic copy → lock + audit.

Time-of-check/time-of-use: the source is fetched once into a private workspace. The bytes that
are hashed, scanned and shown to the human are the ones copied: the copy writes only the files
of the pinned manifest, checks each file's sha256 while writing, and re-hashes the staged copy
before the rename. Anything that changes in between aborts the install with nothing installed.

Nothing from the skill runs: files are copied as data (mode 0644, or 0755 when the pinned
entry is executable; never setuid), symlinks and special files are refused.

One approval can install the same content into several agents' folders (`--agent` repeated):
the human approves one hash; each folder gets its own lock entry and `installed` audit record.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from . import audit, lock
from . import waivers as waivers_mod
from .approval import Approval, approve
from .engines import Engine
from .errors import ApprovalError, BlockedError, UsageError, VerifyError
from .locate import SkillDir, install_name, select
from .report import ScanReport, scan_dir
from .source import GITHUB, Source, fetch, parse_source
from .treehash import TreeHash, tree_hash

DEFAULT_DEST = ".claude/skills"
_CHUNK = 1024 * 1024


@dataclass
class Prepared:
    src: Source
    skill: SkillDir
    name: str
    report: ScanReport


@dataclass
class InstallResult:
    name: str
    path: Path
    report: ScanReport
    approval: Approval
    audit_seq: int
    paths: tuple[Path, ...] = ()


def audit_data(report: ScanReport, name: str | None = None) -> dict:
    data = {
        "source": report.source,
        "commit": report.commit,
        "skill_path": report.skill_path,
        "content_sha256": report.tree.digest,
        "verdict": report.verdict,
        "counts": report.counts,
        "waivers": sorted({f.waiver for f in report.waived if f.waiver}),
        "engines": [{"name": e.name, "version": e.version, "ok": e.ok} for e in report.engines],
    }
    if name:
        data["name"] = name
    return data


@contextmanager
def prepared(
    src: Source,
    engines: list[Engine],
    waivers: list[waivers_mod.Waiver],
    *,
    base_url: str = GITHUB,
    skill_name: str | None = None,
):
    """Fetch `src` into a private workspace, select the skill and scan it (with waivers)."""
    with tempfile.TemporaryDirectory(prefix="skill-scout-ws-") as ws:
        fetched = fetch(src, Path(ws) / "src", base_url=base_url)
        skill = select(fetched.root, skill_name or src.skill)
        name = install_name(skill)
        report = scan_dir(
            skill.path,
            engines,
            source=src.display,
            source_type=src.kind,
            waivers=waivers,
            repo_url=src.repo_url,
            ref=src.ref,
            commit=fetched.commit,
            skill_path=skill.rel,
        )
        yield Prepared(src, skill, name, report)


def block_if_unsafe(p: Prepared, audit_path: Path) -> None:
    if p.report.verdict in ("dangerous", "not_scanned"):
        audit.append(audit_path, "blocked", audit_data(p.report, p.name))
        counts = ", ".join(f"{k} {v}" for k, v in p.report.counts.items() if v) or "engine failure"
        raise BlockedError(f"blocked: {p.name} is {p.report.verdict.upper()} ({counts}); nothing was installed")


def copy_pinned(src_root: Path, tree: TreeHash, dest: Path) -> None:
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


def stage_and_swap(skill_path: Path, tree: TreeHash, target: Path) -> None:
    """Copy the pinned files next to `target`, check the copy, then rename it into place."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".skill-scout-{target.name}-", dir=target.parent))
    try:
        staged = staging / target.name
        staged.mkdir()
        copy_pinned(skill_path, tree, staged)
        if tree_hash(staged).digest != tree.digest:
            raise VerifyError("staged copy does not match the approved content; nothing was installed")
        if target.exists():
            os.replace(target, staging / ".previous")
        os.replace(staged, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def spec_of(src: Source, name: str, lock_dir: Path) -> str:
    """What `update` fetches again: owner/repo@name, or the local folder relative to the lock."""
    if src.kind == "github":
        return f"{src.owner}/{src.repo}@{name}"
    return "./" + lock.rel_to(src.path or Path("."), lock_dir) if src.path else src.raw


def record(
    data: dict,
    key: str,
    p: Prepared,
    approval: Approval,
    audit_path: Path,
    lock_path: Path,
    extra: dict | None = None,
) -> dict:
    """Audit an `installed` event for `key` and write its lock entry (not saved yet)."""
    report = p.report
    rec = audit.append(
        audit_path,
        "installed",
        {**audit_data(report, p.name), "approval": approval.to_json(), "install_path": key, **(extra or {})},
    )
    data["skills"][key] = {
        "name": p.name,
        "spec": spec_of(p.src, p.name, lock_path.parent),
        "ref": p.src.ref,
        "source": report.source,
        "source_type": p.src.kind,
        "repo_url": p.src.repo_url,
        "commit": report.commit,
        "skill_path": report.skill_path,
        "content_sha256": report.tree.digest,
        "files": report.tree.files,
        "bytes": report.tree.size,
        "verdict": report.verdict,
        "counts": report.counts,
        "waivers": sorted({f.waiver for f in report.waived if f.waiver}),
        "engines": [{"name": e.name, "version": e.version} for e in report.engines],
        "approval": approval.to_json(),
        "audit": {"seq": rec["seq"], "hash": rec["hash"]},
    }
    return rec


def install(
    source_spec: str,
    *,
    engines: list[Engine],
    dest: Path | list[Path] = Path(DEFAULT_DEST),
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
    dests = [Path(d) for d in (dest if isinstance(dest, list) else [dest])]
    if not dests:
        raise UsageError("no destination")
    src = parse_source(source_spec, ref)
    lock_path, audit_path = Path(lock_path), Path(audit_path)
    data = lock.load(lock_path)  # fail early on a broken lock file
    with prepared(src, engines, waivers_mod.trusted(data, audit_path), base_url=base_url) as p:
        audit.append(audit_path, "scan", audit_data(p.report, p.name))
        block_if_unsafe(p, audit_path)

        targets = [d / p.name for d in dests]
        for target in targets:
            if target.exists() or target.is_symlink():
                entry = data["skills"].get(lock.rel_to(target, lock_path.parent))
                if not replace:
                    raise UsageError(f"{target} already exists; use `skill-scout update` (or --replace)")
                if entry is None or tree_hash(target).digest != entry.get("content_sha256"):
                    raise VerifyError(f"{target} has changes that are not in the lock file; refusing to replace it")

        where = "".join(f"\n  → {t}" for t in targets)
        try:
            approval = approve(
                p.report, approve_sha256=approve_sha256, env=env, interactive=interactive, ask=ask, extra=where
            )
        except ApprovalError as e:
            audit.append(audit_path, "approval_rejected", {**audit_data(p.report, p.name), "reason": str(e)[:300]})
            raise

        records = []
        for target in targets:  # lock saved after each folder: a failure half-way leaves a true lock
            stage_and_swap(p.skill.path, p.report.tree, target)
            records.append(record(data, lock.rel_to(target, lock_path.parent), p, approval, audit_path, lock_path))
            lock.save(lock_path, data)
        return InstallResult(p.name, targets[0], p.report, approval, records[0]["seq"], tuple(targets))
