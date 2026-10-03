"""W-006: valida planos YAML do runner contra plan.schema.json.

    python -m plan_runner.plan_schema ../docs/orchestration/**/*.plan.yaml

Sai com 0 se todos validarem; 1 com a lista de erros (ficheiro, caminho, mensagem).
O formato e o do runner, nao o do docs/architecture/plan-execute/schemas/Plan.schema.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).with_name("plan.schema.json")


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def plan_errors(data: Any) -> list[str]:
    """Erros de schema de um plano ja lido (lista vazia = valido)."""
    errors = sorted(_validator().iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(raiz)'}: {e.message}" for e in errors]


def file_errors(path: Path) -> list[str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        return [f"(leitura): {e}"]
    return plan_errors(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m plan_runner.plan_schema", description=__doc__.splitlines()[0])
    parser.add_argument("plans", nargs="+", type=Path)
    args = parser.parse_args(argv)
    bad = 0
    for path in args.plans:
        errs = file_errors(path)
        if errs:
            bad += 1
            for err in errs:
                print(f"{path}: {err}")
    print(f"{len(args.plans)} planos; {bad} com erros")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
