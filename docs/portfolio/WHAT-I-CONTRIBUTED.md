# What I contributed: the F1 → F6 knowledge chain (Oct 2026)

Evidence for every line: [`F6-evidence/`](./F6-evidence/README.md). PR list with links: [`F6-evidence/prs.md`](./F6-evidence/prs.md).

- **Document ingestion (F1).** PDF, DOCX and XLSX to Markdown through MarkItDown, tested with reproducible synthetic fixtures and a structure benchmark (lists and tables kept at 100%). PRs #105–#110.
- **Input security.** Conversion runs in a child process with a timeout and a measured memory cap (`RLIMIT_DATA`, 1 GiB), byte limits and ZIP/OOXML checks before parsing, covered by 18 negative tests. PR #108.
- **RAG ingestion with provenance.** Converted documents enter the existing T6 pipeline with a validated `source_meta` sidecar; nothing reaches the knowledge base without valid provenance. PR #109.
- **Web fetch (F2).** A `fetch` primitive with a per-redirect allowlist, robots.txt (RFC 9309), SSRF blocking (including cloud metadata), byte and time ceilings, and provenance with the final URL. PR #111.
- **Provenance in retrieval (F3a).** An additive Postgres migration and a new `match_knowledge_v2` RPC, with the old function untouched. The MCP server switched to it behind a feature flag with a safe fallback. Verified in production: each retrieved chunk now carries its URI, status and document type. PRs #113, #117 and MCP #19.
- **Source validity (F3b).** Validity classes: legal sources need a start date, market data an end date, and web pages expire after 90 days. Expired sources stay in the database but leave retrieval by default, and a local report lists what to renew. No new SQL, and no breaking change for undated sources. PR #120.
- **Knowledge coverage (F3c).** Every knowledge file is either ingested or excluded with a written reason, enforced by a CI test; duplicates of production content are kept out. PR #119.
- **Measured quality.** The security golden set against production scored `source_hit@4` 1.0 and MRR 0.736, and a real end-to-end run (retrieve → Gemini → human gate → report) passed all 5 criteria. PRs #104, #115 and #116.
- **Hardening.** Secret scans over the whole history, local machine paths removed from the docs, two Dependabot alerts fixed, and a clear map of which commands write to production. PR #118 and the F6 PR.
- **Not done yet, on purpose:** source authority and conflict handling (`match_knowledge_v3`) needs a production migration, so it is parked as F3b-AUTH-1 with its unblock criterion. See [`F6-evidence/deferred.md`](./F6-evidence/deferred.md).
