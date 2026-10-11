import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.analysts import TradingAgentsAnalyst, langfuse_handler
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.monitors import EventStore, macro_events, news_events
from economia_trader.office import AGENTS, OfficeBridge, map_entry
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))


class Ex:
    name = "fake"
    supports_testnet = False

    def ticker(self, s):
        return Ticker(s, D({"ACME": "20", "BETA": "10"}[s]), None, None)


def fp(id, ticker):
    return FlowPrint(
        id,
        ticker,
        "bullish",
        D("60000"),
        100,
        1000,
        30,
        D("85"),
        D("3000000000"),
        "2026-10-12T20:00:00+00:00",
        "2026-10-13T11:00:00+00:00",
    )


@pytest.fixture
def state_dir(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    store.add(
        news_events(
            [
                {
                    "date": "2026-10-13T09:00:00Z",
                    "title": "<script>alert(1)</script> ACME deal",
                    "url": "u",
                    "symbols": "ACME",
                }
            ],
            observed_at="2026-10-13T10:00:00+00:00",
        )
    )
    store.add(
        macro_events(
            [{"event": "Consumer Price Index", "date": "2026-10-20", "time": "08:30"}],
            observed_at="2026-10-13T10:00:00+00:00",
        )
    )
    analyst = TradingAgentsAnalyst(
        propagate=lambda t, d: ({}, {"ACME": "Hold", "BETA": "Buy"}[t]), evidence_dir=tmp_path / "evidence"
    )
    Runner(
        Ex(),
        StaticFlowSource([fp("a", "ACME"), fp("b", "BETA")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=RunConfig(confirm_with="tradingagents", max_new_per_run=2),
        state_dir=tmp_path,
        cash="100",
        env={},
        clock=lambda: T0,
        events=store,
        analyst=analyst,
    ).run_once()
    return tmp_path


# ---- dashboard ----


def test_dashboard_shows_everything_and_escapes(state_dir):
    page = build_html(state_dir, now=T0)
    for needle in (
        "Posições",
        "BETA",
        "Resultados por versão",
        "Consumer Price Index",
        "ALTO",
        "Opiniões do analista",
        "veta",
        "confirma",
        "Últimas decisões",
        "paper",
    ):
        assert needle in page, needle
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page
    assert 'class="card alert"' not in page


def test_dashboard_kill_switch_and_refresh(state_dir):
    (state_dir / "KILL").write_text("drill")
    page = build_html(state_dir, now=T0, refresh_s=60)
    assert 'class="card alert"' in page and "ACIONADO" in page
    assert '<meta http-equiv="refresh" content="60">' in page


def test_dashboard_empty_dir(tmp_path):
    page = build_html(tmp_path, now=T0)
    assert "Sem posições abertas." in page and "Diário vazio." in page


def test_cli_dashboard(state_dir, capsys):
    from economia_trader import cli

    out = state_dir / "d.html"
    assert cli.main(["dashboard", "--state-dir", str(state_dir), "--out", str(out)]) == 0
    assert out.read_text().startswith("<!doctype html>")


# ---- office bridge ----


def test_map_entry():
    assert map_entry({"kind": "opinion", "payload": {"ticker": "A", "rating": "Hold", "confirms": False}}) == (
        "analyst",
        "error",
        "A: Hold",
    )
    assert map_entry({"kind": "blocked", "payload": {"code": "kill_switch"}})[:2] == ("risk", "error")
    assert map_entry({"kind": "macro_block", "payload": {"releases": ["CPI"]}})[:2] == ("risk", "syncing")
    assert map_entry({"kind": "fill", "payload": {"side": "buy", "symbol": "A"}})[0] == "executor"
    assert map_entry({"kind": "note", "payload": {}}) is None


class FakeOffice:
    def __init__(self, fail_join=False):
        self.calls = []
        self.fail_join = fail_join

    def __call__(self, url, body):
        self.calls.append((url.rsplit("/", 1)[1], body))
        if url.endswith("/join-agent"):
            if self.fail_join:
                return {"ok": False, "msg": "接入密钥无效"}
            return {"ok": True, "agentId": f"id-{body['name']}"}
        return {"ok": True}


def test_bridge_joins_once_and_syncs_incrementally(state_dir):
    fake = FakeOffice()
    b = OfficeBridge("http://office:19000/", "k1", state_dir / "office.json", post=fake)
    sent = b.sync(state_dir / "journal.jsonl", state_dir / "events.jsonl")
    joins = [c for c in fake.calls if c[0] == "join-agent"]
    assert sent > 0 and len(joins) == len({c[1]["name"] for c in joins}) <= len(AGENTS)
    pushes = [c[1] for c in fake.calls if c[0] == "agent-push"]
    assert {p["state"] for p in pushes} <= {"idle", "writing", "researching", "executing", "syncing", "error"}
    assert all(p["joinKey"] == "k1" for p in pushes)

    fake2 = FakeOffice()  # restart: ids and offsets come from disk, nothing new to send
    b2 = OfficeBridge("http://office:19000", "k1", state_dir / "office.json", post=fake2)
    assert b2.sync(state_dir / "journal.jsonl", state_dir / "events.jsonl") == 0 and fake2.calls == []


def test_bridge_join_failure_is_loud(state_dir):
    b = OfficeBridge("http://office", "bad", state_dir / "o.json", post=FakeOffice(fail_join=True))
    with pytest.raises(RuntimeError, match="join failed"):
        b.sync(state_dir / "journal.jsonl")


def test_http_post_refuses_other_schemes():
    from economia_trader.office import http_post

    with pytest.raises(ValueError):
        http_post("file:///etc/passwd", {})


# ---- tracing ----


def test_langfuse_off_without_keys():
    assert langfuse_handler(env={}) is None
    # keys set but the [tracing] extra not installed in the test env: still None, never a crash
    assert langfuse_handler(env={"LANGFUSE_PUBLIC_KEY": "pk", "LANGFUSE_SECRET_KEY": "sk"}) is None
