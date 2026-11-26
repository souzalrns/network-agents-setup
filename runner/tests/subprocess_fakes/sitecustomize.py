"""Só para os testes: o CLI corre num subprocesso, onde o monkeypatch do conftest não chega.

O conftest põe esta pasta no PYTHONPATH dos subprocessos (`_run_cli`); o Python importa este
`sitecustomize` ao arrancar e troca o MCP da base de conhecimento (precisa de rede e de MCP_API_KEY)
pela mesma base falsa dos testes no processo. Fora dos testes esta pasta não está no caminho.
"""
from __future__ import annotations

try:
    from plan_runner import knowledge_wiring

    class _FakeKnowledge:
        def retrieve(self, kb, query, *, top_k=None, filters=None, require_citations=None):
            return [{"content": f"trecho de teste para: {query[:60]}", "score": 0.9, "doc_id": "teste-1",
                     "citation": {"source": "docs/knowledge/teste.md", "locator": "§1"}, "metadata": None}]

    knowledge_wiring.McpKnowledge = lambda: _FakeKnowledge()
except ImportError:  # pragma: no cover - fora do runner
    pass
