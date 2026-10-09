import textwrap

from planwright.graph import Graph
from planwright.parse import parse_text


def make(src: str) -> Graph:
    return Graph(parse_text(textwrap.dedent(src)))


BASE = """
| ID | Title | Status | Est | Depends |
|----|-------|--------|-----|---------|
| A1 | a | done  | 1d | -      |
| A2 | b | todo  | 2d | A1     |
| A3 | c | todo  | 2d | A1     |
| A4 | d | todo  | 1d | A2, A3 |
| B1 | e | todo  | 1d | -      |
"""


def test_ready_only_items_with_done_deps():
    g = make(BASE)
    ready = {it.id for it in g.ready()}
    # A2, A3 depend only on done A1; B1 has no deps; A4 waits on A2/A3.
    assert ready == {"A2", "A3", "B1"}


def test_blocked_lists_unfinished_deps():
    g = make(BASE)
    assert g.blocked() == {"A4": ["A2", "A3"]}


def test_parallel_layers():
    g = make(BASE)
    layers = g.parallel_layers()
    # Done items are excluded. Layer 0 = startable now; A4 lands after A2+A3.
    assert layers[0] == ["A2", "A3", "B1"]
    assert layers[-1] == ["A4"]


def test_critical_path_is_longest_by_estimate():
    g = make(BASE)
    cp = g.critical_path()
    # A1(1d)+A2(2d)+A4(1d) = 4d, tying with A1+A3+A4; both are 4 days = 32h.
    assert cp.hours == 32.0
    assert cp.ids[0] == "A1" and cp.ids[-1] == "A4"


def test_cycle_detected_and_not_schedulable():
    g = make(
        """
        | ID | Title | Depends |
        |----|-------|---------|
        | A | a | C |
        | B | b | A |
        | C | c | B |
        """
    )
    cycles = g.find_cycles()
    assert len(cycles) == 1
    assert set(cycles[0].nodes) == {"A", "B", "C"}
    assert g.is_schedulable() is False


def test_dangling_dependency():
    g = make("| ID | Title | Depends |\n|--|--|--|\n| A | a | GHOST |\n")
    assert g.dangling_dependencies() == [("A", "GHOST")]
    assert g.is_schedulable() is False


def test_self_dependency():
    g = make("| ID | Title | Depends |\n|--|--|--|\n| A | a | A |\n")
    assert g.self_dependencies() == ["A"]


def test_all_done_has_empty_layers_and_no_ready():
    g = make("| ID | Title | Status | Depends |\n|--|--|--|--|\n| A | a | done | - |\n| B | b | done | A |\n")
    assert g.ready() == []
    assert g.parallel_layers() == []
    assert g.blocked() == {}
