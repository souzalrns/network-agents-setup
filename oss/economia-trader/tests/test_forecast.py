import json
import sys
import types
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.backtest import run_backtest, sma_cross
from economia_trader.cli import main
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Kline, Ticker
from economia_trader.flow import FlowPrint, StaticFlowSource
from economia_trader.forecast import (
    ForecastConfirmer,
    compare_summaries,
    confirmer_for,
    kronos_forecaster,
    load_kronos_package,
    with_forecast_confirm,
)
from economia_trader.office import map_entry
from economia_trader.runner import RunConfig, Runner
from economia_trader.safety import Mode

DAY = 86_400_000
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.stocks.example.json").read_text()))
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def bars(n=100, close=100):
    return [Kline(i * DAY, D(close), D(close + 1), D(close - 1), D(close), D(10)) for i in range(n)]


def series():
    """Flat, rally, crash (open = previous close): one round trip for sma_cross(5, 20)."""
    closes = [100] * 35 + [100 + i for i in range(1, 31)] + [130 - 2 * i for i in range(1, 31)]
    out = []
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c
        out.append(Kline(i * 3_600_000, D(o), D(max(o, c)) + 1, D(min(o, c)) - 1, D(c), D(10)))
    return out


def fixed(*ends):
    """A forecaster whose paths end at ``ends`` (one path per value); records what it was asked."""

    def forecast(klines, horizon, samples, seed):
        forecast.calls.append((len(klines), horizon, samples, seed))
        return [[e] * horizon for e in ends]

    forecast.calls = []
    return forecast


# ---- the confirmer ----


def test_confirms_only_a_clear_rise():
    up = ForecastConfirmer(fixed(103, 102, 101, 99, 104), horizon=3, samples=5)
    op = up.opinion("ACME", bars())
    assert op.confirms and op.rating == "UP" and op.expected_return == pytest.approx(0.018) and op.up_share == 0.8
    assert up.forecaster.calls == [(100, 3, 5, 42)]

    mixed = ForecastConfirmer(fixed(103, 99, 98, 104))  # E[r] +1% but only half the paths up
    assert mixed.opinion("ACME", bars()).rating == "NOT_UP"
    small = ForecastConfirmer(fixed(100.5, 100.4, 100.6))  # all up, but less than +1%
    assert not small.opinion("ACME", bars()).confirms


def test_fails_closed_on_short_history_empty_forecast_and_budget():
    c = ForecastConfirmer(fixed(110), max_runs_per_day=2)
    assert c.opinion("ACME", bars(10)).rating == "NO_DATA"
    assert ForecastConfirmer(fixed()).opinion("ACME", bars()).rating == "NO_FORECAST"
    assert [c.opinion("ACME", bars(), "2026-10-13").rating for _ in range(3)] == ["UP", "UP", "BUDGET"]
    assert c.opinion("ACME", bars(), "2026-10-14").rating == "UP"  # new day, new budget


def test_confirmer_for_reads_the_versioned_config():
    cfg = RunConfig(forecast_horizon=3, forecast_min_expected_return=D("0.05"), forecast_min_up_share=D("1"))
    c = confirmer_for(fixed(104), cfg)
    assert (c.horizon, c.min_expected_return, c.min_up_share) == (3, 0.05, 1.0)
    assert not c.opinion("ACME", bars()).confirms  # +4% < +5%


# ---- the Kronos plug (fake checkout, no torch/weights) ----


def _fake_kronos(root: Path) -> Path:
    pkg = root / "model"
    pkg.mkdir(parents=True)
    # Kronos imports itself as `model` (from model.module import *): the fake does the same.
    (pkg / "__init__.py").write_text("from .kronos import Kronos, KronosTokenizer, KronosPredictor\n")
    (pkg / "module.py").write_text("SCALE = 1.02\n")
    (pkg / "kronos.py").write_text(
        "import pandas as pd\n"
        "from model.module import SCALE\n"
        "class _Hub:\n"
        "    @classmethod\n"
        "    def from_pretrained(cls, name):\n"
        "        return name\n"
        "class Kronos(_Hub): pass\n"
        "class KronosTokenizer(_Hub): pass\n"
        "class KronosPredictor:\n"
        "    def __init__(self, model, tokenizer, device, max_context):\n"
        "        self.seen = (model, tokenizer, device, max_context)\n"
        "    def predict(self, df, x_timestamp, y_timestamp, pred_len, T, top_p, sample_count, verbose):\n"
        "        assert len(df) == len(x_timestamp) and len(y_timestamp) == pred_len and sample_count == 1\n"
        "        last = float(df['close'].iloc[-1])\n"
        "        return pd.DataFrame({'close': [last * SCALE] * pred_len}, index=y_timestamp)\n"
    )
    return root


@pytest.fixture
def clean_model_modules():
    yield
    for name in [m for m in sys.modules if m == "model" or m.startswith("model.")]:
        del sys.modules[name]


def test_load_kronos_package_from_a_checkout(tmp_path, clean_model_modules):
    pytest.importorskip("pandas")
    with pytest.raises(RuntimeError, match="67b630e"):
        load_kronos_package(tmp_path / "missing")
    root = _fake_kronos(tmp_path / "Kronos")
    pkg = load_kronos_package(root)
    assert pkg.KronosPredictor and load_kronos_package(root) is pkg
    assert str(root.resolve()) not in sys.path  # the checkout is on sys.path only during the import
    other = _fake_kronos(tmp_path / "other")
    with pytest.raises(RuntimeError, match="already imported"):
        load_kronos_package(other)


def test_kronos_forecaster_samples_seeded_paths(tmp_path, monkeypatch, clean_model_modules):
    pytest.importorskip("pandas")
    seeds = []
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(manual_seed=seeds.append))
    fc = kronos_forecaster(_fake_kronos(tmp_path / "Kronos"), max_context=50)
    paths = fc(bars(80), 4, 3, 7)
    assert seeds == [7, 8, 9] and len(paths) == 3 and all(len(p) == 4 for p in paths)
    assert paths[0][-1] == pytest.approx(102.0)
    assert ForecastConfirmer(fc, horizon=4, samples=3).opinion("ACME", bars(80)).confirms


# ---- backtest A/B ----


def test_with_forecast_confirm_filters_buys_without_lookahead(limits):
    bars_ = series()
    base = run_backtest(bars_, sma_cross(5, 20), symbol="BTCUSDT", limits=limits).summary()

    veto = fixed(90)
    vetoed = run_backtest(
        bars_,
        with_forecast_confirm(sma_cross(5, 20), ForecastConfirmer(veto, min_bars=20)),
        symbol="BTCUSDT",
        limits=limits,
    )
    assert vetoed.strategy == "sma_cross(5,20)+kronos" and not vetoed.fills and veto.calls
    assert all(n < len(bars_) for n, *_ in veto.calls)  # only the bars known at the decision

    ok = run_backtest(
        bars_,
        with_forecast_confirm(sma_cross(5, 20), ForecastConfirmer(fixed(200), min_bars=20)),
        symbol="BTCUSDT",
        limits=limits,
    ).summary()
    assert ok["trades_closed"] == base["trades_closed"] == 1

    cmp = compare_summaries(base, vetoed.summary())
    assert cmp["trades_closed"] == {"sem": 1, "com": 0} and set(cmp) >= {"return_pct", "max_drawdown_pct"}
    assert cmp["melhora_retorno"] is (D(vetoed.summary()["return_pct"]) > D(base["return_pct"]))


def test_cli_backtest_ab(tmp_path, monkeypatch, capsys):
    kfile = tmp_path / "k.json"
    rows = [[b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close), "10"] for b in series()]
    kfile.write_text(json.dumps(rows))
    lfile = tmp_path / "l.json"
    lfile.write_text(
        json.dumps(
            {"max_order_notional": "100", "max_loss_per_trade": "5", "max_daily_loss": "10", "allowed_symbols": ["X"]}
        )
    )
    argv = ["backtest", "--symbol", "X", "--limits", str(lfile), "--klines-file", str(kfile), "--fast", "5"]
    argv += ["--slow", "20", "--forecast", "kronos"]
    with pytest.raises(SystemExit, match="--kronos-repo"):
        main(argv)
    import economia_trader.cli as cli

    monkeypatch.setattr(cli, "_kronos", lambda args, cfg: ForecastConfirmer(fixed(10), min_bars=20))
    assert main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["comparacao"]["trades_closed"] == {"sem": 1, "com": 0}


# ---- the loop ----


class Ex:
    name = "fake"
    supports_testnet = False

    def __init__(self, broken=False):
        self.broken = broken
        self.asked = []

    def ticker(self, s):
        return Ticker(s, D({"ACME": "20", "BETA": "10"}[s]), None, None)

    def klines(self, s, interval, limit):
        self.asked.append((s, interval, limit))
        if self.broken:
            raise RuntimeError("model blew up")
        return bars(100, close={"ACME": 20, "BETA": 10}[s])


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


def _runner(tmp, cfg, forecaster, ex=None):
    return Runner(
        ex or Ex(),
        StaticFlowSource([fp("a", "ACME"), fp("b", "BETA")]),
        mode=Mode.PAPER,
        limits=LIMITS,
        config=cfg,
        state_dir=tmp,
        cash="100",
        env={},
        clock=lambda: T0,
        forecaster=forecaster,
    )


def test_runner_forecast_vetoes_and_confirms(tmp_path):
    def by_ticker(klines, horizon, samples, seed):
        last = float(klines[-1].close)
        return [[last * (0.9 if last == 20 else 1.1)] * horizon for _ in range(samples)]  # ACME down, BETA up

    cfg = RunConfig(forecast_confirm=True, max_new_per_run=2)
    ex = Ex()
    s = _runner(tmp_path, cfg, confirmer_for(by_ticker, cfg), ex).run_once()
    got = {e["ticker"]: e for e in s["entries"]}
    assert got["ACME"]["status"] == "vetoed" and got["ACME"]["reasons"][0].startswith("forecast: NOT_UP")
    assert got["BETA"]["status"] == "filled"
    assert ex.asked[0] == ("ACME", "1d", 400)
    page = build_html(tmp_path, now=T0)
    assert "Previsões (Kronos)" in page and "+10.00%" in page and "-10.00%" in page


def test_runner_forecast_error_blocks_the_entry_not_the_tick(tmp_path):
    cfg = RunConfig(forecast_confirm=True, max_new_per_run=2)
    s = _runner(tmp_path, cfg, confirmer_for(fixed(999), cfg), Ex(broken=True)).run_once()
    assert [e["status"] for e in s["entries"]] == ["vetoed", "vetoed"]
    assert s["entries"][0]["reasons"] == ["forecast: ERROR (RuntimeError)"]
    lines = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert [x["payload"]["rating"] for x in lines if x["kind"] == "forecast"] == ["ERROR", "ERROR"]


def test_forecast_knobs_are_versioned_parsed_and_required(tmp_path):
    base = RunConfig()
    for kw in ({"forecast_confirm": True}, {"forecast_horizon": 10}, {"forecast_interval": "4h"}):
        assert RunConfig(**kw).version != base.version
    cfg = RunConfig.from_mapping({"forecast_confirm": True, "forecast_interval": "4h", "forecast_min_up_share": "0.7"})
    assert cfg.forecast_confirm and cfg.forecast_interval == "4h" and cfg.forecast_min_up_share == D("0.7")
    with pytest.raises(ValueError, match="forecast_interval"):
        RunConfig.from_mapping({"forecast_interval": "2d"})
    with pytest.raises(ValueError, match="forecaster"):
        _runner(tmp_path, RunConfig(forecast_confirm=True), None)


def test_office_shows_the_forecast():
    entry = {"kind": "forecast", "payload": {"ticker": "A", "rating": "UP", "confirms": True}}
    assert map_entry(entry) == ("analyst", "writing", "A: UP (kronos)")
