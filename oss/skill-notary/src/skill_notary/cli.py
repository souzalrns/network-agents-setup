"""Command line: `skill-notary scan | install | verify`."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import __version__, lock
from .engines import SEVERITIES, get_engines
from .errors import EXIT_ENGINE, EXIT_FINDINGS, EXIT_OK, EXIT_VERIFY, NotaryError
from .install import DEFAULT_DEST, install
from .locate import select
from .report import render_text, scan_dir
from .sarif import to_sarif
from .source import fetch, parse_source
from .verify import verify

FAIL_ON = ("none", "low", "medium", "high", "critical")


def _engines(values: list[str] | None) -> list[str]:
    names = [n.strip() for v in (values or ["asm"]) for n in v.split(",") if n.strip()]
    return names or ["asm"]


def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def cmd_scan(args: argparse.Namespace) -> int:
    engines = get_engines(_engines(args.engine))
    src = parse_source(args.source, args.ref)
    with tempfile.TemporaryDirectory(prefix="skill-notary-ws-") as ws:
        if src.kind == "local":
            target, commit, rel = Path(str(src.path)), None, ""
        else:
            fetched = fetch(src, Path(ws) / "src")
            commit = fetched.commit
            if src.skill:
                skill = select(fetched.root, src.skill)
                target, rel = skill.path, skill.rel
            else:
                target, rel = fetched.root, ""
        report = scan_dir(
            target,
            engines,
            source=src.display,
            source_type=src.kind,
            repo_url=src.repo_url,
            ref=src.ref,
            commit=commit,
            skill_path=rel,
        )
        if args.format == "json":
            text = json.dumps(report.to_json(), indent=2, ensure_ascii=False) + "\n"
        elif args.format == "sarif":
            srcroot = Path(args.srcroot) if args.srcroot else (Path.cwd() if src.kind == "local" else None)
            text = json.dumps(to_sarif([report], srcroot=srcroot, category=args.category), indent=2) + "\n"
        else:
            text = render_text(report)
    _write(text, args.output)
    if report.verdict == "not_scanned":
        return EXIT_ENGINE
    if args.fail_on != "none":
        threshold = SEVERITIES.index(args.fail_on)
        if any(SEVERITIES.index(f.severity) >= threshold for f in report.findings):
            return EXIT_FINDINGS
    return EXIT_OK


def cmd_install(args: argparse.Namespace) -> int:
    result = install(
        args.source,
        engines=get_engines(_engines(args.engine)),
        dest=Path(args.dest),
        lock_path=Path(args.lock),
        audit_path=Path(args.audit),
        ref=args.ref,
        approve_sha256=args.approve_sha256,
        replace=args.replace,
    )
    print(
        f"installed {result.name} → {result.path}\n"
        f"  content {result.report.tree.digest} ({result.report.verdict}), "
        f"approved by {result.approval.actor} ({result.approval.mode}), audit #{result.audit_seq}\n"
        f"  pinned in {args.lock}"
    )
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify(Path(args.lock), Path(args.audit), Path(args.dest) if args.dest else None)
    if args.format == "json":
        print(json.dumps(result.to_json(), indent=2))
    else:
        print(f"skill-notary verify: {result.checked} skill(s) checked — {'OK' if result.ok else 'FAILED'}")
        for p in result.problems:
            print(f"  ✗ {p}")
        for u in result.unmanaged:
            print(f"  ! unmanaged (not in the lock file): {u}")
    return EXIT_OK if result.ok else EXIT_VERIFY


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skill-notary", description="Scan, approve, pin and audit third-party Agent Skills."
    )
    p.add_argument("--version", action="version", version=f"skill-notary {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("source", help="owner/repo[@skill] (skills.sh syntax) or a local directory")
        sp.add_argument("--ref", help="branch, tag or commit to fetch (GitHub sources)")
        sp.add_argument(
            "--engine",
            action="append",
            metavar="NAME",
            help="scan engine: asm (default), cisco; repeat or comma-separate to run several",
        )

    s = sub.add_parser("scan", help="scan a skill (nothing is installed)")
    common(s)
    s.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    s.add_argument("--output", "-o", help="write the report to this file instead of stdout")
    s.add_argument("--srcroot", help="SARIF: repository root the paths are relative to (default: current dir)")
    s.add_argument("--category", default="skill-notary", help="SARIF automationDetails category")
    s.add_argument(
        "--fail-on",
        choices=FAIL_ON,
        default="high",
        help="exit 1 when a finding has this severity or more (default: high)",
    )
    s.set_defaults(func=cmd_scan)

    i = sub.add_parser("install", help="scan, ask a human to approve, then install and pin")
    common(i)
    i.add_argument("--dest", default=DEFAULT_DEST, help=f"skills folder (default: {DEFAULT_DEST})")
    i.add_argument("--lock", default=lock.DEFAULT_LOCK, help=f"lock file (default: {lock.DEFAULT_LOCK})")
    i.add_argument("--audit", default=lock.DEFAULT_AUDIT, help=f"audit log (default: {lock.DEFAULT_AUDIT})")
    i.add_argument(
        "--approve-sha256",
        metavar="HASH",
        help="non-interactive approval: the full content hash from a scan report you reviewed",
    )
    i.add_argument("--replace", action="store_true", help="update a skill that is already installed and pinned")
    i.set_defaults(func=cmd_install)

    v = sub.add_parser("verify", help="check installed skills against the lock file and the audit chain")
    v.add_argument("--lock", default=lock.DEFAULT_LOCK)
    v.add_argument("--audit", default=lock.DEFAULT_AUDIT)
    v.add_argument("--dest", help="also report skill folders here that are not in the lock file")
    v.add_argument("--format", choices=("text", "json"), default="text")
    v.set_defaults(func=cmd_verify)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except NotaryError as e:
        print(f"skill-notary: {e}", file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("skill-notary: interrupted", file=sys.stderr)
        return 130
