"""More evidence, all reused, all optional, all measured per version (P-59, P-62, P-63).

- **Insiders (OSINT, SEC Form 4) via edgartools** (MIT): open-market purchases (code P) by
  officers/directors. ``insider_clusters`` is a deterministic screen: several distinct insiders
  buying the same ticker within a window is a classic, testable signal. ``available_at`` is
  when the filing reached EDGAR, never the trade date (Form 4 can lag up to 2 business days).
- **News sentiment via FinBERT** (ProsusAI/finbert, Apache-2.0): cheap, local classification
  of headlines (positive / negative / neutral) before any LLM sees them.
- **Social + news sentiment via Adanos** (SDK MIT): buzz and bullish % per ticker from Reddit,
  X, news and Polymarket; optional, only with ``ADANOS_API_KEY``.
- ``sentiment_veto``: a deterministic rule the runner applies when ``sentiment_veto`` is on:
  skip an entry if recent headlines are mostly negative or social bullishness is too low.

Every fetcher is a plain function; tests and other vendors plug in without the libraries.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from .contracts import EconomicEvent, dec, now_iso
from .monitors import _iso


def _id(*parts: str) -> str:
    return "ev_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


@dataclass
class Idea:
    """A ticker worth proposing, from any screen, with the evidence that put it there."""

    ticker: str
    source: str
    evidence_ids: tuple[str, ...]
    rationale: str
    score: Decimal = Decimal(0)
    extra: dict[str, Any] = field(default_factory=dict)


# ---- insiders (edgartools) ----


def insider_events(rows: Iterable[dict[str, Any]], *, observed_at: str | None = None) -> list[EconomicEvent]:
    """Rows: ticker, insider, role, side ("buy"/"sell"), shares, price, trade_date, filed_at."""
    observed = observed_at or now_iso()
    out = []
    for r in rows:
        if not r.get("ticker") or not r.get("filed_at") or not r.get("trade_date"):
            continue
        filed = _iso(r["filed_at"])
        value = dec(r.get("shares") or 0) * dec(r.get("price") or 0)
        out.append(
            EconomicEvent(
                id=_id(
                    "insider",
                    str(r.get("accession") or ""),
                    str(r["ticker"]),
                    str(r.get("insider")),
                    str(r["trade_date"]),
                    str(r.get("shares")),
                ),
                source="sec-form4",
                kind="insider_trade",
                payload={
                    "ticker": str(r["ticker"]).upper(),
                    "insider": r.get("insider"),
                    "role": r.get("role"),
                    "side": r.get("side"),
                    "shares": str(r.get("shares")),
                    "price": str(r.get("price")),
                    "value": str(value),
                },
                event_at=_iso(r["trade_date"]),
                published_at=filed,
                observed_at=observed,
                available_at=max(filed, observed),
            )
        )
    return out


def edgar_insider_trades(start: str, end: str, *, identity: str, max_filings: int = 400) -> list[dict[str, Any]]:
    """Form 4 open-market trades filed between ``start`` and ``end`` (YYYY-MM-DD), via edgartools.

    SEC requires a contact identity ("Name email") on every request: pass yours.
    """
    from edgar import get_filings, set_identity

    set_identity(identity)
    filings = get_filings(form="4", filing_date=f"{start}:{end}", amendments=False)
    rows: list[dict[str, Any]] = []
    for i, f in enumerate(filings or []):
        if i >= max_filings:
            break
        try:
            form4 = f.obj()
            trades = form4.market_trades
        except Exception:  # noqa: S112 - a malformed filing must not stop the scan
            continue
        if trades is None or trades.empty:
            continue
        for _, t in trades.iterrows():
            rows.append(
                {
                    "accession": getattr(f, "accession_no", ""),
                    "ticker": getattr(form4.issuer, "ticker", None),
                    "insider": form4.insider_name,
                    "role": form4.position,
                    "side": "buy" if getattr(t, "AcquiredDisposed", "") == "A" else "sell",
                    "shares": getattr(t, "Shares", 0),
                    "price": getattr(t, "Price", 0),
                    "trade_date": str(getattr(t, "Date", ""))[:10],
                    "filed_at": str(getattr(f, "filing_date", ""))[:10],
                }
            )
    return rows


def insider_clusters(
    events: Iterable[dict[str, Any]],
    as_of: str,
    *,
    window_days: int = 10,
    min_insiders: int = 2,
    min_value: Decimal = Decimal("100000"),
) -> list[Idea]:
    """Tickers where >= ``min_insiders`` distinct insiders bought >= ``min_value`` in total,
    within ``window_days`` of ``as_of``, counting only filings known by then."""
    start = (datetime.fromisoformat(as_of) - timedelta(days=window_days)).isoformat()
    by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        if e.get("kind") != "insider_trade" or e.get("available_at", "") > as_of or e.get("event_at", "") < start:
            continue
        p = e.get("payload") or {}
        if p.get("side") == "buy" and p.get("ticker"):
            by_ticker[p["ticker"]].append(e)
    ideas = []
    for ticker, evs in by_ticker.items():
        insiders = {e["payload"].get("insider") for e in evs}
        total = sum((dec(e["payload"].get("value") or 0) for e in evs), Decimal(0))
        if len(insiders) >= min_insiders and total >= min_value:
            ideas.append(
                Idea(
                    ticker=ticker,
                    source="insiders",
                    evidence_ids=tuple(sorted(e["id"] for e in evs)),
                    rationale=f"insider cluster: {len(insiders)} insiders bought ${total:,.0f} in {window_days}d",
                    score=total,
                    extra={"insiders": sorted(str(x) for x in insiders)},
                )
            )
    return sorted(ideas, key=lambda i: i.score, reverse=True)


# ---- sentiment: FinBERT (news) ----

Scorer = Callable[[list[str]], list[tuple[str, float]]]


def finbert_scorer(model: str = "ProsusAI/finbert") -> Scorer:
    """Local FinBERT classifier (``pip install 'economia-trader[nlp]'``). Returns (label, score)."""
    from transformers import pipeline

    clf = pipeline("text-classification", model=model)

    def score(texts: list[str]) -> list[tuple[str, float]]:
        return [(r["label"].lower(), float(r["score"])) for r in clf(texts, truncation=True)]

    return score


def news_sentiment_events(
    news: Iterable[dict[str, Any]], scorer: Scorer, *, observed_at: str | None = None
) -> list[EconomicEvent]:
    """Score stored news events (kind="news") into kind="news_sentiment" events (one per news)."""
    observed = observed_at or now_iso()
    items = [n for n in news if n.get("kind") == "news" and (n.get("payload") or {}).get("title")]
    if not items:
        return []
    labels = scorer([n["payload"]["title"] for n in items])
    out = []
    for n, (label, score) in zip(items, labels, strict=True):
        symbols = n["payload"].get("symbols") or ""
        out.append(
            EconomicEvent(
                id=_id("news_sentiment", n["id"]),
                source="finbert",
                kind="news_sentiment",
                payload={
                    "news_id": n["id"],
                    "tickers": [s.strip().upper() for s in str(symbols).split(",") if s.strip()],
                    "label": label,
                    "score": round(score, 4),
                },
                event_at=n["event_at"],
                published_at=n["published_at"],
                observed_at=observed,
                available_at=max(n["available_at"], observed),
            )
        )
    return out


# ---- sentiment: Adanos (social + news) ----


def adanos_compare(
    tickers: list[str], *, api_key: str, days: int = 7, sources: tuple[str, ...] = ("news", "reddit", "x", "polymarket")
) -> list[dict[str, Any]]:
    """Per-source comparison rows via the Adanos SDK (``pip install adanos``)."""
    from adanos import AdanosClient

    client = AdanosClient(api_key=api_key)
    rows: list[dict[str, Any]] = []
    for src in sources:
        res = getattr(client, src).compare(tickers, days=days)
        data = res.to_dict() if hasattr(res, "to_dict") else res
        for r in (
            (data.get("stocks") or data.get("data") or data.get("results") or []) if isinstance(data, dict) else data
        ):
            rows.append({**r, "source": src})
    return rows


def social_sentiment_events(rows: Iterable[dict[str, Any]], *, observed_at: str | None = None) -> list[EconomicEvent]:
    observed = observed_at or now_iso()
    out = []
    for r in rows:
        if not r.get("ticker"):
            continue
        out.append(
            EconomicEvent(
                id=_id("social", str(r.get("source")), str(r["ticker"]), observed[:13]),  # one per source/ticker/hour
                source=f"adanos-{r.get('source')}",
                kind="social_sentiment",
                payload={
                    "ticker": str(r["ticker"]).upper(),
                    "source": r.get("source"),
                    "buzz": r.get("buzz_score"),
                    "bullish_pct": r.get("bullish_pct"),
                    "trend": r.get("trend"),
                },
                event_at=observed,
                published_at=observed,
                observed_at=observed,
                available_at=observed,
            )
        )
    return out


# ---- the deterministic veto ----


def sentiment_veto(
    events: Iterable[dict[str, Any]],
    ticker: str,
    as_of: str,
    *,
    lookback_hours: float = 48,
    max_negative_share: float = 0.6,
    min_bullish_pct: float = 30,
) -> list[str]:
    """Reasons to skip an entry on ``ticker`` (empty = no veto). Only what was known at ``as_of``."""
    since = (datetime.fromisoformat(as_of) - timedelta(hours=lookback_hours)).isoformat()
    t = ticker.upper()
    news, social = [], []
    for e in events:
        if e.get("available_at", "") > as_of or e.get("available_at", "") < since:
            continue
        p = e.get("payload") or {}
        if e.get("kind") == "news_sentiment" and t in (p.get("tickers") or []):
            news.append(p["label"])
        elif e.get("kind") == "social_sentiment" and p.get("ticker") == t and p.get("bullish_pct") is not None:
            social.append(float(p["bullish_pct"]))
    reasons = []
    if news:
        share = news.count("negative") / len(news)
        if share >= max_negative_share:
            reasons.append(f"news {share:.0%} negative ({len(news)} headlines)")
    if social:
        avg = sum(social) / len(social)
        if avg < min_bullish_pct:
            reasons.append(f"social bullish {avg:.0f}% < {min_bullish_pct:.0f}%")
    return reasons
