"""F2-ALLOW-1: sonda da allowlist (scripts/check_web_allowlist.py), sem rede externa.

A lógica por URL (`probe_url`) corre contra um servidor HTTP local em 127.0.0.1, com
`allow_private=True` e `trust_env=False`, como os testes do `fetch`. A CLI corre com o
`probe_all` trocado por um falso: nada sai para a rede.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("check_web_allowlist", REPO_ROOT / "scripts" / "check_web_allowlist.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_web_allowlist"] = mod
    spec.loader.exec_module(mod)
    return mod


cw = _load()
ALLOW = ["127.0.0.1"]


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status: int, extra=None, body: bytes = b"<p>ok</p>", ctype: str = "text/html"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (API do http.server)
        routes = {
            "/robots.txt": lambda: self._send(200, body=b"User-agent: *\nDisallow: /privado/\n", ctype="text/plain"),
            "/ok": lambda: self._send(200),
            "/redir": lambda: self._send(301, {"Location": "/ok"}),
            "/fora": lambda: self._send(302, {"Location": "https://www.gov.br/x"}),
            "/ciclo": lambda: self._send(302, {"Location": "/ciclo"}),
            "/privado/x": lambda: self._send(200),
            "/redir-privado": lambda: self._send(302, {"Location": "/privado/x"}),
        }
        return routes.get(self.path, lambda: self._send(404))()


@pytest.fixture
def base():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()


@pytest.fixture
def client():
    with httpx.Client(follow_redirects=False, trust_env=False) as c:
        yield c


def _probe(url, client, allowlist=ALLOW, **kw):
    return cw.probe_url(url, allowlist, client=client, allow_private=True, timeout_s=5, **kw)


def test_ok_e_redirect_dentro_da_area(base, client):
    assert _probe(f"{base}/ok", client)["verdict"] == "ok"
    row = _probe(f"{base}/redir", client)
    assert row["verdict"] == "ok" and row["status"] == 200
    assert [h.rsplit("/", 1)[-1] for h in row["hops"]] == ["redir", "ok"]
    assert row["final_host"] == "127.0.0.1"


def test_redirect_para_fora_da_area_e_fora(base, client):
    row = _probe(f"{base}/fora", client)
    assert row["verdict"] == "fora" and row["status"] == 302
    assert row["final_host"] == "www.gov.br" and "www.gov.br" in row["detail"]


def test_http_robots_e_ciclo(base, client):
    assert _probe(f"{base}/nao-existe", client)["verdict"] == "http_error"
    row = _probe(f"{base}/redir-privado", client)  # o robots é verificado na página final
    assert row["verdict"] == "robots_disallowed"
    assert _probe(f"{base}/redir-privado", client, robots=False)["verdict"] == "ok"
    assert "redirects" in _probe(f"{base}/ciclo", client, max_redirects=2)["detail"]


def test_url_pedida_fora_da_lista_nem_sai(client):
    row = cw.probe_url("https://mau.org/", ["exemplo.org"], client=client, timeout_s=5)
    assert row["verdict"] == "fora" and row["status"] is None  # recusado antes do pedido


def test_markdown_poe_os_problemas_primeiro_e_escapa_barras():
    rows = [
        {"area": "research", "domain": "arxiv.org", "verdict": "ok", "status": 200, "hops": ["a"],
         "detail": "", "final_host": "arxiv.org"},
        {"area": "finance", "domain": "cvm.gov.br", "verdict": "fora", "status": 301, "hops": ["a", "b"],
         "detail": "x | y", "final_host": "www.gov.br"},
    ]
    md = cw.to_markdown(rows, ["software"])
    assert "2 pares (área, domínio): ok 1, fora 1." in md and "software" in md
    lines = [ln for ln in md.splitlines() if ln.startswith("| ")]
    assert lines[1].startswith("| finance | cvm.gov.br | fora | 301 | www.gov.br | 1 | x / y |")
    assert lines[2].startswith("| research | arxiv.org | ok |")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "web-allowlist.yaml").write_text(
        yaml.safe_dump({"version": 1, "areas": {"research": ["arxiv.org"], "software": []}}), encoding="utf-8"
    )
    monkeypatch.setattr(cw, "REPO_ROOT", tmp_path)
    seen: list = []

    def fake_probe_all(pairs, workers, timeout_s):
        seen.append(pairs)
        return [{"area": a, "domain": d, "verdict": "fora", "status": 301, "hops": ["x", "y"], "detail": "",
                 "final_host": "y"} for a, d, _ in pairs]

    monkeypatch.setattr(cw, "probe_all", fake_probe_all)
    return seen


def test_cli_informativa_resumo_e_json(repo, tmp_path, monkeypatch, capsys):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out_json = tmp_path / "out.json"
    assert cw.main(["--json", str(out_json)]) == 0  # informativa: 0 mesmo com `fora`
    assert repo == [[("research", "arxiv.org", ["arxiv.org"])]]  # a área vazia não é sondada
    assert "Áreas vazias (deny-by-default): software." in capsys.readouterr().out
    assert "| research | arxiv.org | fora |" in summary.read_text(encoding="utf-8")
    assert json.loads(out_json.read_text(encoding="utf-8"))[0]["final_host"] == "y"


def test_cli_strict_e_area_desconhecida(repo, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert cw.main(["--strict"]) == 1
    assert cw.main(["--area", "inventada"]) == 2
    assert cw.main(["--area", "software"]) == 0 and repo[-1] == []


def test_cli_candidato_corre_com_a_lista_que_teria(repo, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert cw.main(["--candidate", "research=export.arxiv.org", "--candidate", "software=x.org"]) == 0
    assert repo[-1] == [("research", "export.arxiv.org", ["arxiv.org", "export.arxiv.org"]),
                        ("software", "x.org", ["x.org"])]
    assert "## Sonda dos candidatos (ainda fora da allowlist)" in capsys.readouterr().out
    for bad in ("inventada=x.org", "research=https://x.org", "research"):
        assert cw.main(["--candidate", bad]) == 2


def test_raiz_sem_dns_tenta_o_www(monkeypatch):
    calls = []

    def fake_probe_url(url, allowlist, *, client, **kw):
        calls.append(url)
        if url == "https://www.bportugal.pt/":
            return {"verdict": "ok", "status": 200, "hops": [url], "detail": "", "final_host": "www.bportugal.pt"}
        return {"verdict": "http_error", "status": None, "hops": [url], "final_host": None,
                "detail": "o nome não resolve: [Errno -5]"}

    monkeypatch.setattr(cw, "probe_url", fake_probe_url)
    row = cw.probe_domain("bportugal.pt", ["bportugal.pt"], client=None)
    assert calls == ["https://bportugal.pt/", "https://www.bportugal.pt/"]
    assert row["verdict"] == "ok" and row["detail"] == "via www (bportugal.pt não resolve)"
    calls.clear()
    assert cw.probe_domain("www.x.org", ["x.org"], client=None)["verdict"] == "http_error"
    assert calls == ["https://www.x.org/"]  # já é www: não há 2.ª tentativa
