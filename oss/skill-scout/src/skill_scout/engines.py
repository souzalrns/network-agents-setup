"""Scan engines. skill-scout does not write its own rules: it runs mature scanners and merges them.

- `asm`: agentic-skills-manager (MIT, stdlib only; a dependency, always available).
  `python -I -m skills_manager scan <dir> --ci`, static checks only.
- `cisco`: Cisco AI Defense skill-scanner (Apache-2.0, optional: `pip install
  skill-scout[cisco]` or any `skill-scanner` on PATH). `skill-scanner scan <dir> --format
  json --use-behavioral`: static (YAML + YARA), bytecode, pipeline, correlation and AST dataflow
  analyzers, all offline. LLM, VirusTotal and AI Defense analyzers are never enabled (they need
  API keys and send the source out).

Both run in a child process with a timeout and a minimal environment. Neither executes the
skill. AI review modes of either engine are never requested.

Findings keep the rule, severity, path, line, title and remediation only. Descriptions and
snippets are dropped on purpose: for secret rules they contain the matched secret, and the
report (or a SARIF uploaded to GitHub) must never carry it.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .errors import EngineError, FetchError
from .source import minimal_env, run

SEVERITIES = ("info", "low", "medium", "high", "critical")
SCAN_TIMEOUT_S = 300.0
FIELD_MAX = 300
# ANSI escape sequences first: with the single-character class first, ESC alone matched and
# the rest of the sequence ("[31m") stayed in the text.
_CONTROL = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|[\x00-\x1f\x7f]")
_RULE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")


def clean(value: object, limit: int = FIELD_MAX) -> str:
    return _CONTROL.sub("", str(value or "")).strip()[:limit]


@dataclass(frozen=True)
class Finding:
    engine: str
    rule: str
    severity: str
    path: str  # POSIX, relative to the scanned folder
    title: str
    recommendation: str = ""
    line: int | None = None
    category: str = ""
    waiver: str | None = None  # id of the active waiver that accepts this finding (waivers.py)
    waiver_reason: str = ""

    @property
    def rule_id(self) -> str:
        return f"{self.engine}/{self.rule}"

    def to_json(self) -> dict:
        out = {
            "engine": self.engine,
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "title": self.title,
            "recommendation": self.recommendation,
            "category": self.category,
        }
        if self.waiver:
            out["waiver"] = {"id": self.waiver, "reason": self.waiver_reason}
        return out


def _rule(value: object) -> str:
    rule = clean(value, 100)
    return rule if _RULE.match(rule) else "unspecified"


def _path(value: object) -> str:
    p = clean(value, 500).replace("\\", "/").lstrip("/")
    return "." if not p or ".." in p.split("/") else p


def _severity(value: object, default: str = "medium") -> str:
    sev = clean(value, 20).lower()
    return sev if sev in SEVERITIES else default


class Engine:
    name = ""

    def version(self) -> str | None:  # pragma: no cover - interface
        raise NotImplementedError

    def scan(self, path: Path) -> list[Finding]:  # pragma: no cover - interface
        raise NotImplementedError


class AsmEngine(Engine):
    name = "asm"
    dist = "agentic-skills-manager"
    module = "skills_manager"

    def version(self) -> str | None:
        if importlib.util.find_spec(self.module) is None:
            return None
        try:
            return importlib.metadata.version(self.dist)
        except importlib.metadata.PackageNotFoundError:
            return None

    def scan(self, path: Path) -> list[Finding]:
        if self.version() is None:
            raise EngineError(f"engine asm unavailable: pip install {self.dist}")
        cmd = [sys.executable, "-I", "-m", self.module, "scan", str(path), "--ci"]
        report, code = _run_json(cmd, "asm")
        if not isinstance(report.get("safe"), bool):
            raise EngineError("engine asm: report without boolean `safe`")
        if code not in (0, 1) or (code == 0) != report["safe"]:
            raise EngineError(f"engine asm: exit {code} does not match safe={report['safe']}")
        out = []
        for f in report.get("findings") or []:
            if isinstance(f, dict):
                out.append(
                    Finding(
                        "asm",
                        _rule(f.get("rule")),
                        _severity(f.get("severity")),
                        _path(f.get("path")),
                        clean(f.get("issue")),
                        clean(f.get("recommendation")),
                    )
                )
        if report["safe"] is False and not any(f.severity in ("high", "critical") for f in out):
            out.append(Finding("asm", "blocked", "high", ".", "engine asm blocked this source"))
        return out


class CiscoEngine(Engine):
    name = "cisco"
    executable = "skill-scanner"

    def _bin(self) -> str | None:
        return shutil.which(self.executable)

    def version(self) -> str | None:
        exe = self._bin()
        if not exe:
            return None
        with tempfile.TemporaryDirectory(prefix="skill-scout-cisco-") as home:
            try:
                code, out, _ = run([exe, "--version"], timeout=60, env=minimal_env(Path(home)), cwd=Path(home))
            except FetchError:
                return None
        m = re.search(r"(\d+\.\d+\.\d+\S*)", out)
        return m.group(1) if code == 0 and m else None

    def scan(self, path: Path) -> list[Finding]:
        exe = self._bin()
        if not exe:
            raise EngineError("engine cisco unavailable: pip install 'skill-scout[cisco]'")
        report, code = _run_json([exe, "scan", str(path), "--format", "json", "--use-behavioral"], "cisco")
        if code != 0 or not isinstance(report.get("findings"), list):
            raise EngineError(f"engine cisco: exit {code} or report without `findings`")
        out = []
        for f in report["findings"]:
            if not isinstance(f, dict):
                continue
            line = f.get("line_number")
            out.append(
                Finding(
                    "cisco",
                    _rule(f.get("rule_id")),
                    _severity(f.get("severity"), "medium"),
                    _path(f.get("file_path")),
                    clean(f.get("title")),
                    clean(f.get("remediation")),
                    line if isinstance(line, int) and line > 0 else None,
                    clean(f.get("category"), 60),
                )
            )
        return out


ENGINES: dict[str, type[Engine]] = {"asm": AsmEngine, "cisco": CiscoEngine}


def get_engines(names: list[str]) -> list[Engine]:
    unknown = [n for n in names if n not in ENGINES]
    if unknown or not names:
        raise EngineError(f"unknown engine(s): {', '.join(unknown) or '(none)'}; available: {', '.join(ENGINES)}")
    return [ENGINES[n]() for n in dict.fromkeys(names)]


def _run_json(cmd: list[str], engine: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory(prefix=f"skill-scout-{engine}-") as home:
        try:
            code, out, _ = run(cmd, timeout=SCAN_TIMEOUT_S, env=minimal_env(Path(home)), cwd=Path(home))
        except FetchError as e:
            raise EngineError(f"engine {engine}: {e}") from None
    start = out.find("{")
    try:
        report = json.loads(out[start:]) if start >= 0 else None
    except json.JSONDecodeError:
        lines = [ln for ln in out.splitlines() if ln.lstrip().startswith("{")]
        try:
            report = json.loads(lines[-1]) if lines else None
        except json.JSONDecodeError:
            report = None
    if not isinstance(report, dict):
        raise EngineError(f"engine {engine}: no JSON report (exit {code})")
    return report, code
