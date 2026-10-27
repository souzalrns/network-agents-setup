"""Etapa 3 (maestro, 2026-10-27): a matriz de prontidão só diz PROVADA com provas que existem.

Se falhar: corrige a prova citada em config/platform-readiness.yaml (ou tira-a se deixou de
existir) e corre `cd runner && python -m plan_runner.prontidao`. Nunca escrever o estado à mão.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from plan_runner import prontidao as pr

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPS = pr.load(REPO_ROOT)


def test_todas_as_provas_citadas_existem() -> None:
    assert pr.errors(REPO_ROOT, CAPS) == []


def test_matriz_gerada_esta_actualizada() -> None:
    assert (REPO_ROOT / pr.OUT_FILE).read_text(encoding="utf-8") == pr.render(REPO_ROOT, CAPS)


def test_tem_as_8_capacidades_do_plano() -> None:
    assert [c["id"] for c in CAPS] == ["execucao", "aprovacao_humana", "recuperacao", "conhecimento",
                                       "ferramentas", "custos", "observabilidade", "mcp"]


@pytest.mark.parametrize("cap, esperado", [
    ({"testes": ["a"], "runs": [{"doc": "x"}]}, "PROVADA"),
    ({"testes": ["a"], "runs": []}, "TESTADA"),
    ({"testes": [], "runs": [{"doc": "x"}]}, "SEM PROVA"),
])
def test_estado_calculado(cap, esperado) -> None:
    assert pr.state(cap) == esperado


@pytest.mark.parametrize("mutar, erro", [
    (lambda c: c["testes"].append("test_budget.py::nao_existe"), "a função `nao_existe` não está"),
    (lambda c: c["testes"].append("nao_existe.py::x"), "teste `nao_existe.py::x` não existe"),
    (lambda c: c["runs"].append({"doc": "docs/ops/F5-E2E-RUN.md", "anchor": "texto que não está lá"}), "não está em"),
    (lambda c: c["runs"].append({"doc": "docs/nao-existe.md", "anchor": "x"}), "não existe"),
    (lambda c: c["lacunas"].append("H-01"), "não é um item vivo"),
])
def test_prova_inventada_ou_desaparecida_falha(mutar, erro) -> None:
    caps = copy.deepcopy(CAPS)
    mutar(caps[0])
    assert any(erro in e for e in pr.errors(REPO_ROOT, caps)), pr.errors(REPO_ROOT, caps)
