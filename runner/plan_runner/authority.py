"""F3b: autoridade das fontes do L5 (P-31 = D, P-32 = B, P-33 = B; maestro, 2026-10-06).

A política está em `config/knowledge-authority.yaml`. Este módulo é puro (sem BD nem rede):

- `load_policy`: lê e valida o config (níveis fixos, `default` = `curado`);
- `authority_for`: o nível de uma fonte (o `authority` do sidecar ganha; depois a 1.ª
  regra que bater no path ou no esquema do `uri`; senão o default);
- `apply_authority`: valida `authority` e `superseded_by` do sidecar e devolve a
  proveniência com a autoridade, para o `to_source_columns` a pôr no `meta` (jsonb) da
  `knowledge_sources`. A autoridade só é gravada quando difere do default: a
  `match_knowledge_v3` lê `COALESCE(meta->>'authority', 'curado')`, por isso as fontes
  actuais ficam `curado` sem escrita nenhuma.

A leitura está em `scripts/migrations/f3b_authority_v3.sql` (`match_knowledge_v3`).
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from plan_runner.provenance import ProvenanceError

# Do mais forte para o mais fraco. Fixos: a match_knowledge_v3 tem a mesma ordem (P-32 = B).
LEVELS = ("oficial", "curado", "experimental")
# O que a v3 assume sem autoridade gravada (COALESCE no SQL). O config não o pode mudar.
SQL_DEFAULT = "curado"
SUPERSEDED_BY_MAX = 500


@dataclass(frozen=True)
class AuthorityRule:
    authority: str
    paths: tuple[str, ...] = ()
    uri_schemes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorityPolicy:
    default: str = SQL_DEFAULT
    rules: tuple[AuthorityRule, ...] = ()


def load_policy(path: Path) -> AuthorityPolicy:
    """Lê e valida o `config/knowledge-authority.yaml`. Erro claro se estiver mal formado."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("version") != 1:
        raise ValueError(f"{path.name}: version tem de ser 1")
    if tuple(data.get("levels") or ()) != LEVELS:
        raise ValueError(f"{path.name}: levels tem de ser {list(LEVELS)} (P-32 = B)")
    if data.get("default") != SQL_DEFAULT:
        raise ValueError(
            f"{path.name}: default tem de ser '{SQL_DEFAULT}' (é o que a match_knowledge_v3 "
            f"assume sem autoridade gravada)"
        )
    rules = []
    for raw in data.get("rules") or []:
        level = raw.get("authority")
        if level not in LEVELS:
            raise ValueError(f"{path.name}: regra com authority '{level}' fora de {list(LEVELS)}")
        paths, schemes = tuple(raw.get("paths") or ()), tuple(raw.get("uri_schemes") or ())
        if not paths and not schemes:
            raise ValueError(f"{path.name}: regra '{level}' precisa de paths ou uri_schemes")
        rules.append(AuthorityRule(level, paths, schemes))
    return AuthorityPolicy(SQL_DEFAULT, tuple(rules))


def authority_for(policy: AuthorityPolicy, rel: str, meta: dict[str, Any] | None) -> str:
    """O nível da fonte. O `authority` do sidecar ganha a qualquer regra."""
    declared = (meta or {}).get("authority")
    if declared:
        if declared not in LEVELS:
            raise ProvenanceError(f"authority '{declared}' fora de {list(LEVELS)}")
        return declared
    scheme = str((meta or {}).get("uri") or "").split(":", 1)[0].lower()
    for rule in policy.rules:
        if any(fnmatch(rel, pattern) for pattern in rule.paths):
            return rule.authority
        if scheme and scheme in rule.uri_schemes:
            return rule.authority
    return policy.default


def apply_authority(policy: AuthorityPolicy, rel: str, meta: dict[str, Any]) -> dict[str, Any]:
    """Proveniência (sidecar validado ou `default_meta`) com a autoridade da fonte.

    - `authority` fora dos níveis → `ProvenanceError` (INVALID_META no ingest).
    - `superseded_by` só com `status: superseded` (P-31 = D: supersessão explícita) e tem
      de ser texto (o path ou o uri da fonte nova).
    - Autoridade igual ao default → sem a chave (nada a gravar; a v3 assume `curado`).
    """
    out = dict(meta)
    by = out.get("superseded_by")
    if by is not None:
        if not isinstance(by, str) or not by.strip() or len(by) > SUPERSEDED_BY_MAX:
            raise ProvenanceError(
                f"superseded_by tem de ser o path ou o uri da fonte nova (texto, até "
                f"{SUPERSEDED_BY_MAX} caracteres)"
            )
        if out.get("status") != "superseded":
            raise ProvenanceError("superseded_by exige status: superseded (P-31 = D)")
        out["superseded_by"] = by.strip()
    level = authority_for(policy, rel, out)
    if level == policy.default:
        out.pop("authority", None)
    else:
        out["authority"] = level
    return out
