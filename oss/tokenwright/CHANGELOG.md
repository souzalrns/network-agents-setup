# Changelog

All notable changes to `tokenwright` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

### Added
- First release. Extracted from the governed runner (`runner/plan_runner/cost.py`
  in network-agents-setup) as a standalone, dependency-free cost-ledger and budget cap.
- `prices_from_mapping`, `estimate_cost_usd`, `row_cost_usd`, `ledger_cost_usd`.
- `would_exceed` and `guard_next_call` — the projective cap: refuse the next call when
  `spent + projected > cap` (`BudgetExceeded`).
- `CostUnknown` — fail-closed when a model has no confirmed price (never silently 0).
- Reasoning tokens counted via `tokens_total - tokens_in`.
- `tokenwright` CLI: `cost`, `check`. Zero runtime dependencies.
