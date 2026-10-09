"""Orquestração: correr os engines activos da política e juntar num `ScanResult`."""

from __future__ import annotations

from pathlib import Path

from auditron.config import Policy
from auditron.model import ScanResult
from auditron.scanners import SCANNERS


def scan(target: Path, policy: Policy, only: list[str] | None = None) -> ScanResult:
    """Corre os engines activos sobre `target`. `only` limita a esses engines (já filtrados
    pela política: um engine `disabled` nunca corre, mesmo que esteja em `only`)."""
    engines = policy.enabled()
    if only:
        engines = [e for e in engines if e in only]
    result = ScanResult(target=str(target))
    for engine in engines:
        run = SCANNERS[engine](target, policy.is_blocking(engine))
        run.findings = _dedupe(run.findings)  # o pip-audit, com `-r`, repete a mesma vuln
        result.runs.append(run)
    return result


def _dedupe(findings):
    """Remove achados idênticos, preservando a ordem (Finding é hashável: frozen dataclass)."""
    seen, out = set(), []
    for f in findings:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out
