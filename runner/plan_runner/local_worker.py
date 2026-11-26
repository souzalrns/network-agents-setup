"""Worker local (plano setup-estrutura-2, passo 2): corre os passos num servidor compatível com a API OpenAI
(Ollama, llama.cpp `llama-server`, LM Studio, vLLM), sem chave paga e sem enviar nada para fora da máquina.

Como encaixa: o `GeminiWorker` fala o formato do Gemini através de um `transport` injectável. Aqui o transport
traduz esse formato para `/chat/completions` e a resposta de volta, por isso o prompt, as tools, o orçamento de
tokens, o ledger e os gates humanos são exactamente os do worker normal. Muda só quem responde.

Ambiente:
    LOCAL_LLM_MODEL   nome do modelo no servidor (obrigatório), ex. `qwen2.5:3b`
    LOCAL_LLM_URL     base da API (omissão: http://127.0.0.1:11434/v1, o do Ollama)
    LOCAL_LLM_API_KEY chave, se o servidor a exigir (omissão: nenhuma)

Diferenças honestas face ao Gemini: modelos pequenos erram mais o JSON e as tools; o tecto de USD não se aplica
(custo 0); o `countTokens` é uma estimativa (caracteres / 4), não uma contagem verificada.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from typing import Any

import httpx

from .external_worker import DEFAULT_MAX_OUTPUT_TOKENS, GeminiWorker, WorkerError

DEFAULT_URL = "http://127.0.0.1:11434/v1"
Post = Callable[..., httpx.Response]
_MODEL_IN_URL = re.compile(r"/models/(.+):(?:generateContent|streamGenerateContent|countTokens)")


def _lower_types(schema: Any) -> Any:
    """O Gemini aceita tipos em MAIÚSCULAS (`STRING`); o JSON Schema que o OpenAI espera usa minúsculas."""
    if isinstance(schema, dict):
        return {k: (v.lower() if k == "type" and isinstance(v, str) else _lower_types(v)) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_lower_types(v) for v in schema]
    return schema


def to_openai_request(url: str, body: dict[str, Any]) -> dict[str, Any]:
    """Pedido `generateContent` do Gemini -> corpo de `/chat/completions`."""
    m = _MODEL_IN_URL.search(url)
    messages: list[dict[str, Any]] = []
    system = "".join(p.get("text", "") for p in (body.get("systemInstruction") or {}).get("parts", []))
    if system:
        messages.append({"role": "system", "content": system})
    open_calls: list[tuple[str, str]] = []  # (id, nome) das chamadas ainda sem resposta
    n = 0
    for content in body.get("contents", []):
        parts = content.get("parts", [])
        texts = [p["text"] for p in parts if "text" in p]
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        results = [p["functionResponse"] for p in parts if "functionResponse" in p]
        if content.get("role") == "model":
            msg: dict[str, Any] = {"role": "assistant", "content": "".join(texts) or None}
            if calls:
                msg["tool_calls"] = []
                for c in calls:
                    n += 1
                    open_calls.append((f"call_{n}", c["name"]))
                    msg["tool_calls"].append({"id": f"call_{n}", "type": "function",
                                              "function": {"name": c["name"], "arguments": json.dumps(c.get("args") or {}, ensure_ascii=False)}})
            messages.append(msg)
            continue
        for r in results:
            idx = next((i for i, (_, name) in enumerate(open_calls) if name == r.get("name")), None)
            cid = open_calls.pop(idx)[0] if idx is not None else f"call_{n}"
            messages.append({"role": "tool", "tool_call_id": cid, "content": json.dumps(r.get("response", {}), ensure_ascii=False)})
        if texts:
            messages.append({"role": "user", "content": "".join(texts)})
    req: dict[str, Any] = {"model": m.group(1) if m else "", "messages": messages, "stream": False}
    gen = body.get("generationConfig") or {}
    if gen.get("maxOutputTokens"):
        req["max_tokens"] = gen["maxOutputTokens"]
    if gen.get("responseMimeType") == "application/json":
        req["response_format"] = {"type": "json_object"}
    decls = [d for t in body.get("tools", []) for d in t.get("functionDeclarations", [])]
    if decls:
        req["tools"] = [{"type": "function", "function": {"name": d["name"], "description": d.get("description", ""),
                                                          "parameters": _lower_types(d.get("parameters") or {"type": "object", "properties": {}})}}
                        for d in decls]
    return req


_FINISH = {"stop": "STOP", "tool_calls": "STOP", "length": "MAX_TOKENS", "content_filter": "SAFETY"}


def to_gemini_response(resp: dict[str, Any]) -> dict[str, Any]:
    """Resposta de `/chat/completions` -> forma `generateContent` do Gemini (candidates + usageMetadata)."""
    choice = (resp.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    parts: list[dict[str, Any]] = []
    if msg.get("content"):
        parts.append({"text": msg["content"]})
    for call in msg.get("tool_calls") or []:
        fn = call.get("function") or {}
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except ValueError:
            args = {}
        parts.append({"functionCall": {"name": fn.get("name", ""), "args": args if isinstance(args, dict) else {}}})
    usage = resp.get("usage") or {}
    return {
        "candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": _FINISH.get(choice.get("finish_reason"), "STOP")}],
        "usageMetadata": {"promptTokenCount": int(usage.get("prompt_tokens") or 0),
                          "candidatesTokenCount": int(usage.get("completion_tokens") or 0),
                          "totalTokenCount": int(usage.get("total_tokens") or 0)},
        "modelVersion": resp.get("model"),
    }


def estimate_tokens(body: dict[str, Any]) -> int:
    return max(1, len(json.dumps(body, ensure_ascii=False)) // 4)


def make_transport(base_url: str, api_key: str | None = None, post: Post | None = None):
    """Transport (url, headers, body, timeout) -> (código, resposta) que fala com o servidor local."""
    base = base_url.rstrip("/")
    send = post or httpx.post

    def transport(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any]]:
        if ":countTokens" in url:
            return 200, {"totalTokens": estimate_tokens(body)}
        hdr = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            r = send(f"{base}/chat/completions", headers=hdr, json=to_openai_request(url, body), timeout=timeout)
        except httpx.HTTPError:
            return 503, {"error": {"message": f"servidor local sem resposta em {base} (está a correr? `ollama serve`)"}}
        try:
            data = r.json()
        except ValueError:
            return r.status_code, {"error": {"message": r.text[:300]}}
        if r.status_code != 200:
            err = data.get("error") if isinstance(data, dict) else None
            msg = err.get("message") if isinstance(err, dict) else err
            return r.status_code, {"error": {"message": str(msg or "")[:300]}}
        return 200, to_gemini_response(data)

    return transport


class LocalWorker(GeminiWorker):
    """GeminiWorker que fala com um servidor OpenAI-compatível local."""

    name = "local"
    single_model = True
    free = True

    def __init__(self, *, model: str | None = None, base_url: str | None = None, api_key: str | None = None,
                 max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS, timeout: float = 300.0, post: Post | None = None, **kw: Any):
        chosen = model or os.environ.get("LOCAL_LLM_MODEL", "").strip()
        if not chosen:
            raise WorkerError("LOCAL_LLM_MODEL em falta (nome do modelo no servidor local, ex. `qwen2.5:3b`)")
        url = base_url or os.environ.get("LOCAL_LLM_URL", "").strip() or DEFAULT_URL
        key = api_key if api_key is not None else (os.environ.get("LOCAL_LLM_API_KEY", "").strip() or None)
        super().__init__(model=chosen, api_key="local", max_output_tokens=max_output_tokens, timeout=timeout,
                         transport=make_transport(url, key, post), **kw)
