"""Modelo comum dos achados, independente do engine.

Cada engine (pip-audit, bandit, zizmor) fala a sua língua; o auditron normaliza tudo para
`Finding`, agrupa por `ToolRun` e junta num `ScanResult`. A severidade reduz-se a três níveis
(SARIF: error/warning/note) para a política e o relatório serem simples e comparáveis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# Ordem crescente de gravidade. É a do SARIF; o resto do código compara por este índice.
LEVELS = ("note", "warning", "error")


def level_rank(level: str) -> int:
    """Índice do nível (note<warning<error); níveis desconhecidos contam como o mais grave."""
    return LEVELS.index(level) if level in LEVELS else len(LEVELS)


@dataclass(frozen=True)
class Finding:
    """Um achado normalizado. `location`/`line` ficam vazios quando o engine não os dá."""

    tool: str
    rule_id: str
    level: str  # note | warning | error
    message: str
    location: str = ""  # caminho relativo do ficheiro, ou "" (ex.: uma dependência)
    line: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ToolRun:
    """O que um engine fez: versão, estado e achados. `error` != None = o engine falhou."""

    tool: str
    version: str = ""
    blocking: bool = False
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None  # mensagem se o engine não correu/rebentou (não é um achado)

    @property
    def ok(self) -> bool:
        """O engine correu e não encontrou nada (e não rebentou)."""
        return self.error is None and not self.findings

    def counts(self) -> dict[str, int]:
        c = {lv: 0 for lv in LEVELS}
        for f in self.findings:
            c[f.level] = c.get(f.level, 0) + 1
        return c

    def as_dict(self) -> dict:
        return {
            "tool": self.tool,
            "version": self.version,
            "blocking": self.blocking,
            "error": self.error,
            "counts": self.counts(),
            "findings": [f.as_dict() for f in self.findings],
        }


@dataclass
class ScanResult:
    """O resultado de uma passagem do auditron sobre um alvo."""

    target: str
    runs: list[ToolRun] = field(default_factory=list)

    @property
    def findings(self) -> list[Finding]:
        return [f for r in self.runs for f in r.findings]

    def counts(self) -> dict[str, int]:
        c = {lv: 0 for lv in LEVELS}
        for f in self.findings:
            c[f.level] = c.get(f.level, 0) + 1
        return c

    def blocked(self) -> bool:
        """Falha o gate: um engine bloqueante encontrou algo OU rebentou.

        Um engine que rebenta (erro de execução) nunca passa por silêncio: se for bloqueante,
        bloqueia; a ausência de prova não é prova de ausência."""
        return any((r.findings or r.error is not None) for r in self.runs if r.blocking)

    def as_dict(self) -> dict:
        return {
            "auditron": {"target": self.target, "counts": self.counts(), "blocked": self.blocked()},
            "runs": [r.as_dict() for r in self.runs],
        }
