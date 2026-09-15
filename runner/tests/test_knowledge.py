"""Testes de knowledge.py -- contrato L5 `memory.retrieve_knowledge`.

Estilo alinhado com test_hitl_contract.py e test_working_memory.py:
import absoluto de plan_runner, sem tocar em pilots/, sem rede.
"""
from __future__ import annotations

from plan_runner.knowledge import (
    TOP_K_DEFAULT,
    TOP_K_MAX,
    MockKnowledge,
    NullKnowledge,
    grounding_block,
    retrieve_knowledge,
)


def _hit(content: str = "hello", source: str = "doc.md", locator: str = "l.1") -> dict:
    return {
        "content": content,
        "score": 0.9,
        "doc_id": "doc-1",
        "citation": {"source": source, "locator": locator},
        "metadata": {},
    }


def test_null_knowledge_returns_empty():
    assert retrieve_knowledge("marketing", "q", backend=NullKnowledge()) == []


def test_retrieve_knowledge_default_backend_is_null():
    assert retrieve_knowledge("marketing", "q") == []


def test_mock_returns_hits():
    hits = [_hit("a"), _hit("b")]
    out = retrieve_knowledge("marketing", "q", backend=MockKnowledge(hits))
    assert len(out) == 2


def test_mock_respects_top_k():
    hits = [_hit(f"h{i}") for i in range(10)]
    out = retrieve_knowledge("marketing", "q", top_k=3, backend=MockKnowledge(hits))
    assert len(out) == 3


def test_mock_filters_by_citation_when_required():
    with_cit = _hit("a")
    without_cit = {"content": "b", "score": 0.5, "doc_id": "d", "citation": None, "metadata": {}}
    out = retrieve_knowledge(
        "marketing", "q",
        backend=MockKnowledge([with_cit, without_cit]),
        require_citations=True,
    )
    assert len(out) == 1
    assert out[0]["content"] == "a"


def test_mock_keeps_no_citation_when_not_required():
    without_cit = {"content": "b", "score": 0.5, "doc_id": "d", "citation": None, "metadata": {}}
    out = retrieve_knowledge(
        "marketing", "q",
        backend=MockKnowledge([without_cit]),
        require_citations=False,
    )
    assert len(out) == 1


def test_top_k_default_is_8():
    assert TOP_K_DEFAULT == 8


def test_top_k_max_is_30():
    assert TOP_K_MAX == 30


def test_top_k_clamped_to_max():
    hits = [_hit(f"h{i}") for i in range(50)]
    out = retrieve_knowledge("k", "q", top_k=100, backend=MockKnowledge(hits))
    assert len(out) == TOP_K_MAX


def test_top_k_clamped_to_min():
    hits = [_hit("a")]
    out = retrieve_knowledge("k", "q", top_k=0, backend=MockKnowledge(hits))
    assert len(out) == 1


def test_allowlist_blocks_unknown_kb():
    hits = [_hit("a")]
    out = retrieve_knowledge(
        "forbidden", "q",
        backend=MockKnowledge(hits),
        allowed_kbs={"marketing", "design"},
    )
    assert out == []


def test_allowlist_allows_listed_kb():
    hits = [_hit("a")]
    out = retrieve_knowledge(
        "marketing", "q",
        backend=MockKnowledge(hits),
        allowed_kbs={"marketing"},
    )
    assert len(out) == 1


def test_allowlist_none_is_permissive():
    hits = [_hit("a")]
    out = retrieve_knowledge("anything", "q", backend=MockKnowledge(hits))
    assert len(out) == 1


def test_empty_query_returns_empty():
    hits = [_hit("a")]
    out = retrieve_knowledge("marketing", "", backend=MockKnowledge(hits))
    assert out == []


def test_grounding_block_empty():
    block = grounding_block([])
    assert "EMPTY" in block
    assert "nao inventar" in block
    assert "[/L5 CONTEXT]" in block


def test_grounding_block_with_hits():
    block = grounding_block([_hit("Conteudo", source="doc.md", locator="l.42")])
    assert "[L5 CONTEXT]" in block
    assert "Conteudo" in block
    assert "Fonte: doc.md @ l.42" in block
    assert "[/L5 CONTEXT]" in block


def test_grounding_block_multiline_content_is_flat():
    hit = _hit("linha1\nlinha2")
    block = grounding_block([hit])
    assert "linha1 linha2" in block


def test_grounding_block_missing_citation_fields():
    hit = {"content": "x", "score": 0.1, "doc_id": "d", "citation": {}, "metadata": {}}
    block = grounding_block([hit])
    assert "Fonte: ? @ ?" in block
