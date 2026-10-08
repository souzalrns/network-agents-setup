"""Engines (real asm; real cisco when installed), verdicts, and SARIF validated against the official schema."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path

import pytest

from skill_notary import engines as eng
from skill_notary.engines import AsmEngine, CiscoEngine, Finding, get_engines
from skill_notary.errors import EngineError
from skill_notary.report import ScanReport, scan_dir, verdict_for
from skill_notary.sarif import LEVEL, SECURITY_SEVERITY, to_sarif

from .helpers import FAKE_KEY_BODY, make_dangerous, make_risky, make_safe, monorepo, write

HAS_CISCO = CiscoEngine().version() is not None
needs_cisco = pytest.mark.skipif(not HAS_CISCO, reason="cisco skill-scanner not installed (extra [cisco])")
# SARIF 2.1.0 schema, OASIS TC repository at a pinned commit (not redistributed: OASIS licence).
SCHEMA_URL = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/adbb670c018335b0f384e6dd8819f4ea055d7ee1/"
    "sarif-2.1/schema/sarif-schema-2.1.0.json"
)
SCHEMA_SHA256 = "c3b4bb2d6093897483348925aaa73af03b3e3f4bd4ca38cef26dcb4212a2682e"


def _scan(path: Path, names=("asm",)) -> ScanReport:
    return scan_dir(path, get_engines(list(names)), source=str(path.name), source_type="local")


# --------------------------------------------------------------------------- asm (real)


def test_asm_safe_risky_dangerous(tmp_path):
    assert _scan(make_safe(tmp_path / "good")).verdict == "safe"
    risky = _scan(make_risky(tmp_path / "envy"))
    assert risky.verdict == "risky" and [f.rule for f in risky.findings] == ["environment-access"]
    bad = _scan(make_dangerous(tmp_path / "evil"))
    assert bad.verdict == "dangerous"
    assert {"private-key-material", "network-pipe-to-shell", "destructive-remove"} <= {f.rule for f in bad.findings}
    assert bad.counts["critical"] >= 1


def test_the_skill_is_never_executed(tmp_path):
    d = make_safe(tmp_path / "trap")
    marker = tmp_path / "executed"
    write(d / "scripts" / "run.py", f"open({str(marker)!r}, 'w').write('x')\n", 0o755)
    write(d / "scripts" / "run.sh", f"#!/bin/sh\ntouch {marker}\n", 0o755)
    _scan(d)
    assert not marker.exists()


def test_engine_failure_is_not_scanned(tmp_path, monkeypatch):
    monkeypatch.setattr(eng, "_run_json", lambda cmd, name: ({"no": "safe"}, 2))
    r = _scan(make_safe(tmp_path / "s"))
    assert r.verdict == "not_scanned" and r.engines[0].ok is False and "boolean" in r.engines[0].error
    monkeypatch.setattr(eng, "_run_json", lambda cmd, name: ({"safe": False, "findings": []}, 0))
    assert _scan(make_safe(tmp_path / "t")).verdict == "not_scanned"  # exit and `safe` disagree
    monkeypatch.setattr(AsmEngine, "version", lambda self: None)
    assert "unavailable" in _scan(make_safe(tmp_path / "u")).engines[0].error


def test_engine_block_without_high_finding_still_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(
        eng,
        "_run_json",
        lambda cmd, name: (
            {"safe": False, "findings": [{"rule": "x", "severity": "medium", "path": "a", "issue": "m"}]},
            1,
        ),
    )
    assert _scan(make_safe(tmp_path / "s")).verdict == "dangerous"


def test_findings_are_sanitised(tmp_path, monkeypatch):
    hostile = {
        "rule": "\x1b[31mr; rm -rf /",
        "severity": "SEVERE",
        "path": "../../etc/passwd",
        "issue": "a\x07b" + "x" * 1000,
        "recommendation": "\x1b]0;title\x07ok",
    }
    monkeypatch.setattr(eng, "_run_json", lambda cmd, name: ({"safe": True, "findings": [hostile]}, 0))
    f = _scan(make_safe(tmp_path / "s")).findings[0]
    assert (f.rule, f.severity, f.path) == ("unspecified", "medium", ".")
    assert "\x07" not in f.title and len(f.title) == eng.FIELD_MAX and "\x1b" not in f.recommendation


def test_unknown_engine():
    with pytest.raises(EngineError, match="unknown"):
        get_engines(["nope"])


# --------------------------------------------------------------------------- cisco


def test_cisco_parsing_drops_snippets_and_descriptions(tmp_path, monkeypatch):
    report = {
        "findings": [
            {
                "rule_id": "YARA_credential_harvesting_generic",
                "severity": "CRITICAL",
                "title": "CREDENTIAL HARVESTING detected by YARA",
                "file_path": ".env",
                "line_number": 1,
                "description": f"matched {FAKE_KEY_BODY}",
                "snippet": FAKE_KEY_BODY,
                "remediation": "Remove it",
                "category": "hardcoded_secrets",
            },
            {"rule_id": "X", "severity": "INFO", "title": "t", "file_path": "SKILL.md", "line_number": None},
        ]
    }
    monkeypatch.setattr(CiscoEngine, "_bin", lambda self: "/bin/true")
    monkeypatch.setattr(eng, "_run_json", lambda cmd, name: (report, 0))
    found = CiscoEngine().scan(tmp_path)
    assert [(f.severity, f.line) for f in found] == [("critical", 1), ("info", None)]
    assert FAKE_KEY_BODY not in json.dumps([f.to_json() for f in found])


@needs_cisco
def test_cisco_real_engine_adds_lines(tmp_path):
    r = _scan(make_dangerous(tmp_path / "evil"), ("asm", "cisco"))
    assert r.verdict == "dangerous" and {e.name for e in r.engines} == {"asm", "cisco"}
    cisco = [f for f in r.findings if f.engine == "cisco"]
    assert any(f.line for f in cisco) and any(f.severity in ("high", "critical") for f in cisco)
    assert FAKE_KEY_BODY not in json.dumps(r.to_json())
    assert _scan(make_safe(tmp_path / "good"), ("cisco",)).verdict == "safe"


# --------------------------------------------------------------------------- verdicts


@pytest.mark.parametrize(
    "sevs, ok, verdict",
    [
        ([], True, "safe"),
        (["info", "low"], True, "safe"),
        (["medium"], True, "risky"),
        (["low", "high"], True, "dangerous"),
        (["critical"], True, "dangerous"),
        ([], False, "not_scanned"),
        (["medium"], False, "not_scanned"),
    ],
)
def test_verdict_table(sevs, ok, verdict):
    assert verdict_for([Finding("asm", "r", s, "p", "t") for s in sevs], ok) == verdict


def test_symlink_in_a_skill_makes_it_dangerous(tmp_path):
    d = make_safe(tmp_path / "s")
    (d / "link").symlink_to("/etc/passwd")
    r = _scan(d)
    assert r.verdict == "dangerous"
    assert any(f.engine == "skill-notary" and f.rule == "unpinnable-entry" and f.path == "link" for f in r.findings)


def test_many_skills_each_get_a_verdict(tmp_path):
    monorepo(tmp_path)
    r = _scan(tmp_path)
    assert {s.rel: s.verdict for s in r.skills} == {
        "skills/envy-dir": "risky",
        "skills/evil": "dangerous",
        "skills/good": "safe",
    }
    assert r.verdict == "dangerous"
    doc = r.to_json()
    assert doc["schema"] == "skill-notary/report-v1" and doc["content"]["sha256"] == r.tree.digest


# --------------------------------------------------------------------------- SARIF


@pytest.fixture(scope="session")
def sarif_schema(tmp_path_factory):
    try:
        with urllib.request.urlopen(SCHEMA_URL, timeout=20) as resp:
            body = resp.read()
    except OSError as e:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"SARIF schema not reachable offline: {e}")
    assert hashlib.sha256(body).hexdigest() == SCHEMA_SHA256, "SARIF schema changed upstream"
    return json.loads(body)


def _sarif(tmp_path: Path, srcroot: Path | None = None) -> dict:
    monorepo(tmp_path / "repo" / "skills-root")
    report = _scan(tmp_path / "repo" / "skills-root")
    return to_sarif([report], srcroot=srcroot if srcroot is not None else tmp_path / "repo")


def test_sarif_is_valid_against_the_official_schema(tmp_path, sarif_schema):
    import jsonschema

    jsonschema.Draft4Validator(sarif_schema).validate(_sarif(tmp_path))


def test_sarif_meets_github_code_scanning_rules(tmp_path):
    doc = _sarif(tmp_path)
    run = doc["runs"][0]
    assert doc["version"] == "2.1.0" and run["tool"]["driver"]["name"] == "skill-notary"
    assert run["automationDetails"]["id"] == "skill-notary/"
    assert {e["name"] for e in run["tool"]["extensions"]} == {"asm"}
    rules = {r["id"]: r for r in run["tool"]["driver"]["rules"]}
    for rule in rules.values():
        sev = rule["properties"].get("security-severity")
        assert sev is None or 0 < float(sev) <= 10
        assert "security" in rule["properties"]["tags"] and rule["help"]["text"]
    assert rules["asm/private-key-material"]["properties"]["security-severity"] == SECURITY_SEVERITY["critical"]
    for res in run["results"]:
        loc = res["locations"][0]["physicalLocation"]
        uri = loc["artifactLocation"]["uri"]
        assert loc["artifactLocation"]["uriBaseId"] == "%SRCROOT%" and uri.startswith("skills-root/skills/")
        assert not uri.startswith("/") and loc["region"]["startLine"] >= 1
        assert res["level"] == LEVEL[res["properties"]["severity"]]
        assert run["tool"]["driver"]["rules"][res["ruleIndex"]]["id"] == res["ruleId"]
        assert len(res["partialFingerprints"]["skillNotaryFinding/v1"]) == 32


def test_sarif_has_no_secret_and_no_absolute_path(tmp_path):
    text = json.dumps(_sarif(tmp_path))
    assert FAKE_KEY_BODY not in text and "BEGIN OPENSSH" not in text
    assert str(tmp_path) not in text and "file://" not in text


def test_sarif_fingerprints_are_stable(tmp_path):
    a = _sarif(tmp_path / "a")
    b = _sarif(tmp_path / "b")
    fp = lambda d: sorted(r["partialFingerprints"]["skillNotaryFinding/v1"] for r in d["runs"][0]["results"])  # noqa: E731
    assert fp(a) == fp(b)


def test_sarif_outside_srcroot_uses_skillroot(tmp_path):
    doc = _sarif(tmp_path, srcroot=tmp_path / "elsewhere")
    assert {
        r["locations"][0]["physicalLocation"]["artifactLocation"]["uriBaseId"] for r in doc["runs"][0]["results"]
    } == {"SKILLROOT"}


def test_sarif_reports_engine_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(eng, "_run_json", lambda cmd, name: ({}, 2))
    doc = to_sarif([_scan(make_safe(tmp_path / "s"))])
    inv = doc["runs"][0]["invocations"][0]
    assert inv["executionSuccessful"] is False
    assert "engine asm failed" in inv["toolExecutionNotifications"][0]["message"]["text"]
