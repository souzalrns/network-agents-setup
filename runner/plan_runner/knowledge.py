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


# F3b (P-31 = D): regra de conflitos no prompt do worker. Vai dentro do bloco do L5 e só
# com 2 ou mais fontes (o único caso em que pode haver conflito): na directiva de grounding
# custaria ~900 tokens por run em todos os agentes (test_context_opt, calibração do B1).
CONFLICT_RULE = (
    "Se 2 fontes divergirem: a 'substituída por' perde; depois ganha a de maior autoridade "
    "(oficial > curado > experimental) e, com a mesma, a de data mais recente. Diz que há "
    "conflito e cita as 2; sem desempate, ou em domínio de alto risco, (b) + HITL."
)


def _day(value: Any) -> str:
    """ISO 8601 do MCP (`2026-10-05T10:00:00+00:00`) → só o dia."""
    return str(value)[:10]


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
        meta = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
        source = citation.get("source") or "?"
        locator = citation.get("locator") or "?"
        extra = [f"uri: {citation['uri']}"] if citation.get("uri") else []
        # F3b (P-31 = D): autoridade e data de cada fonte, para o worker resolver
        # conflitos pela CONFLICT_RULE (no fim do bloco, com 2+ fontes).
        if meta.get("authority"):
            extra.append(f"autoridade: {meta['authority']}")
        if meta.get("retrieved_at"):
            extra.append(f"data: {_day(meta['retrieved_at'])}")
        if meta.get("status") and meta["status"] != "active":
            extra.append(f"estado: {meta['status']}")
        if meta.get("superseded_by"):
            extra.append(f"substituída por {meta['superseded_by']}")
        if meta.get("effective_from"):
            extra.append(f"em vigor desde {_day(meta['effective_from'])}")
        if meta.get("effective_until"):
            extra.append(f"válido até {_day(meta['effective_until'])}")
        tail = f" | {'; '.join(extra)}" if extra else ""
        lines.append(f"- {content} [Fonte: {source} @ {locator}{tail}]")
    if len(hits) > 1:
        lines.append(CONFLICT_RULE)
    lines.append("[/L5 CONTEXT]")
    return "\n".join(lines)
