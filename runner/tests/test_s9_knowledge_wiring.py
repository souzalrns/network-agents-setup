"""S9 -- testes de integracao da ligacao L5 (retrieve_knowledge) a execucao real.

Mocka o transporte MCP (mesmo padrao de test_mcp_knowledge.py) -- nao chama
nenhum servidor real. Confirma:
    - step SEM bloco `knowledge:` -> nenhum ficheiro de contexto, nenhum
      comportamento novo (regressao dos planos ja existentes)
    - step COM bloco `knowledge:` -> ficheiro de contexto escrito,
      plano continua a completar
    - falha do McpKnowledge (ex.: MCP_API_KEY em falta) -> nao aborta o
      step nem o plano; ficheiro de contexto regista a falha
    - o ficheiro nunca fica dentro de request.json nem de output_artifact
      (aditivo, nao substitutivo)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import engine, knowledge_wiring
from plan_runner.mcp_knowledge import McpKnowledgeError


class _FakeMcpKnowledge:
    def __init__(self, hits=None, raise_error: Exception | None = None):
        self._hits = hits if hits is not None else [
            {"content": "contexto de teste", "score": 0.9, "doc_id": "d1",
             "citation": {"source": "teste.md", "locator": None}, "metadata": None}
        ]
        self._raise_error = raise_error

    def retrieve(self, kb, query, *, top_k, filters, require_citations):
        if self._raise_error:
            raise self._raise_error
        return self._hits


def _write_plan(tmp_path: Path, *, with_knowledge: bool) -> Path:
    knowledge_block = (
        "    knowledge:\n"
        "      kb: marketing\n"
        "      query: teste\n"
    ) if with_knowledge else ""
    plan_text = (
        "id: s9-test\n"
        "version: 1\n"
        "objective: teste\n"
        "steps:\n"
        "  - id: step1\n"
        "    action: research\n"
        "    output_artifact: artifacts/out.md\n"
        f"{knowledge_block}"
    )
    p = tmp_path / "plan.yaml"
    p.write_text(plan_text, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _fake_repo_root(tmp_path, monkeypatch):
    """_validate_out_dir exige que --out fique dentro de <repo>/pilots/."""
    pilots = tmp_path / "pilots"
    pilots.mkdir()
    monkeypatch.setattr(
        engine, "_validate_out_dir",
        lambda out: out.resolve(),
    )
    return pilots


def test_step_without_knowledge_block_has_no_context_file(tmp_path, monkeypatch):
    plan_path = _write_plan(tmp_path, with_knowledge=False)
    out = tmp_path / "pilots" / "run1"

    result = engine.run_plan(plan_path, mode="stub", out_dir=out)

    assert result["state"] == "done"
    assert not (out / "pending_steps" / "step1" / "knowledge_context.md").exists()


def test_step_with_knowledge_block_writes_context_file(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge_wiring, "McpKnowledge", lambda: _FakeMcpKnowledge())

    plan_path = _write_plan(tmp_path, with_knowledge=True)
    out = tmp_path / "pilots" / "run2"

    result = engine.run_plan(plan_path, mode="stub", out_dir=out)

    assert result["state"] == "done"
    ctx = out / "pending_steps" / "step1" / "knowledge_context.md"
    assert ctx.exists()
    text = ctx.read_text(encoding="utf-8")
    assert "[L5 CONTEXT]" in text
    assert "contexto de teste" in text

    # Aditivo: o artefacto normal do step continua a existir, sem alteracao.
    assert (out / "artifacts" / "out.md").exists()


def test_knowledge_retrieval_failure_does_not_abort_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_wiring,
        "McpKnowledge",
        lambda: _FakeMcpKnowledge(raise_error=McpKnowledgeError("falha simulada")),
    )

    plan_path = _write_plan(tmp_path, with_knowledge=True)
    out = tmp_path / "pilots" / "run3"

    result = engine.run_plan(plan_path, mode="stub", out_dir=out)

    assert result["state"] == "done"  # NAO aborta
    ctx = out / "pending_steps" / "step1" / "knowledge_context.md"
    assert ctx.exists()
    assert "[L5 CONTEXT: FALHA]" in ctx.read_text(encoding="utf-8")
    assert "falha simulada" in ctx.read_text(encoding="utf-8")

    # events.jsonl regista a falha
    events = (out / "events.jsonl").read_text(encoding="utf-8")
    assert "knowledge_context_failed" in events


def test_incomplete_knowledge_block_is_skipped(tmp_path, monkeypatch):
    """kb sem query (ou vice-versa) -- nao tenta sequer chamar o MCP."""
    called = {"n": 0}

    class _ShouldNotBeCalled:
        def retrieve(self, *a, **kw):
            called["n"] += 1
            return []

    monkeypatch.setattr(knowledge_wiring, "McpKnowledge", lambda: _ShouldNotBeCalled())

    plan_text = (
        "id: s9-test-incomplete\n"
        "version: 1\n"
        "objective: teste\n"
        "steps:\n"
        "  - id: step1\n"
        "    action: research\n"
        "    output_artifact: artifacts/out.md\n"
        "    knowledge:\n"
        "      kb: marketing\n"  # sem 'query'
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(plan_text, encoding="utf-8")
    out = tmp_path / "pilots" / "run4"

    result = engine.run_plan(plan_path, mode="stub", out_dir=out)

    assert result["state"] == "done"
    assert called["n"] == 0  # nunca chegou a chamar retrieve()


def test_request_json_unchanged_by_knowledge_wiring(tmp_path, monkeypatch):
    """O ficheiro de contexto nunca entra dentro de request.json (aditivo, nao
    substitutivo) -- so existe como ficheiro irmao em pending_steps/<id>/.
    """
    monkeypatch.setattr(knowledge_wiring, "McpKnowledge", lambda: _FakeMcpKnowledge())

    plan_path = _write_plan(tmp_path, with_knowledge=True)
    out = tmp_path / "pilots" / "run5"

    engine.run_plan(plan_path, mode="external", out_dir=out)

    request_path = out / "pending_steps" / "step1" / "request.json"
    assert request_path.exists()
    request_data = json.loads(request_path.read_text(encoding="utf-8"))
    assert "knowledge_context" not in request_data
    assert "knowledge" not in request_data

    ctx_path = out / "pending_steps" / "step1" / "knowledge_context.md"
    assert ctx_path.exists()
