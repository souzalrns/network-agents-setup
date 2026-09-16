"""Testes de embedder.py -- sem chamar a API real do Gemini.

Mocka httpx.post e verifica:
- leitura da chave do ambiente
- format do pedido (model, dims, content)
- parse da resposta
- erros (HTTP != 200, dimensao errada, chave em falta)
"""
from __future__ import annotations

import pytest

from plan_runner import embedder


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


def _valid_payload(n: int = 768) -> dict:
    return {"embedding": {"values": [0.1] * n}}


@pytest.fixture(autouse=True)
def _set_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-tests")


def test_embed_empty_returns_empty(monkeypatch):
    called = {"n": 0}

    def fake_post(*a, **kw):
        called["n"] += 1
        return _FakeResponse(200, _valid_payload())

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    assert embedder.embed_text("") == []
    assert called["n"] == 0


def test_embed_whitespace_returns_empty(monkeypatch):
    called = {"n": 0}

    def fake_post(*a, **kw):
        called["n"] += 1
        return _FakeResponse(200, _valid_payload())

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    assert embedder.embed_text("   \n\t  ") == []
    assert called["n"] == 0


def test_embed_calls_gemini_with_correct_payload(monkeypatch):
    captured = {}

    def fake_post(url, *, params=None, json=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        return _FakeResponse(200, _valid_payload())

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    out = embedder.embed_text("ola mundo")

    assert len(out) == 768
    assert captured["params"] == {"key": "fake-key-for-tests"}
    assert captured["json"]["model"] == "models/gemini-embedding-001"
    assert captured["json"]["outputDimensionality"] == 768
    assert captured["json"]["content"]["parts"][0]["text"] == "ola mundo"


def test_embed_raises_on_http_error(monkeypatch):
    def fake_post(*a, **kw):
        return _FakeResponse(500, text="internal")

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    with pytest.raises(embedder.EmbedderError, match="HTTP 500"):
        embedder.embed_text("x")


def test_embed_raises_on_wrong_dimensions(monkeypatch):
    def fake_post(*a, **kw):
        return _FakeResponse(200, {"embedding": {"values": [0.0] * 3072}})

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    with pytest.raises(embedder.EmbedderError, match="3072 dimensoes"):
        embedder.embed_text("x")


def test_embed_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(embedder.EmbedderError, match="GEMINI_API_KEY"):
        embedder.embed_text("x")


def test_embed_batch_returns_list_of_embeddings(monkeypatch):
    def fake_post(*a, **kw):
        return _FakeResponse(200, _valid_payload())

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    out = embedder.embed_batch(["a", "b", "c"])
    assert len(out) == 3
    assert all(len(v) == 768 for v in out)


def test_embed_truncates_oversized_text(monkeypatch):
    captured = {}

    def fake_post(url, *, params=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeResponse(200, _valid_payload())

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    big = "x" * (embedder.MAX_CHARS_PER_REQUEST + 500)
    embedder.embed_text(big)
    sent = captured["json"]["content"]["parts"][0]["text"]
    assert len(sent) == embedder.MAX_CHARS_PER_REQUEST
