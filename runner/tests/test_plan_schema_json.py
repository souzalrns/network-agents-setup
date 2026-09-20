"""Testes do bloco `knowledge` em docs/architecture/plan-execute/schemas/Plan.schema.json (B9).

Nota de escopo (ver EXECUTION-PROMPTS.md B9): este schema NAO e carregado por
nenhum validador em tempo de execucao -- runner/plan_runner/graph.py e
models.py fazem a validacao real dos planos usados por engine.py/
langgraph_engine.py, em Python puro, sem depender de JSON Schema.
`docs/architecture/plan-execute/README.md` documenta o proprio directorio
como "setup / documentacao" ("Nao liga sozinho ao agent-network-mcp"). Este
ficheiro testa o SCHEMA em si (fiel ao seu unico exemplo real,
examples/piloto-netos.plan.yaml), nao uma integracao com o plan_runner.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from tests.conftest import RUNNER_DIR

REPO_ROOT = RUNNER_DIR.parent
SCHEMA_PATH = REPO_ROOT / "docs" / "architecture" / "plan-execute" / "schemas" / "Plan.schema.json"
EXAMPLE_PATH = REPO_ROOT / "docs" / "architecture" / "plan-execute" / "examples" / "piloto-netos.plan.yaml"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))


def _load_example() -> dict:
    return yaml.safe_load(EXAMPLE_PATH.read_text(encoding="utf-8-sig"))


def test_schema_has_knowledge_property_on_step():
    schema = _load_schema()
    step_props = schema["properties"]["steps"]["items"]["properties"]
    assert "knowledge" in step_props
    knowledge = step_props["knowledge"]
    assert knowledge["required"] == ["kb", "query"]
    assert "knowledge" not in schema["properties"]["steps"]["items"]["required"], (
        "knowledge deve ser opt-in por step, nao obrigatorio"
    )


def test_real_example_still_validates_after_adding_knowledge(tmp_path):
    """Nao-regressao: o unico plano real deste directorio continua valido."""
    schema = _load_schema()
    example = _load_example()
    jsonschema.validate(instance=example, schema=schema)


def test_real_example_with_well_formed_knowledge_block_validates():
    schema = _load_schema()
    example = _load_example()
    example["steps"][0]["knowledge"] = {"kb": "marketing", "query": "seo brief checklist"}
    jsonschema.validate(instance=example, schema=schema)


def test_knowledge_with_wrong_kb_type_fails_validation():
    schema = _load_schema()
    example = _load_example()
    example["steps"][0]["knowledge"] = {"kb": 123, "query": "seo brief checklist"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=example, schema=schema)


def test_knowledge_missing_query_fails_validation():
    schema = _load_schema()
    example = _load_example()
    example["steps"][0]["knowledge"] = {"kb": "marketing"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=example, schema=schema)


def test_knowledge_rejects_unknown_property():
    schema = _load_schema()
    example = _load_example()
    example["steps"][0]["knowledge"] = {
        "kb": "marketing",
        "query": "x",
        "nao_existe_no_contrato": True,
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=example, schema=schema)
