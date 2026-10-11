"""groundwright: the retrieval grounding/provenance gate."""

from __future__ import annotations

import json

import pytest

from groundwright import (
    GoldenError,
    anchor_errors,
    evaluate,
    load_golden,
    regression_failures,
)

GOLDEN = {
    "kb": "security",
    "source": "docs/policy.md",
    "k": 3,
    "cases": [
        {"id": "c1", "question": "retention?", "anchor": "retained for 30 days"},
        {"id": "c2", "question": "encryption?", "anchor": "aes-256 at rest", "source": "docs/sec.md"},
    ],
}


def _hit(source, content, uri=None, metadata=None):
    cite = {"source": source}
    if uri:
        cite["uri"] = uri
    h = {"citation": cite, "content": content}
    if metadata is not None:
        h["metadata"] = metadata
    return h


# ---- load_golden ----


def test_load_golden_ok():
    assert load_golden(GOLDEN) is GOLDEN


def test_load_golden_collects_errors():
    with pytest.raises(GoldenError) as e:
        load_golden({"kb": "", "k": 0, "cases": []})
    msg = str(e.value)
    assert "`kb` missing" in msg and "`k` must be" in msg and "`cases` is empty" in msg


def test_load_golden_duplicate_id():
    bad = {
        "kb": "k",
        "source": "s",
        "k": 1,
        "cases": [
            {"id": "x", "question": "q", "anchor": "a"},
            {"id": "x", "question": "q2", "anchor": "a2"},
        ],
    }
    with pytest.raises(GoldenError):
        load_golden(bad)


# ---- evaluate: perfect retriever ----


def test_evaluate_perfect():
    def retrieve(kb, question, k):
        if "retention" in question:
            return [_hit("docs/policy.md", "data is retained for 30 days", uri="u1", metadata={"x": 1})]
        return [_hit("docs/sec.md", "we use AES-256 at rest", uri="u2", metadata={"x": 1})]

    rep = evaluate(GOLDEN, retrieve)
    s = rep["summary"]
    assert s["source_hit@3"] == 1.0
    assert s["chunk_hit@1"] == 1.0
    assert s["provenance_ok"] == 1.0
    assert s["provenance_v2_ok"] == 1.0
    assert regression_failures(s) == []


def test_evaluate_wrong_source_fails_gate():
    def retrieve(kb, question, k):
        return [_hit("docs/WRONG.md", "irrelevant text")]

    rep = evaluate(GOLDEN, retrieve)
    s = rep["summary"]
    assert s["source_hit@3"] == 0.0
    fails = regression_failures(s)
    assert any("source_hit@3" in f for f in fails)


def test_evaluate_hit_without_source_breaks_provenance():
    def retrieve(kb, question, k):
        return [_hit("", "some text")]  # empty source

    rep = evaluate(GOLDEN, retrieve)
    assert rep["summary"]["provenance_ok"] == 0.0
    assert any("provenance_ok" in f for f in regression_failures(rep["summary"]))


def test_evaluate_no_hits_provenance_none():
    rep = evaluate(GOLDEN, lambda kb, q, k: [])
    assert rep["summary"]["provenance_ok"] is None
    assert any("no case returned hits" in f for f in regression_failures(rep["summary"]))


def test_provenance_v2_requires_metadata_and_uri():
    def retrieve(kb, question, k):
        return [_hit("docs/policy.md", "retained for 30 days")]  # no uri, no metadata

    rep = evaluate(GOLDEN, retrieve)
    assert rep["summary"]["provenance_ok"] == 1.0  # source present
    assert rep["summary"]["provenance_v2_ok"] == 0.0  # but no metadata/uri


def test_custom_thresholds():
    def retrieve(kb, question, k):
        # only c1 right -> source_hit@3 = 0.5
        if "retention" in question:
            return [_hit("docs/policy.md", "retained for 30 days")]
        return [_hit("docs/WRONG.md", "x")]

    s = evaluate(GOLDEN, retrieve)["summary"]
    assert s["source_hit@3"] == 0.5
    assert regression_failures(s, min_source_hit=0.4) == [] or all(
        "source_hit" not in f for f in regression_failures(s, min_source_hit=0.4)
    )
    assert any("source_hit" in f for f in regression_failures(s, min_source_hit=0.9))


# ---- anchor_errors (offline) ----


def test_anchor_errors_exactly_one():
    chunks = [
        _hit("docs/policy.md", "intro ... retained for 30 days ... end"),
        _hit("docs/sec.md", "we use aes-256 at rest here"),
    ]
    assert anchor_errors(GOLDEN, chunks) == []


def test_anchor_errors_missing_and_duplicate():
    chunks = [
        _hit("docs/policy.md", "retained for 30 days"),
        _hit("docs/policy.md", "retained for 30 days again"),  # c1 anchor in 2 chunks
        # c2 anchor in 0 chunks of docs/sec.md
    ]
    errs = anchor_errors(GOLDEN, chunks)
    assert any("c1" in e and "2 chunks" in e for e in errs)
    assert any("c2" in e and "0 chunks" in e for e in errs)


# ---- CLI ----


def test_cli_validate(tmp_path, capsys):
    from groundwright.cli import main

    g = tmp_path / "g.json"
    g.write_text(json.dumps(GOLDEN), encoding="utf-8")
    ch = tmp_path / "c.json"
    ch.write_text(
        json.dumps(
            [
                _hit("docs/policy.md", "retained for 30 days"),
                _hit("docs/sec.md", "aes-256 at rest"),
            ]
        ),
        encoding="utf-8",
    )
    assert main(["validate", str(g), str(ch)]) == 0


def test_cli_gate_fail(tmp_path, capsys):
    from groundwright.cli import main

    rep = tmp_path / "r.json"
    rep.write_text(json.dumps({"summary": {"k": 3, "provenance_ok": 1.0, "source_hit@3": 0.5}}), encoding="utf-8")
    assert main(["gate", str(rep)]) == 1  # 0.5 < default 0.8
    assert main(["gate", str(rep), "--min-source-hit", "0.4"]) == 0


def test_cli_version(capsys):
    from groundwright.cli import main

    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "groundwright" in capsys.readouterr().out
