"""The plan↔execution contract: a planwright export must import into a plan that
validates against the runner's plan.schema.json. See docs/architecture/PLAN-CONTRACT.md.
"""

from __future__ import annotations

import pytest

from plan_runner.plan_import import CONTRACT_SCHEMA, ContractError, import_contract
from plan_runner.plan_schema import plan_errors

# A planwright-plan/v1 contract, as `planwright export` emits it. Kept here
# independently so the runner never imports the planwright package.
CONTRACT = {
    "schema": CONTRACT_SCHEMA,
    "items": [
        {
            "id": "A1",
            "title": "core",
            "status": "done",
            "owner": "ana",
            "estimate_hours": 8.0,
            "depends": [],
            "track": "eng",
            "autonomy": "auto",
            "complexity": "C2",
        },
        {
            "id": "A2",
            "title": "decide",
            "status": "todo",
            "owner": "boss",
            "estimate_hours": 4.0,
            "depends": ["A1"],
            "track": None,
            "autonomy": "human",
            "complexity": "C4",
        },
    ],
}


def test_import_produces_schema_valid_plan():
    plan = import_contract(CONTRACT, plan_id="demo")
    assert plan_errors(plan) == []  # validates against plan.schema.json
    assert plan["id"] == "demo"
    assert [s["id"] for s in plan["steps"]] == ["A1", "A2"]


def test_mapping_title_depends_and_autonomy():
    plan = import_contract(CONTRACT, plan_id="demo")
    a2 = plan["steps"][1]
    assert a2["task"] == "decide"
    assert a2["depends_on"] == ["A1"]
    assert a2["human_gate"] is True  # autonomy=human → gate
    # auto item has no human_gate
    assert "human_gate" not in plan["steps"][0]
    # action is a documented placeholder (track when present, else 'unassigned')
    assert plan["steps"][0]["action"] == "eng"
    assert plan["steps"][1]["action"] == "unassigned"


def test_rejects_non_contract():
    with pytest.raises(ContractError):
        import_contract({"schema": "something-else", "items": []}, plan_id="x")


def test_rejects_empty_items():
    with pytest.raises(ContractError):
        import_contract({"schema": CONTRACT_SCHEMA, "items": []}, plan_id="x")
