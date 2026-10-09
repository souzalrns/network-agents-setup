import textwrap

import pytest

from planwright.mermaid import render_board, render_deps
from planwright.model import parse_autonomy, parse_complexity
from planwright.parse import ParseError, parse_text
from planwright.report import render_action

PLAN = textwrap.dedent(
    """
    | ID | Title | Status | Owner | Est | Depends | Autonomy | Complexity |
    |----|-------|--------|-------|-----|---------|----------|------------|
    | A1 | core      | done  | ana  | 1d | -      | auto     | C2 |
    | A2 | feature   | todo  | ana  | 2d | A1     | auto     | C3 |
    | A3 | decide    | todo  | boss | 4h | -      | human    | C4 |
    | A4 | ship      | todo  | ana  | 1d | A2, A3 | assisted | C2 |
    """
)


def test_parse_autonomy_complexity_aliases():
    assert parse_autonomy("autonomous") == "auto"
    assert parse_autonomy("human_gate") == "human"
    assert parse_autonomy("-") is None
    assert parse_complexity("high") == "C3"
    assert parse_complexity("C4") == "C4"
    assert parse_complexity("") is None
    with pytest.raises(ValueError):
        parse_autonomy("robot")
    with pytest.raises(ValueError):
        parse_complexity("C9")


def test_parse_reads_optional_columns():
    plan = parse_text(PLAN)
    a2 = plan.get("A2")
    assert a2.autonomy == "auto"
    assert a2.complexity == "C3"
    a3 = plan.get("A3")
    assert a3.autonomy == "human"


def test_optional_columns_absent_is_fine():
    plan = parse_text("| ID | Title |\n|--|--|\n| X | x |\n")
    assert plan.get("X").autonomy is None
    assert plan.get("X").complexity is None


def test_bad_optional_value_raises_parse_error():
    bad = "| ID | Title | Complexity |\n|--|--|--|\n| X | x | enormous |\n"
    with pytest.raises(ParseError, match="complexity"):
        parse_text(bad)


def test_render_deps_is_valid_mermaid():
    out = render_deps(parse_text(PLAN))
    assert out.startswith("```mermaid")
    assert "flowchart LR" in out
    assert "A1 --> A2" in out
    assert "A2 --> A4" in out and "A3 --> A4" in out
    assert "classDef done" in out
    assert out.rstrip().endswith("```")


def test_render_board_buckets():
    out = render_board(parse_text(PLAN))
    assert "flowchart TB" in out
    # A1 done; A2/A3 ready (deps done or none); A4 blocked (A2,A3 not done)
    assert "subgraph Done" in out
    assert "subgraph Ready" in out
    assert "subgraph Blocked" in out


def test_render_action_ranks_human_blocker_first():
    out = render_action(parse_text(PLAN))
    # A3 is human AND blocks A4 → should rank first in "Agora".
    agora = out.split("##")[1]
    assert "A3" in agora
    first_line = next(ln for ln in agora.splitlines() if ln.strip().startswith("1."))
    assert "A3" in first_line
    assert "[C4][human]" in first_line
    # Critical path line present
    assert "Crítico" in out


def test_render_action_handles_no_metadata():
    plan = parse_text("| ID | Title | Status | Est | Depends |\n|--|--|--|--|--|\n| X | x | todo | 1d | - |\n")
    out = render_action(plan)
    assert "Agora" in out
    assert "X" in out
