"""Scan a folder with the selected engines and turn the findings into a verdict.

Verdict (the default policy of the engines: high and critical block):
- `dangerous`: any high or critical finding, or a file that cannot be pinned (symlink,
  special file). Never installable;
- `risky`: medium findings. Installable only after a human approves this exact content;
- `safe`: info or low findings only. Still needs approval: a clean static scan is not proof
  that a skill is safe;
- `not_scanned`: an engine failed. Fail-closed: never installable.

Findings accepted by an active waiver (waivers.py) stay in the report, marked, but do not count
for the verdict. The Agent Skills spec checks (spec.py) run on every scan.
"""

from __future__ import annotations

import datetime as _dt
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, spec
from . import waivers as waivers_mod
from .engines import SEVERITIES, Engine, Finding
from .errors import EngineError
from .locate import SkillDir, discover
from .treehash import TreeHash, tree_hash

REPORT_SCHEMA = "skill-scout/report-v1"
VERDICTS = ("safe", "risky", "dangerous", "not_scanned")
BLOCKING = ("high", "critical")


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def verdict_for(findings: list[Finding], engines_ok: bool) -> str:
    if not engines_ok:
        return "not_scanned"
    sev = {f.severity for f in findings if f.waiver is None}
    if sev & set(BLOCKING):
        return "dangerous"
    return "risky" if "medium" in sev else "safe"


def max_severity(findings: list[Finding]) -> str:
    return max((f.severity for f in findings if f.waiver is None), key=SEVERITIES.index, default="none")


def _counts(findings: list[Finding]) -> dict[str, int]:
    c = Counter(f.severity for f in findings if f.waiver is None)
    return {s: c.get(s, 0) for s in SEVERITIES}


@dataclass
class EngineRun:
    name: str
    version: str | None
    ok: bool
    error: str | None = None
    findings: int = 0

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "ok": self.ok,
            "error": self.error,
            "findings": self.findings,
        }


@dataclass
class SkillVerdict:
    rel: str
    name: str | None
    verdict: str
    counts: dict[str, int]

    def to_json(self) -> dict:
        return {"path": self.rel, "name": self.name, "verdict": self.verdict, "counts": self.counts}


@dataclass
class ScanReport:
    source: str
    source_type: str
    scanned_path: Path
    tree: TreeHash
    engines: list[EngineRun]
    findings: list[Finding]
    skills: list[SkillVerdict] = field(default_factory=list)
    repo_url: str | None = None
    ref: str | None = None
    commit: str | None = None
    skill_path: str = ""
    generated_at: str = field(default_factory=now)

    @property
    def engines_ok(self) -> bool:
        return bool(self.engines) and all(e.ok for e in self.engines)

    @property
    def verdict(self) -> str:
        return verdict_for(self.findings, self.engines_ok)

    @property
    def counts(self) -> dict[str, int]:
        """Active findings per severity (waived ones excluded)."""
        return _counts(self.findings)

    @property
    def waived(self) -> list[Finding]:
        return [f for f in self.findings if f.waiver]

    def to_json(self) -> dict:
        return {
            "schema": REPORT_SCHEMA,
            "tool": {"name": "skill-scout", "version": __version__},
            "generated_at": self.generated_at,
            "source": {
                "spec": self.source,
                "type": self.source_type,
                "repo_url": self.repo_url,
                "ref": self.ref,
                "commit": self.commit,
                "skill_path": self.skill_path,
            },
            "content": self.tree.to_json(),
            "verdict": self.verdict,
            "max_severity": max_severity(self.findings),
            "counts": self.counts,
            "waived": len(self.waived),
            "engines": [e.to_json() for e in self.engines],
            "skills": [s.to_json() for s in self.skills],
            "findings": [f.to_json() for f in sorted(self.findings, key=_order)],
        }


def _order(f: Finding) -> tuple:
    return (-SEVERITIES.index(f.severity), f.path, f.engine, f.rule)


def _owner(path: str, skills: list[SkillDir]) -> SkillDir | None:
    best = None
    for s in skills:
        if s.rel == "" or path == s.rel or path.startswith(f"{s.rel}/"):
            if best is None or len(s.rel) > len(best.rel):
                best = s
    return best


def scan_dir(
    path: Path,
    engines: list[Engine],
    *,
    source: str,
    source_type: str,
    waivers: list[waivers_mod.Waiver] | None = None,
    **meta,
) -> ScanReport:
    """Hash and scan `path` (one skill, or a tree with many) with every engine, then apply waivers."""
    tree = tree_hash(path)
    runs: list[EngineRun] = []
    findings: list[Finding] = []
    for engine in engines:
        version = engine.version()
        try:
            found = engine.scan(path)
        except EngineError as e:
            runs.append(EngineRun(engine.name, version, False, str(e)))
            continue
        runs.append(EngineRun(engine.name, version, True, findings=len(found)))
        findings.extend(found)
    for entry in tree.unsupported:
        rel = entry.rsplit(" (", 1)[0]
        findings.append(
            Finding(
                "skill-scout",
                "unpinnable-entry",
                "high",
                rel,
                f"Cannot be pinned or installed: {entry}",
                "Remove symlinks and special files from the skill.",
            )
        )
    skills = discover(path)
    for s in skills:
        findings.extend(spec.check(s))
    findings = waivers_mod.apply(findings, tree.digest, waivers or [])
    verdicts = []
    for s in skills:
        own = [f for f in findings if _owner(f.path, skills) is s]
        verdicts.append(
            SkillVerdict(s.rel, s.name, verdict_for(own, bool(runs) and all(r.ok for r in runs)), _counts(own))
        )
    return ScanReport(source, source_type, path, tree, runs, findings, verdicts, **meta)


def render_text(report: ScanReport) -> str:
    d = report.to_json()
    src = d["source"]
    lines = [
        f"skill-scout {__version__} — {report.source}",
        f"  verdict:   {report.verdict.upper()}  (max severity: {d['max_severity']})",
        f"  content:   {report.tree.digest}  ({report.tree.files} files, {report.tree.size} bytes)",
    ]
    if src["commit"]:
        lines.append(f"  commit:    {src['commit']}" + (f"  ({src['skill_path']})" if src["skill_path"] else ""))
    lines.append(
        "  engines:   "
        + ", ".join(f"{e.name} {e.version or '?'}" + ("" if e.ok else f" FAILED ({e.error})") for e in report.engines)
    )
    counts = ", ".join(f"{k} {v}" for k, v in d["counts"].items() if v)
    active = len(report.findings) - len(report.waived)
    lines.append(
        f"  findings:  {active}"
        + (f" ({counts})" if counts else "")
        + (f", {len(report.waived)} waived" if report.waived else "")
    )
    if len(report.skills) > 1:
        lines.append("  skills:")
        lines += [f"    {s.verdict:<11} {s.rel or '.'}" for s in report.skills]
    for f in sorted(report.findings, key=_order)[:200]:
        loc = f.path + (f":{f.line}" if f.line else "")
        tag = "WAIVED" if f.waiver else f.severity.upper()
        extra = f" — waiver {f.waiver}: {f.waiver_reason}" if f.waiver else ""
        lines.append(f"  [{tag:<8}] {loc}: {f.title} ({f.engine}/{f.rule}){extra}")
    if len(report.findings) > 200:
        lines.append(f"  … {len(report.findings) - 200} more (use --format json)")
    return "\n".join(lines) + "\n"
