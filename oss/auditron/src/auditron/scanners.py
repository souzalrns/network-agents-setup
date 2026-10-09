"""Wrappers dos engines: cada um corre a ferramenta instalada e devolve um `ToolRun`.

Regras transversais:
- shell nunca (lista de argumentos, sem `shell=True`);
- a saída é lida mesmo quando o engine sai com código != 0 (ter achados não é falhar);
- se o engine não está instalado, não corre ou cospe algo que não dá para ler, o `ToolRun`
  leva `error` — e se for bloqueante, bloqueia (a falha não passa por silêncio).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from auditron.model import Finding, ToolRun

# Pastas que nunca interessam a uma análise de código-fonte.
_EXCLUDE = (".git", "node_modules", ".venv", "venv", "build", "dist", "__pycache__", ".mypy_cache")
_TIMEOUT = 600


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=_TIMEOUT, cwd=cwd, check=False)  # noqa: S603


def _version(tool: str) -> str:
    exe = shutil.which(tool)
    if not exe:
        return ""
    try:
        out = _run([exe, "--version"])
    except (OSError, subprocess.SubprocessError):
        return ""
    text = (out.stdout or out.stderr or "").strip().splitlines()
    return text[0].strip() if text else ""


def _missing(tool: str, blocking: bool) -> ToolRun:
    return ToolRun(tool=tool, blocking=blocking, error=f"{tool} não está instalado (pip install auditron)")


# ---------------------------------------------------------------- pip-audit (SCA das dependências)


def _iter_requirements(target: Path):
    for p in sorted(target.rglob("requirements*.txt")):
        if not any(part in _EXCLUDE for part in p.parts):
            yield p


def pip_audit(target: Path, blocking: bool) -> ToolRun:
    if not shutil.which("pip-audit"):
        return _missing("pip-audit", blocking)
    run = ToolRun(tool="pip-audit", version=_version("pip-audit"), blocking=blocking)
    reqs = list(_iter_requirements(target))
    if not reqs:
        return run  # nada de requirements → nada a auditar (limpo)
    for req in reqs:
        proc = _run(["pip-audit", "-r", str(req), "-f", "json", "--progress-spinner", "off"])
        try:
            data = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            run.error = f"pip-audit não deu JSON para {req} ({(proc.stderr or '').strip()[:200]})"
            return run
        rel = req.relative_to(target).as_posix()
        for dep in data.get("dependencies", []):
            for vuln in dep.get("vulns", []):
                fix = ", ".join(vuln.get("fix_versions") or []) or "sem correcção publicada"
                run.findings.append(
                    Finding(
                        tool="pip-audit",
                        rule_id=vuln.get("id", "VULN"),
                        level="error",
                        message=f"{dep.get('name')} {dep.get('version')}: {vuln.get('id')} (corrige em: {fix})",
                        location=rel,
                    )
                )
    return run


# ---------------------------------------------------------------- bandit (SAST de Python)

_BANDIT_LEVEL = {"HIGH": "error", "MEDIUM": "warning", "LOW": "note"}


def bandit(target: Path, blocking: bool) -> ToolRun:
    if not shutil.which("bandit"):
        return _missing("bandit", blocking)
    run = ToolRun(tool="bandit", version=_version("bandit"), blocking=blocking)
    proc = _run(["bandit", "-r", str(target), "-f", "json", "-ll", "-ii", "-x", ",".join(_EXCLUDE)])
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        run.error = f"bandit não deu JSON ({(proc.stderr or '').strip()[:200]})"
        return run
    for r in data.get("results", []):
        loc = r.get("filename", "")
        try:
            loc = Path(loc).resolve().relative_to(target.resolve()).as_posix()
        except (ValueError, OSError):
            pass
        run.findings.append(
            Finding(
                tool="bandit",
                rule_id=r.get("test_id", "B000"),
                level=_BANDIT_LEVEL.get(r.get("issue_severity", "LOW"), "note"),
                message=r.get("issue_text", "").strip(),
                location=loc,
                line=r.get("line_number"),
            )
        )
    return run


# ---------------------------------------------------------------- zizmor (segurança dos workflows)


def zizmor(target: Path, blocking: bool) -> ToolRun:
    if not shutil.which("zizmor"):
        return _missing("zizmor", blocking)
    run = ToolRun(tool="zizmor", version=_version("zizmor"), blocking=blocking)
    workflows = target / ".github" / "workflows"
    if not workflows.is_dir():
        return run  # sem workflows → nada a auditar (limpo)
    proc = _run(["zizmor", "--format=sarif", "--persona=regular", "--no-online-audits", str(workflows)])
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        run.error = f"zizmor não deu SARIF ({(proc.stderr or '').strip()[:200]})"
        return run
    run.findings.extend(_sarif_results(data))
    return run


def _sarif_results(data: dict) -> list[Finding]:
    out: list[Finding] = []
    for run in data.get("runs", []):
        for res in run.get("results", []):
            loc, line = "", None
            locs = res.get("locations") or []
            if locs:
                phys = locs[0].get("physicalLocation", {})
                loc = phys.get("artifactLocation", {}).get("uri", "")
                line = phys.get("region", {}).get("startLine")
            out.append(
                Finding(
                    tool="zizmor",
                    rule_id=res.get("ruleId", "zizmor"),
                    level=res.get("level", "warning")
                    if res.get("level") in ("error", "warning", "note")
                    else "warning",
                    message=(res.get("message", {}) or {}).get("text", "").strip(),
                    location=loc,
                    line=line,
                )
            )
    return out


SCANNERS = {"pip-audit": pip_audit, "bandit": bandit, "zizmor": zizmor}
