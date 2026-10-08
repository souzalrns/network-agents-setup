"""`find`: search the skills.sh directory, and (with --scan) scan every result before you pick one.

The search is the one `npx skills find` runs (skills CLI 1.7.1, MIT: `searchSkillsAPI`):
`GET {SKILLS_API_URL or https://skills.sh}/api/search?q=…&limit=…` → `{"skills": [{name, id,
source, installs}]}`, called directly over HTTPS (no `npx`, so no code downloaded and run):
https only, no redirects, 10 s timeout, 256 KB cap, every field sanitised (control and ANSI
characters removed; names outside `[A-Za-z0-9._/@:-]` dropped). Results are data for a human,
never instructions. `find` never installs; `--scan` runs the normal scan on each of the first N
results, so the list shows a verdict and a content hash next to the install count.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from .engines import Engine
from .errors import FetchError, ScoutError, UsageError
from .install import prepared
from .source import GITHUB, parse_source

API_ENV = "SKILLS_API_URL"  # same variable as the skills CLI
API_DEFAULT = "https://skills.sh"
TIMEOUT_S = 10.0
MAX_BYTES = 256 * 1024
MAX_LIMIT = 50
# ANSI escape sequences first: with the single-character class first, ESC alone matched and
# the rest of the sequence ("[31m") stayed in the text.
_CONTROL = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|[\x00-\x1f\x7f]")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@:-]{0,199}$")


def _clean(value: object) -> str:
    return _CONTROL.sub("", str(value or "")).strip()[:200]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # a redirect could lead to http or another host
        return None


def http_get(url: str) -> bytes:
    if urllib.parse.urlsplit(url).scheme != "https":
        raise FetchError("the skills API must be https")
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(  # noqa: S310 - https only, enforced above
        url, headers={"Accept": "application/json", "User-Agent": "skill-scout"}
    )
    try:
        with opener.open(req, timeout=TIMEOUT_S) as resp:
            if resp.status != 200:
                raise FetchError(f"skills API: HTTP {resp.status}")
            body = resp.read(MAX_BYTES + 1)
    except OSError as e:
        raise FetchError(f"skills API unreachable: {type(e).__name__}") from None
    if len(body) > MAX_BYTES:
        raise FetchError("skills API: response above the size limit")
    return body


@dataclass
class Candidate:
    name: str
    source: str
    slug: str
    installs: int | None
    spec: str | None  # owner/repo@name, when installable by skill-scout
    scan: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "slug": self.slug,
            "installs": self.installs,
            "spec": self.spec,
            "url": f"https://skills.sh/{self.slug}" if self.slug else None,
            "installed": False,
            "scan": self.scan,
        }


def search(query: str, limit: int = 10, get=None) -> list[Candidate]:
    query = _clean(query)
    if not query:
        raise UsageError("empty query")
    limit = max(1, min(int(limit), MAX_LIMIT))
    base = (os.environ.get(API_ENV) or API_DEFAULT).rstrip("/")
    raw = (get or http_get)(f"{base}/api/search?" + urllib.parse.urlencode({"q": query, "limit": str(limit)}))
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise FetchError("skills API: response is not JSON") from None
    items = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise FetchError("skills API: response without a `skills` list")
    out: list[Candidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name, slug, source = _clean(item.get("name")), _clean(item.get("id")), _clean(item.get("source"))
        if not _TOKEN.match(name) or (slug and not _TOKEN.match(slug)):
            continue
        source = source if source and _TOKEN.match(source) else ""
        spec = None
        if source:
            try:
                spec = parse_source(f"{source}@{name}").display
            except UsageError:
                spec = None
        installs = item.get("installs")
        out.append(
            Candidate(name, source, slug, installs if isinstance(installs, int) and installs >= 0 else None, spec)
        )
    out.sort(key=lambda c: -(c.installs or 0))
    return out[:limit]


def scan_candidates(cands: list[Candidate], engines: list[Engine], n: int, base_url: str = GITHUB) -> None:
    """Scan the first `n` candidates in place (verdict + content hash); errors stay per candidate."""
    for c in cands[:n]:
        if not c.spec:
            c.scan = {"verdict": "not_scanned", "error": "no owner/repo source"}
            continue
        try:
            with prepared(parse_source(c.spec), engines, [], base_url=base_url) as p:
                c.scan = {
                    "verdict": p.report.verdict,
                    "content_sha256": p.report.tree.digest,
                    "commit": p.report.commit,
                    "counts": p.report.counts,
                }
        except ScoutError as e:
            c.scan = {"verdict": "not_scanned", "error": str(e)[:200]}
