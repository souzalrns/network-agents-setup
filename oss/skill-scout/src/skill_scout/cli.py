"""Command line: `skill-scout find | scan | install | list | update | uninstall | waive | verify`."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import __version__, lock
from . import waivers as waivers_mod
from .agents import AGENTS, dests_for
from .engines import SEVERITIES, get_engines
from .errors import EXIT_ENGINE, EXIT_FINDINGS, EXIT_OK, EXIT_VERIFY, ScoutError
from .find import scan_candidates, search
from .install import install
from .lifecycle import list_skills, uninstall, update, waive
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


def _dests(args: argparse.Namespace) -> list[Path]:
    if args.dest:
        return [Path(d) for d in args.dest]
    return [Path(d) for d in dests_for(args.agent)]


def _lock_waivers(lock_file: str, audit_file: str) -> list[waivers_mod.Waiver]:
    if not Path(lock_file).is_file():
        return []
    return waivers_mod.trusted(lock.load(Path(lock_file)), Path(audit_file))


def cmd_find(args: argparse.Namespace) -> int:
    cands = search(args.query, args.limit)
    if args.scan:
        scan_candidates(cands, get_engines(_engines(args.engine)), args.scan)
    if args.format == "json":
        print(json.dumps([c.to_json() for c in cands], indent=2, ensure_ascii=False))
        return EXIT_OK
    if not cands:
        print(f"no skills found for {args.query!r}")
    for c in cands:
        installs = f"{c.installs:>8} installs" if c.installs is not None else " " * 17
        verdict = ""
        if c.scan:
            verdict = f"  [{c.scan['verdict']}]" + (
                f" {c.scan['content_sha256'][:12]}…" if "content_sha256" in c.scan else ""
            )
        print(f"{installs}  {c.spec or c.name}{verdict}")
    if cands:
        print("\nNothing was installed. Next: skill-scout scan <spec>, then skill-scout install <spec>.")
    return EXIT_OK


def cmd_scan(args: argparse.Namespace) -> int:
    engines = get_engines(_engines(args.engine))
    src = parse_source(args.source, args.ref)
    waivers = _lock_waivers(args.lock, args.audit)
    with tempfile.TemporaryDirectory(prefix="skill-scout-ws-") as ws:
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
            waivers=waivers,
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
        if any(SEVERITIES.index(f.severity) >= threshold for f in report.findings if f.waiver is None):
            return EXIT_FINDINGS
    return EXIT_OK


def cmd_install(args: argparse.Namespace) -> int:
    result = install(
        args.source,
        engines=get_engines(_engines(args.engine)),
        dest=_dests(args),
        lock_path=Path(args.lock),
        audit_path=Path(args.audit),
        ref=args.ref,
        approve_sha256=args.approve_sha256,
        replace=args.replace,
    )
    where = "\n".join(f"  → {p}" for p in result.paths)
    print(
        f"installed {result.name}\n{where}\n"
        f"  content {result.report.tree.digest} ({result.report.verdict}), "
        f"approved by {result.approval.actor} ({result.approval.mode}), audit #{result.audit_seq}\n"
        f"  pinned in {args.lock}"
    )
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    rows = list_skills(Path(args.lock))
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif not rows:
        print(f"no skills in {args.lock}")
    for r in rows if args.format == "text" else []:
        waived = f", {len(r['waivers'])} waiver(s)" if r["waivers"] else ""
        print(
            f"{r['status']:<14} {r['install_path']}  {r['source']}  "
            f"{(r['commit'] or '')[:12]}  {r['verdict']}{waived}  approved by {r['approved_by']}"
        )
    return EXIT_OK if all(r["status"] == "ok" for r in rows) else EXIT_VERIFY


def cmd_update(args: argparse.Namespace) -> int:
    results = update(
        engines=get_engines(_engines(args.engine)),
        lock_path=Path(args.lock),
        audit_path=Path(args.audit),
        name=args.name,
        check=args.check,
        approve_sha256=args.approve_sha256,
    )
    if args.format == "json":
        print(json.dumps([r.to_json() for r in results], indent=2))
    for r in results if args.format == "text" else []:
        change = ""
        if r.changes:
            change = f" (+{len(r.changes['added'])} ~{len(r.changes['changed'])} -{len(r.changes['removed'])})"
        new = f" → {r.new[:12]}…" if r.new and r.new != r.old else ""
        print(f"{r.status:<11} {r.install_path}{new}{change}" + (f"  {r.message}" if r.message else ""))
    if any(r.status in ("blocked", "drifted") for r in results):
        return EXIT_VERIFY
    if args.check and any(r.status == "available" for r in results):
        return EXIT_FINDINGS
    return EXIT_OK


def cmd_uninstall(args: argparse.Namespace) -> int:
    dest = Path(args.dest) if args.dest else (Path(dests_for([args.agent])[0]) if args.agent else None)
    removed = uninstall(
        args.name,
        lock_path=Path(args.lock),
        audit_path=Path(args.audit),
        dest=dest,
        discard_changes=args.discard_local_changes,
    )
    print("\n".join(f"uninstalled {k}" for k in removed))
    return EXIT_OK


def cmd_waive(args: argparse.Namespace) -> int:
    w = waive(
        args.source,
        engines=get_engines(_engines(args.engine)),
        rule=args.rule,
        path=args.path,
        reason=args.reason,
        expires=args.expires,
        ref=args.ref,
        lock_path=Path(args.lock),
        audit_path=Path(args.audit),
        approve_sha256=args.approve_sha256,
    )
    print(
        f"waiver {w.id}: {w.rule} on {w.path} accepted for content {w.content_sha256[:12]}… until {w.expires}\n"
        f"  reason: {w.reason}\n  recorded in {args.lock} and {args.audit}"
    )
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify(Path(args.lock), Path(args.audit), Path(args.dest) if args.dest else None)
    if args.format == "json":
        print(json.dumps(result.to_json(), indent=2))
    else:
        print(f"skill-scout verify: {result.checked} skill(s) checked — {'OK' if result.ok else 'FAILED'}")
        for p in result.problems:
            print(f"  ✗ {p}")
        for u in result.unmanaged:
            print(f"  ! unmanaged (not in the lock file): {u}")
    return EXIT_OK if result.ok else EXIT_VERIFY


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skill-scout",
        description="Find, scan, approve, pin and audit third-party Agent Skills.",
        epilog="Agents for --agent: " + ", ".join(sorted(AGENTS)),
    )
    p.add_argument("--version", action="version", version=f"skill-scout {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def engine(sp):
        sp.add_argument(
            "--engine",
            action="append",
            metavar="NAME",
            help="scan engine: asm (default), cisco; repeat or comma-separate to run several",
        )

    def source(sp):
        sp.add_argument("source", help="owner/repo[@skill] (skills.sh syntax) or a local directory")
        sp.add_argument("--ref", help="branch, tag or commit to fetch (GitHub sources)")
        engine(sp)

    def files(sp, audit_file=True):
        sp.add_argument("--lock", default=lock.DEFAULT_LOCK, help=f"lock file (default: {lock.DEFAULT_LOCK})")
        if audit_file:
            sp.add_argument("--audit", default=lock.DEFAULT_AUDIT, help=f"audit log (default: {lock.DEFAULT_AUDIT})")

    def approval(sp):
        sp.add_argument(
            "--approve-sha256",
            metavar="HASH",
            help="non-interactive approval: the full content hash from a scan report you reviewed",
        )

    f = sub.add_parser("find", help="search skills.sh (nothing is installed); --scan N scans the first N results")
    f.add_argument("query")
    f.add_argument("--limit", type=int, default=10)
    f.add_argument("--scan", type=int, default=0, metavar="N")
    f.add_argument("--format", choices=("text", "json"), default="text")
    engine(f)
    f.set_defaults(func=cmd_find)

    s = sub.add_parser("scan", help="scan a skill (nothing is installed)")
    source(s)
    s.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    s.add_argument("--output", "-o", help="write the report to this file instead of stdout")
    s.add_argument("--srcroot", help="SARIF: repository root the paths are relative to (default: current dir)")
    s.add_argument("--category", default="skill-scout", help="SARIF automationDetails category")
    s.add_argument(
        "--fail-on",
        choices=FAIL_ON,
        default="high",
        help="exit 1 when an active finding has this severity or more (default: high)",
    )
    s.add_argument("--lock", default=lock.DEFAULT_LOCK, help="apply the waivers of this lock file (if it exists)")
    s.add_argument("--audit", default=lock.DEFAULT_AUDIT, help="audit log that must vouch for those waivers")
    s.set_defaults(func=cmd_scan)

    i = sub.add_parser("install", help="scan, ask a human to approve, then install and pin")
    source(i)
    i.add_argument(
        "--agent",
        action="append",
        metavar="AGENT",
        help="install for this agent (repeatable; default claude-code); see the list below",
    )
    i.add_argument("--dest", action="append", metavar="DIR", help="skills folder (overrides --agent; repeatable)")
    files(i)
    approval(i)
    i.add_argument("--replace", action="store_true", help="replace an installed, unmodified copy (prefer `update`)")
    i.set_defaults(func=cmd_install)

    ls = sub.add_parser("list", help="installed skills, with their status against the lock file")
    files(ls, audit_file=False)
    ls.add_argument("--format", choices=("text", "json"), default="text")
    ls.set_defaults(func=cmd_list)

    u = sub.add_parser("update", help="fetch again; show what changed; a human approves the new content")
    u.add_argument("name", nargs="?", help="only this skill (default: all)")
    u.add_argument("--check", action="store_true", help="only report available updates (exit 1 if any)")
    files(u)
    approval(u)
    engine(u)
    u.add_argument("--format", choices=("text", "json"), default="text")
    u.set_defaults(func=cmd_update)

    rm = sub.add_parser("uninstall", help="remove an installed skill (refuses if it was modified)")
    rm.add_argument("name")
    rm.add_argument("--agent", help="the agent whose copy to remove, when installed for several")
    rm.add_argument("--dest", help="the skills folder whose copy to remove")
    rm.add_argument("--discard-local-changes", action="store_true")
    files(rm)
    rm.set_defaults(func=cmd_uninstall)

    w = sub.add_parser("waive", help="accept one finding as a false positive, for this exact content, until a date")
    source(w)
    w.add_argument("--rule", required=True, help="engine/rule, as in the report (e.g. asm/destructive-remove)")
    w.add_argument("--path", required=True, help="the finding's path, as in the report")
    w.add_argument("--reason", required=True, help="why this is a false positive (at least 10 characters)")
    w.add_argument("--expires", help="YYYY-MM-DD (default: 90 days; max 365)")
    files(w)
    approval(w)
    w.set_defaults(func=cmd_waive)

    v = sub.add_parser("verify", help="check installed skills against the lock file and the audit chain")
    files(v)
    v.add_argument("--dest", help="also report skill folders here that are not in the lock file")
    v.add_argument("--format", choices=("text", "json"), default="text")
    v.set_defaults(func=cmd_verify)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ScoutError as e:
        print(f"skill-scout: {e}", file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("skill-scout: interrupted", file=sys.stderr)
        return 130
