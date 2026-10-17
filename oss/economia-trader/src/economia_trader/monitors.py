"""News and macro monitoring -> ``EconomicEvent`` (with the four clocks), on **OpenBB**.

We do not scrape: OpenBB (Apache-2.0) already normalises the sources. Lean install, no paid
keys: ``pip install 'economia-trader[data]'`` brings ``openbb-core`` + the ``news``, ``bls`` and
``federal_reserve`` extensions (~85 packages instead of ~238 for the ``openbb`` meta-package).

- ``news_events``: company news (OpenBB ``news.company``, provider ``nasdaq``, no key).
- ``macro_events``: the BLS release calendar (CPI, Employment Situation, PPI, JOLTS, ...), plus
  an optional hand-kept file for dates OpenBB does not list (e.g. FOMC decisions), plus the weekly
  Forex Factory calendar (``forexfactory_calendar``: Fed, ECB, CPI, NFP... with consensus and previous,
  the same public feed the OpenTerminal calendar uses). It is only ever used to *pause* new entries.
- ``EventStore``: append-only, de-duplicated ``events.jsonl``; the runner reads it to block new
  entries around high-impact releases, and the dashboard reads it to show what moved.

Fetchers are plain callables, so tests (and other vendors) plug in without OpenBB.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .contracts import EconomicEvent, now_iso, to_dict

HIGH_IMPACT = (
    "consumer price",
    "cpi",
    "employment situation",
    "nonfarm",
    "fomc",
    "federal open market",
    "interest rate decision",
    "producer price",
    "ppi",
    "personal income and outlays",
    "pce",
    "gross domestic product",
    "gdp",
    "jolts",
    "retail sales",
)

NewsFetcher = Callable[[list[str], int], list[dict[str, Any]]]
CalendarFetcher = Callable[[str, str], list[dict[str, Any]]]


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    s = str(value)
    if len(s) == 10:  # a bare date
        return f"{s}T00:00:00+00:00"
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="seconds")


def _event_id(*parts: str) -> str:
    return "ev_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def is_high_impact(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in HIGH_IMPACT)


# ---- events from fetched rows ----


def news_events(
    rows: Iterable[dict[str, Any]], *, observed_at: str | None = None, source: str = "openbb"
) -> list[EconomicEvent]:
    observed = observed_at or now_iso()
    out = []
    for r in rows:
        if not r.get("title") or not r.get("date"):
            continue
        published = _iso(r["date"])
        out.append(
            EconomicEvent(
                id=_event_id("news", str(r.get("url") or r["title"])),
                source=source,
                kind="news",
                payload={
                    "title": r["title"],
                    "url": r.get("url"),
                    "symbols": r.get("symbols"),
                    "excerpt": (r.get("excerpt") or "")[:500],
                },
                event_at=published,
                published_at=published,
                observed_at=observed,
                available_at=max(published, observed),
            )
        )
    return out


def macro_events(
    rows: Iterable[dict[str, Any]], *, observed_at: str | None = None, source: str = "openbb-bls"
) -> list[EconomicEvent]:
    """Scheduled releases. ``event_at`` is the release time; the schedule itself is known now."""
    observed = observed_at or now_iso()
    out = []
    for r in rows:
        name = r.get("event") or r.get("release") or r.get("title") or r.get("name")
        day = r.get("date")
        if not name or not day:
            continue
        at = _iso(day)
        if r.get("time") and len(str(day)) == 10:
            try:  # US release times are Eastern; convert to UTC (DST-aware)
                local = datetime.fromisoformat(f"{day}T{str(r['time'])[:5]}:00").replace(
                    tzinfo=ZoneInfo(r.get("tz") or "America/New_York")
                )
                at = _iso(local)
            except ValueError:
                pass
        out.append(
            EconomicEvent(
                id=_event_id("macro", str(name), at),
                source=source,
                kind="macro_release",
                payload={
                    "name": name,
                    "importance": r.get("importance"),
                    # the vendor's own flag when it has one (Forex Factory "impact": "High"), else our list
                    "high_impact": r["high_impact"]
                    if isinstance(r.get("high_impact"), bool)
                    else is_high_impact(str(name)),
                    "country": r.get("country"),
                    "consensus": r.get("consensus"),
                    "previous": r.get("previous"),
                    "actual": r.get("actual"),
                },
                event_at=at,
                published_at=observed,  # the schedule is what we know now
                observed_at=observed,
                available_at=observed,
            )
        )
    return out


# ---- the store ----


class EventStore:
    """Append-only ``events.jsonl``, de-duplicated by event id."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def add(self, events: Iterable[EconomicEvent]) -> int:
        seen = {e["id"] for e in self.all()}
        new = [e for e in events if e.id not in seen]
        if new:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                for e in new:
                    fh.write(json.dumps(to_dict(e), ensure_ascii=False, sort_keys=True) + "\n")
        return len(new)

    def high_impact_within(self, as_of: str, hours: float) -> list[dict[str, Any]]:
        """High-impact releases whose time is within ``hours`` before or after ``as_of``."""
        now = datetime.fromisoformat(as_of)
        window = timedelta(hours=hours)
        hits = []
        for e in self.all():
            if e.get("kind") != "macro_release" or not (e.get("payload") or {}).get("high_impact"):
                continue
            if e.get("available_at", "") > as_of:
                continue  # never use what we could not have known
            if abs(datetime.fromisoformat(e["event_at"]) - now) <= window:
                hits.append(e)
        return hits


# ---- OpenBB fetchers (the default plugs) ----


def _records(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return [r if isinstance(r, dict) else r.model_dump() for r in obj]
    return [r.model_dump() for r in (obj.results or [])]


def openbb_company_news(symbols: list[str], limit: int = 20) -> list[dict[str, Any]]:
    from openbb import obb

    rows: list[dict[str, Any]] = []
    for s in symbols:
        rows += _records(obb.news.company(symbol=s, limit=limit, provider="nasdaq"))
    return rows


def openbb_macro_calendar(start: str, end: str) -> list[dict[str, Any]]:
    from openbb import obb

    return _records(obb.bls.calendar(start_date=start, end_date=end))


FOREX_FACTORY = "https://nfs.faireconomy.media/"


def _ff_json(url: str) -> Any:
    if not url.startswith(FOREX_FACTORY):
        raise ValueError(f"refusing URL outside the Forex Factory export: {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "economia-trader"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosemgrep  # noqa: S310
        return json.loads(resp.read().decode())


def forexfactory_calendar(
    countries: Iterable[str] = ("USD",), *, fetch: Callable[[str], Any] = _ff_json
) -> list[dict[str, Any]]:
    """This week's economic calendar (public export, no key) as rows for ``macro_events``.

    Only a schedule: a high-impact release (``"impact": "High"``) feeds ``macro_block`` (no new entries
    around it). It never opens a trade. The export only exists for the current week: run it daily.
    """
    wanted = {c.upper() for c in countries}
    rows = fetch(f"{FOREX_FACTORY}ff_calendar_thisweek.json")
    out = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or str(r.get("country", "")).upper() not in wanted:
            continue
        if not r.get("title") or not r.get("date") or r.get("impact") == "Holiday":
            continue
        out.append(
            {
                "event": r["title"],
                "date": r["date"],
                "country": r.get("country"),
                "importance": r.get("impact"),
                "high_impact": r.get("impact") == "High",
                "consensus": r.get("forecast") or None,
                "previous": r.get("previous") or None,
            }
        )
    return out


def load_calendar_file(path: str | Path) -> list[dict[str, Any]]:
    """Hand-kept schedule (e.g. FOMC decision days): ``[{"event": ..., "date": "YYYY-MM-DD", "time": "14:00"}]``."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
