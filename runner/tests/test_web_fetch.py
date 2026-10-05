"""F2: primitiva `fetch` (scripts/web_fetch.py) contra um servidor HTTP local, sem rede externa.

O servidor corre numa thread em 127.0.0.1, por isso os testes passam `allow_private=True`
(que a CLI não expõe) e `trust_env=False` (ignorar proxies do ambiente). Cada rota cobre um
caso do contrato do ADR §3 (fetch): allowlist em cada redirect, robots.txt (RFC 9309),
tectos de bytes e de tempo, content-type, HTTP 5xx, página vazia, charset, proveniência.

A lógica de rede usa um conversor falso (corre sem o `markitdown`); a conversão real
HTML → Markdown e a saída pelo T6 ficam nos testes com `require("markitdown")`.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests.optional_deps import require

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ing = _load("ingest_document", "scripts/ingest_document.py")
wf = _load("web_fetch", "scripts/web_fetch.py")

PAGE = (
    "<!doctype html><html><head><title>Página sintética</title>"
    "<script>alert(1)</script></head><body>"
    "<h1>Relatório sintético</h1><p>Parágrafo de teste do fetch.</p>"
    "<ul><li>Primeiro</li><li>Segundo</li></ul>"
    "<table><tr><th>Formato</th><th>Estado</th></tr><tr><td>HTML</td><td>testado</td></tr></table>"
    "</body></html>"
)
ALLOW = ["127.0.0.1"]


class _Handler(BaseHTTPRequestHandler):
    robots_mode = "normal"  # normal | 404 | 500 | grande

    def log_message(self, *args):  # silencioso nos testes
        pass

    def _send(
        self, status: int, body: bytes = b"", ctype: str = "text/html; charset=utf-8", extra=None
    ):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (API do http.server)
        path = self.path
        if path == "/robots.txt":
            mode = type(self).robots_mode
            if mode == "404":
                return self._send(404, b"nao ha", "text/plain")
            if mode == "500":
                return self._send(500, b"erro", "text/plain")
            if mode == "grande":
                return self._send(200, b"#" * (wf.ROBOTS_MAX_BYTES + 10), "text/plain")
            return self._send(200, b"User-agent: *\nDisallow: /privado/\n", "text/plain")
        if path in ("/ok.html", "/privado/x.html"):
            return self._send(200, PAGE.encode("utf-8"))
        if path == "/redir":
            return self._send(302, extra={"Location": "/ok.html"})
        if path == "/redir-ciclo":
            return self._send(302, extra={"Location": "/redir-ciclo"})
        if path == "/redir-fora":
            return self._send(302, extra={"Location": "http://fora.invalid/x"})
        if path == "/grande":
            return self._send(200, b"<p>" + b"x" * 5000 + b"</p>")
        if path == "/grande-sem-cl":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            for _ in range(50):
                self.wfile.write(b"<p>" + b"y" * 1000 + b"</p>")
            return None
        if path == "/lento":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            for _ in range(40):
                self.wfile.write(b"<p>gota</p>")
                self.wfile.flush()
                time.sleep(0.1)
            return None
        if path == "/erro":
            return self._send(500, b"<p>falhou</p>")
        if path == "/doc.pdf":
            return self._send(200, b"%PDF-1.4", "application/pdf")
        if path == "/vazio.html":
            return self._send(200, b"<html><body>   </body></html>")
        if path == "/latin1.html":
            body = "<html><body><p>ação e índice</p></body></html>".encode("iso-8859-1")
            return self._send(200, body, "text/html; charset=iso-8859-1")
        return self._send(404, b"<p>nao existe</p>")


@pytest.fixture
def server():
    _Handler.robots_mode = "normal"
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, args=(0.05,), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def _fake_converter(path: Path, document_type: str):
    assert document_type == "html"
    return ing.Converted(markdown=path.read_text(encoding="utf-8"), title="Título falso")


def _fetch(url: str, **kwargs):
    kwargs.setdefault("allowlist", ALLOW)
    kwargs.setdefault("allow_private", True)
    kwargs.setdefault("trust_env", False)
    kwargs.setdefault("converter", _fake_converter)
    return wf.fetch(url, **kwargs)


def _code(url: str, **kwargs) -> str:
    with pytest.raises(wf.FetchError) as exc:
        _fetch(url, **kwargs)
    return exc.value.code


# --- unidades sem rede ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("host", "ok"),
    [
        ("exemplo.org", True),
        ("www.exemplo.org", True),
        ("WWW.Exemplo.Org.", True),
        ("maliciosoexemplo.org", False),
        ("exemplo.org.malicioso.net", False),
    ],
)
def test_allowlist_dominio_e_subdominios(host: str, ok: bool) -> None:
    assert wf.host_allowed(host, ["exemplo.org"]) is ok


@pytest.mark.parametrize(
    ("ip", "public"),
    [
        ("8.8.8.8", True),
        ("127.0.0.1", False),
        ("10.0.0.5", False),
        ("192.168.1.1", False),
        ("169.254.169.254", False),  # metadados da cloud
        ("::1", False),
        ("0.0.0.0", False),
    ],
)
def test_enderecos_nao_publicos(ip: str, public: bool) -> None:
    assert wf.is_public_address(ip) is public


def test_clean_uri_tira_credenciais_e_fragmento() -> None:
    url = "https://user:segredo@Exemplo.org:8443/a/b?q=1#secção"
    assert wf.clean_uri(url) == "https://exemplo.org:8443/a/b?q=1"


@pytest.mark.parametrize("url", ["ftp://exemplo.org/x", "http:///sem-host", "file:///etc/passwd"])
def test_uri_invalido(url: str) -> None:
    with pytest.raises(wf.FetchError) as exc:
        wf.check_url(url, ["exemplo.org"])
    assert exc.value.code == "invalid_uri"


def test_por_omissao_recusa_enderecos_privados() -> None:
    with pytest.raises(wf.FetchError) as exc:
        wf.check_url("http://127.0.0.1/x", ["127.0.0.1"])
    assert exc.value.code == "blocked_private_address"


def test_allowlist_vazia_recusa_tudo() -> None:
    with pytest.raises(wf.FetchError) as exc:
        wf.fetch("https://exemplo.org/", allowlist=[])
    assert exc.value.code == "blocked_by_allowlist"


def test_codigo_fora_do_contrato() -> None:
    with pytest.raises(ValueError):
        wf.FetchError("inventado", "x")


# --- servidor local: caminho feliz e proveniência -------------------------------------------


def test_pagina_ok_com_proveniencia(server) -> None:
    out = _fetch(f"{server}/ok.html")
    meta = out["source_meta"]
    assert meta["uri"] == meta["final_url"] == f"{server}/ok.html"
    assert meta["document_type"] == "html"
    assert meta["http_status"] == 200
    assert meta["content_type"] == "text/html"
    assert meta["title"] == "Título falso"
    assert out["warnings"] == []
    assert "Relatório sintético" in out["content"]


def test_redirect_dentro_da_allowlist_regista_o_final(server) -> None:
    out = _fetch(f"{server}/redir")
    assert out["source_meta"]["final_url"] == f"{server}/ok.html"
    assert out["source_meta"]["uri"] == f"{server}/redir"
    assert "redirected" in out["warnings"]


def test_redirect_para_fora_da_allowlist_e_recusado(server) -> None:
    assert _code(f"{server}/redir-fora") == "blocked_by_allowlist"


def test_redirects_em_ciclo_param(server) -> None:
    assert _code(f"{server}/redir-ciclo", max_redirects=3) == "http_error"


# --- robots.txt -------------------------------------------------------------------------------


def test_robots_proibe_o_caminho(server) -> None:
    assert _code(f"{server}/privado/x.html") == "robots_disallowed"


def test_robots_404_e_sem_regras(server) -> None:
    _Handler.robots_mode = "404"
    assert _fetch(f"{server}/privado/x.html")["source_meta"]["http_status"] == 200


def test_robots_5xx_e_tudo_proibido(server) -> None:
    _Handler.robots_mode = "500"
    assert _code(f"{server}/ok.html") == "robots_disallowed"


def test_robots_acima_do_tecto_nao_bloqueia(server) -> None:
    _Handler.robots_mode = "grande"
    assert _fetch(f"{server}/ok.html")["source_meta"]["http_status"] == 200


# --- limites e erros ----------------------------------------------------------------------------


def test_content_length_acima_do_tecto(server) -> None:
    assert _code(f"{server}/grande", max_bytes=1000) == "too_large"


def test_streaming_sem_content_length_acima_do_tecto(server) -> None:
    assert _code(f"{server}/grande-sem-cl", max_bytes=10_000) == "too_large"


def test_resposta_lenta_esgota_o_prazo_total(server) -> None:
    inicio = time.monotonic()
    assert _code(f"{server}/lento", timeout_s=1.0) == "timeout"
    assert time.monotonic() - inicio < 3.5  # não esperou pelos ~4 s da resposta


def test_http_5xx(server) -> None:
    assert _code(f"{server}/erro") == "http_error"


def test_404(server) -> None:
    assert _code(f"{server}/nao-existe") == "http_error"


def test_content_type_nao_html(server) -> None:
    assert _code(f"{server}/doc.pdf") == "unsupported_content_type"


def test_pagina_vazia(server) -> None:
    def vazio(path, document_type):
        return ing.Converted(markdown="   \n", title="T")

    assert _code(f"{server}/vazio.html", converter=vazio) == "empty_content"


def test_charset_do_cabecalho(server) -> None:
    out = _fetch(f"{server}/latin1.html")
    assert "ação e índice" in out["content"]
    assert "decode_errors_replaced" not in out["warnings"]


def test_erro_de_conversao_vira_fetch_error(server) -> None:
    def falha(path, document_type):
        raise ing.IngestError("conversion_failed", "html estragado")

    assert _code(f"{server}/ok.html", converter=falha) == "conversion_failed"


def test_erro_tipado_de_outra_copia_do_modulo_e_reconhecido(server) -> None:
    # Regressão: o `fetch` reconhece o erro pelo `code`, não pela classe (outra cópia do
    # ingest_document em sys.modules tem outra classe IngestError).
    class OutraIngestError(Exception):
        code = "timeout"
        detail = "a conversão passou do tempo"

    def lento(path, document_type):
        raise OutraIngestError()

    assert _code(f"{server}/ok.html", converter=lento) == "timeout"


def test_excepcao_qualquer_do_conversor_vira_conversion_failed(server) -> None:
    def rebenta(path, document_type):
        raise RuntimeError("inesperado")

    with pytest.raises(wf.FetchError) as exc:
        _fetch(f"{server}/ok.html", converter=rebenta)
    assert exc.value.code == "conversion_failed"
    assert "RuntimeError: inesperado" in str(exc.value)


# --- conversão real e saída pelo T6 -------------------------------------------------------------


def test_conversao_real_html_para_markdown(server) -> None:
    require("markitdown")
    out = _fetch(f"{server}/ok.html", converter=None)
    content = out["content"]
    assert "# Relatório sintético" in content.splitlines()
    assert "Parágrafo de teste do fetch." in content
    assert "alert(1)" not in content  # <script> removido
    assert "| HTML | testado |" in content
    assert out["source_meta"]["title"] == "Página sintética"


def test_saida_pelo_t6_com_proveniencia_valida(server, tmp_path) -> None:
    require("markitdown")
    out = _fetch(f"{server}/ok.html", converter=None)
    md, meta = ing.write_ingested(out, tmp_path, "pagina")
    assert ing.validate_ingested(md) == []
    assert f"{server}/ok.html" in meta.read_text(encoding="utf-8")


def test_cli_exige_allowlist(capsys) -> None:
    assert wf.main(["https://exemplo.org/"]) == 2


def test_cli_erro_tipado(capsys) -> None:
    assert wf.main(["ftp://exemplo.org/x", "--allow", "exemplo.org"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "invalid_uri"
