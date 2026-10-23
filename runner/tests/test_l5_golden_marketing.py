"""F3b-GS-1: golden set do L5 de marketing (config/l5-golden-marketing.yaml), sem rede.

Mesmas garantias do golden de security (test_l5_eval.py), para o pack
`docs/knowledge/marketing/` (F3c):
- o golden set é válido (groundwright) e tem ~20 casos com ids únicos;
- cada âncora cai em exactamente 1 chunk da fonte do caso (chunking real);
- a pergunta não copia a âncora (mede procura semântica);
- cada fonte está no MANIFEST com a kb `marketing` (senão o retrieve nunca a devolve);
- todos os 7 ficheiros do pack têm pelo menos um caso.
A medição real é `python -m plan_runner.l5_eval run --golden config/l5-golden-marketing.yaml`.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from plan_runner import l5_eval as ev

GOLDEN = ev.REPO_ROOT / "config" / "l5-golden-marketing.yaml"
PACK = ev.REPO_ROOT / "docs" / "knowledge" / "marketing"


@pytest.fixture(scope="module")
def golden():
    return ev.load_golden(GOLDEN)


def _source(golden, case) -> str:
    return case.get("source") or golden["source"]


def test_golden_tem_cerca_de_20_casos_unicos_da_kb_marketing(golden) -> None:
    assert golden["kb"] == "marketing" and golden["k"] == 4
    assert 18 <= len(golden["cases"]) <= 22
    assert len({c["id"] for c in golden["cases"]}) == len(golden["cases"])


def test_cada_ancora_cai_em_exactamente_um_chunk_da_fonte(golden) -> None:
    assert ev.anchor_errors(golden, ev._local_chunks(golden)) == []


def test_as_perguntas_nao_copiam_a_ancora(golden) -> None:
    for case in golden["cases"]:
        assert ev._norm(case["anchor"]) not in ev._norm(case["question"]), case["id"]


def test_fontes_estao_no_manifest_com_a_kb_marketing(golden) -> None:
    name = "ingest_delta_golden_marketing"
    spec = importlib.util.spec_from_file_location(name, ev.REPO_ROOT / "scripts" / "ingest_delta.py")
    delta = importlib.util.module_from_spec(spec)
    sys.modules[name] = delta  # o @dataclass do ingest_delta precisa do módulo registado
    spec.loader.exec_module(delta)
    kb_by_path = {path: kb for path, kb, _ in delta.MANIFEST}
    for case in golden["cases"]:
        assert kb_by_path.get(_source(golden, case)) == "marketing", case["id"]


def test_todo_o_pack_tem_pelo_menos_um_caso(golden) -> None:
    pack = {str(p.relative_to(ev.REPO_ROOT)).replace("\\", "/") for p in PACK.glob("*.md")}
    covered = {_source(golden, c) for c in golden["cases"]}
    assert pack and pack <= covered, sorted(pack - covered)


def test_validate_cli_passa_offline(capsys) -> None:
    assert ev.main(["validate", "--golden", str(GOLDEN)]) == 0
    assert "0 erros" in capsys.readouterr().out
