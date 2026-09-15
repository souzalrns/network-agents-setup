"""L5 knowledge retrieval -- lado Python do contrato `memory.retrieve_knowledge`.

Contrato: docs/architecture/memory/contracts.md (retrieve_knowledge)
Arquitetura: docs/architecture/memory/ARCHITECTURE.md (L5)
Padrao de retrieve: docs/architecture/memory/rag-l5.md
Grounding: docs/architecture/memory/GROUNDING.md

Este modulo e ADITIVO. Nao substitui nada. Nao toca no engine, no CLI, no
agent-network-mcp. Implementa o protocolo (KnowledgeBackend) + duas
implementacoes sem infra:

    NullKnowledge  -- no-op, devolve []  (default)
    MockKnowledge  -- hits fixos           (testes)

O McpKnowledge (chama o agent-network-mcp via HTTP) fica para C8e, quando
o MCP estiver pronto. Sem LLM, sem Supabase, sem dependencias novas.
"""
from __future__ import annotations

from typing import Any, Protocol

TOP_K_DEFAULT = 8
TOP_K_MAX = 30


class KnowledgeBackend(Protocol):
    def retrieve(
        self,
        kb: str,
        query: str,
        *,
        top_k: int,
        filters: dict[str, Any] | None,
        require_citations: bool,
    ) -> list[dict[str, Any]]:  # pragma: no cover - protocol
        ...


class NullKnowledge:
    def retrieve(
        self,
        kb: str,
        query: str,
        *,
        top_k: int,
        filters: dict[str, Any] | None,
        require_citations: bool,
    ) -> list[dict[str, Any]]:
        _ = (kb, query, top_k, filters, require_citations)
        return []


class MockKnowledge:
    def __init__(self, hits: list[dict[str, Any]] | None = None):
        self._hits = list(hits or [])

    def retrieve(
        self,
        kb: str,
        query: str,
        *,
        top_k: int,
        filters: dict[str, Any] | None,
        require_citations: bool,
    ) -> list[dict[str, Any]]:
        _ = (kb, query, filters)
        results = list(self._hits)[:top_k]
        if require_citations:
            results = [h for h in results if h.get("citation")]
        return results


def _validate_top_k(top_k: int) -> int:
    if top_k < 1:
        return 1
    if top_k > TOP_K_MAX:
        return TOP_K_MAX
    return top_k


def retrieve_knowledge(
    kb: str,
    query: str,
    *,
    top_k: int = TOP_K_DEFAULT,
    filters: dict[str, Any] | None = None,
    require_citations: bool = True,
    backend: KnowledgeBackend | None = None,
    allowed_kbs: set[str] | None = None,
) -> list[dict[str, Any]]:
    if allowed_kbs is not None and kb not in allowed_kbs:
        return []
    if not query:
        return []

    impl = backend if backend is not None else NullKnowledge()
    return impl.retrieve(
        kb,
        query,
        top_k=_validate_top_k(top_k),
        filters=filters,
        require_citations=require_citations,
    )


def grounding_block(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return (
            "[L5 CONTEXT: EMPTY]\n"
            "Contexto vazio -- nao inventar. Se o dado nao consta aqui, "
            "diz que nao tens, nao completes de memoria.\n"
            "[/L5 CONTEXT]"
        )

    lines: list[str] = ["[L5 CONTEXT]"]
    for hit in hits:
        content = (hit.get("content") or "").strip().replace("\n", " ")
        citation = hit.get("citation") or {}
        source = citation.get("source") or "?"
        locator = citation.get("locator") or "?"
        lines.append(f"- {content} [Fonte: {source} @ {locator}]")
    lines.append("[/L5 CONTEXT]")
    return "\n".join(lines)
