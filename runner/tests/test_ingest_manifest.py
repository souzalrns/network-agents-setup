"""F0.4: o pack de security no MANIFEST do ingest (scripts/ingest_delta.py), sem BD.

- a entrada existe com o agent_id que o consumidor usa (kb `security` do bloco
  `knowledge:` do security-audit-demo e do golden set);
- está no grupo P0 e cabe no orçamento por omissão da 1.ª corrida (50 chunks) mesmo no
  pior caso (todos os P0 anteriores novos), medido com o chunker real;
- o `_kb_for` dá `security` (antes caía em `global`).
O comportamento incremental (UNCHANGED por content_hash) é testado contra Postgres no
test-rag (tests/test_rag_canonical.py, `test_f04_*`).
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest
import yaml

from plan_runner.chunking import chunk_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK = "docs/knowledge/security-agents-stack.md"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # o @dataclass do ingest_delta precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def manifest():
    return _load("ingest_delta_manifest", "scripts/ingest_delta.py").MANIFEST


def _chunks(rel: str, agent_id: str) -> int:
    return len(chunk_markdown((REPO_ROOT / rel).read_text(encoding="utf-8"), source_path=rel, agent_id=agent_id))


def test_pack_security_esta_no_manifest_com_o_agent_id_do_consumidor(manifest):
    entries = [e for e in manifest if e[0] == PACK]
    assert entries == [(PACK, "security", "P0")]
    plan = yaml.safe_load((REPO_ROOT / "docs/orchestration/security/templates/examples/"
                           "security-audit-demo.plan.yaml").read_text(encoding="utf-8"))
    kbs = {s["knowledge"]["kb"] for s in plan["steps"] if "knowledge" in s}
    golden = yaml.safe_load((REPO_ROOT / "config/l5-golden-security.yaml").read_text(encoding="utf-8"))
    assert kbs == {"security"} == {golden["kb"]}
    assert golden["source"] == PACK


def test_pack_cabe_no_orcamento_da_primeira_corrida_no_pior_caso(manifest):
    idx = [e[0] for e in manifest].index(PACK)
    before = manifest[:idx]
    assert all(p == "P0" for _, _, p in before), "o pack tem de ficar no grupo P0"
    worst = sum(_chunks(rel, aid) for rel, aid, _ in before) + _chunks(PACK, "security")
    assert worst <= 50, f"P0 anteriores + pack = {worst} chunks > 50 (orçamento por omissão)"


def test_kb_for_security(monkeypatch):
    # o ingest_apply carrega o .env do repo ao ser importado: isolar o os.environ
    monkeypatch.setattr(os, "environ", dict(os.environ))
    ia = _load("ingest_apply_kb", "scripts/ingest_apply.py")
    assert ia._kb_for("security") == "security"
    assert ia._kb_for("marketing") == "marketing" and ia._kb_for("saude") == "global"  # o resto não muda


@pytest.mark.parametrize("state,expected", [
    (None, False),
    ({"content_hash": "h", "agent_id": "a", "chunk_count": 3, "rows": 3}, True),
    ({"content_hash": "x", "agent_id": "a", "chunk_count": 3, "rows": 3}, False),   # conteúdo mudou
    ({"content_hash": "h", "agent_id": "b", "chunk_count": 3, "rows": 3}, False),   # dono mudou
    ({"content_hash": "h", "agent_id": "a", "chunk_count": 3, "rows": 2}, False),   # linhas em falta
    ({"content_hash": "h", "agent_id": "a", "chunk_count": 0, "rows": 0}, False),   # nunca escrito
])
def test_is_unchanged(monkeypatch, state, expected):
    monkeypatch.setattr(os, "environ", dict(os.environ))
    ia = _load("ingest_apply_unch", "scripts/ingest_apply.py")
    assert ia.is_unchanged(state, content_hash="h", agent_id="a") is expected


def test_is_unchanged_com_agent_id_composto(monkeypatch):
    monkeypatch.setattr(os, "environ", dict(os.environ))
    ia = _load("ingest_apply_comp", "scripts/ingest_apply.py")
    state = {"content_hash": "h", "agent_id": "a+b", "chunk_count": 3, "rows": 6}  # 1 linha por agente
    assert ia.is_unchanged(state, content_hash="h", agent_id="a+b") is True
    assert ia.is_unchanged({**state, "rows": 3}, content_hash="h", agent_id="a+b") is False
