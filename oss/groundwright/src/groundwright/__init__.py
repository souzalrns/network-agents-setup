"""groundwright: a retrieval **grounding gate** — did retrieval return the expected
source, by evidence, and does it still pass the regression threshold?

groundwright does not judge whether an *answer* is good (that is answer-quality eval:
ragas, deepeval). It checks the step before: for a golden set of questions with the
**expected source** and a text **anchor**, does your retriever return that source
(provenance) and the chunk that actually contains the anchor — and does the run stay
above a provenance/source-hit threshold you set (a regression gate)?

    from groundwright import evaluate, regression_failures

    golden = {
        "kb": "security", "source": "docs/policy.md", "k": 5,
        "cases": [
            {"id": "c1", "question": "what is the data retention policy?",
             "anchor": "retained for 30 days", "source": "docs/policy.md"},
        ],
    }

    def retrieve(kb, question, k):
        # your retriever -> [{"citation": {"source": ..., "uri"?: ...},
        #                     "content": ..., "metadata"?: {...}}, ...]
        ...

    report = evaluate(golden, retrieve)          # {"summary": {...}, "cases": [...]}
    failures = regression_failures(report["summary"])   # [] means the gate passes

The retriever is a **plug**: ``Retrieve = (kb, question, k) -> list[hit]``. groundwright
never talks to a vector DB, an MCP or an index — it measures whatever retriever you give
it, so the same gate runs in CI with a fake retriever and in production with the real one.

Metrics: ``provenance_ok`` (every hit carries a source), ``source_hit@k`` (the expected
source is in the top-k), ``chunk_hit@{1,3,k}`` (the anchor chunk is ranked), ``mrr_chunk``,
and ``provenance_v2_ok`` (hits carry metadata + a citation uri). Zero dependencies.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_MIN_PROVENANCE_OK",
    "DEFAULT_MIN_SOURCE_HIT",
    "GoldenError",
    "Retrieve",
    "__version__",
    "anchor_errors",
    "evaluate",
    "load_golden",
    "regression_failures",
]

# A retriever: (kb, question, k) -> list of hits. A hit is a dict shaped like
# {"citation": {"source": str, "uri"?: str}, "content": str, "metadata"?: dict}.
Retrieve = Callable[[str, str, int], list[dict[str, Any]]]

DEFAULT_MIN_PROVENANCE_OK = 1.0
DEFAULT_MIN_SOURCE_HIT = 0.8


class GoldenError(ValueError):
    """The golden set is invalid. Carries every problem found."""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def load_golden(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a golden set (a plain mapping). Raises ``GoldenError`` listing all problems.

    Required: ``kb`` (str), ``source`` (str), ``k`` (int >= 1), ``cases`` (non-empty list).
    Each case: unique ``id``, non-empty ``question`` and ``anchor`` (optional per-case
    ``source`` overrides the top-level one; optional ``stale`` flag).
    """
    errors: list[str] = []
    for key in ("kb", "source"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"`{key}` missing")
    if not isinstance(data.get("k"), int) or isinstance(data.get("k"), bool) or data.get("k", 0) < 1:
        errors.append("`k` must be an int >= 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("`cases` is empty")
        cases = []
    seen: set[str] = set()
    for i, case in enumerate(cases):
        cid = case.get("id") if isinstance(case, dict) else None
        if not cid or cid in seen:
            errors.append(f"case {i}: `id` missing or repeated")
        seen.add(cid)
        for key in ("question", "anchor"):
            if not isinstance(case, dict) or not str(case.get(key) or "").strip():
                errors.append(f"{cid or i}: `{key}` missing")
    if errors:
        raise GoldenError("invalid golden set: " + "; ".join(errors))
    return data


def _has_v2_provenance(hit: dict[str, Any]) -> bool:
    """The hit carries rich provenance: a non-empty ``metadata`` and a ``citation.uri``."""
    metadata = hit.get("metadata")
    return isinstance(metadata, dict) and bool(metadata) and bool((hit.get("citation") or {}).get("uri"))


def evaluate(golden: dict[str, Any], retrieve: Retrieve) -> dict[str, Any]:
    """Run the golden set through ``retrieve`` and measure grounding/provenance.

    Returns ``{"summary": {...}, "cases": [...]}``. ``retrieve`` is called once per case
    with ``(kb, question, k)`` and must return a list of hits (see ``Retrieve``).
    """
    kb, k = golden["kb"], golden["k"]
    rows = []
    for case in golden["cases"]:
        source = case.get("source", golden["source"])
        hits = (retrieve(kb, case["question"], k) or [])[:k]
        sources = [((h.get("citation") or {}).get("source") or "") for h in hits]
        src_rank = next((i for i, s in enumerate(sources, 1) if s == source), None)
        chunk_rank = next(
            (
                i
                for i, (s, h) in enumerate(zip(sources, hits, strict=False), 1)
                if s == source and _norm(case["anchor"]) in _norm(h.get("content", ""))
            ),
            None,
        )
        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "hits": len(hits),
                "source_rank": src_rank,
                "chunk_rank": chunk_rank,
                "provenance_ok": bool(hits) and all(sources),
                "provenance_v2_ok": bool(hits) and all(_has_v2_provenance(h) for h in hits),
                "retrieved_sources": sources,
                "stale": bool(case.get("stale")),
            }
        )
    n = len(rows)

    def at(r: int) -> float:
        return round(sum(1 for x in rows if x["chunk_rank"] and x["chunk_rank"] <= r) / n, 3)

    with_hits = [x for x in rows if x["hits"]]
    summary = {
        "kb": kb,
        "source": golden["source"],
        "k": k,
        "cases": n,
        "chunk_hit@1": at(1),
        "chunk_hit@3": at(min(3, k)),
        f"chunk_hit@{k}": at(k),
        f"source_hit@{k}": round(sum(1 for x in rows if x["source_rank"]) / n, 3),
        "mrr_chunk": round(sum(1 / x["chunk_rank"] for x in rows if x["chunk_rank"]) / n, 3),
        "no_hits": n - len(with_hits),
        "provenance_ok": (
            round(sum(1 for x in with_hits if x["provenance_ok"]) / len(with_hits), 3) if with_hits else None
        ),
        "provenance_v2_ok": (
            round(sum(1 for x in with_hits if x["provenance_v2_ok"]) / len(with_hits), 3) if with_hits else None
        ),
    }
    return {"summary": summary, "cases": rows}


def regression_failures(
    summary: dict[str, Any],
    *,
    min_provenance_ok: float = DEFAULT_MIN_PROVENANCE_OK,
    min_source_hit: float = DEFAULT_MIN_SOURCE_HIT,
) -> list[str]:
    """The regression gate: what falls below the thresholds. Empty list = the run passes.

    Thresholds are parameters (defaults: provenance_ok == 1.0, source_hit@k >= 0.8).
    """
    failures = []
    prov = summary.get("provenance_ok")
    if prov is None:
        failures.append(f"provenance_ok has no value: no case returned hits (requires {min_provenance_ok})")
    elif prov < min_provenance_ok:
        failures.append(f"provenance_ok = {prov} (requires {min_provenance_ok}): there are hits with no source")
    key = f"source_hit@{summary['k']}"
    if summary[key] < min_source_hit:
        failures.append(f"{key} = {summary[key]} (requires >= {min_source_hit})")
    return failures


def anchor_errors(golden: dict[str, Any], chunks: list[dict[str, Any]]) -> list[str]:
    """Offline check: each case's anchor must fall in exactly one chunk of its source.

    ``chunks`` is your chunking of the sources, each ``{"citation": {"source"}, "content"}``.
    Use it to validate a golden set against your chunker before any retrieval runs.
    """
    errors = []
    for case in golden["cases"]:
        source = case.get("source", golden["source"])
        n = sum(
            1
            for c in chunks
            if (c.get("citation") or {}).get("source") == source
            and _norm(case["anchor"]) in _norm(c.get("content", ""))
        )
        if n != 1:
            errors.append(f"{case['id']}: anchor {case['anchor']!r} in {n} chunks of {source} (expected 1)")
    return errors
