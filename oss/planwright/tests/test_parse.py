import textwrap

import pytest

from planwright.model import HOURS_PER_DAY, Status
from planwright.parse import ParseError, parse_text


def test_parses_minimal_table():
    plan = parse_text(
        textwrap.dedent(
            """
            | ID | Title | Status | Est | Depends |
            |----|-------|--------|-----|---------|
            | A1 | first | done   | 1d  | -       |
            | A2 | second| todo   | 2h  | A1      |
            """
        )
    )
    assert len(plan) == 2
    a2 = plan.get("A2")
    assert a2.title == "second"
    assert a2.status is Status.TODO
    assert a2.depends == ["A1"]
    assert a2.estimate_hours == 2.0
    assert plan.get("A1").estimate_hours == HOURS_PER_DAY


def test_ignores_prose_and_other_tables_before_the_plan():
    plan = parse_text(
        textwrap.dedent(
            """
            # Title

            Some prose.

            | foo | bar |
            |-----|-----|
            | 1   | 2   |

            Now the plan:

            | ID | Title |
            |----|-------|
            | X1 | only  |
            """
        )
    )
    # The first table lacks id+title, so it is skipped; the plan table is found.
    assert len(plan) == 1
    assert plan.get("X1").title == "only"


def test_portuguese_and_alias_headers():
    plan = parse_text(
        textwrap.dedent(
            """
            | ID | Título | Estado   | Estimativa | Depende de | Fase |
            |----|--------|----------|------------|------------|------|
            | A1 | um     | em curso | M          | -          | core |
            """
        )
    )
    a1 = plan.get("A1")
    assert a1.status is Status.DOING
    assert a1.track == "core"
    assert a1.estimate_hours == 2 * HOURS_PER_DAY  # size M


def test_multiple_deps_separators():
    plan = parse_text("| ID | Title | Depends |\n|--|--|--|\n| C | c | A, B C |\n")
    assert plan.get("C").depends == ["A", "B", "C"]


def test_missing_table_raises():
    with pytest.raises(ParseError, match="no plan table"):
        parse_text("# just prose, no table\n")


def test_missing_separator_raises():
    with pytest.raises(ParseError, match="separator"):
        parse_text("| ID | Title |\n| A1 | x |\n")


def test_ragged_row_raises():
    with pytest.raises(ParseError, match="cells"):
        parse_text("| ID | Title | Status |\n|--|--|--|\n| A1 | x |\n")


def test_bad_status_and_estimate_raise():
    with pytest.raises(ParseError, match="unknown status"):
        parse_text("| ID | Title | Status |\n|--|--|--|\n| A1 | x | floating |\n")
    with pytest.raises(ParseError, match="bad estimate"):
        parse_text("| ID | Title | Est |\n|--|--|--|\n| A1 | x | 3 fortnights |\n")


def test_empty_id_raises():
    with pytest.raises(ParseError, match="empty ID"):
        parse_text("| ID | Title |\n|--|--|\n|  | x |\n")
