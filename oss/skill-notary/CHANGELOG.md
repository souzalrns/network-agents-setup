# Changelog

## 0.1.0 (unreleased)

First version (phase 1: match the existing tools, then do what they do not).

- `scan`: one skill, a folder of skills or `owner/repo[@skill]`; engines `asm`
  (agentic-skills-manager, default) and `cisco` (Cisco AI Defense skill-scanner, optional),
  merged; verdict `safe` / `risky` / `dangerous` / `not_scanned`; text, JSON and SARIF 2.1.0
  output for GitHub code scanning.
- `install`: hardened shallow fetch, scan, block high/critical, human approval bound to the
  content hash (typed prefix in a terminal, or `--approve-sha256`), refusal when an AI agent is
  detected, atomic copy of exactly the approved bytes, lock file and hash-chained audit log.
- `verify`: audit chain, content drift of every installed skill, lock ↔ audit consistency,
  unmanaged skill folders.
