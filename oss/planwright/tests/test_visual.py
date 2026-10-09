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


def test_mermaid_node_ids_do_not_collide():
    # 'A-1' and 'A_1' both sanitise to 'A_1' — the map must keep them distinct.
    plan = parse_text("| ID | Title | Depends |\n|--|--|--|\n| A-1 | a | - |\n| A_1 | b | A-1 |\n")
    out = render_deps(plan)
    decl = [ln for ln in out.splitlines() if ln.strip().endswith('"]') and "[" in ln]
    tokens = [ln.strip().split("[")[0] for ln in decl]
    assert len(tokens) == len(set(tokens)) == 2  # no duplicate node tokens
    assert "-->" in out


def test_mermaid_escapes_quotes_and_collapses_newlines():
    plan = parse_text('| ID | Title |\n|--|--|\n| X | he said "hi" |\n')
    out = render_deps(plan)
    label_line = next(ln for ln in out.splitlines() if ln.strip().startswith("X["))
    inner = label_line.split('["', 1)[1].rsplit('"]', 1)[0]
    assert '"' not in inner


def test_mermaid_empty_plan_is_safe():
    out = render_deps(parse_text("| ID | Title |\n|--|--|\n"))
    assert "flowchart LR" in out
    assert out.rstrip().endswith("```")


def test_mermaid_unicode_titles_pass_through():
    plan = parse_text("| ID | Title |\n|--|--|\n| X | ação à prova de münchen |\n")
    out = render_deps(plan)
    assert "ação" in out


def test_action_ranks_by_transitive_impact():
    plan = parse_text(
        "| ID | Title | Status | Est | Depends |\n|--|--|--|--|--|\n"
        "| H  | hub   | todo | 1d | -  |\n"
        "| M1 | mid   | todo | 1d | H  |\n"
        "| M2 | leaf  | todo | 1d | M1 |\n"
        "| L  | small | todo | 1d | -  |\n"
        "| L2 | leaf2 | todo | 1d | L  |\n"
    )
    out = render_action(plan)
    agora = out.split("##")[1]
    order = [ln.split(".")[1].split()[0] for ln in agora.splitlines() if ln.strip()[:2] in ("1.", "2.")]
    assert order[0] == "H"  # unblocks 2 transitively, beats L (unblocks 1)
    assert "destrava 2 a jusante" in agora
