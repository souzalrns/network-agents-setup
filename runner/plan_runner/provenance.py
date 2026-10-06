"""F3a: proveniência de uma fonte do T6 (ADR-F3-PROVENANCE-RETRIEVE, P-26 = A).

Lê o `<nome>.meta.yaml` que o F1 (`scripts/ingest_document.py`) e o F2
(`scripts/web_fetch.py`) gravam ao lado do `.md`, valida-o (regra 3 do
ADR-INGESTION-PRIMITIVES: nada entra no L5 sem `source_meta` válido) e converte-o nas
colunas da `knowledge_sources` que a migração `scripts/migrations/f3_provenance_retrieve.sql`
acrescenta.

- Sem sidecar (os .md escritos à mão do MANIFEST): proveniência derivada do git
  (`uri` = path, `document_type` = "md", `status` = "active"). Sem regressão.
- Com sidecar inválido: `ProvenanceError`. O `ingest_apply` recusa a fonte inteira
  (nunca grava proveniência parcial nem chunks sem a proveniência declarada).

`REQUIRED_META` tem de ser igual ao de `scripts/ingest_document.py` (há um teste).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

import yaml

REQUIRED_META = ("uri", "title", "document_type", "retrieved_at", "content_hash", "status")
ALLOWED_STATUS = ("active", "superseded", "revoked", "expired", "deleted")
# Colunas da knowledge_sources (migração F3a), pela ordem do SQL do writer.
SOURCE_COLUMNS = (
    "uri",
    "final_url",
    "title",
    "document_type",
    "retrieved_at",
    "status",
    "jurisdiction",
    "effective_from",
    "effective_until",
)
DATETIME_FIELDS = ("retrieved_at", "effective_from", "effective_until")


class ProvenanceError(ValueError):
    """O `.meta.yaml` existe mas não é válido."""


def sidecar_path(md_path: Path) -> Path:
    return md_path.with_suffix(".meta.yaml")


def _as_datetime(value: Any, field: str) -> datetime | date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime | date):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ProvenanceError(f"{field}: '{value}' não é uma data ISO 8601") from exc


def default_meta(rel: str) -> dict[str, Any]:
    """Proveniência de um .md sem sidecar: o que o git já diz."""
    return {"uri": rel, "document_type": "md", "status": "active"}


def load_meta(md_path: Path, content_hash: str) -> dict[str, Any] | None:
    """Lê e valida o sidecar. `None` se não houver; `ProvenanceError` se for inválido.

    `content_hash` é o SHA-256 do `.md` que o T6 já calculou (`sha256_file`).
    """
    path = sidecar_path(md_path)
    if not path.is_file():
        return None
    try:
        meta = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProvenanceError(f"{path.name}: YAML inválido: {exc}") from exc
    if not isinstance(meta, dict):
        raise ProvenanceError(f"{path.name}: tem de ser um mapa YAML")
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise ProvenanceError(f"{path.name}: faltam campos {missing}")
    if meta["content_hash"] != content_hash:
        raise ProvenanceError(
            f"{path.name}: content_hash {str(meta['content_hash'])[:12]}… ≠ sha256 do .md "
            f"{content_hash[:12]}… (o .md mudou depois da conversão?)"
        )
    if meta["status"] not in ALLOWED_STATUS:
        raise ProvenanceError(f"{path.name}: status '{meta['status']}' fora de {ALLOWED_STATUS}")
    for field in DATETIME_FIELDS:
        meta[field] = _as_datetime(meta.get(field), field)
    start, end = meta.get("effective_from"), meta.get("effective_until")
    if start and end and _comparable(end) <= _comparable(start):
        raise ProvenanceError(f"{path.name}: effective_until tem de ser depois de effective_from")
    return meta


def _comparable(value: datetime | date) -> datetime:
    """`date` → meia-noite; sem fuso → UTC (o Postgres grava timestamptz)."""
    if not isinstance(value, datetime):
        value = datetime.combine(value, time())
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def to_source_columns(meta: dict[str, Any]) -> dict[str, Any]:
    """Colunas da knowledge_sources + `meta` (jsonb com o resto, em texto)."""
    columns = {k: meta.get(k) for k in SOURCE_COLUMNS}
    columns["status"] = columns["status"] or "active"
    extra = {k: v for k, v in meta.items() if k not in SOURCE_COLUMNS and k != "content_hash"}
    columns["meta"] = {k: _jsonable(v) for k, v in extra.items()}
    return columns


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return value
