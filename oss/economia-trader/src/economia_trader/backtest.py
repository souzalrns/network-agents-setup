"""Offline replay of a strategy over historical klines, through the *same* risk engine, gate
and paper broker the live loop uses. No look-ahead: a decision taken on bar ``i`` (seeing only
bars ``0..i``) fills at bar ``i+1``'s open; stops are checked against each bar's low.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from .contracts import SimulationRun, TradeProposal
from .exchanges.base import Kline
from .paper import PaperBroker
from .risk import PortfolioState, RiskLimits
from .safety import KillSwitch, Mode
from .trader import Trader

# A strategy sees the bars so far and the book, and may propose one trade.
Strategy = Callable[[list[Kline], PortfolioState, RiskLimits, str], TradeProposal | None]


class NullJournal:
    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {}


def size_for_risk(price: Decimal, stop: Decimal, limits: RiskLimits) -> Decimal:
    """Largest qty whose loss at stop (incl. fees) and notional both fit the limits."""
    per_unit = (price - stop) + price * limits.fee_rate * 2
    if per_unit <= 0:
        return Decimal(0)
    qty = min(limits.max_loss_per_trade / per_unit, limits.max_order_notional / price)
    return qty.quantize(Decimal("0.000001"), rounding="ROUND_DOWN")


def sma_cross(fast: int = 10, slow: int = 30, stop_pct: Decimal = Decimal("0.03")) -> Strategy:
    """Baseline, not alpha: long on fast-over-slow SMA cross, flat on the cross back."""

    def strategy(bars: list[Kline], state: PortfolioState, limits: RiskLimits, symbol: str) -> TradeProposal | None:
        if len(bars) < slow + 1:
            return None
        closes = [b.close for b in bars]

        def sma(n: int, end: int) -> Decimal:
            return sum(closes[end - n : end], Decimal(0)) / n

        now_f, now_s = sma(fast, len(closes)), sma(slow, len(closes))
        prev_f, prev_s = sma(fast, len(closes) - 1), sma(slow, len(closes) - 1)
        price = closes[-1]
        held = state.positions.get(symbol)
        if not held and prev_f <= prev_s and now_f > now_s:
            stop = price * (1 - stop_pct)
            qty = size_for_risk(price, stop, limits)
            if qty > 0:
                return TradeProposal(
                    symbol,
                    "buy",
                    qty,
                    stop_loss=stop.quantize(Decimal("0.0001")),
                    rationale=f"sma{fast}>sma{slow}",
                    proposer="sma_cross",
                )
        if held and prev_f >= prev_s and now_f < now_s:
            return TradeProposal(symbol, "sell", held.qty, rationale=f"sma{fast}<sma{slow}", proposer="sma_cross")
        return None

    strategy.__name__ = f"sma_cross({fast},{slow})"
    return strategy


class _NoExchange:
    name = "backtest"
    supports_testnet = False

    def ticker(self, symbol: str) -> Any:  # pragma: no cover - backtest always passes the mark
        raise RuntimeError("backtest passes marks explicitly")


def run_backtest(
    bars: list[Kline],
    strategy: Strategy,
    *,
    symbol: str,
    limits: RiskLimits,
    cash: Decimal | str = "1000",
    exchange_name: str = "bybit",
    journal: Any = None,
) -> SimulationRun:
    broker = PaperBroker(cash, fee_rate=limits.fee_rate)
    # A backtest must never be stopped or redirected by the operator's live kill switch/env.
    trader = Trader(
        _NoExchange(),
        mode=Mode.PAPER,
        limits=limits,
        journal=journal or NullJournal(),  # type: ignore[arg-type]
        broker=broker,
        kill_switch=KillSwitch("/nonexistent/economia-trader-backtest", env={}),
        env={},
    )
    run = SimulationRun(exchange_name, symbol, getattr(strategy, "__name__", "strategy"), broker.cash)
    day = None
    pending: TradeProposal | None = None
    for i, bar in enumerate(bars):
        d = datetime.fromtimestamp(bar.open_time_ms / 1000, tz=timezone.utc).date()
        if d != day:
            broker.new_day()
            day = d
        if pending is not None:  # decided on the previous close, fills at this open
            out = trader.submit(pending, bar.open)
            run.rejected += out.status == "rejected"
            run.blocked += out.status == "blocked"
            if out.fill:
                run.fills.append(out.fill)
            pending = None
        stop = trader.stops.get(symbol)
        if stop is not None and bar.low <= stop:
            for out in trader.check_stops({symbol: min(stop, bar.open)}):
                if out.fill:
                    run.fills.append(out.fill)
        run.equity_curve.append(broker.equity({symbol: bar.close}))
        if i + 1 < len(bars):
            pending = strategy(bars[: i + 1], broker.state, limits, symbol)
    return run
