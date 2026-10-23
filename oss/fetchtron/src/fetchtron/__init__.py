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

DNS rebinding (0.2.0): on every hop the host is resolved **once**, every address must be
public, and the connection goes to that checked address (``Host`` and TLS SNI/certificate
still use the hostname), so a second, different DNS answer is never used. Behind an
environment proxy the proxy resolves the name instead; then the IP is not pinned and the
result carries the warning ``dns_not_pinned_proxy`` (see POSITIONING.md).
"""

from __future__ import annotations

import ipaddress
import socket
import time
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from hashlib import sha256
from urllib.parse import urljoin, urlsplit, urlunsplit

__version__ = "0.2.0"

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
DEFAULT_USER_AGENT = "fetchtron/0.2 (+https://pypi.org/project/fetchtron/)"

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


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _check_url(url: str, allowlist, *, allow_private: bool) -> list[str]:
    """Validate scheme + allowlist, resolve the host **once** and return its addresses.

    Every address must be public (unless ``allow_private``). The caller connects to one of
    these addresses (``_pinned``), never to a second DNS answer: that closes the
    DNS-rebinding window between this check and the connection.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise FetchError("invalid_uri", f"only http/https with a host: {clean_uri(url)}")
    if not host_allowed(parts.hostname, allowlist):
        raise FetchError("blocked_by_allowlist", f"{parts.hostname} is not in the allowlist {list(allowlist)}")
    port = parts.port or _default_port(parts.scheme)
    try:
        infos = socket.getaddrinfo(parts.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise FetchError("http_error", f"the name {parts.hostname} does not resolve: {exc}") from exc
    ips: list[str] = []
    for info in infos:
        ip = info[4][0].split("%")[0]  # drop an IPv6 zone id
        if not allow_private and not is_public_address(ip):
            raise FetchError("blocked_private_address", f"{parts.hostname} resolves to {ip} (not public)")
        if ip not in ips:
            ips.append(ip)
    if not ips:
        raise FetchError("http_error", f"the name {parts.hostname} has no address")
    return sorted(ips, key=lambda ip: ":" in ip)  # IPv4 first (IPv6 is often unroutable)


def _proxied(url: str, trust_env: bool) -> bool:
    """True if an environment proxy would carry this URL (then the proxy resolves the name)."""
    if not trust_env:
        return False
    parts = urlsplit(url)
    proxies = urllib.request.getproxies_environment()
    if not (proxies.get(parts.scheme) or proxies.get("all")):
        return False
    return not urllib.request.proxy_bypass_environment(parts.hostname or "", proxies)


def _pinned(url: str, ip: str) -> tuple[str, dict, dict]:
    """The request for ``url`` sent to ``ip``: (url with the IP, headers, httpx extensions).

    ``Host`` keeps the name (virtual hosting) and, for https, the ``sni_hostname``
    extension makes httpcore use the name for SNI **and** certificate verification.
    """
    parts = urlsplit(url)
    host = parts.hostname or ""
    ip_host = f"[{ip}]" if ":" in ip else ip
    netloc = ip_host if parts.port is None else f"{ip_host}:{parts.port}"
    if "@" in parts.netloc:  # keep user:pass for httpx's basic auth
        netloc = f"{parts.netloc.rsplit('@', 1)[0]}@{netloc}"
    headers = {"Host": host if parts.port is None else f"{host}:{parts.port}"}
    extensions = {"sni_hostname": host} if parts.scheme == "https" else {}
    return urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, "")), headers, extensions


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


def _get(client, url: str, max_bytes: int, deadline: float, what: str, ips=None):
    """GET ``url``; with ``ips``, connect only to those checked addresses (in order).

    The next address is tried only when the connection itself fails (e.g. an unroutable
    IPv6 record); any other error is final.
    """
    import httpx

    targets = [_pinned(url, ip) for ip in ips] if ips else [(url, {}, {})]
    for i, (target, headers, extensions) in enumerate(targets):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FetchError("timeout", f"{what}: the total request deadline passed")
        try:
            with client.stream("GET", target, headers=headers, extensions=extensions, timeout=remaining) as response:
                body = _read_limited(response, max_bytes, deadline, what)
                return response, body
        except httpx.ConnectError as exc:
            if i + 1 < len(targets):
                continue
            raise FetchError("http_error", f"{what}: {type(exc).__name__}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise FetchError("timeout", f"{what}: {type(exc).__name__}") from exc
        except httpx.HTTPError as exc:
            raise FetchError("http_error", f"{what}: {type(exc).__name__}: {exc}") from exc
    raise AssertionError("unreachable")  # pragma: no cover


def _robots_allows(client, url: str, deadline: float, user_agent: str, ips=None) -> None:
    """RFC 9309: 4xx = no rules (allowed); 5xx or unreachable = everything disallowed."""
    parts = urlsplit(url)
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    try:
        response, body = _get(client, robots_url, ROBOTS_MAX_BYTES, deadline, "robots.txt", ips)
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
    ``allow_private``) with the connection pinned to the checked address (DNS rebinding;
    not behind an environment proxy, which resolves the name itself: warning
    ``dns_not_pinned_proxy``), robots.txt (unless ``robots=False``), and caps on
    ``max_bytes``, ``timeout_s`` (total) and ``max_redirects``. ``content_types``, if given, is an
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
            ips = _check_url(current, allowlist, allow_private=allow_private)
            if _proxied(current, trust_env):
                ips = None  # the proxy resolves the name; pinning would bypass or break it
                if "dns_not_pinned_proxy" not in warnings:
                    warnings.append("dns_not_pinned_proxy")
            if robots:
                _robots_allows(client, current, deadline, user_agent, ips)
            response, body = _get(client, current, max_bytes, deadline, "page", ips)
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
