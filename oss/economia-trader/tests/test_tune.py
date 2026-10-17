"""Walk-forward tuning: pick on the past, keep only what also wins out of sample, never outside the limits."""

import json
import math
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.cli import main
from economia_trader.exchanges.base import Kline
from economia_trader.tune import bars_hash, candidates, segments, walk_forward

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.example.json").read_text()))
SPACE = json.loads((EXAMPLES / "tune.grid.example.json").read_text())
HOUR = 3_600_000


def wave(n=600, amp=0.04, period=24, base=50_000.0, drift=0.0):
    """Hourly bars of a sine around ``base`` (a range market: what a grid is for)."""
    out, prev = [], base
    for i in range(n):
        close = base * (1 + amp * math.sin(2 * math.pi * i / period)) * (1 + drift * i)
        hi, lo = max(prev, close) * 1.002, min(prev, close) * 0.998
        out.append(
            Kline(
                1_700_000_000_000 + i * HOUR, D(f"{prev:.2f}"), D(f"{hi:.2f}"), D(f"{lo:.2f}"), D(f"{close:.2f}"), D(1)
            )
        )
        prev = close
    return out


def flat(n=600, price="50000"):
    p = D(price)
    return [Kline(1_700_000_000_000 + i * HOUR, p, p, p, p, D(1)) for i in range(n)]


def tune(bars, space=SPACE, **kw):
    kw.setdefault("folds", 4)
    return walk_forward(
        bars, kind=space["strategy"], base=space["base"], search=space["search"], limits=LIMITS, symbol="BTCUSDT", **kw
    )


def test_candidates_start_with_the_current_config_and_are_capped():
    cands = candidates({"a": 1, "b": 2}, {"a": [1, 3], "b": [2, 4]})
    assert cands[0] == {"a": 1, "b": 2}
    assert len(cands) == 4  # the base is not repeated
    with pytest.raises(ValueError, match="narrow the search"):
        candidates({"a": 0}, {"a": list(range(501))})


def test_segments_need_enough_bars():
    assert [len(s) for s in segments(wave(100), 4)] == [20] * 5
    with pytest.raises(ValueError, match="too few"):
        segments(wave(60), 4)


def test_folds_are_in_time_order_and_test_never_overlaps_train():
    r = tune(wave())
    for row in r["per_fold"]:
        assert row["train_range_ms"][1] < row["test_range_ms"][0]
    assert r["bars_hash"] == bars_hash(wave())  # reproducible fingerprint of the data


def test_a_candidate_outside_the_limits_is_never_scored():
    space = {**SPACE, "search": {"order_notional": ["8", "80"]}}  # 80 > max_order_notional 50
    r = tune(wave(), space)
    refused = r["refused_by_limits"]
    assert list(refused) == ["1"]
    assert any("max_order_notional" in reason for reason in refused["1"])
    assert all(row["pick"] != 1 for row in r["per_fold"])
    if r["verdict"]:
        assert r["verdict"]["params"]["order_notional"] == "8"


def test_a_bad_current_config_is_replaced_by_one_that_wins_out_of_sample():
    # a range far wider than the 4% wave: the grid barely trades; a tighter range does better on unseen data
    base = {**SPACE["base"], "range_pct": "0.30", "levels": 4}  # fits the limits, but never trades on this wave
    r = tune(wave(), {**SPACE, "base": base, "search": {"range_pct": ["0.09", "0.30"]}})
    v = r["verdict"]
    assert r["accepted"], r["reasons"]
    assert v["params"]["range_pct"] == "0.09"
    assert v["oos"]["runs"] == v["baseline_oos"]["runs"] == 4  # a real comparison, same unseen segments
    assert v["baseline_oos"]["trades_closed"] == 0 and v["oos"]["trades_closed"] >= 3
    assert D(v["oos"]["mean_score"]) - D(v["baseline_oos"]["mean_score"]) > D("0.1")
    assert r["config_hash"]  # fingerprint of the tuned config file (paper runs log the anchored version)


def test_a_current_config_outside_the_limits_is_said_out_loud():
    base = {**SPACE["base"], "range_pct": "0.30"}  # 6 levels: a full stop-out loses 6 > max_daily_loss 5
    r = tune(wave(), {**SPACE, "base": base, "search": {"range_pct": ["0.09", "0.30"]}})
    assert "max_daily_loss" in r["refused_by_limits"]["0"][0]
    assert r["verdict"]["baseline_oos"]["runs"] == 0
    assert any("does not fit the limits" in n for n in r["verdict"]["notes"])


def test_a_hairline_win_is_noise_and_the_current_config_stays():
    r = tune(wave())  # the example config is already decent on this wave: the best pick wins by ~0.01
    assert not r["accepted"]
    assert any("by more than 0.1" in x for x in r["reasons"])
    assert r["verdict"]["overfit_gap"] is not None


def test_no_trades_out_of_sample_is_not_accepted():
    r = tune(flat())
    assert not r["accepted"]
    assert any("trades closed" in x or "does not beat" in x for x in r["reasons"])
    assert r["verdict"] is None or r["verdict"]["oos"]["trades_closed"] < 3


def test_when_nothing_beats_the_current_config_it_stays():
    space = {**SPACE, "search": {}}  # only the current config: it cannot beat itself
    r = tune(wave(), space)
    assert not r["accepted"]
    assert any("does not beat" in x for x in r["reasons"])


def test_sma_space_works_too():
    space = {"strategy": "sma", "base": {"fast": 10, "slow": 30}, "search": {"fast": [5, 10], "slow": [20, 30]}}
    r = tune(wave(), space)
    assert r["strategy"] == "sma" and r["candidates"] == 4
    space_bad = {"strategy": "sma", "base": {"fast": 30, "slow": 10}, "search": {}}
    assert tune(wave(), space_bad)["refused_by_limits"]["0"]


def test_cli_writes_the_config_only_when_accepted(tmp_path, capsys):
    kl = tmp_path / "k.json"
    kl.write_text(
        json.dumps([[b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close), "1"] for b in flat()])
    )
    out, log = tmp_path / "best.json", tmp_path / "tune.jsonl"
    args = ["tune", "--symbol", "BTCUSDT", "--klines-file", str(kl), "--limits", str(EXAMPLES / "limits.example.json")]
    args += ["--space", str(EXAMPLES / "tune.grid.example.json"), "--out", str(out), "--log", str(log)]
    rc = main(args)
    printed = json.loads(capsys.readouterr().out)
    assert rc == 1 and printed["accepted"] is False and printed["written"] is None
    assert not out.exists()  # a rejected tuning never replaces the config
    rec = json.loads(log.read_text().splitlines()[-1])
    assert rec["bars_hash"] == printed["bars_hash"] and rec["accepted"] is False


def test_out_of_sample_is_each_folds_pick_on_the_next_segment_only():
    """No selection bias: the OOS numbers are exactly the per-fold picks on their unseen next segment, and the
    config to deploy is the latest fold's pick (a regime change makes the picks differ across folds)."""
    calm, wild = wave(300, amp=0.015), wave(300, amp=0.06)
    bars = [
        Kline(1_700_000_000_000 + i * HOUR, b.open, b.high, b.low, b.close, b.volume) for i, b in enumerate(calm + wild)
    ]
    r = tune(bars, {**SPACE, "search": {"range_pct": ["0.04", "0.06", "0.12", "0.16"]}})
    rows = [row for row in r["per_fold"] if row["pick"] is not None]
    v = r["verdict"]
    assert v["picks_per_fold"] == [row["pick"] for row in rows]
    assert v["chosen"] == rows[-1]["pick"]
    assert v["oos"]["trades_closed"] == sum(row["oos"]["trades_closed"] for row in rows if row["oos"])
    assert v["oos"]["runs"] == sum(1 for row in rows if row["oos"])
