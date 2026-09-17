"""Testes de mcp_knowledge.py -- sem chamar o agent-network-mcp real.

Mocka os 3 niveis do transporte MCP Streamable HTTP:
    httpx.AsyncClient          -- cliente HTTP
    streamable_http_client     -- streams de leitura/escrita
    ClientSession              -- initialize() + call_tool()

E verifica:
- sucesso (hits devolvidos tal como vieram no JSON)
- erro reportado pela propria tool (isError=True)
- timeout / falha de rede (incluindo o caso real de ExceptionGroup
  embrulhado pelo anyio.TaskGroup interno do streamable_http_client --
  ver nota no proprio mcp_knowledge.py, confirmado com servidor real)
- resposta vazia (sem bloco de texto no content)
- MCP_API_KEY em falta
- filters=None e omitido do payload (nao mandado como null -- a tool do
  lado JS usa Zod .optional(), que rejeita null explicito; confirmado
  com um servidor MCP real de teste)
"""
from __future__ import annotations

import json

import httpx
import pytest

from plan_runner import mcp_knowledge
from plan_runner.mcp_knowledge import McpKnowledge, McpKnowledgeError


# ---------------------------------------------------------------------------
# Fakes -- um por camada do transporte MCP
# ---------------------------------------------------------------------------


class _FakeTextBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeCallToolResult:
    def __init__(self, *, is_error: bool = False, texts: list[str] | None = None):
        self.isError = is_error
        self.content = [_FakeTextBlock(t) for t in (texts or [])]


class _FakeSession:
    """Stand-in para ClientSession -- guarda a ultima chamada para inspeccao."""

    def __init__(self, result: _FakeCallToolResult | None = None, raise_on_init: Exception | None = None):
        self._result = result
        self._raise_on_init = raise_on_init
        self.last_call: tuple[str, dict] | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def initialize(self):
        if self._raise_on_init:
            raise self._raise_on_init

    async def call_tool(self, name, arguments):
        self.last_call = (name, arguments)
        return self._result


class _FakeStreamCtx:
    """Stand-in para o context manager devolvido por streamable_http_client."""

    def __init__(self, raise_on_enter: BaseException | None = None):
        self._raise_on_enter = raise_on_enter

    async def __aenter__(self):
        if self._raise_on_enter:
            raise self._raise_on_enter
        return ("fake-read-stream", "fake-write-stream", lambda: None)

    async def __aexit__(self, *exc):
        return False


class _FakeHttpxClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("MCP_API_KEY", "fake-key-for-tests-0123456789")
    monkeypatch.delenv("MCP_URL", raising=False)


def _patch_transport(monkeypatch, *, session: _FakeSession, stream_ctx: _FakeStreamCtx | None = None):
    monkeypatch.setattr(mcp_knowledge.httpx, "AsyncClient", lambda **kw: _FakeHttpxClient())
    monkeypatch.setattr(
        mcp_knowledge,
        "streamable_http_client",
        lambda url, http_client=None: (stream_ctx or _FakeStreamCtx()),
    )
    monkeypatch.setattr(mcp_knowledge, "ClientSession", lambda read, write: session)


def _hits_payload(hits: list[dict]) -> str:
    return json.dumps({"hits": hits, "hitCount": len(hits)})


# ---------------------------------------------------------------------------
# Sucesso
# ---------------------------------------------------------------------------


def test_retrieve_success_returns_hits(monkeypatch):
    hit = {
        "content": "trecho relevante",
        "score": 0.91,
        "doc_id": "id-1",
        "citation": {"source": "fonte.md", "locator": None},
        "metadata": None,
    }
    result = _FakeCallToolResult(texts=[_hits_payload([hit])])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    hits = client.retrieve("viannalegal", "prazo", top_k=8, filters=None, require_citations=False)

    assert hits == [hit]
    assert session.last_call[0] == "retrieve_knowledge"


def test_retrieve_passes_kb_query_topk_and_require_citations(monkeypatch):
    result = _FakeCallToolResult(texts=[_hits_payload([])])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    client.retrieve("sst", "epi obrigatorio", top_k=5, filters=None, require_citations=True)

    name, args = session.last_call
    assert name == "retrieve_knowledge"
    assert args["kb"] == "sst"
    assert args["query"] == "epi obrigatorio"
    assert args["top_k"] == 5
    assert args["require_citations"] is True


# ---------------------------------------------------------------------------
# filters=None nao vai como null (bug real encontrado e corrigido)
# ---------------------------------------------------------------------------


def test_retrieve_omits_filters_key_when_none(monkeypatch):
    result = _FakeCallToolResult(texts=[_hits_payload([])])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)

    _, args = session.last_call
    assert "filters" not in args


def test_retrieve_includes_filters_when_provided(monkeypatch):
    result = _FakeCallToolResult(texts=[_hits_payload([])])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    client.retrieve("viannalegal", "x", top_k=8, filters={"tipo": "artigo"}, require_citations=False)

    _, args = session.last_call
    assert args["filters"] == {"tipo": "artigo"}


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------


def test_retrieve_raises_on_tool_error(monkeypatch):
    result = _FakeCallToolResult(is_error=True, texts=["Supabase não configurado"])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="Supabase"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_on_empty_response(monkeypatch):
    result = _FakeCallToolResult(texts=[])  # nenhum bloco de texto
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="[Rr]esposta vazia"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_on_invalid_json(monkeypatch):
    result = _FakeCallToolResult(texts=["isto nao e json"])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="JSON"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_on_missing_hits_field(monkeypatch):
    result = _FakeCallToolResult(texts=[json.dumps({"hitCount": 0})])
    session = _FakeSession(result=result)
    _patch_transport(monkeypatch, session=session)

    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="hits"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_on_httpx_timeout(monkeypatch):
    def raise_timeout(**kw):
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(mcp_knowledge.httpx, "AsyncClient", raise_timeout)

    client = McpKnowledge(timeout=1.0)
    with pytest.raises(McpKnowledgeError, match="Timeout"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_on_connection_failure_wrapped_in_exception_group(monkeypatch):
    """Regressao: streamable_http_client corre num anyio.TaskGroup -- falhas
    de rede chegam embrulhadas num BaseExceptionGroup, nao como
    httpx.HTTPError direto. Confirmado com ligacao recusada a um servidor
    MCP real em 2026-09-17 -- sem o apanhador de ExceptionGroup em
    mcp_knowledge.py, isto propagava-se sem tratamento.
    """
    inner = ConnectionRefusedError("All connection attempts failed")
    wrapped = BaseExceptionGroup("unhandled errors in a TaskGroup", [inner])
    stream_ctx = _FakeStreamCtx(raise_on_enter=wrapped)
    session = _FakeSession()
    _patch_transport(monkeypatch, session=session, stream_ctx=stream_ctx)

    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="connection attempts failed"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


def test_retrieve_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    client = McpKnowledge()
    with pytest.raises(McpKnowledgeError, match="MCP_API_KEY"):
        client.retrieve("viannalegal", "x", top_k=8, filters=None, require_citations=False)


# ---------------------------------------------------------------------------
# URL
# ---------------------------------------------------------------------------


def test_mcp_url_uses_default_when_env_not_set(monkeypatch):
    monkeypatch.delenv("MCP_URL", raising=False)
    assert mcp_knowledge._mcp_url() == "http://localhost:3000/api/mcp"


def test_mcp_url_uses_env_when_set(monkeypatch):
    monkeypatch.setenv("MCP_URL", "https://agent-network-mcp-oddn.vercel.app/")
    assert mcp_knowledge._mcp_url() == "https://agent-network-mcp-oddn.vercel.app/api/mcp"
