# Changelog

All notable changes to `groundwright` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

### Added
- First release. Extracted from the governed runner (`runner/plan_runner/l5_eval.py`
  in network-agents-setup) as a standalone, retriever-agnostic grounding gate.
- `evaluate(golden, retrieve)` → provenance/source-hit/anchor-chunk metrics; the
  retriever is a `Retrieve = (kb, question, k) -> list[hit]` callable (the seam).
- `regression_failures(summary, *, min_provenance_ok=1.0, min_source_hit=0.8)` — the
  gate, with thresholds as parameters.
- `load_golden` (validation) and `anchor_errors` (offline golden↔chunking check).
- `groundwright` CLI: `validate`, `gate`. Zero runtime dependencies; no LLM in the loop.

### Notes
- This reverses the repo's RE1=B *as a generic rag-eval product* by shipping the narrow,
  defensible thing instead: a deterministic retrieval-provenance gate, not an
  answer-quality (LLM-judge) evaluator. See POSITIONING.md.
