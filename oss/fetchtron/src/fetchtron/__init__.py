"""fetchtron: a safe HTTP GET with the guardrails most clients leave to you.

One call fetches a URL and *contains* it: an allowlist that is **deny-by-default**,
SSRF protection (private / loopback / link-local / reserved / metadata addresses are
refused), robots.txt (RFC 9309), and hard caps on size, time and redirects — with the
allowlist and SSRF checks **re-run on every redirect hop**, so a 302 cannot walk the
request to an internal address or an off-list host.

    from fetchtron import fetch, FetchError

    try:
        got = fetch("https://example.org/doc", allowlist=["example.org"])
    except FetchError as e:
        print(e.code, e)        # e.g. blocked_by_allowlist, blocked_private_address
    else:
        print(got.final_url, got.status, got.content_type, len(got.content))
        print(got.text)         # decoded best-effort; got.content is the raw bytes

The allowlist is **data you pass in** (a list of domains; a domain also covers its
subdomains). Where the policy comes from — a config file, an area map, a per-tenant
rule — is the caller's business; fetchtron only enforces it.

Honest limit (see POSITIONING.md): the host is resolved for the SSRF check and then
again by the HTTP client, so a DNS-rebinding window exists. Roadmap closes it by
pinning the resolved IP into the connection.
"""

from __future__ import annotations

import ipaddress
import socket
import time
import urllib.robotparser
from dataclasses import dataclass, field
from hashlib import sha256
from urllib.parse import urljoin, urlsplit, urlunsplit

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_USER_AGENT",
    "ERROR_CODES",
    "FetchError",
    "Fetched",
    "__version__",
    "clean_uri",
    "fetch",
    "host_allowed",
    "is_public_address",
]

DEFAULT_TIMEOUT_S = 20.0
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 5
ROBOTS_MAX_BYTES = 512 * 1024  # RFC 9309 §2.5: a client must read at least 500 KiB
REDIRECT_CODES = (301, 302, 303, 307, 308)
DEFAULT_USER_AGENT = "fetchtron/0.1 (+https://pypi.org/project/fetchtron/)"

ERROR_CODES = (
    "invalid_uri",
    "blocked_by_allowlist",
    "blocked_private_address",
    "robots_disallowed",
    "timeout",
    "http_error",
    "too_large",
    "unsupported_content_type",
)


class FetchError(Exception):
    """A typed fetch failure. ``code`` is one of ``ERROR_CODES``."""

    def __init__(self, code: str, message: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"error code outside the contract: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = message


@dataclass(frozen=True)
class Fetched:
    """A fetched resource plus the provenance of how it was obtained."""

    url: str  # the cleaned original URL (no credentials, no fragment)
    final_url: str  # after redirects, cleaned
    status: int
    content_type: str
    content: bytes
    text: str  # best-effort decode of content
    content_hash: str  # sha256 hex of content bytes
    warnings: list[str] = field(default_factory=list)


def clean_uri(url: str) -> str:
    """URL for provenance: drop credentials (``user:pass@``) and the fragment."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    netloc = f"{host}:{parts.port}" if parts.port else host
    return urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, ""))


def host_allowed(host: str, allowlist) -> bool:
    """True iff ``host`` is a domain in the allowlist or a subdomain of one."""
    host = host.lower().rstrip(".")
    for domain in allowlist:
        domain = domain.lower().strip().rstrip(".")
        if domain and (host == domain or host.endswith(f".{domain}")):
            return True
    return False


# Address properties that make an IP non-public (169.254.169.254 is is_link_local).
_NON_PUBLIC_FLAGS = (
    "is_private",
    "is_loopback",
    "is_link_local",
    "is_multicast",
    "is_reserved",
    "is_unspecified",
)


def is_public_address(ip: str) -> bool:
    """False for loopback, private, link-local (incl. cloud metadata), reserved, …"""
    addr = ipaddress.ip_address(ip)
    return not any(getattr(addr, flag) for flag in _NON_PUBLIC_FLAGS)


def _check_url(url: str, allowlist, *, allow_private: bool) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise FetchError("invalid_uri", f"only http/https with a host: {clean_uri(url)}")
    if not host_allowed(parts.hostname, allowlist):
        raise FetchError("blocked_by_allowlist", f"{parts.hostname} is not in the allowlist {list(allowlist)}")
    if allow_private:
        return
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise FetchError("http_error", f"the name {parts.hostname} does not resolve: {exc}") from exc
    for info in infos:
        ip = info[4][0]
        if not is_public_address(ip):
            raise FetchError("blocked_private_address", f"{parts.hostname} resolves to {ip} (not public)")


def _read_limited(response, max_bytes: int, deadline: float, what: str) -> bytes:
    declared = response.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise FetchError("too_large", f"{what}: Content-Length {declared} > cap {max_bytes}")
    body = bytearray()
    for chunk in response.iter_bytes():
        body += chunk
        if len(body) > max_bytes:
            raise FetchError("too_large", f"{what}: exceeded {max_bytes} bytes")
        if time.monotonic() > deadline:
            raise FetchError("timeout", f"{what}: the total request deadline passed")
    return bytes(body)


def _get(client, url: str, max_bytes: int, deadline: float, what: str):
    import httpx

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise FetchError("timeout", f"{what}: the total request deadline passed")
    try:
        with client.stream("GET", url, timeout=remaining) as response:
            body = _read_limited(response, max_bytes, deadline, what)
            return response, body
    except httpx.TimeoutException as exc:
        raise FetchError("timeout", f"{what}: {type(exc).__name__}") from exc
    except httpx.HTTPError as exc:
        raise FetchError("http_error", f"{what}: {type(exc).__name__}: {exc}") from exc


def _robots_allows(client, url: str, deadline: float, user_agent: str) -> None:
    """RFC 9309: 4xx = no rules (allowed); 5xx or unreachable = everything disallowed."""
    parts = urlsplit(url)
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    try:
        response, body = _get(client, robots_url, ROBOTS_MAX_BYTES, deadline, "robots.txt")
    except FetchError as exc:
        if exc.code == "too_large":
            body, response = b"", None  # RFC 9309 §2.5: read the start only; here, no rules
        else:
            raise FetchError(
                "robots_disallowed",
                f"robots.txt unreachable ({exc.code}: {exc.detail}): treated as disallowed",
            ) from exc
    if response is not None and response.status_code >= 500:
        raise FetchError(
            "robots_disallowed",
            f"robots.txt returned {response.status_code}: treated as disallowed (RFC 9309 §2.3.1.4)",
        )
    if response is not None and 400 <= response.status_code < 500:
        return
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.decode("utf-8", errors="replace").splitlines())
    if not parser.can_fetch(user_agent, url):
        raise FetchError("robots_disallowed", f"robots.txt disallows {clean_uri(url)}")


def fetch(
    url: str,
    *,
    allowlist,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    robots: bool = True,
    allow_private: bool = False,
    content_types=None,
    user_agent: str = DEFAULT_USER_AGENT,
    trust_env: bool = True,
) -> Fetched:
    """Fetch one URL safely and return its bytes, text and provenance.

    Enforces, on the first request and **every redirect hop**: the deny-by-default
    ``allowlist`` (a domain also covers its subdomains), SSRF protection (unless
    ``allow_private``), robots.txt (unless ``robots=False``), and caps on ``max_bytes``,
    ``timeout_s`` (total) and ``max_redirects``. ``content_types``, if given, is an
    iterable of allowed content-type prefixes (e.g. ``["text/html"]``); omit it to
    accept any. Raises ``FetchError`` with a ``code`` from ``ERROR_CODES``.

    ``allow_private`` and ``robots=False`` are for testing against a local server; a
    production caller leaves them at their safe defaults.
    """
    import httpx

    if not allowlist:
        raise FetchError("blocked_by_allowlist", "empty allowlist: nothing may be fetched")
    deadline = time.monotonic() + timeout_s
    warnings: list[str] = []
    current = url
    headers = {"User-Agent": user_agent}
    with httpx.Client(follow_redirects=False, headers=headers, trust_env=trust_env) as client:
        for _hop in range(max_redirects + 1):
            _check_url(current, allowlist, allow_private=allow_private)
            if robots:
                _robots_allows(client, current, deadline, user_agent)
            response, body = _get(client, current, max_bytes, deadline, "page")
            location = response.headers.get("location")
            if response.status_code in REDIRECT_CODES and location:
                current = urljoin(current, location)
                continue
            break
        else:
            raise FetchError("http_error", f"more than {max_redirects} redirects")

    if response.status_code >= 400:
        raise FetchError("http_error", f"HTTP {response.status_code} at {clean_uri(current)}")
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_types is not None and not any(content_type == t or content_type.startswith(t) for t in content_types):
        raise FetchError("unsupported_content_type", f"{content_type or '(none)'} not in {list(content_types)}")

    encoding = response.encoding or "utf-8"
    try:
        text = body.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        text = body.decode("utf-8", errors="replace")
        warnings.append("decode_errors_replaced")
    if current != url:
        warnings.append("redirected")
    return Fetched(
        url=clean_uri(url),
        final_url=clean_uri(current),
        status=response.status_code,
        content_type=content_type,
        content=body,
        text=text,
        content_hash=sha256(body).hexdigest(),
        warnings=warnings,
    )
