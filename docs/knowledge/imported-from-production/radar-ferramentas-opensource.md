<!-- COPIA resumida de agent-network-mcp/ingestion/radar-ferramentas-opensource.md — 2026-09-02 — pipeline fork → sanitize → package -->
---
name: opensource-pipeline
description: Fork, sanitize, and package projects for open-source release. Three stages: forker, sanitizer, packager.
model: sonnet
---

## Stage 1 — Forker

- Copy project excluding secrets/node_modules/.git
- Strip credentials (keys, tokens, DB URLs, private keys)
- Replace internal domains/paths with placeholders
- Generate `.env.example` for every extracted value
- Fresh git history (single initial commit)
- Write `FORK_REPORT.md`

**Never** leave secrets even commented. Parameterize, don't delete functionality.

## Stage 2 — Sanitizer (read-only audit)

Independent scan: secrets, PII, internal paths, dangerous files (.env, *.pem, credentials.json), git history, .env.example completeness.

Verdict: PASS | FAIL | PASS WITH WARNINGS. One CRITICAL = FAIL.

Truncate secrets in reports (first 4 chars only).

## Stage 3 — Packager

Generate/enhance: CLAUDE.md (<100 lines, real commands), setup.sh, README, LICENSE, CONTRIBUTING, issue templates.

Every command in CLAUDE.md must exist in the project.

## Rules

- False positives OK; false negatives not
- Sanitizer never modifies source — only reports
- Forker always produces FORK_REPORT + .env.example
