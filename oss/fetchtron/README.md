# fetchtron

**A safe HTTP GET with the guardrails most clients leave to you.**

One call fetches a URL and *contains* it: a **deny-by-default** domain allowlist, SSRF
protection, robots.txt (RFC 9309), and hard caps on size, time and redirects — with the
allowlist and SSRF checks **re-run on every redirect hop**, so a `302` cannot walk the
request to an internal address or an off-list host.

```python
from fetchtron import fetch, FetchError

try:
    got = fetch("https://example.org/doc", allowlist=["example.org"])
except FetchError as e:
    print(e.code)          # blocked_by_allowlist | blocked_private_address | robots_disallowed | ...
else:
    print(got.final_url, got.status, got.content_type, len(got.content))
    print(got.text)        # decoded best-effort; got.content is the raw bytes
```

Or from the shell (deny-by-default: at least one `--allow` is required):

```console
$ fetchtron get https://example.org/doc --allow example.org --json
```

## What it guards

| Guard | Behaviour |
|-------|-----------|
| **Allowlist** | deny-by-default; a domain also covers its subdomains; **re-checked every redirect hop** |
| **SSRF** | refuses loopback, private, link-local (incl. `169.254.169.254` cloud metadata), reserved, multicast and unspecified addresses |
| **robots.txt** | RFC 9309: `4xx` = no rules (allowed); `5xx` or unreachable = disallowed |
| **Caps** | `max_bytes` (streamed, never the whole page in memory), `timeout_s` (total), `max_redirects` |
| **Scheme** | `http`/`https` with a host only |
| **Provenance** | cleaned `url`/`final_url` (no credentials, no fragment), `status`, `content_type`, `content_hash` |

The allowlist is **data you pass in** — where the policy comes from (a config file, a
per-tenant rule, an area map) is your business; fetchtron only enforces it. It is
content-agnostic: pass `content_types=["text/html"]` to restrict, or omit it for any.

## Why it exists

The classic SSRF bug is a plain `requests.get(url)` that follows a redirect to
`http://169.254.169.254/…` or `http://10.0.0.5/…`. Raw clients give you none of this
containment; you are expected to bolt it on, and most code doesn't. fetchtron is that
containment in one call, on a maintained client.

## How it compares

See `POSITIONING.md` for the evidence-based comparison with raw `requests`/`httpx`,
`advocate`, and the web tools in `langchain`/`smolagents` — including the one place a
competitor does better (DNS-rebinding) and how fetchtron's roadmap closes it.

## Install

```console
pip install fetchtron
```

MIT licensed. Part of the [network-agents-setup](https://github.com/souzalrns/network-agents-setup)
ecosystem; extracted from its governed runner so any project can fetch the web safely.
