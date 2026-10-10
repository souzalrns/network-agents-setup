"""Views (gantt / load / cost): derived lenses over the plan, zero-dep, honest.

They never measure — they draw effort bars, group effort by owner, and estimate
token/USD from Complexity. Real usage is the runner's ledger.
"""

import json
import textwrap

import pytest

from planwright.mermaid import render_gantt
from planwright.parse import parse_text
from planwright.views import (
    DEFAULT_COST_MODEL,
    CostModelError,
    load_cost_model,
    render_cost,
    render_load,
)

PLAN = textwrap.dedent(
    """
    | ID | Title | Status | Owner | Est | Depends | Autonomy | Complexity | Track |
    |----|-------|--------|-------|-----|---------|----------|------------|-------|
    | A1 | core      | done  | ana  | 1d | -      | auto     | C2 | eng |
    | A2 | feature   | todo  | ana  | 2d | A1     | auto     | C3 | eng |
    | A3 | decide    | todo  | boss | 4h | -      | human    | C4 | gov |
    | A4 | ship      | todo  | ana  | -  | A2, A3 | assisted | -  | eng |
    """
)


# -- gantt -----------------------------------------------------------------


def test_gantt_has_sections_ids_and_after():
    out = render_gantt(parse_text(PLAN))
    assert "```mermaid" in out and "gantt" in out
    assert "dateFormat X" in out
    assert "section eng" in out and "section gov" in out
    # A2 depends on A1 -> uses `after A1`; a root uses `0`
    assert "after A1" in out
    assert ", 0, " in out  # A1/A3 are roots


def test_gantt_marks_critical_path_and_unsized_default():
    out = render_gantt(parse_text(PLAN))
    assert "crit" in out  # the critical path is marked
    # A4 is unsized (`-`) -> nominal 1d bar
    a4 = next(ln for ln in out.splitlines() if ln.strip().startswith("A4"))
    assert a4.endswith("1d")


def test_gantt_label_is_colon_free():
    # `:` is gantt's name/metadata separator; the task name must not contain one.
    out = render_gantt(parse_text(PLAN))
    for ln in out.splitlines():
        s = ln.strip()
        if " :" in s and not s.startswith(("section", "title", "gantt", "dateFormat", "axisFormat")):
            name = s.split(" :", 1)[0]
            assert ":" not in name


def test_gantt_empty_and_unschedulable():
    assert "gantt" in render_gantt(parse_text("| ID | Title |\n|--|--|\n"))
    cycle = parse_text("| ID | Title | Depends |\n|--|--|--|\n| X | x | Y |\n| Y | y | X |\n")
    assert "indisponível" in render_gantt(cycle)


# -- load ------------------------------------------------------------------


def test_load_groups_by_owner_and_flags_unsized():
    out = render_load(parse_text(PLAN))
    assert "### ana" in out and "### boss" in out
    assert "sem estimativa: A4" in out  # A4 has no Est


def test_load_no_owner_bucket():
    out = render_load(parse_text("| ID | Title | Est |\n|--|--|--|\n| X | x | 2h |\n"))
    assert "(sem owner)" in out


# -- cost ------------------------------------------------------------------


def test_cost_from_complexity_and_human_is_zero():
    out = render_cost(parse_text(PLAN))
    assert "~15k" in out  # C3 (A2)
    assert "C4" in out  # A3 shown...
    a3 = next(ln for ln in out.splitlines() if ln.strip().startswith("A3"))
    assert "$0.00" in a3  # ...but human -> 0
    assert "não é o ledger" in out


def test_cost_default_model_values():
    assert DEFAULT_COST_MODEL["C4"] == (100_000, 5.00)
    assert load_cost_model() == DEFAULT_COST_MODEL  # no override -> defaults


def test_cost_override_file(tmp_path, monkeypatch):
    f = tmp_path / "cost.json"
    f.write_text(json.dumps({"C2": [1000, 0.01]}), encoding="utf-8")
    monkeypatch.setenv("PLANWRIGHT_COST_MODEL", str(f))
    model = load_cost_model()
    assert model["C2"] == (1000, 0.01)  # overridden
    assert model["C4"] == (100_000, 5.00)  # others keep defaults


def test_cost_override_malformed_fails_loud(tmp_path, monkeypatch):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"C9": [1, 1]}), encoding="utf-8")  # unknown band
    monkeypatch.setenv("PLANWRIGHT_COST_MODEL", str(f))
    with pytest.raises(CostModelError):
        load_cost_model()
    f.write_text(json.dumps({"C2": [1, 2, 3]}), encoding="utf-8")  # wrong shape
    with pytest.raises(CostModelError):
        load_cost_model()
