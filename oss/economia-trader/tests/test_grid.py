import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.backtest import run_backtest
from economia_trader.cli import main
from economia_trader.dashboard import build_html
from economia_trader.exchanges.base import Kline, Ticker
from economia_trader.grid import GridBook, GridBot, GridConfig, buy_and_hold, decide, grid_strategy
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.example.json").read_text()))
HOUR = 3_600_000


def cfg(**kw):
    base = {
        "symbol": "BTCUSDT",
        "lower": "94000",
        "upper": "106000",
        "levels": 6,
        "order_notional": "8",
        "max_lots": 4,
        "stop_pct": "0.03",
    }
    return GridConfig.from_mapping({**base, **kw})


def bars(closes):
    out = []
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c
        out.append(Kline(i * HOUR, D(o), D(max(o, c)) + 10, D(min(o, c)) - 10, D(c), D(1)))
    return out


# ---- config and the limits check ----


def test_levels_stop_and_anchor():
    g = cfg()
    lv = g.prices()
    assert lv[0] == D("94000.00") and lv[-1] == D("106000.00") and len(lv) == 7
    assert all(float(lv[i + 1] / lv[i]) == pytest.approx(float(lv[1] / lv[0]), rel=1e-4) for i in range(6))
    assert g.stop == D("91180.00")
    rel = GridConfig.from_mapping(json.loads((EXAMPLES / "grid.example.json").read_text()))
    assert not rel.anchored and rel.anchor(D("100000")).lower == D("94000.00")
    assert rel.version == GridConfig.from_mapping(json.loads((EXAMPLES / "grid.example.json").read_text())).version
    with pytest.raises(ValueError, match="either"):
        GridConfig.from_mapping({"symbol": "X", "order_notional": "1"})


def test_problems_fail_closed_against_the_limits():
    assert cfg().problems(LIMITS) == []
    assert any("max_order_notional" in p for p in cfg(order_notional="60").problems(LIMITS))
    assert any("max_loss_per_trade" in p for p in cfg(stop_pct="0.5").problems(LIMITS))
    assert any("full stop-out" in p for p in cfg(max_lots=6, order_notional="12").problems(LIMITS))
    assert any("exposure cap" in p for p in cfg(max_lots=6, order_notional="9", stop_pct="0.01").problems(LIMITS))
    assert any("round-trip fees" in p for p in cfg(lower="99900", upper="100000").problems(LIMITS))
    assert any("allowed_symbols" in p for p in cfg(symbol="DOGEUSDT").problems(LIMITS))


# ---- the decision ----


def test_decide_buys_the_level_crossed_and_sells_at_the_next():
    g, book = cfg(), GridBook()
    lv = g.prices()
    buy = decide(g, book, D("99000"), LIMITS)  # between L2 (97,841) and L3 (99,820): lot 3
    assert buy.side == "buy" and buy.stop_loss == g.stop and buy.take_profit == lv[4]
    assert book.lots == {3: buy.qty} and buy.qty == D("0.00008080")
    assert decide(g, book, D("99500"), LIMITS) is None  # lot 3 held, nothing new crossed
    sell = decide(g, book, lv[4], LIMITS)
    assert sell.side == "sell" and sell.qty == buy.qty and book.lots == {}


def test_decide_respects_range_stop_and_cap():
    g = cfg(max_lots=2)
    assert decide(g, GridBook(), D("90000"), LIMITS) is None  # below the range: never buy
    assert decide(g, GridBook(), D("107000"), LIMITS) is None  # above it: nothing to buy
    book = GridBook({3: D("0.0001"), 4: D("0.0001")})
    assert decide(g, book, D("95000"), LIMITS) is None  # cap reached (and no target hit)
    one = GridBook({3: D("0.0001")})
    assert decide(g, one, D("95000"), LIMITS).side == "buy" and set(one.lots) == {1, 3}  # never a level far above


def test_reconcile_undoes_rejected_actions_and_clears_after_a_stop():
    book = GridBook({1: D("0.0001")}, {"side": "buy", "level": 1, "qty": "0.0001"})
    book.reconcile(D("0"))
    assert book.lots == {}
    book = GridBook({}, {"side": "sell", "level": 2, "qty": "0.0002"})
    book.reconcile(D("0.0002"))
    assert book.lots == {2: D("0.0002")}


# ---- backtest: no look-ahead, and the comparison ----


def test_backtest_grid_trades_a_range_and_the_stop_bounds_a_crash():
    sideways = [100000, 98500, 97000, 98500, 100500, 102000, 100500, 98000, 99500, 101500, 103500, 101000] * 4
    run = run_backtest(bars(sideways), grid_strategy(cfg(), LIMITS), symbol="BTCUSDT", limits=LIMITS, cash="100")
    s = run.summary()
    assert s["trades_closed"] >= 6 and D(s["realized_pnl"]) > 0 and s["rejected_by_risk"] == 0
    crash = [100000, 98000, 96000, 94500, 93000, 91000, 88000, 85000]
    run = run_backtest(bars(crash), grid_strategy(cfg(), LIMITS), symbol="BTCUSDT", limits=LIMITS, cash="100")
    loss = -D(run.summary()["realized_pnl"])
    assert loss > 0 and loss <= LIMITS.max_daily_loss  # the stop sold everything; the loss fits the day cap
    hold = buy_and_hold(bars(crash), "100", LIMITS.fee_rate)
    assert D(hold["return_pct"]) < D(run.summary()["return_pct"])


def test_cli_backtest_grid_compares_three(tmp_path, capsys):
    k = tmp_path / "k.json"
    closes = [100000, 98500, 97000, 98500, 100500, 102000, 100500, 98000, 99500, 101500, 103500, 101000] * 3
    k.write_text(
        json.dumps([[b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close), "1"] for b in bars(closes)])
    )
    argv = [
        "backtest",
        "--symbol",
        "BTCUSDT",
        "--limits",
        str(EXAMPLES / "limits.example.json"),
        "--klines-file",
        str(k),
        "--strategy",
        "grid",
        "--grid-config",
        str(EXAMPLES / "grid.example.json"),
        "--cash",
        "100",
    ]
    assert main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out["comparacao"]["return_pct"]) == {"grid", "sma_cross", "buy_and_hold"}
    assert out["levels"][0] == "94000.00"  # anchored on the first bar, not on the future
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"symbol": "BTCUSDT", "range_pct": "0.6", "order_notional": "40", "levels": 6}))
    assert main([*argv[:-4], "--grid-config", str(bad), "--cash", "100"]) == 2
    assert "refused" in json.loads(capsys.readouterr().out)


# ---- the paper loop ----


class Ex:
    name = "fake"
    supports_testnet = False

    def __init__(self, prices):
        self.prices = list(prices)

    def ticker(self, s):
        return Ticker(s, D(self.prices.pop(0)), None, None)


def test_grid_bot_paper_loop_anchors_trades_persists_and_shows(tmp_path):
    t = [datetime(2026, 10, 13, 9, tzinfo=timezone.utc)]

    def clock():
        t[0] += timedelta(hours=1)
        return t[0]

    rel = GridConfig.from_mapping(json.loads((EXAMPLES / "grid.example.json").read_text()))
    prices = ["100000", "98500", "99900"]
    bot = GridBot(
        Ex(prices), mode=Mode.PAPER, limits=LIMITS, config=rel, state_dir=tmp_path, cash="100", env={}, clock=clock
    )
    first = bot.run_once()
    assert first["action"]["side"] == "buy" and first["action"]["status"] == "filled"
    second = bot.run_once()
    assert second["action"]["side"] == "buy" and len(second["lots"]) == 2
    # a new process picks up the same anchored range and lots
    bot2 = GridBot(Ex(["101900"]), mode=Mode.PAPER, limits=LIMITS, config=rel, state_dir=tmp_path, env={}, clock=clock)
    assert bot2.config.lower == D("94000.00")
    third = bot2.run_once()
    assert third["action"]["side"] == "sell" and third["action"]["status"] == "filled"
    page = build_html(tmp_path, now=t[0])
    assert "Grid BTCUSDT" in page and "grid ancorado em 100000" in page


def test_grid_bot_refuses_a_grid_that_does_not_fit(tmp_path):
    big = cfg(order_notional="45", max_lots=6)
    bot = GridBot(Ex(["100000"]), mode=Mode.PAPER, limits=LIMITS, config=big, state_dir=tmp_path, env={})
    out = bot.run_once()
    assert out["refused"] and "action" not in out
