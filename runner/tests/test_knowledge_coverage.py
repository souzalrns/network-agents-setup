"""F3c (P-35 = A, P-36 = A): cada .md de docs/knowledge/ está no MANIFEST ou no EXCLUDED.

Sem BD. As razões de exclusão são verificadas contra o repo, não só declaradas:
- os duplicados dizem na 1.ª linha que são cópia de agent-network-mcp/ingestion/;
- o pack de design só fica de fora enquanto nenhum plano usar `kb: design` (F3c-DESIGN-1);
- o pack de marketing migrado tem consumidor (planos com `kb: marketing`) e cabe no
  orçamento por omissão de uma corrida (50 chunks), medido com o chunker real.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

import pytest

from plan_runner.chunking import chunk_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO_ROOT / "docs/knowledge"
MARKETING_PACK = sorted(
    p.relative_to(REPO_ROOT).as_posix() for p in (KNOWLEDGE / "marketing").glob("*.md")
)


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # o @dataclass do ingest_delta precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def delta():
    return _load("ingest_delta_coverage", "scripts/ingest_delta.py")


def _plan_kbs() -> set[str]:
    kbs = set()
    for plan in (REPO_ROOT / "docs/orchestration").rglob("*.plan.yaml"):
        kbs.update(re.findall(r"^\s*kb:\s*([A-Za-z0-9_+-]+)", plan.read_text(encoding="utf-8"), re.M))
    return kbs


def test_todo_md_de_docs_knowledge_esta_no_manifest_ou_excluido(delta):
    on_disk = {p.relative_to(REPO_ROOT).as_posix() for p in KNOWLEDGE.rglob("*.md")}
    manifest = {p for p, _, _ in delta.MANIFEST}
    excluded = set(delta.EXCLUDED)
    sem_decisao = sorted(on_disk - manifest - excluded)
    assert not sem_decisao, (
        "ficheiros de docs/knowledge/ sem decisão de ingestão (pôr no MANIFEST ou no "
        f"EXCLUDED de scripts/ingest_delta.py, com razão): {sem_decisao}"
    )
    assert not manifest & excluded, f"no MANIFEST e no EXCLUDED ao mesmo tempo: {sorted(manifest & excluded)}"


def test_excluidos_existem_e_tem_razao(delta):
    for rel, reason in delta.EXCLUDED.items():
        assert (REPO_ROOT / rel).is_file(), f"{rel} não existe (tirar do EXCLUDED)"
        assert rel.startswith("docs/knowledge/") and rel.endswith(".md")
        assert isinstance(reason, str) and len(reason) > 20, f"{rel}: razão vazia ou curta"


def test_duplicados_sao_mesmo_copias_do_ingestion_do_mcp(delta):
    dups = [rel for rel, reason in delta.EXCLUDED.items() if reason == delta.EXCLUDE_DUP]
    assert len(dups) == 7
    for rel in dups:
        first = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines()[0]
        assert "agent-network-mcp/ingestion/" in first, f"{rel}: a 1.ª linha não diz que é cópia"


def test_design_so_fica_de_fora_sem_consumidor(delta):
    design = [rel for rel in delta.EXCLUDED if rel.startswith("docs/knowledge/design/")]
    assert len(design) == 11  # 10 packs + README
    assert "design" not in _plan_kbs(), (
        "há um plano com `kb: design`: reavaliar o F3c-DESIGN-1 (migrar o pack de design)"
    )


def test_pack_de_marketing_migrado_com_consumidor_e_no_orcamento(delta, monkeypatch):
    entries = {p: (a, prio) for p, a, prio in delta.MANIFEST}
    assert len(MARKETING_PACK) == 7
    for rel in MARKETING_PACK:
        assert entries.get(rel) == ("marketing", "P1"), rel
    assert "marketing" in _plan_kbs()
    # o ingest_apply carrega o .env do repo ao ser importado: isolar o os.environ
    monkeypatch.setattr(os, "environ", dict(os.environ))
    ia = _load("ingest_apply_coverage", "scripts/ingest_apply.py")
    assert ia._kb_for("marketing") == "marketing"
    chunks = sum(
        len(chunk_markdown((REPO_ROOT / rel).read_text(encoding="utf-8"), source_path=rel, agent_id="marketing"))
        for rel in MARKETING_PACK
    )
    assert 0 < chunks <= 50, f"o pack de marketing tem {chunks} chunks (> 50, o orçamento por omissão)"
