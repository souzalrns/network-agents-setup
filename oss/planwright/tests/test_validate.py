import textwrap

from planwright.validate import validate_text


def v(src: str):
    return validate_text(textwrap.dedent(src))


def test_clean_plan_is_ok():
    r = v(
        """
        | ID | Title | Status | Est | Depends |
        |----|-------|--------|-----|---------|
        | A1 | a | done | 1d | -  |
        | A2 | b | doing| 2d | A1 |
        """
    )
    assert r.errors == []
    assert r.warnings == []
    assert r.ok(strict=True)


def test_duplicate_id_is_error():
    r = v("| ID | Title |\n|--|--|\n| A | a |\n| A | b |\n")
    assert any(f.code == "duplicate-id" for f in r.errors)
    assert not r.ok()


def test_dangling_dependency_is_error():
    r = v("| ID | Title | Depends |\n|--|--|--|\n| A | a | GHOST |\n")
    assert any(f.code == "dangling-dependency" for f in r.errors)


def test_cycle_is_error():
    r = v(
        """
        | ID | Title | Depends |
        |----|-------|---------|
        | A | a | B |
        | B | b | A |
        """
    )
    assert any(f.code == "cycle" for f in r.errors)


def test_started_without_estimate_is_warning():
    r = v("| ID | Title | Status | Est |\n|--|--|--|--|\n| A | a | doing | - |\n")
    assert r.errors == []
    assert any(f.code == "started-without-estimate" for f in r.warnings)
    assert r.ok(strict=False) is True  # warning does not fail a non-strict run
    assert r.ok(strict=True) is False  # but does under strict


def test_done_before_dependency_is_warning():
    r = v(
        """
        | ID | Title | Status | Est | Depends |
        |----|-------|--------|-----|---------|
        | A | a | todo | 1d | -  |
        | B | b | done | 1d | A  |
        """
    )
    assert any(f.code == "done-before-dependency" for f in r.warnings)


def test_parse_error_becomes_error_finding():
    r = v("no table here\n")
    assert len(r.errors) == 1
    assert r.errors[0].code == "parse"
