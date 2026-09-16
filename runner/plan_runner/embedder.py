"""Gemini embeddings (768 dims) para o pipeline T6.

Design: docs/T6-INGEST-PIPELINE.md (secao 4: KnowledgeChunk.embedding).
Contrato: docs/architecture/memory/contracts.md (retrieve_knowledge).

Este modulo e ADITIVO. Nao substitui nada. Nao toca no engine, no CLI,
no ingest_delta.py. So gera embeddings a partir de texto.

Modelo: gemini-embedding-001 (free tier).
Dimensoes: 768 (outputDimensionality) -- bate certo com o vector(768) da
tabela knowledge_chunks no Supabase.

Sem LLM generativo, sem Supabase, sem dependencias novas alem de httpx
(ja instalado). Le GEMINI_API_KEY do ambiente.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

GEMINI_MODEL = "gemini-embedding-001"
GEMINI_DIMS = 768
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:embedContent"
)

# Limite de caracteres por pedido (a API tem limite de tokens).
# ~4 chars por token; deixamos margem para 8000 tokens.
MAX_CHARS_PER_REQUEST = 30000


class EmbedderError(RuntimeError):
    """Erro ao gerar embedding (rede, auth, dimensao errada, etc.)."""


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise EmbedderError(
            "GEMINI_API_KEY nao definida no ambiente. "
            "Adiciona ao .env e exporta antes de correr."
        )
    return key


def embed_text(text: str, *, timeout: float = 30.0) -> list[float]:
    """Gera um embedding (768 dims) para um texto.

    Args:
        text: texto a embeddar. Vazio -> lista vazia.
        timeout: timeout HTTP em segundos.

    Returns:
        Lista de 768 floats.

    Raises:
        EmbedderError: se a API falhar, ou se a dimensao for != 768.
    """
    if not text or not text.strip():
        return []

    if len(text) > MAX_CHARS_PER_REQUEST:
        # Trunca (o caller deve chunkaar antes; isto e defesa em profundidade).
        text = text[:MAX_CHARS_PER_REQUEST]

    key = _api_key()
    body: dict[str, Any] = {
        "model": f"models/{GEMINI_MODEL}",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": GEMINI_DIMS,
    }

    try:
        r = httpx.post(
            GEMINI_URL,
            params={"key": key},
            json=body,
            timeout=timeout,
        )
    except httpx.HTTPError as e:
        raise EmbedderError(f"Falha HTTP ao chamar Gemini: {e}") from e

    if r.status_code != 200:
        raise EmbedderError(
            f"Gemini devolveu HTTP {r.status_code}: {r.text[:200]}"
        )

    data = r.json()
    values = (data.get("embedding") or {}).get("values") or []
    if len(values) != GEMINI_DIMS:
        raise EmbedderError(
            f"Gemini devolveu {len(values)} dimensoes (esperado {GEMINI_DIMS}). "
            "Verifica outputDimensionality e o modelo."
        )
    return [float(v) for v in values]


def embed_batch(
    texts: list[str],
    *,
    timeout: float = 60.0,
) -> list[list[float]]:
    """Gera embeddings para uma lista de textos (sequencial).

    A API do Gemini nao tem batch endpoint no free tier, logo iteramos.
    Se um falhar, propaga o erro (o caller decide o que fazer).
    """
    out: list[list[float]] = []
    for t in texts:
        out.append(embed_text(t, timeout=timeout))
    return out
