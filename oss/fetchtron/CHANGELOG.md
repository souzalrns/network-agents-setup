# Changelog

All notable changes to `fetchtron` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

### Added
- First release. Extracted from the governed runner (`scripts/web_fetch.py` in
  network-agents-setup) as a standalone, content-agnostic safe-GET core.
- `fetch(url, *, allowlist, ...)` → `Fetched` (url, final_url, status, content_type,
  content bytes, text, content_hash, warnings). Raises `FetchError` with a `code`.
- Guards, re-checked on every redirect hop: deny-by-default domain allowlist
  (`host_allowed`), SSRF (`is_public_address` — blocks private/loopback/link-local/
  metadata/reserved), robots.txt (RFC 9309, fail-closed), and caps on size (streamed),
  total time and redirects. Optional `content_types` filter.
- `fetchtron` CLI: `fetchtron get <url> --allow DOMAIN [...]`.
- One runtime dependency (`httpx`); the guards are pure stdlib. Ships its own types.

### Known limitations
- DNS rebinding: the host is resolved for the check and again for the connection (TOCTOU
  window). See POSITIONING.md; the roadmap pins the resolved IP into the connection.
