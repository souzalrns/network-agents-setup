"""Testes de chunking.py -- divisao de markdown em chunks (T6 secao 6).

Estilo alinhado com test_knowledge.py, test_hitl_contract.py,
test_working_memory.py: import absoluto de plan_runner, sem rede.
"""
from __future__ import annotations

from plan_runner.chunking import (
    MAX_CHARS,
    chunk_markdown,
)

# -- Vazio / sem headers ------------------------------------------------------

def test_empty_text_returns_empty():
    assert chunk_markdown("", source_path="d.md", agent_id="m") == []


def test_whitespace_only_returns_empty():
    assert chunk_markdown("   \n\n  \n", source_path="d.md", agent_id="m") == []


def test_no_headers_single_chunk():
    text = "# Titulo\n\nParagrafo com " + "x" * 300
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert len(out) == 1
    assert "Paragrafo" in out[0]["content"]


# -- Splitting por H2/H3 ------------------------------------------------------

def test_two_h2_sections():
    text = (
        "Preambulo.\n\n"
        "## Seccao A\n\n" + "a" * 300 + "\n\n"
        "## Seccao B\n\n" + "b" * 300 + "\n"
    )
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert len(out) == 3  # preambulo + A + B
    assert "Preambulo" in out[0]["content"]
    assert "Seccao A" in out[1]["content"]
    assert "Seccao B" in out[2]["content"]


def test_h3_is_also_a_split():
    text = (
        "## A\n\n" + "a" * 300 + "\n\n"
        "### A.1\n\n" + "x" * 300 + "\n"
    )
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert len(out) == 2
    assert "## A" in out[0]["content"]
    assert "### A.1" in out[1]["content"]


def test_h1_does_not_split():
    text = "# Top\n\n## A\n\n" + "a" * 300 + "\n"
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    # # Top fica no preambulo (antes do ## A).
    assert len(out) == 2
    assert "# Top" in out[0]["content"]
    assert "## A" in out[1]["content"]


# -- Limites de tamanho -------------------------------------------------------

def test_oversized_section_is_split():
    big = "x" * (MAX_CHARS * 2 + 100)
    text = f"## A\n\n{big}\n"
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert len(out) >= 2
    for c in out:
        assert len(c["content"]) <= MAX_CHARS + 10  # tolerancia


def test_small_fragment_merged_into_previous():
    text = (
        "## A\n\n" + "a" * 300 + "\n\n"
        "## B\n\ncurto\n"
    )
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    # "curto" < MIN_CHARS -> junta-se ao chunk A.
    assert len(out) == 1
    assert "Seccao" not in out[0]["content"] or "curto" in out[0]["content"]
    assert "curto" in out[0]["content"]


# -- Formato / metadados ------------------------------------------------------

def test_chunk_has_required_fields():
    text = "## A\n\n" + "a" * 300 + "\n"
    out = chunk_markdown(text, source_path="docs/x.md", agent_id="marketing")
    c = out[0]
    assert c["doc_id"] == "docs/x.md"
    assert c["kb"] == "marketing"
    assert c["agent_id"] == "marketing"
    assert c["citation"]["source"] == "docs/x.md"
    assert c["citation"]["locator"].startswith("l.")
    assert c["chunk_index"] == 0


def test_chunk_index_is_sequential():
    text = (
        "## A\n\n" + "a" * 300 + "\n\n"
        "## B\n\n" + "b" * 300 + "\n\n"
        "## C\n\n" + "c" * 300 + "\n"
    )
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert [c["chunk_index"] for c in out] == list(range(len(out)))


def test_kb_can_be_overridden():
    text = "## A\n\n" + "a" * 300 + "\n"
    out = chunk_markdown(text, source_path="d.md", agent_id="m", kb="design")
    assert out[0]["kb"] == "design"


def test_locator_reflects_lines():
    text = (
        "## A\n\n" + "a" * 300 + "\n\n"
        "## B\n\n" + "b" * 300 + "\n"
    )
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    # O chunk B deve comecar depois do chunk A.
    assert out[0]["citation"]["locator"] != out[1]["citation"]["locator"]


# -- UTF-8 --------------------------------------------------------------------

def test_utf8_content_preserved():
    text = "## Acao\n\nConteudo com acentos: acao, coracao, 中文.\n"
    out = chunk_markdown(text, source_path="d.md", agent_id="m")
    assert len(out) == 1
    assert "acao" in out[0]["content"]
    assert "中文" in out[0]["content"]


# -- Configuravel -------------------------------------------------------------

def test_custom_max_chars():
    text = "## A\n\n" + ("x" * 500) + "\n"
    out = chunk_markdown(
        text, source_path="d.md", agent_id="m", max_chars=300, min_chars=10
    )
    assert len(out) >= 2
