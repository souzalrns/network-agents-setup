"""A single static HTML page with the state of the trader, built from the files it already
writes (``state.json``, ``journal.jsonl``, ``events.jsonl``). No server, no JS dependency: open
it in a browser, or regenerate it from cron after each tick (``--refresh`` adds an auto-reload).

Shows: mode, version, kill switch, cash and positions (with stop / take-profit); results per
strategy version; upcoming high-impact releases; latest news; analyst opinions; forecasts; risk rejections
and gate blocks; auto-kills; the last decisions in order.
"""

from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .predictions import latest_odds
from .report import report


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _e(v: Any) -> str:
    return html.escape("" if v is None else str(v))


class Link:
    """A table cell that links out (e.g. to the ticker's page in OpenStock). Only http(s)."""

    def __init__(self, text: Any, href: str | None) -> None:
        self.text, self.href = text, href

    def html(self) -> str:
        if not self.href or not self.href.startswith(("http://", "https://")):
            return _e(self.text)
        return f'<a href="{_e(self.href)}" target="_blank" rel="noopener noreferrer">{_e(self.text)}</a>'


def _cell(c: Any) -> str:
    return c.html() if isinstance(c, Link) else _e(c)


def _ticker(sym: Any, base: str | None, *, terminal: str | None = None) -> Any:
    """Ticker -> link to our market terminal (``<terminal>/?symbol=<SYM>``, oss/economia-trader/terminal) or,
    without it, to ``<openstock>/stocks/<SYM>`` (OpenStock used as-is, side by side)."""
    if not sym or not (terminal or base):
        return sym
    sym_q = quote(str(sym).upper(), safe="")
    if terminal:
        return Link(sym, f"{terminal.rstrip('/')}/?symbol={sym_q}")
    return Link(sym, f"{base.rstrip('/')}/stocks/{sym_q}")  # type: ignore[union-attr]


STALE_AFTER_S = 900  # a loop that ticks every few minutes and has been silent this long is not running


def _last_tick(journal: list[dict[str, Any]], now: datetime) -> tuple[str, bool]:
    """("há N min", stale?) from the last ``run`` entry; ("nenhum", True) before the first tick."""
    last = next((e for e in reversed(journal) if e.get("kind") == "run"), None)
    if not last:
        return "nenhum", True
    age = max(0.0, (now - datetime.fromisoformat(last["ts"])).total_seconds())  # ts = when it was written
    text = f"há {int(age)} s" if age < 90 else f"há {int(age // 60)} min" if age < 5400 else f"há {age / 3600:.1f} h"
    return (f"SEM ATUALIZAÇÃO · {text}" if age > STALE_AFTER_S else text), age > STALE_AFTER_S


def _table(head: list[str], rows: list[list[Any]], empty: str) -> str:
    if not rows:
        return f'<p class="muted">{_e(empty)}</p>'
    th = "".join(f"<th>{_e(h)}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td>{_cell(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def _card(label: str, value: Any, *, alert: bool = False) -> str:
    cls = "card alert" if alert else "card"
    return f'<div class="{cls}"><div class="k">{_e(label)}</div><div class="v">{_e(value)}</div></div>'


def _money(v: Any) -> str:
    try:
        return f"{Decimal(str(v)):,.2f}"
    except (InvalidOperation, ValueError):
        return "—" if v in (None, "") else str(v)


def _usage(model: str, u: dict[str, Any]) -> str:
    if "in" in u:
        return f"{model}: {u.get('in', 0)}/{u.get('out', 0)} tokens"
    return f"{model}: {u.get('calls', 0)} chamadas, {u.get('cached', 0)} em cache"


def _summary(entry: dict[str, Any]) -> str:
    k, p = entry["kind"], entry.get("payload") or {}
    if k == "proposal":
        return f"proposta {p.get('side')} {p.get('qty')} {p.get('symbol')} · {p.get('proposer')}"
    if k == "assessment":
        return "risco: aprovado" if p.get("approved") else "risco: rejeitado — " + "; ".join(p.get("reasons", []))
    if k == "opinion":
        effect = "confirma" if p.get("confirms") else "veta"
        return f"analista {p.get('by') or '?'} {p.get('ticker')}: {p.get('rating')} ({effect})"
    if k == "forecast":
        return f"previsão {p.get('ticker')}: {p.get('rating')} ({'confirma' if p.get('confirms') else 'veta'})"
    if k == "blocked":
        return f"bloqueado: {p.get('code')}"
    if k == "fill":
        return f"fill {p.get('side')} {p.get('qty')} {p.get('symbol')} @ {p.get('price')}"
    if k == "order":
        return f"ordem {p.get('side')} {p.get('qty')} {p.get('symbol')} ({p.get('network')})"
    if k == "intent":
        return f"ordem preparada {p.get('side')} {p.get('qty')} {p.get('symbol')} ({p.get('mode')})"
    if k == "grid_refused":
        return "grid recusado: " + "; ".join(p.get("problems", []))
    if k == "grid_anchor":
        return f"grid ancorado em {p.get('price')} ({p.get('symbol')})"
    if k == "odds_block":
        return "pausa por probabilidades: " + "; ".join(p.get("reasons", []))
    if k == "macro_block":
        return "pausa macro: " + ", ".join(p.get("releases", []))
    if k == "auto_kill":
        return f"AUTO-KILL: {p.get('reason')}"
    if k == "run":
        return f"tick · candidatos {', '.join((p.get('screen') or {}).get('candidates', [])) or '—'}"
    return k


def build_html(
    state_dir: str | Path,
    *,
    now: datetime | None = None,
    refresh_s: int | None = None,
    openstock_url: str | None = None,
    openterminal_url: str | None = None,
) -> str:
    sd = Path(state_dir)
    now = now or datetime.now(timezone.utc)
    state = json.loads((sd / "state.json").read_text()) if (sd / "state.json").exists() else {}
    journal = _rows(sd / "journal.jsonl")
    events = _rows(sd / "events.jsonl")
    rep = (
        report(sd / "journal.jsonl")
        if journal
        else {"by_version": {}, "rejected_by_risk": {}, "blocked_by_gate": {}, "auto_kills": []}
    )
    killed = (sd / "KILL").exists()
    broker = state.get("broker") or {}
    positions = broker.get("positions") or state.get("positions") or {}
    stops = state.get("stops", {})
    meta = state.get("meta", {})

    pos_rows = [
        [
            _ticker(s, openstock_url, terminal=openterminal_url),
            p["qty"],
            p["avg_price"],
            stops.get(s, "—"),
            (meta.get(s) or {}).get("take_profit", "—"),
            (meta.get(s) or {}).get("entry_at", "—")[:16],
        ]
        for s, p in positions.items()
    ]
    ver_rows = [
        [
            v,
            r["entries"],
            r["closed"],
            r["win_rate"] if r["win_rate"] is not None else "—",
            r["pnl"],
            r["avg_win"] or "—",
            r["avg_loss"] or "—",
            r["expectancy"] or "—",
        ]
        for v, r in rep["by_version"].items()
    ]
    iso_now = now.isoformat(timespec="seconds")
    upcoming = sorted(
        (e for e in events if e.get("kind") == "macro_release" and e.get("event_at", "") >= iso_now),
        key=lambda e: e["event_at"],
    )[:8]
    macro_rows = [
        [
            e["event_at"][:16].replace("T", " "),
            e["payload"].get("name"),
            "ALTO" if e["payload"].get("high_impact") else "—",
        ]
        for e in upcoming
    ]
    grid = state.get("grid") or {}
    lots = grid.get("lots") or {}
    grid_rows = [
        [str(i), _money(price), _money(grid["levels"][i + 1]), lots.get(str(i), "—")]
        for i, price in list(enumerate(grid.get("levels") or []))[:-1][::-1]
    ]
    odds_rows = [
        [
            Link(e["payload"]["question"], e["payload"].get("url")),
            f"{e['payload']['yes_prob']:.0%}",
            _money(e["payload"].get("volume")),
            (e["payload"].get("end_date") or "—")[:10],
        ]
        for e in latest_odds(events, iso_now)[:8]
    ]
    news = sorted((e for e in events if e.get("kind") == "news"), key=lambda e: e["published_at"], reverse=True)[:10]
    news_rows = [
        [
            e["published_at"][:16].replace("T", " "),
            _ticker(
                (e["payload"].get("symbols") or "").split(",")[0].strip(), openstock_url, terminal=openterminal_url
            ),
            Link(e["payload"].get("title"), e["payload"].get("url")),
        ]
        for e in news
    ]
    sentiment = {
        e["payload"].get("news_id"): e["payload"].get("label") for e in events if e.get("kind") == "news_sentiment"
    }
    for row, e in zip(news_rows, news, strict=True):
        row.insert(2, sentiment.get(e["id"], "—"))
    insiders = sorted(
        (e for e in events if e.get("kind") == "insider_trade"), key=lambda e: e["event_at"], reverse=True
    )[:12]
    insider_rows = [
        [
            e["event_at"][:10],
            _ticker(e["payload"].get("ticker"), openstock_url, terminal=openterminal_url),
            e["payload"].get("insider"),
            e["payload"].get("role"),
            "compra" if e["payload"].get("side") == "buy" else "venda",
            _money(e["payload"].get("value")),
        ]
        for e in insiders
    ]
    social = [e for e in events if e.get("kind") == "social_sentiment"][-12:]
    social_rows = [
        [
            _ticker(e["payload"].get("ticker"), openstock_url, terminal=openterminal_url),
            e["payload"].get("source"),
            e["payload"].get("bullish_pct"),
            e["payload"].get("buzz"),
            e["payload"].get("trend"),
        ]
        for e in reversed(social)
    ]
    vetoes = [e["payload"] for e in journal if e["kind"] == "sentiment_veto"][-8:]
    ops = [e["payload"] for e in journal if e["kind"] == "opinion"][-10:]
    op_rows = [
        [
            _ticker(o.get("ticker"), openstock_url, terminal=openterminal_url),
            o.get("by") or "—",
            o.get("rating"),
            "confirma" if o.get("confirms") else "veta",
            ", ".join(_usage(m, u) for m, u in (o.get("usage") or {}).items()) or "—",
        ]
        for o in reversed(ops)
    ]
    fcs = [e["payload"] for e in journal if e["kind"] == "forecast"][-10:]
    fc_rows = [
        [
            _ticker(f.get("ticker"), openstock_url, terminal=openterminal_url),
            f.get("rating"),
            "confirma" if f.get("confirms") else "veta",
            f"{f['expected_return']:+.2%}" if f.get("expected_return") is not None else "—",
            f"{f['up_share']:.0%}" if f.get("up_share") is not None else "—",
        ]
        for f in reversed(fcs)
    ]
    timeline = [[e["ts"][:19].replace("T", " "), e["kind"], _summary(e)] for e in journal[-25:]][::-1]
    rej = Counter(rep["rejected_by_risk"]).most_common(6)

    tick_text, stale = _last_tick(journal, now)
    cards = [
        ("Modo", state.get("mode", "—")),
        ("Último tick", tick_text),
        ("Exchange", state.get("exchange", "—")),
        ("Versão", state.get("config_version", "—")),
        ("Kill switch", "ACIONADO" if killed else "livre"),
        ("Caixa (paper)", _money(broker.get("cash"))),
        ("P&L realizado hoje", _money(state.get("realized_today") or broker.get("realized_today"))),
    ]
    card_html = "".join(
        _card(k, v, alert=(k == "Kill switch" and killed) or (k == "Último tick" and stale)) for k, v in cards
    )
    refresh = f'<meta http-equiv="refresh" content="{int(refresh_s)}">' if refresh_s else ""
    gate_rows = [["gate", f"{k}: {v}"] for k, v in rep["blocked_by_gate"].items()]
    gate_rows += [["auto-kill", r] for r in rep["auto_kills"]]
    sections = [
        (
            "Posições",
            ["Ativo", "Qtd", "Preço médio", "Stop", "Take-profit", "Entrada"],
            pos_rows,
            "Sem posições abertas.",
        ),
        (
            "Resultados por versão",
            ["Versão", "Entradas", "Fechadas", "Acerto", "P&L", "Ganho méd.", "Perda méd.", "Expectância"],
            ver_rows,
            "Ainda sem trades.",
        ),
        (
            "Próximos releases macro",
            ["Quando (UTC)", "Release", "Impacto"],
            macro_rows,
            "Sem calendário (corre economia-trader monitor --macro).",
        ),
        (
            f"Grid {grid.get('symbol', '')} (stop {_money(grid.get('stop'))})",
            ["Nível", "Compra a ≤", "Vende a", "Lote em carteira"],
            grid_rows,
            "Sem grid (economia-trader grid --config grid.json).",
        ),
        (
            "Probabilidades macro (Polymarket, só leitura)",
            ["Mercado", "Sim", "Volume", "Fecha"],
            odds_rows,
            "Sem dados (corre economia-trader monitor --polymarket).",
        ),
        (
            "Opiniões do analista",
            ["Ativo", "Analista", "Rating", "Efeito", "Uso acumulado"],
            op_rows,
            "Sem opiniões (confirm_with desligado).",
        ),
        (
            "Previsões (Kronos)",
            ["Ativo", "Sinal", "Efeito", "Retorno esperado", "Caminhos em alta"],
            fc_rows,
            "Sem previsões (forecast_confirm desligado).",
        ),
        ("Rejeições do risco", ["Motivo", "Vezes"], [list(r) for r in rej], "Nenhuma."),
        ("Bloqueios e auto-kills", ["Tipo", "Detalhe"], gate_rows, "Nenhum."),
        (
            "Insiders (SEC Form 4)",
            ["Data", "Ativo", "Insider", "Cargo", "Lado", "Valor"],
            insider_rows,
            "Sem dados (economia-trader monitor --insiders --sec-identity ...).",
        ),
        (
            "Sentimento social (Adanos)",
            ["Ativo", "Fonte", "Bullish %", "Buzz", "Tendência"],
            social_rows,
            "Sem dados (monitor --adanos TICKERS, com ADANOS_API_KEY).",
        ),
        (
            "Vetos por sentimento",
            ["Ativo", "Motivos"],
            [
                [_ticker(v.get("ticker"), openstock_url, terminal=openterminal_url), "; ".join(v.get("reasons", []))]
                for v in reversed(vetoes)
            ],
            "Nenhum.",
        ),
        (
            "Notícias recentes",
            ["Publicada (UTC)", "Ativos", "FinBERT", "Título"],
            news_rows,
            "Sem notícias (corre economia-trader monitor --news ...).",
        ),
        ("Últimas decisões", ["Quando (UTC)", "Tipo", "Resumo"], timeline, "Diário vazio."),
    ]
    blocks = "".join(
        f'<section><h2>{_e(t)}</h2><div class="scroll">{_table(h, r, empty)}</div></section>'
        for t, h, r, empty in sections
        if grid or not t.startswith("Grid ")  # the grid block only for a grid state dir
    )
    terminal_link = f" · {Link('terminal de mercado', openterminal_url).html()}" if openterminal_url else ""
    return (
        '<!doctype html><html lang="pt"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"{refresh}<title>economia-trader</title><style>{CSS}</style></head><body><main>"
        f'<h1>economia-trader</h1><p class="muted">Gerado {_e(iso_now)} · fonte: {_e(sd)}{terminal_link}</p>'
        f'<div class="cards">{card_html}</div><div class="grid">{blocks}</div></main></body></html>\n'
    )


CSS = """
:root{--bg:#f7f7f5;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e4e4df;--accent:#2a6f4e;--alert:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#151614;--fg:#ecece8;--muted:#9a9a92;--card:#1f201d;
--line:#2e2f2b;--accent:#6fcf97;--alert:#ff8a80}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
padding:16px}
main{max-width:1100px;margin:0 auto}h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:20px 0 8px}
.muted{color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}
.card .k{color:var(--muted);font-size:12px}.card .v{font-size:16px;font-weight:600;word-break:break-all}
.card.alert{border-color:var(--alert)}.card.alert .v{color:var(--alert)}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 16px}
.grid>section{min-width:0}
.grid section:nth-child(1),.grid section:nth-child(2),.grid section:nth-child(7),.grid section:nth-child(10),
.grid section:nth-child(11)
{grid-column:1/-1}
@media (max-width:760px){.grid{grid-template-columns:minmax(0,1fr)}}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}
th{color:var(--muted);font-weight:500}
a{color:var(--accent)}
"""
