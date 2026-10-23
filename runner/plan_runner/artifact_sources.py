"""Fontes de um artefacto (F3-ART-1): o `result.json` de cada passo lista o que o informou.

Done do EXECUTION-PLAN §7 F3: "provenance em todos os artefactos". Junta, sem repetir:
- o contexto do L5 injectado no passo (`knowledge_sources.json`, escrito pelo
  `knowledge_wiring` ao lado do `knowledge_context.md`), com uri, locator, estado e validade;
- as tools do passo que devolveram fontes (`retrieve_knowledge`, `read_repo_file`, `fetch_url`),
  com a proveniência estruturada quando a tool a dá (o `fetch_url` dá URL final, título,
  data e hash do conteúdo).

Só lê o que já está no disco ou no registo das chamadas: não chama rede nem modelos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

KNOWLEDGE_SOURCES_FILE = "knowledge_sources.json"
MAX_SOURCES = 50


def knowledge_sources(hits: list[dict[str, Any]], kb: str) -> list[dict[str, Any]]:
    """As citações dos hits do L5, no formato das fontes do artefacto (v2 traz estado e validade)."""
    out: list[dict[str, Any]] = []
    for h in hits or []:
        if not isinstance(h, dict):
            continue
        cit = h.get("citation") if isinstance(h.get("citation"), dict) else {}
        meta = h.get("metadata") if isinstance(h.get("metadata"), dict) else {}
        src = {
            "kind": "l5",
            "kb": kb,
            "source": cit.get("source") or h.get("source"),
            "uri": cit.get("uri"),
            "locator": cit.get("locator"),
            "status": meta.get("status"),
            "document_type": meta.get("document_type"),
            "valid_from": meta.get("valid_from"),
            "valid_to": meta.get("valid_to"),
        }
        out.append({k: v for k, v in src.items() if v not in (None, "")})
    return out


def _key(src: dict[str, Any]) -> tuple[Any, ...]:
    return (src.get("kind"), src.get("final_url") or src.get("uri") or src.get("source"), src.get("locator"))


def collect(pending_dir: Path, tools_meta: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Fontes do passo, sem duplicados, pela ordem em que entraram (L5 primeiro, depois as tools)."""
    found: list[dict[str, Any]] = []
    path = pending_dir / KNOWLEDGE_SOURCES_FILE
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            found.extend(s for s in data if isinstance(s, dict))
        except (json.JSONDecodeError, OSError):
            found.append({"kind": "l5", "error": f"{KNOWLEDGE_SOURCES_FILE} ilegível"})
    for call in (tools_meta or {}).get("calls") or []:
        if not isinstance(call, dict) or not call.get("ok"):
            continue
        if call.get("provenance"):
            found.extend({**p, "tool": call.get("tool")} for p in call["provenance"] if isinstance(p, dict))
            continue
        for s in call.get("sources") or []:
            found.append({"kind": "tool", "tool": call.get("tool"), "source": str(s)})
    out, seen = [], set()
    for src in found:
        k = _key(src)
        if k in seen:
            continue
        seen.add(k)
        out.append(src)
    return out[:MAX_SOURCES]
