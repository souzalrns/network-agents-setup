"""Testes de working_memory.py -- leitura de MEMORY.md por cliente.

Estilo alinhado com test_events.py e test_hitl_contract.py:
tmp_path + import absoluto de plan_runner, sem tocar em pilots/.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from plan_runner.working_memory import (
    TOKEN_LIMIT_SOFT,
    memory_status,
    read_memory,
    resolve_memory_path,
)

# -- Helpers ------------------------------------------------------------------

def _write_memory(repo_root: Path, client_id: str, text: str) -> Path:
    path = repo_root / "memory" / client_id / "MEMORY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# -- resolve_memory_path ------------------------------------------------------

def test_resolve_returns_none_when_missing(tmp_path: Path):
    assert resolve_memory_path(tmp_path, "demo") is None


def test_resolve_returns_path_when_exists(tmp_path: Path):
    _write_memory(tmp_path, "demo", "# Memory\n")
    p = resolve_memory_path(tmp_path, "demo")
    assert p is not None
    assert p.name == "MEMORY.md"
    assert p.parent.name == "demo"
    assert p.parent.parent.name == "memory"


def test_resolve_returns_none_for_empty_client_id(tmp_path: Path):
    _write_memory(tmp_path, "demo", "# Memory\n")
    assert resolve_memory_path(tmp_path, "") is None


# -- read_memory --------------------------------------------------------------

def test_read_memory_missing(tmp_path: Path):
    assert read_memory("demo", repo_root=tmp_path) is None


def test_read_memory_returns_content(tmp_path: Path):
    _write_memory(tmp_path, "demo", "# Contexto\nCliente demo.\n")
    text = read_memory("demo", repo_root=tmp_path)
    assert text is not None
    assert "Cliente demo." in text


def test_read_memory_utf8(tmp_path: Path):
    _write_memory(tmp_path, "demo", "# Contexto\nAção, éàç, 中文.\n")
    text = read_memory("demo", repo_root=tmp_path)
    assert text is not None
    assert "Ação" in text
    assert "中文" in text


def test_read_memory_via_out_dir_pilots(tmp_path: Path):
    # Simula a convencao do runner: <repo>/pilots/<run>
    repo = tmp_path
    _write_memory(repo, "demo", "# Memory\n")
    out_dir = repo / "pilots" / "run-1"
    out_dir.mkdir(parents=True)
    text = read_memory("demo", out_dir=out_dir)
    assert text == "# Memory\n"


def test_read_memory_via_out_dir_no_pilots(tmp_path: Path):
    # Se out_dir nao esta sob pilots/, o repo root e o pai do out_dir.
    repo = tmp_path
    _write_memory(repo, "demo", "# Memory\n")
    out_dir = repo / "some" / "out"
    out_dir.mkdir(parents=True)
    text = read_memory("demo", out_dir=out_dir)
    # out_dir.parent = tmp_path/some -> nao tem memory/, logo None.
    assert text is None


# -- _resolve_repo_root (via read_memory) -------------------------------------

def test_read_memory_requires_one_of_repo_root_or_out_dir():
    with pytest.raises(ValueError):
        read_memory("demo")


def test_read_memory_rejects_both_repo_root_and_out_dir(tmp_path: Path):
    with pytest.raises(ValueError):
        read_memory("demo", repo_root=tmp_path, out_dir=tmp_path)


# -- memory_status ------------------------------------------------------------

def test_status_missing(tmp_path: Path):
    status = memory_status("demo", repo_root=tmp_path)
    assert status["client_id"] == "demo"
    assert status["exists"] is False
    assert status["path"] is None
    assert status["chars"] == 0
    assert status["approx_tokens"] == 0
    assert status["over_limit"] is False
    assert status["limit"] == TOKEN_LIMIT_SOFT


def test_status_existing_within_limit(tmp_path: Path):
    _write_memory(tmp_path, "demo", "x" * 100)
    status = memory_status("demo", repo_root=tmp_path)
    assert status["exists"] is True
    assert status["chars"] == 100
    assert status["approx_tokens"] == 25
    assert status["over_limit"] is False
    assert status["path"] is not None
    assert status["path"].endswith("MEMORY.md")


def test_status_over_limit_flag(tmp_path: Path):
    # Acima do limite: (TOKEN_LIMIT_SOFT + 10) * 4 chars
    big = "x" * ((TOKEN_LIMIT_SOFT + 10) * 4)
    _write_memory(tmp_path, "demo", big)
    status = memory_status("demo", repo_root=tmp_path)
    assert status["exists"] is True
    assert status["approx_tokens"] > TOKEN_LIMIT_SOFT
    assert status["over_limit"] is True


def test_status_at_exact_limit_is_not_over(tmp_path: Path):
    # Exatamente no limite: nao e over (limite e "acima de").
    exact = "x" * (TOKEN_LIMIT_SOFT * 4)
    _write_memory(tmp_path, "demo", exact)
    status = memory_status("demo", repo_root=tmp_path)
    assert status["approx_tokens"] == TOKEN_LIMIT_SOFT
    assert status["over_limit"] is False
