# Changelog

All notable changes to `fetchtron` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-23

### Security
- **DNS rebinding closed.** On every hop the host is resolved once, every A/AAAA record
  must be public, and the connection goes to that checked address: the URL carries the
  IP, `Host` keeps the name and, for https, the `sni_hostname` extension makes httpcore use
  the name for SNI **and** certificate verification. robots.txt and every redirect hop use
  the same pinned addresses, so a second (rebinding) DNS answer is never used.
- If the connection to one checked address fails (e.g. an unroutable IPv6 record), the
  next checked address is tried; any other error is final. IPv4 first.

### Changed
- Behind an environment proxy (`trust_env` + `HTTP(S)_PROXY`/`ALL_PROXY`, not bypassed by
  `NO_PROXY`) the proxy resolves the name, so the IP is not pinned there and the result
  carries the warning `dns_not_pinned_proxy`.
- The resolution uses the scheme's default port (80 for http; it was always 443).

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
