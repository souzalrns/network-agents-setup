"""Prediction-market odds from **Polymarket**, read-only (decision of 2026-10-12: read, never trade).

The public Gamma API (``gamma-api.polymarket.com``) needs no account and no key. We keep the binary
(Yes/No) markets whose question matches macro keywords (Fed, rates, recession, CPI, inflation) and enough
volume, and store a snapshot of the "Yes" price per market per hour as an ``EconomicEvent`` of kind
``prediction_market``. The price of "Yes" is read as the market's probability.

Two uses, both deterministic:

- the dashboard shows the latest odds;
- ``odds_block`` (``RunConfig.odds_block``): no new entries while a matching market's latest odds are at or
  above a threshold (e.g. ``{"recession": 0.5}``). Only snapshots we had at the time count, and only fresh
  ones (``ODDS_MAX_AGE_H``). No snapshot means no block: the odds add caution, they are not a gate to open.

Placing bets is out: it needs a crypto wallet and is restricted in several jurisdictions.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from .contracts import EconomicEvent, now_iso

GAMMA = "https://gamma-api.polymarket.com"
DEFAULT_KEYWORDS = (
    "fed",
    "federal reserve",
    "fomc",
    "interest rate",
    "rate cut",
    "rate hike",
    "recession",
    "cpi",
    "inflation",
)
ODDS_MAX_AGE_H = 48

Fetch = Callable[[str], Any]


def _http_json(url: str) -> Any:
    if not url.startswith(GAMMA + "/"):
        raise ValueError(f"refusing URL outside the Gamma API: {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310 (fixed https host)
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosemgrep  # noqa: S310
        return json.loads(resp.read().decode())


def gamma_markets(*, limit: int = 500, pages: int = 4, fetch: Fetch = _http_json) -> list[dict[str, Any]]:
    """Open markets, largest volume first (``pages`` x ``limit`` at most)."""
    rows: list[dict[str, Any]] = []
    for page in range(pages):
        query = urllib.parse.urlencode(
            {
                "active": "true",
                "closed": "false",
                "archived": "false",
                "order": "volume",
                "ascending": "false",
                "limit": limit,
                "offset": page * limit,
            }
        )
        batch = fetch(f"{GAMMA}/markets?{query}")
        if not isinstance(batch, list):
            break
        rows += [r for r in batch if isinstance(r, dict)]
        if len(batch) < limit:
            break
    return rows


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _matches(question: str, keywords: Iterable[str]) -> bool:
    q = question.lower()
    return any(re.search(rf"\b{re.escape(k.lower())}\b", q) for k in keywords)


def yes_probability(row: dict[str, Any]) -> float | None:
    """Price of "Yes" in a binary Yes/No market, or None for anything else."""
    outcomes = [str(o).strip().lower() for o in _as_list(row.get("outcomes"))]
    prices = _as_list(row.get("outcomePrices"))
    if outcomes != ["yes", "no"] or len(prices) != 2:
        return None
    p = _number(prices[0])
    return p if 0.0 <= p <= 1.0 else None


def prediction_events(
    rows: Iterable[dict[str, Any]],
    *,
    keywords: Iterable[str] = DEFAULT_KEYWORDS,
    min_volume: float = 50_000,
    observed_at: str | None = None,
) -> list[EconomicEvent]:
    observed = observed_at or now_iso()
    keywords = tuple(keywords)
    out = []
    for r in rows:
        question, slug = str(r.get("question") or ""), str(r.get("slug") or "")
        if not question or not slug or not _matches(question, keywords):
            continue
        volume = _number(r.get("volumeNum", r.get("volume")))
        prob = yes_probability(r)
        if prob is None or volume < min_volume:
            continue
        out.append(
            EconomicEvent(
                id="ev_" + hashlib.sha256(f"pm|{slug}|{observed[:13]}".encode()).hexdigest()[:16],  # 1/market/hour
                source="polymarket",
                kind="prediction_market",
                payload={
                    "question": question,
                    "slug": slug,
                    "yes_prob": round(prob, 4),
                    "volume": round(volume),
                    "end_date": r.get("endDate"),
                    "url": f"https://polymarket.com/market/{slug}",
                },
                event_at=observed,
                published_at=observed,
                observed_at=observed,
                available_at=observed,
            )
        )
    return out


def latest_odds(
    events: Iterable[dict[str, Any]], as_of: str, *, max_age_h: float = ODDS_MAX_AGE_H
) -> list[dict[str, Any]]:
    """The latest snapshot per market that was known at ``as_of`` and is not older than ``max_age_h``."""
    now = datetime.fromisoformat(as_of)
    latest: dict[str, dict[str, Any]] = {}
    for e in events:
        if e.get("kind") != "prediction_market" or e.get("available_at", "") > as_of:
            continue
        if now - datetime.fromisoformat(e["available_at"]) > timedelta(hours=max_age_h):
            continue
        slug = (e.get("payload") or {}).get("slug")
        if slug and (slug not in latest or e["available_at"] > latest[slug]["available_at"]):
            latest[slug] = e
    return sorted(latest.values(), key=lambda e: -float(e["payload"].get("volume") or 0))


def odds_block(events: Iterable[dict[str, Any]], as_of: str, rules: Iterable[tuple[str, Decimal]]) -> list[str]:
    """Reasons to hold new entries: a market matching ``pattern`` at or above ``max_prob``."""
    reasons = []
    odds = latest_odds(events, as_of)
    for pattern, max_prob in rules:
        for e in odds:
            p = e["payload"]
            if _matches(p["question"], (pattern,)) and Decimal(str(p["yes_prob"])) >= max_prob:
                reasons.append(f"{p['question']}: {p['yes_prob']:.0%} >= {float(max_prob):.0%}")
    return reasons
