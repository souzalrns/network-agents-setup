# groundwright

**A retrieval grounding gate — did retrieval return the expected source, by evidence?**

groundwright does **not** judge whether an *answer* is good (that is answer-quality
eval: ragas, deepeval). It checks the step before: for a golden set of questions with
the **expected source** and a text **anchor**, does your retriever return that source
(provenance) and the chunk that actually contains the anchor — and does the run stay
above a provenance / source-hit threshold you set (a **regression gate**)?

```python
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

report = evaluate(golden, retrieve)                  # {"summary": {...}, "cases": [...]}
failures = regression_failures(report["summary"])    # [] = the gate passes
```

## The retriever is a plug

`Retrieve = (kb, question, k) -> list[hit]`. groundwright never talks to a vector DB, an
MCP or an index — it measures whatever retriever you give it, so the **same gate runs in
CI with a fake retriever and in production with the real one**.

## Metrics

| Metric | Meaning |
|--------|---------|
| `provenance_ok` | every returned hit carries a source (attribution) |
| `source_hit@k` | the expected source is in the top-k |
| `chunk_hit@{1,3,k}` | the chunk that contains the anchor is ranked at/within N |
| `mrr_chunk` | mean reciprocal rank of the anchor chunk |
| `provenance_v2_ok` | hits carry both `metadata` and a citation `uri` (rich provenance) |

`regression_failures(summary, min_provenance_ok=1.0, min_source_hit=0.8)` is the gate:
an empty list means the run passes; thresholds are parameters.

## Why it exists (and what it is not)

RAG quality has two separate questions. *"Is the answer good?"* is owned by `ragas` /
`deepeval` (LLM-as-judge). *"Did we retrieve the right source, and can we prove it?"* is
**retrieval provenance** — and it is where silent regressions hide: a reindex, a chunker
change or a model swap quietly stops returning the authoritative source, and an
answer-quality score may still look fine. groundwright gates that, deterministically,
with no LLM in the loop. See `POSITIONING.md`.

## API

- `load_golden(data) -> dict` — validate a golden set (raises `GoldenError`)
- `evaluate(golden, retrieve) -> {"summary", "cases"}`
- `regression_failures(summary, *, min_provenance_ok=1.0, min_source_hit=0.8) -> list[str]`
- `anchor_errors(golden, chunks) -> list[str]` — offline: each anchor in exactly one chunk
- CLI: `groundwright validate <golden.json> <chunks.json>` · `groundwright gate <report.json>`

## Install

```console
pip install groundwright
```

MIT licensed. Part of the [network-agents-setup](https://github.com/souzalrns/network-agents-setup)
ecosystem; extracted from its governed runner's L5 retrieval gate.
