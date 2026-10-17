"""OpenTerminal integration on the Python side: the Forex Factory calendar only pauses entries, and the
dashboard links to the market terminal and says when the loop has gone quiet."""

import json
from datetime import datetime, timedelta

import pytest
from test_dashboard_office import T0, state_dir  # noqa: F401 (pytest fixture)

from economia_trader.dashboard import build_html
from economia_trader.monitors import EventStore, _ff_json, forexfactory_calendar, macro_events

FF = [
    {
        "title": "FOMC Statement",
        "country": "USD",
        "date": "2026-10-28T14:00:00-04:00",
        "impact": "High",
        "forecast": "4.25%",
        "previous": "4.50%",
    },
    {
        "title": "Crude Oil Inventories",
        "country": "USD",
        "date": "2026-10-28T10:30:00-04:00",
        "impact": "Low",
        "forecast": "",
        "previous": "1.2M",
    },
    {
        "title": "Main Refinancing Rate",
        "country": "EUR",
        "date": "2026-10-29T08:15:00-04:00",
        "impact": "High",
        "forecast": "2.00%",
        "previous": "2.00%",
    },
    {"title": "Bank Holiday", "country": "USD", "date": "2026-10-26T00:00:00-04:00", "impact": "Holiday"},
]


def test_calendar_keeps_the_wanted_countries_and_the_vendor_impact_flag():
    seen = []
    rows = forexfactory_calendar(["usd"], fetch=lambda url: seen.append(url) or FF)
    assert seen == ["https://nfs.faireconomy.media/ff_calendar_thisweek.json"]
    assert [r["event"] for r in rows] == ["FOMC Statement", "Crude Oil Inventories"]  # EUR and the holiday out
    events = macro_events(rows, observed_at="2026-10-25T12:00:00+00:00", source="forexfactory")
    fomc, oil = events
    assert fomc.payload["high_impact"] is True and fomc.payload["consensus"] == "4.25%"
    assert oil.payload["high_impact"] is False  # "Low" from the vendor, even though the name is unknown to us
    assert fomc.event_at == "2026-10-28T18:00:00+00:00"  # 14:00 New York (EDT) in UTC


def test_a_high_impact_release_pauses_entries_around_it(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    store.add(
        macro_events(forexfactory_calendar(["USD"], fetch=lambda url: FF), observed_at="2026-10-25T12:00:00+00:00")
    )
    near = store.high_impact_within("2026-10-28T09:00:00+00:00", 24)
    assert [e["payload"]["name"] for e in near] == ["FOMC Statement"]  # the low-impact one never pauses
    assert store.high_impact_within("2026-10-20T09:00:00+00:00", 24) == []


def test_calendar_fetch_refuses_any_other_host():
    with pytest.raises(ValueError, match="outside the Forex Factory"):
        _ff_json("https://example.org/ff_calendar_thisweek.json")


def test_dashboard_links_tickers_to_the_terminal_and_flags_a_quiet_loop(state_dir):  # noqa: F811
    # the journal's ts is when each line was written (wall clock): that is what "is the loop alive" means
    runs = [json.loads(x) for x in (state_dir / "journal.jsonl").read_text().splitlines() if '"run"' in x]
    ticked = datetime.fromisoformat(runs[-1]["ts"])
    page = build_html(state_dir, now=ticked + timedelta(seconds=30), openterminal_url="http://localhost:3000/")
    assert 'href="http://localhost:3000/?symbol=ACME"' in page
    assert ">terminal de mercado</a>" in page
    assert "há 30 s" in page and "SEM ATUALIZAÇÃO" not in page
    late = build_html(state_dir, now=ticked + timedelta(hours=2))
    assert "SEM ATUALIZAÇÃO" in late
    bad = build_html(state_dir, now=T0, openterminal_url="javascript:alert(1)")
    assert "javascript:" not in bad  # only http(s) links are ever rendered
