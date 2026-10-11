"""fetchguard: the guardrails of a safe GET (allowlist, SSRF, robots, caps)."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest

from fetchguard import FetchError, clean_uri, fetch, host_allowed, is_public_address
from fetchguard.cli import main

# ---- pure guards (no network) ----


def test_is_public_address():
    assert is_public_address("8.8.8.8") is True
    assert is_public_address("127.0.0.1") is False  # loopback
    assert is_public_address("10.0.0.1") is False  # private
    assert is_public_address("169.254.169.254") is False  # link-local (cloud metadata)
    assert is_public_address("::1") is False


def test_host_allowed_covers_subdomains():
    assert host_allowed("example.org", ["example.org"]) is True
    assert host_allowed("www.example.org", ["example.org"]) is True
    assert host_allowed("evil.org", ["example.org"]) is False
    assert host_allowed("notexample.org", ["example.org"]) is False  # not a subdomain


def test_clean_uri_strips_credentials_and_fragment():
    assert clean_uri("https://u:p@example.org/a?q=1#frag") == "https://example.org/a?q=1"


def test_empty_allowlist_blocks():
    with pytest.raises(FetchError) as e:
        fetch("https://example.org/", allowlist=[])
    assert e.value.code == "blocked_by_allowlist"


def test_offlist_host_blocked_before_any_request():
    with pytest.raises(FetchError) as e:
        fetch("https://evil.test/", allowlist=["example.org"])
    assert e.value.code == "blocked_by_allowlist"


def test_non_http_scheme_blocked():
    with pytest.raises(FetchError) as e:
        fetch("file:///etc/passwd", allowlist=["passwd"])
    assert e.value.code == "invalid_uri"


# ---- local server ----


class _Handler(BaseHTTPRequestHandler):
    routes: ClassVar[dict] = {}

    def log_message(self, *a):  # silence
        pass

    def do_GET(self):
        spec = self.routes.get(self.path)
        if spec is None:
            self.send_response(404)
            self.end_headers()
            return
        status, headers, body = spec
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv, f"http://localhost:{srv.server_port}"
    srv.shutdown()


def _routes(srv, mapping):
    _Handler.routes = mapping


def test_success(server):
    srv, base = server
    _routes(
        srv,
        {
            "/robots.txt": (404, {}, b""),
            "/p": (200, {"Content-Type": "text/html; charset=utf-8"}, b"<h1>hi</h1>"),
        },
    )
    got = fetch(f"{base}/p", allowlist=["localhost"], allow_private=True)
    assert got.status == 200
    assert got.content_type == "text/html"
    assert got.text == "<h1>hi</h1>"
    assert got.content_hash and got.warnings == []


def test_ssrf_blocks_localhost_by_default(server):
    srv, base = server
    _routes(srv, {"/robots.txt": (404, {}, b""), "/p": (200, {}, b"x")})
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/p", allowlist=["localhost"])  # allow_private defaults to False
    assert e.value.code == "blocked_private_address"


def test_robots_disallow(server):
    srv, base = server
    _routes(
        srv,
        {
            "/robots.txt": (200, {"Content-Type": "text/plain"}, b"User-agent: *\nDisallow: /"),
            "/p": (200, {"Content-Type": "text/html"}, b"x"),
        },
    )
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/p", allowlist=["localhost"], allow_private=True)
    assert e.value.code == "robots_disallowed"


def test_robots_5xx_is_disallowed(server):
    srv, base = server
    _routes(srv, {"/robots.txt": (503, {}, b""), "/p": (200, {}, b"x")})
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/p", allowlist=["localhost"], allow_private=True)
    assert e.value.code == "robots_disallowed"


def test_robots_404_allows(server):
    srv, base = server
    _routes(srv, {"/robots.txt": (404, {}, b""), "/p": (200, {"Content-Type": "text/html"}, b"ok")})
    got = fetch(f"{base}/p", allowlist=["localhost"], allow_private=True)
    assert got.text == "ok"


def test_too_large(server):
    srv, base = server
    _routes(srv, {"/robots.txt": (404, {}, b""), "/p": (200, {"Content-Type": "text/html"}, b"x" * 5000)})
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/p", allowlist=["localhost"], allow_private=True, max_bytes=1000)
    assert e.value.code == "too_large"


def test_content_type_filter(server):
    srv, base = server
    _routes(srv, {"/robots.txt": (404, {}, b""), "/p": (200, {"Content-Type": "text/plain"}, b"x")})
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/p", allowlist=["localhost"], allow_private=True, content_types=["text/html"])
    assert e.value.code == "unsupported_content_type"


def test_redirect_followed_within_allowlist(server):
    srv, base = server
    _routes(
        srv,
        {
            "/robots.txt": (404, {}, b""),
            "/a": (302, {"Location": "/b"}, b""),
            "/b": (200, {"Content-Type": "text/html"}, b"final"),
        },
    )
    got = fetch(f"{base}/a", allowlist=["localhost"], allow_private=True)
    assert got.text == "final" and got.final_url.endswith("/b")
    assert "redirected" in got.warnings


def test_redirect_to_offlist_host_blocked(server):
    srv, base = server
    _routes(
        srv,
        {
            "/robots.txt": (404, {}, b""),
            "/a": (302, {"Location": "http://evil.test/x"}, b""),
        },
    )
    with pytest.raises(FetchError) as e:
        fetch(f"{base}/a", allowlist=["localhost"], allow_private=True)
    assert e.value.code == "blocked_by_allowlist"


# ---- CLI ----


def test_cli_requires_allow(capsys):
    assert main(["get", "https://example.org/"]) == 2
    assert "deny-by-default" in capsys.readouterr().err


def test_cli_fetcherror_exit_1(capsys):
    assert main(["get", "https://evil.test/", "--allow", "example.org"]) == 1
    assert "blocked_by_allowlist" in capsys.readouterr().err


def test_cli_success(server, capsys):
    srv, base = server
    _routes(srv, {"/robots.txt": (404, {}, b""), "/p": (200, {"Content-Type": "text/html"}, b"hello")})
    # allow_private is not exposed on the CLI; drive success through the API-backed path
    # by pointing at a public-looking host is not possible here, so assert the CLI wiring
    # via the API in test_success; here we only check the deny-by-default and error paths.
    assert main(["get", f"{base}/p", "--allow", "localhost"]) == 1  # SSRF-blocked (localhost)
    assert "blocked_private_address" in capsys.readouterr().err


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "fetchguard" in capsys.readouterr().out
