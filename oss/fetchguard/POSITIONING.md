# fetchguard — positioning & competitive analysis

> Evidence-based, per the repo playbook (`docs/initiatives/REPO-EVAL-PLAYBOOK.md`).
> The honest question: *what do the others have that we don't, and what would make
> fetchguard the recommended choice in its lane?*

## The lane

fetchguard answers one question: **can an agent or a server GET this URL without
becoming an SSRF or exfiltration vector?** It is a *containment layer* around a single
HTTP GET — allowlist + SSRF + robots + caps. It is **not** a scraper, **not** a crawler,
**not** an HTTP client (it uses one), and **not** an HTML parser.

## The competitors (and what each actually does)

### Raw `requests` / `httpx`
- **What they are:** excellent general HTTP clients.
- **What they have that we don't:** everything about HTTP — sessions, auth, HTTP/2,
  async, connection pooling. fetchguard uses `httpx` precisely because it is better at
  HTTP than anything we'd write.
- **Why they are not this lane:** no allowlist, no SSRF guard, no robots, and —
  critically — `follow_redirects=True` will happily chase a `302` to
  `http://169.254.169.254/…`. The containment is left entirely to the caller, and most
  callers skip it. fetchguard is that containment, with the client underneath.

### `advocate` (requests + SSRF-blocking pool manager)
- **What it is:** the closest prior art. A `requests` wrapper whose connection pool
  validates the **connected IP** against a blocklist, which is the right place to stop
  DNS rebinding.
- **What it has that we don't (honest):** because it checks at connect time, it closes
  the **DNS-rebinding** window that fetchguard currently leaves open (fetchguard resolves
  the name for its check and the client resolves again for the connection — a TOCTOU gap).
- **Where fetchguard is ahead:** `advocate` is `requests`-only and effectively
  unmaintained (no `httpx`/async, stale releases); it has **no allowlist** (it blocks bad
  IPs but does not enforce "only these domains"), **no robots.txt**, and **no per-hop
  re-validation tied to an allowlist**. fetchguard adds deny-by-default allowlisting,
  robots, and caps, on a maintained client — and names the rebinding gap openly (below).

### `langchain` web tools / `smolagents` web tools
- **What they are:** convenience fetch/search tools and document loaders built for
  **capability** — get the agent the content.
- **What they have that we don't:** integration with their agent frameworks, parsing,
  chunking, search back-ends.
- **Why they are not this lane:** no SSRF guard, no deny-by-default allowlist, robots
  support is optional at best. They are built to reach the web, not to contain it.
  fetchguard is the layer you put *under* such a tool so it cannot be turned against your
  own network.

## Where fetchguard wins (and the evidence)

| Property | fetchguard | raw requests/httpx | advocate | langchain/smolagents |
|----------|-----------|--------------------|----------|----------------------|
| Deny-by-default **allowlist** (domain + subdomains) | ✅ (`host_allowed`) | ❌ | ❌ | ❌ |
| **SSRF** block (private/loopback/link-local/metadata) | ✅ (`is_public_address`) | ❌ | ✅ | ❌ |
| Re-checked on **every redirect hop** | ✅ (manual loop) | ❌ (auto-follow) | partial | ❌ |
| **robots.txt** (RFC 9309, fail-closed) | ✅ | ❌ | ❌ | ⚠️ optional |
| Caps: size (streamed), total time, redirects | ✅ | ❌ (manual) | ❌ | ❌ |
| Maintained client / async-ready base | ✅ (httpx) | ✅ | ❌ (requests, stale) | ✅ |
| One small, single-purpose package | ✅ | n/a | ✅ | ❌ (framework) |

The distinctive combination is **allowlist + SSRF + robots + caps re-checked per hop, in
one call on a maintained client**. No single competitor offers all of it.

## Honest limits (what fetchguard does NOT do yet)

- **DNS rebinding.** The host is resolved for the SSRF check, then resolved again by
  `httpx` for the connection — a TOCTOU window `advocate` closes at connect time.
  **Roadmap:** resolve once, assert all A/AAAA records are public, and pin the chosen IP
  into the connection (a custom `httpx` transport) so the checked address is the connected
  address.
- **GET only.** No POST/PUT; it is a read primitive.
- **Not a crawler.** One URL, one response (following redirects). No link discovery.
- **Not a parser.** Returns bytes + best-effort text; HTML→Markdown, extraction and
  chunking belong to the caller.

## What would make it "more the choice" (roadmap, not claims)

- Close the DNS-rebinding gap (pin the resolved IP) — the one place `advocate` leads.
- An async `fetch` (httpx is async-ready) for agent runtimes.
- Optional structured audit record of every blocked attempt (for SIEM ingestion).
