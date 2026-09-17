"""McpKnowledge -- backend KnowledgeBackend que chama o agent-network-mcp via HTTP.

Design: docs/architecture/memory/rag-l5.md
Contrato: docs/architecture/memory/contracts.md (retrieve_knowledge)
Tool consumida: retrieve_knowledge, em app/api/mcp/route.js (agent-network-mcp),
que expoe retrieveKnowledgeHits() de lib/knowledge.js -- ver C8e.

Este modulo e ADITIVO. Nao substitui NullKnowledge nem MockKnowledge (em
knowledge.py, que nao e tocado aqui). Nao toca no engine, no CLI, no
langgraph_engine. So implementa o protocolo KnowledgeBackend chamando o
agent-network-mcp por HTTP.

Transporte: MCP Streamable HTTP (a mesma que app/api/mcp/route.js fala,
via createMcpHandler). Handshake: initialize() -> call_tool("retrieve_knowledge").

Nota sobre a versao do pacote `mcp`: a partir da 2.x, o SDK oficial passou a
depender de `httpx2` em vez de `httpx` para o transporte Streamable HTTP
(verificado nos metadados do pacote em 2026-09-17). Para poder usar `httpx`
como pedido -- e porque o `requirements.txt` deste projeto ja fixa
`httpx>=0.28.0`, nao `httpx2` -- este modulo fixa `mcp==1.30.0`, a ultima
serie que ainda depende de `httpx` puro. Ver requirements.txt.

Limitacoes conhecidas dos hits devolvidos (herdadas de retrieveKnowledgeHits,
documentadas la e repetidas aqui para quem so ler este ficheiro):
  - hit["metadata"] vem sempre None (a tabela knowledge_chunks nao tem
    coluna metadata).
  - hit["citation"]["locator"] vem sempre None (o schema so guarda a fonte,
    nao uma posicao dentro dela).
  - filters e aceite no payload mas SEM EFEITO do lado do MCP.

Le do ambiente:
    MCP_API_KEY  -- obrigatoria (sem default; falha explicitamente se em falta)
    MCP_URL      -- opcional, default "http://localhost:3000"

Assume que o runner e inteiramente sincrono (confirmado por inspeccao de
engine.py/cli.py/langgraph_engine.py em 2026-09-17 -- nenhum tem `async def`
nem importa `asyncio`). `retrieve()` usa `anyio.run()` para uma so chamada
assincrona interna; se algum dia o runner passar a ser assincrono, isto
tem de mudar para nao tentar abrir um segundo event loop dentro de um ja
em execucao.
"""
from __future__ import annotations

import json
import os
from typing import Any

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL_DEFAULT = "http://localhost:3000"
MCP_TOOL_NAME = "retrieve_knowledge"
MCP_PATH = "/api/mcp"


class McpKnowledgeError(RuntimeError):
    """Erro ao consultar o agent-network-mcp (rede, auth, timeout, resposta malformada)."""


def _api_key() -> str:
    key = os.environ.get("MCP_API_KEY", "").strip()
    if not key:
        raise McpKnowledgeError(
            "MCP_API_KEY nao definida no ambiente. "
            "E a mesma chave que o agent-network-mcp exige em app/api/mcp/route.js."
        )
    return key


def _mcp_url() -> str:
    base = os.environ.get("MCP_URL", MCP_URL_DEFAULT).strip() or MCP_URL_DEFAULT
    return base.rstrip("/") + MCP_PATH


class McpKnowledge:
    """Implementa KnowledgeBackend chamando o agent-network-mcp via HTTP.

    Uso:
        from plan_runner.mcp_knowledge import McpKnowledge
        from plan_runner.knowledge import retrieve_knowledge

        hits = retrieve_knowledge("viannalegal", "prazo de contestacao",
                                   backend=McpKnowledge())
    """

    def __init__(self, *, timeout: float = 30.0):
        self._timeout = timeout

    def retrieve(
        self,
        kb: str,
        query: str,
        *,
        top_k: int,
        filters: dict[str, Any] | None,
        require_citations: bool,
    ) -> list[dict[str, Any]]:
        return anyio.run(
            self._retrieve_async, kb, query, top_k, filters, require_citations
        )

    async def _retrieve_async(
        self,
        kb: str,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
        require_citations: bool,
    ) -> list[dict[str, Any]]:
        api_key = _api_key()
        url = _mcp_url()

        headers = {"Authorization": f"Bearer {api_key}"}

        # A tool do lado MCP usa Zod .optional() (aceita undefined, NAO
        # aceita null explicito) para filters/top_k/require_citations.
        # `filters` e o unico destes que o protocolo KnowledgeBackend deixa
        # chegar como None -- omite a chave em vez de mandar null, senao a
        # validacao Zod do lado do servidor rejeita o pedido (confirmado
        # com um servidor MCP real de teste em 2026-09-17).
        arguments: dict[str, Any] = {
            "kb": kb,
            "query": query,
            "top_k": top_k,
            "require_citations": require_citations,
        }
        if filters is not None:
            arguments["filters"] = filters

        try:
            async with httpx.AsyncClient(
                headers=headers, timeout=self._timeout
            ) as http_client:
                async with streamable_http_client(
                    url, http_client=http_client
                ) as (read_stream, write_stream, _get_session_id):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(MCP_TOOL_NAME, arguments)
        except httpx.TimeoutException as e:
            raise McpKnowledgeError(
                f"Timeout ({self._timeout}s) a chamar o agent-network-mcp em {url}: {e}"
            ) from e
        except httpx.HTTPError as e:
            raise McpKnowledgeError(
                f"Falha HTTP a chamar o agent-network-mcp em {url}: {e}"
            ) from e
        except BaseExceptionGroup as eg:
            # streamable_http_client corre dentro de um anyio.TaskGroup --
            # falhas de rede (ligacao recusada, timeout dentro do stream,
            # 401/403 na abertura da sessao) chegam aqui embrulhadas num
            # ExceptionGroup, NAO como httpx.HTTPError direto. Confirmado
            # com um teste real de ligacao recusada em 2026-09-17 -- sem
            # este apanhador, a excepcao propagava-se sem tratamento.
            leaf = _first_leaf_exception(eg)
            raise McpKnowledgeError(
                f"Falha a chamar o agent-network-mcp em {url}: {leaf}"
            ) from eg

        if result.isError:
            error_text = _first_text(result) or "erro sem detalhe"
            raise McpKnowledgeError(f"MCP devolveu erro na tool {MCP_TOOL_NAME}: {error_text}")

        raw = _first_text(result)
        if not raw:
            raise McpKnowledgeError(
                f"Resposta vazia da tool {MCP_TOOL_NAME} -- nenhum content de texto devolvido."
            )

        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            raise McpKnowledgeError(
                f"Resposta da tool {MCP_TOOL_NAME} nao e JSON valido: {raw[:200]}"
            ) from e

        hits = payload.get("hits")
        if hits is None:
            raise McpKnowledgeError(
                f"Resposta da tool {MCP_TOOL_NAME} nao tem campo 'hits': {raw[:200]}"
            )
        return hits


def _first_leaf_exception(exc: BaseException) -> BaseException:
    """Desce por um BaseExceptionGroup aninhado ate a primeira excepcao real."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


def _first_text(result: Any) -> str | None:
    """Extrai o primeiro bloco de texto de um CallToolResult, ou None."""
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text is not None:
            return text
    return None
