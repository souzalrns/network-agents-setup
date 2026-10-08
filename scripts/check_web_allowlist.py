"""Sonda da allowlist do `fetch` (F2-ALLOW-1): cada domínio de cada área, com rede real.

Para cada (área, domínio) do `config/web-allowlist.yaml`, pede `https://<domínio>/` com as
mesmas regras do `scripts/web_fetch.py` (allowlist da ÁREA em cada redirect, SSRF, robots.txt
na página final) e diz o que o `fetch --area <área>` encontraria:

- `ok`: a raiz responde < 400, todos os saltos ficam na área e o robots.txt deixa;
- `fora`: um redirect sai da lista da área (o `fetch` daria `blocked_by_allowlist`);
- `robots_disallowed`, `http_error`, `timeout`, `blocked_private_address`: o código do `fetch`.

É INFORMATIVA: serve de evidência para o maestro decidir correcções à lista (PENDENCIAS §10).
Não muda o ficheiro e, sem `--strict`, sai sempre com 0. Só a raiz de cada domínio é pedida
(um GET, sem ler o corpo), mais o robots.txt do host final: 2 a 3 pedidos por domínio.

    python scripts/check_web_allowlist.py                   # tabela Markdown no stdout
    python scripts/check_web_allowlist.py --area finance    # uma área
    python scripts/check_web_allowlist.py --json out.json   # também em JSON
    python scripts/check_web_allowlist.py --strict          # sai com 1 se algum não der `ok`

No GitHub Actions, a tabela vai também para o `$GITHUB_STEP_SUMMARY`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wf = _load("web_fetch", "scripts/web_fetch.py")
wa = wf._load_web_allowlist()


def probe_url(
    url: str,
    allowlist: list[str],
    *,
    client,
    timeout_s: float = 15.0,
    max_redirects: int = wf.DEFAULT_MAX_REDIRECTS,
    allow_private: bool = False,
    robots: bool = True,
) -> dict[str, Any]:
    """O que o `fetch` encontraria em `url` com esta allowlist, sem ler o corpo da página.

    `allow_private` existe para os testes (servidor local), como no `fetch`."""
    import httpx

    deadline = time.monotonic() + timeout_s
    hops: list[str] = []
    status: int | None = None

    def result(verdict: str, detail: str = "") -> dict[str, Any]:
        return {"verdict": verdict, "status": status, "hops": hops, "detail": detail,
                "final_host": urlsplit(hops[-1]).hostname if hops else None}

    for _hop in range(max_redirects + 1):
        hops.append(wf.clean_uri(url))
        try:
            wf.check_url(url, allowlist, allow_private=allow_private)
        except wf.FetchError as exc:
            return result("fora" if exc.code == "blocked_by_allowlist" else exc.code, exc.detail)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return result("timeout", "o prazo total acabou")
        try:
            with client.stream("GET", url, timeout=remaining) as response:
                status = response.status_code
                location = response.headers.get("location")
        except httpx.TimeoutException as exc:
            return result("timeout", type(exc).__name__)
        except httpx.HTTPError as exc:
            return result("http_error", f"{type(exc).__name__}: {exc}")
        if status in wf.REDIRECT_CODES and location:
            url = urljoin(url, location)
            continue
        break
    else:
        return result("http_error", f"mais de {max_redirects} redirects")
    if status >= 400:
        return result("http_error", f"HTTP {status}")
    if robots:
        try:
            wf.robots_allows(client, url, deadline)
        except wf.FetchError as exc:
            return result(exc.code, exc.detail)
    return result("ok")


def probe_all(areas: dict[str, list[str]], *, workers: int = 8, timeout_s: float = 15.0) -> list[dict]:
    import httpx

    headers = {"User-Agent": wf.USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    def one(item: tuple[str, str]) -> dict:
        area, domain = item
        with httpx.Client(follow_redirects=False, headers=headers) as client:
            row = probe_url(f"https://{domain}/", areas[area], client=client, timeout_s=timeout_s)
        return {"area": area, "domain": domain, **row}

    items = [(a, d) for a, ds in areas.items() for d in ds]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, items))


def _cell(text: Any) -> str:
    return str(text if text is not None else "—").replace("|", "/").replace("\n", " ")


def to_markdown(rows: list[dict], empty_areas: list[str]) -> str:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: (kv[0] != "ok", kv[0])))
    lines = [
        "## Sonda da allowlist do fetch (F2-ALLOW-1)",
        "",
        f"{len(rows)} pares (área, domínio): {summary or 'nenhum'}."
        + (f" Áreas vazias (deny-by-default): {', '.join(empty_areas)}." if empty_areas else ""),
        "",
        "Informativa: uma linha que não dá `ok` é evidência para o maestro, não uma correcção automática.",
        "",
        "| Área | Domínio | Resultado | HTTP | Host final | Saltos | Detalhe |",
        "|---|---|---|---|---|---|---|",
    ]
    order = sorted(rows, key=lambda r: (r["verdict"] == "ok", r["area"], r["domain"]))
    for r in order:
        lines.append(
            f"| {_cell(r['area'])} | {_cell(r['domain'])} | {_cell(r['verdict'])} | {_cell(r['status'])} "
            f"| {_cell(r['final_host'])} | {len(r['hops']) - 1} | {_cell(r['detail'])[:160]} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python scripts/check_web_allowlist.py", description=__doc__.splitlines()[0])
    parser.add_argument("--area", action="append", help="só estas áreas (repetível)")
    parser.add_argument("--json", help="grava também os resultados em JSON neste caminho")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout-s", type=float, default=15.0)
    parser.add_argument("--strict", action="store_true", help="sai com 1 se algum par não der `ok`")
    try:
        opts = parser.parse_args(argv)
    except SystemExit:
        return 2
    path = REPO_ROOT / wa.ALLOWLIST_FILE
    data = wa.load(path)
    areas = data.get("areas") if isinstance(data.get("areas"), dict) else None
    if areas is None:
        print(f"error: {wa.ALLOWLIST_FILE.as_posix()} sem `areas`", file=sys.stderr)
        return 2
    wanted = opts.area or list(areas)
    unknown = [a for a in wanted if a not in areas]
    if unknown:
        print(f"error: área(s) fora de {wa.ALLOWLIST_FILE.as_posix()}: {', '.join(unknown)}", file=sys.stderr)
        return 2
    chosen = {a: list(areas[a] or []) for a in wanted}
    rows = probe_all({a: d for a, d in chosen.items() if d}, workers=opts.workers, timeout_s=opts.timeout_s)
    report = to_markdown(rows, [a for a, d in chosen.items() if not d])
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(report)
    if opts.json:
        Path(opts.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if opts.strict and any(r["verdict"] != "ok" for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
