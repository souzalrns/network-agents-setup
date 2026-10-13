"""F2: primitiva `fetch` (ADR-INGESTION-PRIMITIVES §2-§3), a partir do `scrape.yml` do MCP.

Contrato:

    fetch(uri, allowlist, limites) -> {"content": str, "source_meta": dict, "warnings": [str]}

O que acrescenta ao `scrape.yml` (ANM:.github/workflows/scrape.yml, que lia a página inteira,
sem allowlist nem robots, e escrevia directamente na tabela `scrapes` do Supabase):
- **allowlist** de domínios (o domínio e os subdomínios), verificada em cada redirect;
- **robots.txt** (RFC 9309): 4xx = sem regras; 5xx ou inacessível = tudo proibido;
- **sem endereços privados** (SSRF): loopback, rede privada, link-local, multicast,
  reservados. Limitação conhecida: o nome é resolvido aqui e outra vez pelo httpx (DNS
  rebinding fica fora do F2a);
- **limites**: tamanho (lido em streaming, nunca a página inteira), prazo total do pedido
  (trava respostas lentas em gotas), redirects, content-type HTML;
- **HTML → Markdown** pelo mesmo adapter MarkItDown do F1 (`HtmlConverter`, `strict=True`), no
  processo filho com timeout e limite de memória (T6d);
- **proveniência**: `uri` (sem credenciais nem fragmento), `final_url`, `http_status`,
  `content_type`, `retrieved_at`, `content_hash`;
- **saída pelo T6**: com `--out-dir`, grava pelo `write_ingested` do F1 (`.md` + `.meta.yaml`).
  Nunca escreve no Supabase.

Fora do F2a (registado no `PENDENCIAS_T6.md`): o fallback Playwright para páginas feitas em
JavaScript, o Crawl4AI (só se superar isto, com evidência) e o `discover`.

Uso (só lê e imprime JSON; com `--out-dir` grava os 2 ficheiros):

    python scripts/web_fetch.py https://arxiv.org/abs/2401.00001 --area research [--out-dir DIR]
    python scripts/web_fetch.py https://arxiv.org/abs/2401.00001 --area research --allow arxiv.org

F2-ALLOW-1 (P-25 = A): `--area` é obrigatória e dá a allowlist da área
(`config/web-allowlist.yaml`); um `--allow` só a estreita (tem de caber nela).
Regras: `runner/plan_runner/web_allowlist.py`.

Núcleo de *fetch seguro* devolvido em 2026-10-13 (flywheel,
docs/initiatives/REPO-EVAL-PLAYBOOK.md): o laço de pedidos de `fetch()` — allowlist
deny-by-default, SSRF e robots.txt re-verificados a cada redirect, tectos de tamanho, tempo
e redirects — vem do pacote publicado `fetchtron` (PyPI, extraído de `oss/fetchtron`), tal
como `clean_uri`, `host_allowed` e `is_public_address`. Aqui fica a cola do runner: a
área→allowlist (`web_allowlist`), o contrato de erros em PT (`FetchError`, com os códigos
do T6), a conversão HTML→Markdown do T6 (MarkItDown) e a proveniência. `check_url` e
`robots_allows` ficam por serem a sonda do `scripts/check_web_allowlist.py` (que não lê o
corpo da página).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import socket
import sys
import tempfile
import time
import urllib.robotparser
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import fetchtron
from fetchtron import clean_uri, host_allowed, is_public_address

ERROR_CODES = (
    # ADR §3, item 6 (fetch)
    "blocked_by_allowlist",
    "robots_disallowed",
    "timeout",
    "http_error",
    "too_large",
    "empty_content",
    # F2a: extensões registadas no ADR §9
    "invalid_uri",
    "blocked_private_address",
    "unsupported_content_type",
    "conversion_failed",
)

DEFAULT_TIMEOUT_S = 20.0  # o do scrape.yml
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 5
ROBOTS_MAX_BYTES = 512 * 1024  # RFC 9309 §2.5: pelo menos 500 KiB
HTML_TYPES = ("text/html", "application/xhtml+xml")
REDIRECT_CODES = (301, 302, 303, 307, 308)
USER_AGENT = "network-agents-setup-fetch/1.0 (+https://github.com/souzalrns/network-agents-setup)"


class FetchError(Exception):
    """Erro tipado do `fetch`; `code` é um dos ERROR_CODES."""

    def __init__(self, code: str, message: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"código de erro fora do contrato: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = message


REPO_ROOT = Path(__file__).resolve().parents[1]  # onde está o config/web-allowlist.yaml


def _load_web_allowlist():
    """`runner/plan_runner/web_allowlist.py` pelo caminho (o script corre fora do pacote)."""
    path = Path(__file__).resolve().parents[1] / "runner" / "plan_runner" / "web_allowlist.py"
    spec = importlib.util.spec_from_file_location("web_allowlist", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("web_allowlist", mod)
    spec.loader.exec_module(mod)
    return mod


def _load_ingest_document():
    name = "ingest_document"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().with_name("ingest_document.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # o @dataclass precisa do módulo registado
    spec.loader.exec_module(module)
    return module


# --- URL, allowlist e endereços ----------------------------------------------------------


def check_url(url: str, allowlist, *, allow_private: bool = False) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise FetchError("invalid_uri", f"só http/https com host: {clean_uri(url)}")
    if not host_allowed(parts.hostname, allowlist):
        raise FetchError(
            "blocked_by_allowlist", f"{parts.hostname} não está na allowlist {list(allowlist)}"
        )
    if allow_private:
        return
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise FetchError("http_error", f"o nome {parts.hostname} não resolve: {exc}") from exc
    for info in infos:
        ip = info[4][0]
        if not is_public_address(ip):
            raise FetchError(
                "blocked_private_address", f"{parts.hostname} resolve para {ip} (não é público)"
            )


# --- HTTP ---------------------------------------------------------------------------------


def _read_limited(response, max_bytes: int, deadline: float, what: str) -> bytes:
    declared = response.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise FetchError("too_large", f"{what}: Content-Length {declared} > tecto {max_bytes}")
    body = bytearray()
    for chunk in response.iter_bytes():
        body += chunk
        if len(body) > max_bytes:
            raise FetchError("too_large", f"{what}: passou de {max_bytes} bytes")
        if time.monotonic() > deadline:
            raise FetchError("timeout", f"{what}: o prazo total do pedido acabou")
    return bytes(body)


def _get(client, url: str, max_bytes: int, deadline: float, what: str):
    import httpx

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise FetchError("timeout", f"{what}: o prazo total do pedido acabou")
    try:
        with client.stream("GET", url, timeout=remaining) as response:
            body = _read_limited(response, max_bytes, deadline, what)
            return response, body
    except httpx.TimeoutException as exc:
        raise FetchError("timeout", f"{what}: {type(exc).__name__}") from exc
    except httpx.HTTPError as exc:
        raise FetchError("http_error", f"{what}: {type(exc).__name__}: {exc}") from exc


def robots_allows(client, url: str, deadline: float, user_agent: str = USER_AGENT) -> None:
    """RFC 9309: 4xx = sem regras (permitido); 5xx ou inacessível = tudo proibido."""
    parts = urlsplit(url)
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    try:
        response, body = _get(client, robots_url, ROBOTS_MAX_BYTES, deadline, "robots.txt")
    except FetchError as exc:
        if exc.code == "too_large":
            body, response = b"", None  # RFC 9309 §2.5: lê só o início; aqui, sem regras
        else:
            raise FetchError(
                "robots_disallowed",
                f"robots.txt inacessível ({exc.code}: {exc.detail}): tratado como proibido",
            ) from exc
    if response is not None and 500 <= response.status_code:
        raise FetchError(
            "robots_disallowed",
            f"robots.txt deu {response.status_code}: tratado como proibido (RFC 9309 §2.3.1.4)",
        )
    if response is not None and 400 <= response.status_code < 500:
        return
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.decode("utf-8", errors="replace").splitlines())
    if not parser.can_fetch(user_agent, url):
        raise FetchError("robots_disallowed", f"o robots.txt proíbe {clean_uri(url)}")


# --- fetch --------------------------------------------------------------------------------


def fetch(
    uri: str,
    *,
    allowlist: list[str] | tuple[str, ...],
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    robots: bool = True,
    allow_private: bool = False,
    trust_env: bool = True,
    converter=None,
) -> dict[str, Any]:
    """Vai buscar 1 página HTML e devolve Markdown com proveniência. Levanta `FetchError`.

    `allow_private` e `robots=False` existem para os testes (servidor local); a CLI não os
    expõe.
    """
    if not allowlist:
        raise FetchError("blocked_by_allowlist", "allowlist vazia: nada pode ser buscado")
    ing = _load_ingest_document()
    try:
        got = fetchtron.fetch(
            uri,
            allowlist=allowlist,
            timeout_s=timeout_s,
            max_bytes=max_bytes,
            max_redirects=max_redirects,
            robots=robots,
            allow_private=allow_private,
            content_types=HTML_TYPES,
            user_agent=USER_AGENT,
            trust_env=trust_env,
        )
    except fetchtron.FetchError as exc:
        raise FetchError(exc.code, exc.detail) from exc
    url = got.final_url
    html = got.text
    redirected = "redirected" in got.warnings
    warnings = [w for w in got.warnings if w != "redirected"]

    if converter is None:
        converter = partial(ing.isolated_converter, timeout_s=max(timeout_s, 30.0))
    with tempfile.TemporaryDirectory(prefix="fetch-") as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        try:
            converted = converter(page, "html")
        except Exception as exc:  # o conversor pode vir de outra cópia do módulo: pelo `code`
            code = getattr(exc, "code", None)
            detail = getattr(exc, "detail", None) or f"{type(exc).__name__}: {exc}"
            raise FetchError(
                "timeout" if code == "timeout" else "conversion_failed", detail
            ) from exc
    content = ing.normalize(converted.markdown)
    if not content:
        raise FetchError("empty_content", f"a página {clean_uri(url)} não deu texto")
    warnings.extend(converted.warnings)
    title = (converted.title or "").strip()
    if not title:
        title = urlsplit(url).hostname or "página"
        warnings.append("title_from_host")
    if redirected:
        warnings.append("redirected")

    source_meta = {
        "uri": clean_uri(uri),
        "final_url": clean_uri(url),
        "title": title,
        "document_type": "html",
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "content_hash": sha256(content.encode("utf-8")).hexdigest(),
        "status": "active",
        "http_status": got.status,
        "content_type": got.content_type,
    }
    return {"content": content, "source_meta": source_meta, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/web_fetch.py",
        description="Busca 1 página HTML de um domínio da allowlist e imprime o JSON.",
    )
    parser.add_argument("url")
    parser.add_argument(
        "--allow", action="append", help="estreita a allowlist (repetível); tem de caber na área"
    )
    parser.add_argument("--area", help="área do config/web-allowlist.yaml (obrigatória, F2-ALLOW-1)")
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--out-dir", help="grava <nome>.md e <nome>.meta.yaml (pelo T6)")
    parser.add_argument("--name")
    parser.add_argument("--overwrite", action="store_true")
    try:
        opts = parser.parse_args(argv)
    except SystemExit:
        return 2
    if not opts.area:
        print("error: --area <área> é obrigatória (config/web-allowlist.yaml)", file=sys.stderr)
        return 2
    wa = _load_web_allowlist()
    try:
        allowlist, policy_warnings = wa.resolve_allowlist(REPO_ROOT, opts.area, opts.allow)
    except wa.AllowlistError as exc:
        # recusado antes de qualquer pedido de rede
        print(json.dumps({"error": "blocked_by_allowlist", "message": str(exc)}, ensure_ascii=False))
        return 1
    try:
        result = fetch(
            opts.url, allowlist=allowlist, timeout_s=opts.timeout_s, max_bytes=opts.max_bytes
        )
    except FetchError as exc:
        print(json.dumps({"error": exc.code, "message": exc.detail}, ensure_ascii=False))
        return 1
    result["warnings"] = list(result.get("warnings") or []) + policy_warnings
    if opts.out_dir:
        ing = _load_ingest_document()
        parts = urlsplit(result["source_meta"]["final_url"])
        name = opts.name or ing.slugify(f"{parts.hostname} {parts.path}")
        try:
            md, meta = ing.write_ingested(result, opts.out_dir, name, overwrite=opts.overwrite)
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps({"md": md.as_posix(), "meta": meta.as_posix()}, ensure_ascii=False))
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
