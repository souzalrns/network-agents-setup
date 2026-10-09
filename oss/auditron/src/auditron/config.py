"""Política do auditron: que engines correm e quais bloqueiam.

Sem ficheiro, vale o `DEFAULT`: os três engines correm; só o `pip-audit` bloqueia (a base típica
é limpa, vulnerabilidade conhecida numa dependência é factual), e o `bandit`/`zizmor` informam até
o repo fazer a triagem dos seus achados. Um `auditron.toml` no repo sobrepõe-se, por engine.

    [auditron]
    blocking = ["pip-audit", "bandit"]   # quais bloqueiam o gate
    disabled = ["zizmor"]                 # quais nem correm
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # 3.10: o tomllib ainda não está no stdlib
    import tomli as tomllib

ENGINES = ("pip-audit", "bandit", "zizmor")


@dataclass
class Policy:
    blocking: tuple[str, ...] = ("pip-audit",)
    disabled: tuple[str, ...] = ()

    def enabled(self) -> list[str]:
        return [e for e in ENGINES if e not in self.disabled]

    def is_blocking(self, engine: str) -> bool:
        return engine in self.blocking


DEFAULT = Policy()


def _validate(blocking: list[str], disabled: list[str]) -> None:
    unknown = sorted({*blocking, *disabled} - set(ENGINES))
    if unknown:
        raise ValueError(f"engines desconhecidos na política: {', '.join(unknown)} (conhecidos: {', '.join(ENGINES)})")
    both = sorted(set(blocking) & set(disabled))
    if both:
        raise ValueError(f"engine não pode ser `blocking` e `disabled` ao mesmo tempo: {', '.join(both)}")


def load(path: Path | None) -> Policy:
    """Lê o `auditron.toml` (secção `[auditron]`); sem caminho ou sem ficheiro, devolve o DEFAULT."""
    if path is None or not path.is_file():
        return DEFAULT
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    section = data.get("auditron", data) if isinstance(data, dict) else {}
    blocking = list(section.get("blocking", DEFAULT.blocking))
    disabled = list(section.get("disabled", DEFAULT.disabled))
    if not all(isinstance(x, str) for x in [*blocking, *disabled]):
        raise ValueError("`blocking`/`disabled` têm de ser listas de nomes de engine")
    _validate(blocking, disabled)
    return Policy(blocking=tuple(blocking), disabled=tuple(disabled))
