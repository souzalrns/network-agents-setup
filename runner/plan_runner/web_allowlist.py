"""F2-ALLOW-1 (P-25 = A): allowlist do `fetch` por área.

`config/web-allowlist.yaml` diz, por área do `config/areas.yaml`, que domínios o
`scripts/web_fetch.py` pode buscar. Os domínios são política: escolhe-os o maestro. Até lá
as listas ficam vazias, e uma área sem domínios não busca nada.

Regras do ficheiro (validadas no E7, `python -m plan_runner.areas`):
- `version` inteiro; `areas` é um mapa área → lista de domínios;
- cada área existe no `config/areas.yaml`;
- cada domínio é um nome DNS em minúsculas, sem esquema, caminho, porta, `*` nem IP
  literal (um IP fugia à verificação de SSRF por nome), e sem repetidos na mesma área.
  Um domínio aceita também os subdomínios (`exemplo.org` aceita `www.exemplo.org`),
  como a allowlist do `fetch`.

Uso no `fetch` (`resolve_allowlist`):
- `--area X` sem `--allow`: busca só nos domínios da área;
- `--area X` com `--allow d`: cada `d` tem de caber na área (o próprio ou um subdomínio);
  a chamada só pode estreitar a política, nunca alargá-la;
- só `--allow` (sem área): como no F2a, mas o resultado leva o aviso `no_area_allowlist`.
  Fica assim enquanto as listas estiverem vazias; tornar a área obrigatória é o passo
  seguinte, quando o maestro der os domínios.

Só depende do PyYAML: o `scripts/web_fetch.py` carrega este ficheiro pelo caminho.
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

import yaml

ALLOWLIST_FILE = Path("config") / "web-allowlist.yaml"
NO_AREA_WARNING = "no_area_allowlist"
# Nome DNS: rótulos de 1 a 63 [a-z0-9-] (sem hífen nas pontas), pelo menos 2 rótulos.
_LABEL = r"(?!-)[a-z0-9-]{1,63}(?<!-)"
_DOMAIN = re.compile(rf"^{_LABEL}(\.{_LABEL})+$")


class AllowlistError(ValueError):
    """A chamada pede um domínio fora da política da área (ou a área não tem política)."""


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def domain_error(domain: Any) -> str | None:
    """Motivo pelo qual `domain` não é um domínio válido na allowlist; None se for."""
    if not isinstance(domain, str) or not domain:
        return "tem de ser texto não vazio"
    if domain != domain.strip().lower():
        return "tem de estar em minúsculas e sem espaços"
    if "://" in domain or "/" in domain:
        return "sem esquema nem caminho (só o domínio)"
    if ":" in domain or _is_ip(domain):
        return "sem porta nem IP literal"
    if "*" in domain:
        return "sem `*` (um domínio já aceita os subdomínios)"
    if len(domain) > 253 or not _DOMAIN.match(domain):
        return "não é um nome DNS válido"
    return None


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    return data if isinstance(data, dict) else {}


def validate(repo_root: Path, area_ids: set[str]) -> list[str]:
    """Erros do `config/web-allowlist.yaml` (E7). Sem ficheiro, nada a validar: os mini-repos dos
    testes não o têm; no repo real, `test_web_allowlist.py` exige que exista."""
    path = repo_root / ALLOWLIST_FILE
    rel = ALLOWLIST_FILE.as_posix()
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"{rel}: não é YAML legível ({e})"]
    if not isinstance(data, dict):
        return [f"{rel}: tem de ser um objecto"]
    errors: list[str] = []
    if not isinstance(data.get("version"), int) or isinstance(data.get("version"), bool):
        errors.append(f"{rel}: `version` tem de ser inteiro")
    areas = data.get("areas")
    if not isinstance(areas, dict):
        return errors + [f"{rel}: `areas` tem de ser um mapa área → lista de domínios"]
    for area, domains in areas.items():
        where = f"{rel}: área `{area}`"
        if area not in area_ids:
            errors.append(f"{where}: não existe no config/areas.yaml")
        if domains is None:
            continue  # `area:` sem valor = lista vazia
        if not isinstance(domains, list):
            errors.append(f"{where}: os domínios têm de ser uma lista")
            continue
        seen: set[str] = set()
        for d in domains:
            why = domain_error(d)
            if why:
                errors.append(f"{where}: domínio {d!r} inválido ({why})")
            elif d in seen:
                errors.append(f"{where}: domínio `{d}` repetido")
            else:
                seen.add(d)
    return errors


def area_domains(repo_root: Path, area: str) -> list[str]:
    """Domínios da área. Lança AllowlistError se a área não estiver no ficheiro."""
    areas = load(repo_root / ALLOWLIST_FILE).get("areas")
    if not isinstance(areas, dict) or area not in areas:
        raise AllowlistError(f"a área `{area}` não está em {ALLOWLIST_FILE.as_posix()}")
    return list(areas.get(area) or [])


def _covers(domain: str, host: str) -> bool:
    host = host.lower().strip().rstrip(".")
    return host == domain or host.endswith(f".{domain}")


def resolve_allowlist(
    repo_root: Path, area: str | None, allow: list[str] | None
) -> tuple[list[str], list[str]]:
    """(allowlist efectiva, avisos) para uma chamada do `fetch`. Lança AllowlistError."""
    allow = [a.strip().lower() for a in (allow or []) if a and a.strip()]
    if area is None:
        if not allow:
            raise AllowlistError("sem `--area` nem `--allow`: nada pode ser buscado")
        return allow, [NO_AREA_WARNING]
    domains = area_domains(repo_root, area)
    if not domains:
        raise AllowlistError(
            f"a área `{area}` não tem domínios em {ALLOWLIST_FILE.as_posix()} (o maestro escolhe-os)"
        )
    if not allow:
        return domains, []
    outside = [a for a in allow if not any(_covers(d, a) for d in domains)]
    if outside:
        raise AllowlistError(
            f"{', '.join(outside)} fora da allowlist da área `{area}` ({', '.join(domains)})"
        )
    return allow, []
