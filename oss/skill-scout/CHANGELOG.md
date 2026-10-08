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
- `find`: skills.sh search (the `npx skills find` API, over HTTPS, no `npx`), `--scan N` shows a
  verdict and content hash per result; never installs.
- `list`, `update` (content diff + a new human approval; `--check` for CI; commit pins never move;
  local edits never overwritten), `uninstall` (refuses a modified copy).
- `--agent NAME` (repeatable): the project skills folders of ~80 agents (skills CLI table); one
  approval installs into several folders. Lock keys are install paths.
- `waive`: accept one finding for one exact content, with a reason, an expiry and a human
  approval, recorded in the lock and the audit chain; never critical. Only audit-backed waivers
  count. SARIF marks waived results as accepted suppressions.
- Agent Skills spec checks on every scan (quality rules in SARIF, not security).
- Fix: the control-character filter removed only ESC from ANSI sequences; it now removes whole
  CSI and OSC sequences.
- Renamed from the working name `skill-notary` (decision P-43).
