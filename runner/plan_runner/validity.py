"""F3b: validade das fontes do L5 (P-27 = C, P-28 = C, P-29 = A; maestro, 2026-10-06).

A política está em `config/knowledge-validity.yaml`. Este módulo é puro (sem BD nem rede):

- `classify`: a classe de validade de uma fonte (path, esquema do `uri` ou
  `validity_class` no sidecar);
- `apply_validity`: aplica a classe ao sidecar já validado pelo `provenance.load_meta`:
  data exigida em falta com sidecar → `ProvenanceError` (INVALID_META no ingest); sem
  sidecar → aviso; TTL → `effective_until` = `retrieved_at` + `ttl_days`;
- `validity_state`: o estado de uma fonte num instante, para o relatório local
  (`scripts/validity_report.py`).

A filtragem na leitura já existe desde o F3a: a `match_knowledge_v2` deixa de fora o que
expirou (`effective_until <= valid_at`) ou ainda não vigora (`effective_from > valid_at`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from plan_runner.provenance import ProvenanceError, _comparable

DATE_FIELDS = ("effective_from", "effective_until")
EVERGREEN = "evergreen"  # fora das classes: sem data, vale até superseded/revoked


@dataclass(frozen=True)
class ValidityClass:
    id: str
    description: str
    paths: tuple[str, ...] = ()
    uri_schemes: tuple[str, ...] = ()
    require: tuple[str, ...] = ()
    ttl_days: int | None = None


@dataclass(frozen=True)
class ValidityPolicy:
    classes: tuple[ValidityClass, ...]
    expiring_within_days: int = 30

    def by_id(self, class_id: str) -> ValidityClass | None:
        return next((c for c in self.classes if c.id == class_id), None)


def load_policy(path: Path) -> ValidityPolicy:
    """Lê e valida o `config/knowledge-validity.yaml`. Erro claro se estiver mal formado."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("version") != 1:
        raise ValueError(f"{path.name}: version tem de ser 1")
    classes = []
    for raw in data.get("classes") or []:
        cid = raw.get("id")
        if not cid or cid == EVERGREEN:
            raise ValueError(f"{path.name}: classe sem id ou com o id reservado '{EVERGREEN}'")
        require = tuple(raw.get("require") or ())
        bad = [f for f in require if f not in DATE_FIELDS]
        if bad:
            raise ValueError(f"{path.name}: {cid}: require só aceita {DATE_FIELDS}, não {bad}")
        ttl = raw.get("ttl_days")
        if ttl is not None and (not isinstance(ttl, int) or isinstance(ttl, bool) or ttl <= 0):
            raise ValueError(f"{path.name}: {cid}: ttl_days tem de ser um inteiro positivo")
        paths, schemes = tuple(raw.get("paths") or ()), tuple(raw.get("uri_schemes") or ())
        if not paths and not schemes:
            raise ValueError(f"{path.name}: {cid}: precisa de paths ou uri_schemes")
        if not require and ttl is None:
            raise ValueError(f"{path.name}: {cid}: precisa de require ou ttl_days")
        classes.append(
            ValidityClass(cid, raw.get("description", ""), paths, schemes, require, ttl)
        )
    ids = [c.id for c in classes]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: ids de classe repetidos: {ids}")
    within = (data.get("report") or {}).get("expiring_within_days", 30)
    return ValidityPolicy(tuple(classes), within)


def classify(policy: ValidityPolicy, rel: str, meta: dict[str, Any] | None) -> ValidityClass | None:
    """A classe da fonte, ou None (evergreen). O `validity_class` do sidecar ganha."""
    declared = (meta or {}).get("validity_class")
    if declared:
        if declared == EVERGREEN:
            return None
        found = policy.by_id(declared)
        if found is None:
            known = [c.id for c in policy.classes] + [EVERGREEN]
            raise ProvenanceError(f"validity_class '{declared}' desconhecida (conhecidas: {known})")
        return found
    scheme = str((meta or {}).get("uri") or "").split(":", 1)[0].lower()
    for cls in policy.classes:
        if any(fnmatch(rel, pattern) for pattern in cls.paths):
            return cls
        if scheme and scheme in cls.uri_schemes:
            return cls
    return None


def apply_validity(
    policy: ValidityPolicy, rel: str, meta: dict[str, Any] | None
) -> tuple[dict[str, Any] | None, list[str]]:
    """Aplica a classe ao sidecar (já validado). Devolve (meta, avisos).

    - Sidecar com a data exigida em falta → ProvenanceError (a fonte não entra).
    - Sem sidecar numa classe que exige data → aviso; a fonte entra como antes.
    - TTL: sem `effective_until` do autor, `effective_until` = `retrieved_at` + `ttl_days`.
    """
    cls = classify(policy, rel, meta)
    if cls is None:
        return meta, []
    if meta is None:
        if cls.require:
            warning = (
                f"VALIDITY_MISSING: classe {cls.id} exige {list(cls.require)} e não há sidecar "
                f"(<nome>.meta.yaml) com a data da fonte"
            )
            return None, [warning]
        return None, []
    missing = [f for f in cls.require if not meta.get(f)]
    if missing:
        raise ProvenanceError(f"classe {cls.id} exige {missing} no sidecar (P-27/P-28)")
    if cls.ttl_days and not meta.get("effective_until"):
        retrieved = meta.get("retrieved_at")
        if not retrieved:
            raise ProvenanceError(f"classe {cls.id}: TTL sem retrieved_at")
        meta = {
            **meta,
            "effective_until": _comparable(retrieved) + timedelta(days=cls.ttl_days),
            "effective_until_source": f"ttl:{cls.ttl_days}d",
        }
    return meta, []


def validity_state(
    policy: ValidityPolicy,
    rel: str,
    meta: dict[str, Any] | None,
    *,
    at: datetime,
) -> dict[str, Any]:
    """O estado de uma fonte no instante `at` (para o relatório; nunca levanta).

    Estados: `sem_data` (evergreen), `valido`, `a_expirar`, `expirado`, `ainda_nao_vigora`,
    `falta_data` (classe exige e não há) e `sidecar_invalido`.
    """
    try:
        meta, warnings = apply_validity(policy, rel, meta)
        cls = classify(policy, rel, meta)
    except ProvenanceError as exc:
        return {"source": rel, "class": None, "state": "sidecar_invalido", "detail": str(exc)}
    row: dict[str, Any] = {
        "source": rel,
        "class": cls.id if cls else EVERGREEN,
        "effective_from": _iso((meta or {}).get("effective_from")),
        "effective_until": _iso((meta or {}).get("effective_until")),
        "detail": "",
    }
    if warnings:
        return {**row, "state": "falta_data", "detail": warnings[0]}
    if (meta or {}).get("status", "active") != "active":
        return {**row, "state": meta["status"]}
    start, end = (meta or {}).get("effective_from"), (meta or {}).get("effective_until")
    now = at if at.tzinfo else at.replace(tzinfo=UTC)
    if start and _comparable(start) > now:
        return {**row, "state": "ainda_nao_vigora"}
    if end:
        end_c = _comparable(end)
        if end_c <= now:
            return {**row, "state": "expirado"}
        if end_c <= now + timedelta(days=policy.expiring_within_days):
            return {**row, "state": "a_expirar"}
        return {**row, "state": "valido"}
    return {**row, "state": "valido" if cls else "sem_data"}


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None
