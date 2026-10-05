# `fetch`: páginas web com proveniência (F2a)

> Primitiva do contrato `docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md` (§2–§3, "RESEARCH ≠ WEB SCRAPING").
> Código: `scripts/web_fetch.py`. Testes: `runner/tests/test_web_fetch.py`. Estado da cadeia: `docs/initiatives/PENDENCIAS_T6.md`.

## 1. O que faz

```
fetch(uri, allowlist, limites) -> {"content": str, "source_meta": dict, "warnings": [str]}
```

```bash
pip install -r runner/requirements-ingest.txt   # o MarkItDown converte o HTML
python scripts/web_fetch.py https://exemplo.org/pagina --allow exemplo.org [--out-dir docs/knowledge/ingested]
```

- **Entrada:** 1 URL http/https e a allowlist de domínios (obrigatória; a CLI exige pelo menos 1 `--allow`).
- **Saída:** Markdown normalizado, mais o `source_meta`: `uri` (sem credenciais nem fragmento), `final_url` (depois dos redirects), `title`, `document_type: html`, `retrieved_at`, `content_hash`, `status`, `http_status` e `content_type`.
- **Para o L5:** com `--out-dir`, grava pelo `write_ingested` do F1 (`.md` + `.meta.yaml`), e daí segue o mesmo caminho do T6 (`INGEST-DOCUMENT.md` §7). **Nunca escreve no Supabase.**

## 2. Protecções (o que o `scrape.yml` não tinha)

O `ANM:.github/workflows/scrape.yml` lê a página inteira, sem allowlist nem robots, e grava directamente na tabela `scrapes` do Supabase, por fora do T6.

| Protecção | Como | Código quando falha |
|---|---|---|
| Allowlist | O domínio e os subdomínios (`exemplo.org` aceita `www.exemplo.org`, recusa `maliciosoexemplo.org`). Verificada **em cada redirect** | `blocked_by_allowlist` |
| robots.txt (RFC 9309) | Lido para cada host; 4xx = sem regras; 5xx ou inacessível = tudo proibido; acima de 512 KiB = sem regras | `robots_disallowed` |
| SSRF | Recusa nomes que resolvem para loopback, rede privada, link-local (incluindo os metadados da cloud, `169.254.169.254`), multicast, reservados | `blocked_private_address` |
| Tamanho | Content-Length acima do tecto é recusado logo; sem Content-Length, a leitura é em streaming e pára no tecto (5 MiB por omissão) | `too_large` |
| Tempo | Prazo **total** do pedido (20 s por omissão), verificado durante a leitura: trava respostas lentas em gotas | `timeout` |
| Redirects | No máximo 5, cada um verificado (allowlist, endereço, robots) | `http_error` |
| Tipo | Só `text/html` e `application/xhtml+xml` | `unsupported_content_type` |
| Conversão | O `HtmlConverter` do MarkItDown com `strict=True`, no processo filho com timeout e limite de memória (T6d). Sem `strict`, um HTML muito aninhado cairia em silêncio para texto simples | `conversion_failed` / `timeout` |
| Página sem texto | — | `empty_content` |
| URL inválida | Só http/https com host | `invalid_uri` |

**Avisos:** `redirected` (o `final_url` é diferente do `uri`), `title_from_host` (a página sem `<title>`) e `decode_errors_replaced` (charset inválido).

**Limitação conhecida:** o nome é resolvido para a verificação de SSRF e depois outra vez pelo httpx. Um ataque de DNS rebinding entre as 2 resoluções fica fora do F2a.

## 3. Evidência: corrida real (2026-10-06)

A sessão cloud só deixa sair para os hosts da política de rede: `example.com`, `python.org` e `wikipedia.org` deram 403 no proxy. O `pypi.org` está acessível, e a corrida real foi feita nele:

| URL | Resultado | Título | Chars | Tabelas | Tempo |
|---|---|---|---|---|---|
| `https://pypi.org/project/markitdown/` | 200 | `markitdown · PyPI` | 22 407 | sim | 1.2 s |
| `https://pypi.org/project/httpx/` | 200 | `httpx · PyPI` | 34 024 | sim | 1.4 s |
| `https://pypi.org/help/` | 200 | `Help · PyPI` | 52 258 | não | 1.5 s |
| `https://pypi.org/simple/` | `robots_disallowed` (o robots.txt real do pypi.org proíbe `/simple/`) | — | — | — | — |
| `https://pypi.org/project/markitdown/` com `--allow example.com` | `blocked_by_allowlist` | — | — | — | — |

Para correr contra outros hosts nesta sessão, é preciso acrescentá-los à política de rede do ambiente cloud. Na máquina do DEV não há essa restrição.

## 4. Testes (sem rede externa)

`runner/tests/test_web_fetch.py` arranca um servidor HTTP local numa thread, com uma rota por caso: robots (normal, 404, 500, grande), redirect (normal, em ciclo, para fora da allowlist), tamanho (com e sem Content-Length), resposta lenta, 5xx, 404, PDF, página vazia, latin-1, conversão real e saída pelo T6.

- A lógica de rede usa um conversor falso e corre sem o `markitdown` (jobs `test` e `test-slow`).
- A conversão real corre no job `test-ingest`.
- Verificação por mutação: sem o prazo total, o teste da resposta lenta falha; sem a verificação da allowlist por redirect, o teste do redirect para fora falha.

## 5. Fora do F2a

| O quê | Porquê | Onde fica |
|---|---|---|
| Fallback Playwright para páginas feitas em JavaScript (o `scrape.yml` tem-no) | Pesado (Chromium); só com caso real que o justifique | F2 canónico |
| Crawl4AI `>=0.9.3` | Decisão canónica: só se superar isto, com evidência | F2 canónico |
| `discover` (pesquisa) | Precisa de uma API de pesquisa (custo ou chave) | F2 canónico |
| Allowlist por área (ADR §3, item 4) | São domínios de política, ou seja, decisão do maestro | P-25 |
| O destino do `scrape.yml` | Escreve em produção, por fora do T6 | P-24 |
