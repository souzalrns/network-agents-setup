"""Chunking markdown por seccoes (T6 - pipeline de ingestao de knowledge).

Design: docs/T6-INGEST-PIPELINE.md secao 6 (Chunking).
    - Preferir secoes `##` / `###` auto-contidas
    - ~200-600 tokens por chunk
    - Metadados: source_path, titulo, agent_id
    - Nao misturar dois playbooks num chunk

Este modulo e ADITIVO. Nao substitui nada. Nao toca no engine, no CLI,
no ingest_delta.py. So produz chunks (lista de dicts) a partir de texto.

Sem LLM, sem Supabase, sem rede, sem dependencias novas (so stdlib).

Saida compativel com o contrato `retrieve_knowledge` (C8d):
    content, doc_id, kb, agent_id, citation (source, locator), chunk_index
"""
from __future__ import annotations

import re
from typing import Any

# Limites (T6 secao 6: ~200-600 tokens). Aproximacao: 4 chars = 1 token.
MAX_CHARS = 2400   # ~600 tokens
MIN_CHARS = 200    # ~50 tokens; fragmentos menores juntam-se ao anterior


_HEADER_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)


def _split_by_headers(text: str) -> list[tuple[str, int, int]]:
    """Divide o texto em secoes por H2/H3.

    Devolve lista de (conteudo, linha_inicio, linha_fim), em ordem.
    A primeira "seccao" pode ser o preambulo (antes do primeiro H2).
    Linhas contadas a partir de 1.
    """
    if not text:
        return []

    lines = text.splitlines(keepends=True)

    header_line_idx: list[int] = []
    for i, line in enumerate(lines):
        if _HEADER_RE.match(line):
            header_line_idx.append(i)

    if not header_line_idx:
        return [(text, 1, len(lines))]

    sections: list[tuple[str, int, int]] = []

    first = header_line_idx[0]
    if first > 0:
        pre = "".join(lines[:first]).strip()
        if pre:
            sections.append((pre, 1, first))

    for j, start in enumerate(header_line_idx):
        end = header_line_idx[j + 1] if j + 1 < len(header_line_idx) else len(lines)
        body = "".join(lines[start:end]).strip()
        if body:
            sections.append((body, start + 1, end))

    return sections


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Corta texto em fatias de <= max_chars (best-effort)."""
    return [
        text[i : i + max_chars].strip()
        for i in range(0, len(text), max_chars)
    ]


def _split_oversized(text: str, max_chars: int) -> list[str]:
    """Divide uma seccao grande em pedacos <= max_chars, por paragrafos.

    Se um paragrafo sozinho ainda for maior que max_chars, e cortado
    em fatias duras.
    """
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    buf: list[str] = []
    buf_len = 0

    for para in text.split("\n\n"):
        para_len = len(para)
        if para_len > max_chars:
            # Fecha o buffer antes de cortar o paragrafo gigante.
            if buf:
                parts.append("\n\n".join(buf).strip())
                buf = []
                buf_len = 0
            parts.extend(_hard_split(para, max_chars))
            continue

        # +2 pelo "\n\n" que vamos inserir entre paragrafos.
        added = para_len + (2 if buf else 0)
        if buf and buf_len + added > max_chars:
            parts.append("\n\n".join(buf).strip())
            buf = []
            buf_len = 0
        buf.append(para)
        buf_len += (para_len + (2 if buf_len else 0)) if buf_len else para_len

    if buf:
        parts.append("\n\n".join(buf).strip())

    return [p for p in parts if p]


def _merge_small(
    chunks: list[tuple[str, int, int]],
    min_chars: int,
    max_chars: int,
) -> list[tuple[str, int, int]]:
    """Junta chunks pequenos ao anterior, SEM exceder max_chars."""
    if not chunks:
        return []

    merged: list[tuple[str, int, int]] = [chunks[0]]
    for content, start, end in chunks[1:]:
        prev_content, prev_start, prev_end = merged[-1]
        combined_len = len(prev_content) + 2 + len(content)
        if len(content) < min_chars and combined_len <= max_chars:
            merged[-1] = (
                prev_content + "\n\n" + content,
                prev_start,
                end,
            )
        else:
            merged.append((content, start, end))
    return merged


def chunk_markdown(
    text: str,
    *,
    source_path: str,
    agent_id: str,
    kb: str = "marketing",
    max_chars: int = MAX_CHARS,
    min_chars: int = MIN_CHARS,
) -> list[dict[str, Any]]:
    """Divide markdown em chunks por secoes H2/H3.

    Args:
        text: conteudo markdown.
        source_path: path relativo (ex. "docs/knowledge/ai-findability.md").
        agent_id: agent dono (ex. "marketing").
        kb: id da base de conhecimento (default "marketing").
        max_chars: limite por chunk (default ~600 tokens).
        min_chars: fragmentos menores juntam-se ao anterior (se couberem).

    Returns:
        Lista de dicts no formato compativel com retrieve_knowledge:
            {
                "content": str,
                "doc_id": str,
                "kb": str,
                "agent_id": str,
                "citation": {"source": str, "locator": str},
                "chunk_index": int,
            }
        Lista vazia se `text` for vazio/so-espacos.
    """
    if not text or not text.strip():
        return []

    sections = _split_by_headers(text)

    expanded: list[tuple[str, int, int]] = []
    for content, start, end in sections:
        if len(content) <= max_chars:
            expanded.append((content, start, end))
        else:
            for piece in _split_oversized(content, max_chars):
                expanded.append((piece, start, end))

    merged = _merge_small(expanded, min_chars, max_chars)

    out: list[dict[str, Any]] = []
    for idx, (content, start, end) in enumerate(merged):
        out.append(
            {
                "content": content,
                "doc_id": source_path,
                "kb": kb,
                "agent_id": agent_id,
                "citation": {
                    "source": source_path,
                    "locator": f"l.{start}-{end}",
                },
                "chunk_index": idx,
            }
        )
    return out
