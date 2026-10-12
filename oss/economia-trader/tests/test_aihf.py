import json
import sys
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.analysts import AiHedgeFundAnalyst, Opinion, subprocess_bridge
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def sig(persona, value, abstained=False, cached=False):
    return {"persona": persona, "value": value, "abstained": abstained, "reasoning": "r", "cached": cached}


def bridge_of(*signals):
    def bridge(req):
        bridge.requests.append(req)
        return {"signals": list(signals), "model": req["model"]}

    bridge.requests = []
    return bridge


def test_confirms_on_mean_conviction_and_majority(tmp_path):
    b = bridge_of(sig("buffett", 0.8), sig("lynch", 0.6, cached=True), sig("druckenmiller", -0.3))
    a = AiHedgeFundAnalyst(bridge=b, evidence_dir=tmp_path)
    op = a.opinion("ACME", "2026-10-13")
    assert op.confirms and op.rating == "BULLISH +0.37 (2/3)"
    assert b.requests == [
        {
            "ticker": "ACME",
            "date": "2026-10-13",
            "personas": ["buffett", "lynch", "druckenmiller"],
            "model": "gemini-3.8-flash",
        }
    ]
    assert op.usage == {"gemini-3.8-flash": {"calls": 2, "cached": 1}}
    saved = json.loads(Path(op.evidence_path).read_text())
    assert saved["aihf"] == "2.5.0" and len(saved["signals"]) == 3


def test_vetoes_weak_split_no_view_errors_and_budget(tmp_path):
    weak = AiHedgeFundAnalyst(
        bridge=bridge_of(sig("buffett", 0.9), sig("lynch", -0.5), sig("graham", -0.1)),
        personas=["buffett", "lynch", "graham"],
        evidence_dir=tmp_path,
    )
    assert weak.opinion("ACME", "d").rating.startswith("NOT_BULLISH")
    blind = AiHedgeFundAnalyst(bridge=bridge_of(sig("buffett", 0.0, abstained=True)), evidence_dir=tmp_path)
    assert blind.opinion("ACME", "d").rating == "NO_VIEW"

    def broken(req):
        raise RuntimeError("FINANCIAL_DATASETS_API_KEY missing")

    op = AiHedgeFundAnalyst(bridge=broken, evidence_dir=tmp_path).opinion("ACME", "d")
    assert (op.rating, op.confirms) == ("ERROR (RuntimeError)", False)
    capped = AiHedgeFundAnalyst(bridge=bridge_of(sig("buffett", 1.0)), max_runs_per_day=1, evidence_dir=tmp_path)
    assert [capped.opinion("ACME", "d").rating for _ in range(2)][1] == "BUDGET"


def test_refuses_unknown_personas_and_typesafe():
    with pytest.raises(ValueError, match="personas"):
        AiHedgeFundAnalyst(bridge=bridge_of(), personas=["soros"])
    with pytest.raises(ValueError, match="TypeSafe"):
        AiHedgeFundAnalyst(bridge=bridge_of(), model="jev-1.13.0")


# ---- the subprocess seam: own interpreter, only data/LLM keys in the env ----


def _fake_python(tmp_path, body):
    exe = tmp_path / "python"
    exe.write_text(f"#!/bin/sh\nexec {sys.executable} -c '{body}'\n")
    exe.chmod(0o755)
    return exe


ECHO = 'import json,os,sys; r=json.load(sys.stdin); print(json.dumps({"signals":[],"env":sorted(os.environ),"req":r}))'


def test_subprocess_bridge_passes_only_allowlisted_env(tmp_path):
    exe = _fake_python(tmp_path, ECHO)
    env = {
        "PATH": "/usr/bin:/bin",
        "GOOGLE_API_KEY": "g",
        "FINANCIAL_DATASETS_API_KEY": "f",
        "BYBIT_API_SECRET": "x",
        "ALPACA_SECRET_KEY": "y",
        "TYPESAFE_API_KEY": "z",
    }
    out = subprocess_bridge(exe, env=env)({"ticker": "ACME"})
    assert out["req"] == {"ticker": "ACME"}
    leaked = set(out["env"]) & {"BYBIT_API_SECRET", "ALPACA_SECRET_KEY", "TYPESAFE_API_KEY"}
    assert not leaked and {"GOOGLE_API_KEY", "FINANCIAL_DATASETS_API_KEY"} <= set(out["env"])


def test_subprocess_bridge_failure_becomes_a_veto(tmp_path):
    exe = _fake_python(tmp_path, 'import sys; sys.stderr.write("boom: no key\\n"); sys.exit(3)')
    with pytest.raises(RuntimeError, match="exited 3: boom: no key"):
        subprocess_bridge(exe, env={"PATH": "/usr/bin:/bin"})({})
    a = AiHedgeFundAnalyst(bridge=subprocess_bridge(exe, env={"PATH": "/usr/bin:/bin"}), evidence_dir=tmp_path)
    assert a.opinion("ACME", "d").rating == "ERROR (RuntimeError)"


# ---- the loop: two analysts, each must confirm ----


class Ex:
    name = "fake"
    supports_testnet = False

    def ticker(self, s):
        return Ticker(s, D({"ACME": "20", "BETA": "10"}[s]), None, None)


class TA:
    name = "tradingagents"

    def __init__(self, ok):
        self.ok, self.asked = ok, []

    def opinion(self, ticker, day):
        self.asked.append(ticker)
        return Opinion(ticker, day, "Buy" if self.ok[ticker] else "Hold", self.ok[ticker], f"/e/{ticker}.json")


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


def test_runner_chains_analysts_and_stops_at_first_veto(tmp_path):
    ta = TA({"ACME": False, "BETA": True})
    aihf = AiHedgeFundAnalyst(bridge=bridge_of(sig("buffett", 0.9)), personas=["buffett"], evidence_dir=tmp_path)
    cfg = RunConfig(confirm_with="tradingagents+ai-hedge-fund", max_new_per_run=2)
    runner = Runner(
        Ex(),
        StaticFlowSource([fp("a", "ACME"), fp("b", "BETA")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=cfg,
        state_dir=tmp_path,
        cash="100",
        env={},
        clock=lambda: T0,
        analyst=[ta, aihf],
    )
    s = runner.run_once()
    got = {e["ticker"]: e for e in s["entries"]}
    assert got["ACME"]["reasons"] == ["analyst tradingagents: Hold"] and got["BETA"]["status"] == "filled"
    assert aihf.bridge.requests[0]["ticker"] == "BETA"  # ACME was vetoed first: ai-hedge-fund not paid for
    rows = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert [(r["payload"]["ticker"], r["payload"]["by"]) for r in rows if r["kind"] == "opinion"] == [
        ("ACME", "tradingagents"),
        ("BETA", "tradingagents"),
        ("BETA", "ai-hedge-fund"),
    ]
    proposal = next(r["payload"] for r in rows if r["kind"] == "proposal")
    assert sum(e.startswith("opinion:") for e in proposal["evidence_ids"]) == 2
    page = build_html(tmp_path, now=T0)
    assert "ai-hedge-fund" in page and "1 chamadas, 0 em cache" in page


def test_confirm_with_is_validated():
    assert RunConfig.from_mapping({"confirm_with": "ai-hedge-fund"}).analysts == ("ai-hedge-fund",)
    with pytest.raises(ValueError, match="unknown analysts"):
        RunConfig.from_mapping({"confirm_with": "tradingagents+soros"})
