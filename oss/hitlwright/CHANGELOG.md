# Changelog

All notable changes to `hitlwright` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

### Added
- First release. Extracted from the governed runner (`runner/plan_runner/hitl.py`
  in network-agents-setup) as a standalone, store-light approval contract.
- Typed `hitl-request-v1` request/decision records; `build_request`, `write_request`,
  `read_decision`, `build_decision`, `write_decision`, `latest_request`,
  `pending_request`. Append-only JSONL (`hitl-requests.jsonl` / `hitl-decisions.jsonl`).
- Shipped JSON Schema (`schema_path()`), validated in the test suite with jsonschema
  (a test-only dependency); zero runtime dependencies.
- `hitlwright` CLI: `request`, `decide`, `pending`, `decision`.
