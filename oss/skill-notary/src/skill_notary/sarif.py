"""SARIF 2.1.0 for GitHub code scanning (and any SARIF viewer).

One run, `tool.driver` = skill-notary, `tool.extensions` = the engines that ran. Rule ids are
`<engine>/<rule>`. What GitHub reads (docs: "SARIF support for code scanning"):
- `properties.security-severity` on each rule (critical 9.5, high 8.0, medium 5.5, low 3.0;
  info has none, so it shows as a plain note) and `properties.tags` with `security`;
- `level`: critical/high → error, medium → warning, low/info → note;
- a location per result, relative to `%SRCROOT%` (the repository root given by --srcroot), with
  `region.startLine` (1 when the engine gives no line);
- `partialFingerprints`, stable across runs (rule, path, title; never the line), so an alert
  survives unrelated edits;
- `automationDetails.id` as the category, and at most 25 000 results per run (capped at 5000).
Findings never carry descriptions or snippets (see engines.py), so no matched secret reaches it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import __version__
from .engines import Finding
from .report import ScanReport

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
INFO_URI = "https://github.com/souzalrns/network-agents-setup/tree/main/oss/skill-notary"
MAX_RESULTS = 5000
SECURITY_SEVERITY = {"critical": "9.5", "high": "8.0", "medium": "5.5", "low": "3.0"}
LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}
ENGINE_URI = {
    "asm": "https://github.com/mazen160/skills-manager",
    "cisco": "https://github.com/cisco-ai-defense/skill-scanner",
    "skill-notary": INFO_URI,
}


def _uri(report: ScanReport, finding: Finding, srcroot: Path | None) -> tuple[str, str]:
    rel = "" if finding.path in ("", ".") else finding.path
    if srcroot is not None:
        try:
            base = report.scanned_path.resolve().relative_to(srcroot.resolve()).as_posix()
        except ValueError:
            base = None
        if base is not None:
            full = "/".join(p for p in (base if base != "." else "", rel) if p)
            return full or ".", "%SRCROOT%"
    return rel or ".", "SKILLROOT"


def fingerprint(f: Finding, uri: str) -> str:
    return hashlib.sha256(f"{f.engine}/{f.rule}\0{uri}\0{f.title}".encode()).hexdigest()[:32]


def to_sarif(reports: list[ScanReport], *, srcroot: Path | None = None, category: str = "skill-notary") -> dict:
    rules: dict[str, dict] = {}
    results: list[dict] = []
    engines: dict[str, str | None] = {}
    notifications: list[dict] = []
    truncated = 0
    for report in reports:
        for e in report.engines:
            engines.setdefault(e.name, e.version)
            if not e.ok:
                notifications.append(
                    {
                        "level": "error",
                        "message": {"text": f"engine {e.name} failed: {e.error}"},
                        "descriptor": {"id": f"engine-{e.name}"},
                    }
                )
        for f in report.findings:
            if len(results) >= MAX_RESULTS:
                truncated += 1
                continue
            rule_id = f"{f.engine}/{f.rule}"
            if rule_id not in rules:
                props: dict = {
                    "tags": ["security", "agent-skills", f.engine] + ([f.category] if f.category else []),
                    "precision": "medium",
                }
                if f.severity in SECURITY_SEVERITY:
                    props["security-severity"] = SECURITY_SEVERITY[f.severity]
                rules[rule_id] = {
                    "id": rule_id,
                    "name": "".join(w.capitalize() for w in f.rule.replace("-", "_").replace(".", "_").split("_") if w)
                    or "Unspecified",
                    "shortDescription": {"text": f.title or rule_id},
                    "fullDescription": {"text": f.title or rule_id},
                    "help": {
                        "text": f.recommendation or "Review this finding before installing the skill.",
                        "markdown": f.recommendation or "Review this finding before installing the skill.",
                    },
                    "helpUri": ENGINE_URI.get(f.engine, INFO_URI),
                    "defaultConfiguration": {"level": LEVEL[f.severity]},
                    "properties": props,
                }
            uri, base_id = _uri(report, f, srcroot)
            results.append(
                {
                    "ruleId": rule_id,
                    "ruleIndex": list(rules).index(rule_id),
                    "level": LEVEL[f.severity],
                    "message": {
                        "text": (f.title or rule_id)
                        + (f" Recommendation: {f.recommendation}" if f.recommendation else "")
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": uri, "uriBaseId": base_id},
                                "region": {"startLine": f.line or 1},
                            }
                        }
                    ],
                    "partialFingerprints": {"skillNotaryFinding/v1": fingerprint(f, uri)},
                    "properties": {
                        "engine": f.engine,
                        "severity": f.severity,
                        "source": report.source,
                        "verdict": report.verdict,
                    },
                }
            )
    if truncated:
        notifications.append(
            {
                "level": "warning",
                "message": {"text": f"{truncated} results above {MAX_RESULTS} omitted"},
                "descriptor": {"id": "results-truncated"},
            }
        )
    run = {
        "tool": {
            "driver": {
                "name": "skill-notary",
                "version": __version__,
                "semanticVersion": __version__,
                "informationUri": INFO_URI,
                "rules": list(rules.values()),
            },
            "extensions": [
                {"name": n, "version": v or "unknown", "informationUri": ENGINE_URI.get(n, INFO_URI)}
                for n, v in engines.items()
            ],
        },
        "automationDetails": {"id": f"{category}/"},
        "invocations": [
            {"executionSuccessful": all(r.engines_ok for r in reports), "toolExecutionNotifications": notifications}
        ],
        "results": results,
        "properties": {
            "reports": [
                {"source": r.source, "verdict": r.verdict, "content_sha256": r.tree.digest, "commit": r.commit}
                for r in reports
            ]
        },
    }
    # No `originalUriBaseIds`: it would put an absolute local path (and the user name) in a file
    # that is uploaded; GitHub resolves %SRCROOT% to the repository root by itself.
    return {"$schema": SARIF_SCHEMA, "version": "2.1.0", "runs": [run]}
