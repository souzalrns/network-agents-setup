import json
import subprocess
import sys
import textwrap
from pathlib import Path

from planwright.export import CONTRACT_SCHEMA, plan_to_contract
from planwright.parse import parse_plan, parse_text

SRC = str(Path(__file__).resolve().parent.parent / "src")

# O plano do cenário canónico (docs/architecture/CANONICAL-SCENARIO.md). O runner
# prova a execução em runner/tests/test_canonical_composition.py com uma cópia deste
# contrato; este teste é a outra ponta: garante que o `export` emite mesmo isto.
CANON_PLAN_MD = Path(__file__).resolve().parent.parent / "examples" / "composicao-canonica.PLAN.md"

PLAN = textwrap.dedent(
    """
    | ID | Title | Status | Owner | Est | Depends | Autonomy | Complexity | Track |
    |----|-------|--------|-------|-----|---------|----------|------------|-------|
    | A1 | core      | done  | ana  | 1d | -      | auto     | C2 | eng |
    | A2 | feature   | todo  | ana  | 2d | A1     | human    | C4 | eng |
    """
)


def test_contract_shape_and_fields():
    c = plan_to_contract(parse_text(PLAN))
    assert c["schema"] == CONTRACT_SCHEMA
    assert [i["id"] for i in c["items"]] == ["A1", "A2"]
    a2 = c["items"][1]
    assert a2["title"] == "feature"
    assert a2["status"] == "todo"
    assert a2["depends"] == ["A1"]
    assert a2["estimate_hours"] == 16.0
    assert a2["autonomy"] == "human"
    assert a2["complexity"] == "C4"
    assert a2["track"] == "eng"


def test_contract_is_json_serializable():
    c = plan_to_contract(parse_text(PLAN))
    round_tripped = json.loads(json.dumps(c))
    assert round_tripped == c


def test_optional_fields_are_null_when_absent():
    c = plan_to_contract(parse_text("| ID | Title |\n|--|--|\n| X | x |\n"))
    it = c["items"][0]
    assert it["autonomy"] is None
    assert it["complexity"] is None
    assert it["owner"] is None
    assert it["estimate_hours"] is None
    assert it["depends"] == []


def test_canonical_plan_exports_the_expected_contract():
    """O plano canónico exporta o backbone que o runner espera importar:
    ids, dependências e `autonomy=human` só em `decide` (-> human_gate no runner)."""
    c = plan_to_contract(parse_plan(str(CANON_PLAN_MD)))
    assert c["schema"] == CONTRACT_SCHEMA
    by_id = {i["id"]: i for i in c["items"]}
    assert list(by_id) == ["research", "decide", "draft", "finalize"]
    assert by_id["decide"]["depends"] == ["research"]
    assert by_id["draft"]["depends"] == ["decide"]
    assert by_id["finalize"]["depends"] == ["draft"]
    assert [i["id"] for i in c["items"] if i["autonomy"] == "human"] == ["decide"]
    assert by_id["decide"]["track"] == "governance"  # vira o `action` placeholder do esqueleto


def test_cli_export_emits_valid_json(tmp_path):
    p = tmp_path / "PLAN.md"
    p.write_text(PLAN, encoding="utf-8")
    import os

    env = {**os.environ, "PYTHONPATH": SRC}
    r = subprocess.run(
        [sys.executable, "-m", "planwright.cli", "export", str(p)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["schema"] == CONTRACT_SCHEMA
    assert len(data["items"]) == 2
