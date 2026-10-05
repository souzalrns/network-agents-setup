"""Dependências opcionais dos testes de ingestão (F1): skip em local, erro no CI.

O `markitdown` e os geradores de fixtures ficam fora do `requirements.txt` (pesados e só do
F1). Em local, a falta deles dá skip com o motivo. No job `test-ingest` do CI,
`INGEST_TEST_REQUIRED=1` torna a falta um erro, para o job nunca ficar verde sem ter corrido
(o mesmo padrão do `RAG_TEST_REQUIRED` no `test-rag`).
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

import pytest

INGEST_REQUIRED_ENV = "INGEST_TEST_REQUIRED"
# Os únicos módulos opcionais dos testes de ingestão (lista branca).
OPTIONAL_MODULES = frozenset({"markitdown", "fpdf", "docx", "openpyxl"})
INSTALL_HINT = (
    "correr com `pip install -r requirements-ingest.txt -r requirements-fixtures.txt` "
    "(a partir de runner/)"
)


def require(module: str) -> ModuleType:
    """Importa `module`; sem ele, skip (local) ou erro (com INGEST_TEST_REQUIRED=1)."""
    if module not in OPTIONAL_MODULES:
        raise ValueError(f"{module} não é uma dependência opcional conhecida: {OPTIONAL_MODULES}")
    if os.environ.get(INGEST_REQUIRED_ENV) == "1":
        # Falso positivo: o nome passou pela lista branca acima; não vem de input externo.
        # nosemgrep: non-literal-import
        return importlib.import_module(module)
    return pytest.importorskip(
        module, reason=f"{module} não instalado: é opcional (F1); {INSTALL_HINT}"
    )
