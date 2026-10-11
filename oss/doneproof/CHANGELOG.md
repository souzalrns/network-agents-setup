# Changelog

All notable changes to `doneproof` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

### Added
- First release. Extracted from the governed runner
  (`runner/plan_runner/done_when.py` in network-agents-setup) as a standalone,
  store-agnostic acceptance primitive.
- `evaluate(root, conditions, gate_resolved=None)` — classifies each condition
  into `passed` / `failed` / `unverifiable` against real evidence.
- Two verifiable forms: `<path> exists` (with path-traversal guard) and
  `human_gate_resolved on <step>` (via the pluggable `gate_resolved` predicate).
- `is_satisfied(result)` — true iff nothing failed (unverifiable does not fail).
- `doneproof` CLI: `doneproof check <root> [conditions...] [--resolved STEP] [--json]`.
- Zero runtime dependencies (pure stdlib); ships its own types (PEP 561).
