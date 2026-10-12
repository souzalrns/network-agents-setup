"""A bounded spot grid for crypto (decision of 2026-10-12): buy-only, inside a price range, with a cap on
how much it accumulates and one stop below the range. Every order goes through the same risk engine,
gate, kill switch and journal as everything else; there is no exchange-side bot.

How it trades (one decision per tick, sells first):

- the range ``[lower, upper]`` is cut into ``levels`` steps (geometric by default);
- a lot ``i`` is bought when the price is at or below level ``L_i`` (and still inside the range), for
  ``order_notional`` of quote currency;
- that lot is sold when the price reaches the next level ``L_{i+1}``;
- at most ``max_lots`` lots are held; below the range nothing new is bought;
- all lots share one stop, ``lower * (1 - stop_pct)``: the trader's stop sells everything there.

Before it starts, ``GridConfig.problems(limits)`` checks that the grid fits the risk limits at its worst:
each lot's loss at the stop fits ``max_loss_per_trade``, the full inventory fits the exposure cap, a full
stop-out on one day fits ``max_daily_loss``, and each step pays more than the fees of a round trip.

A grid earns in sideways markets and loses in a strong fall (the stop bounds that). Prove it in the backtest
against buy-and-hold and ``sma_cross`` before paper, and in paper before anything else.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

from .backtest import Strategy
from .contracts import TradeProposal, dec
from .exchanges.base import Exchange, ExchangeError, Kline
from .journal import Journal
from .paper import PaperBroker
from .risk import PortfolioState, Position, RiskLimits
from .safety import Approver, KillSwitch, Mode, deny_all
from .trader import Trader

QTY_STEP = Decimal("0.00000001")


@dataclass(frozen=True)
class GridConfig:
    symbol: str
    order_notional: Decimal
    levels: int = 6
    lower: Decimal | None = None  # absolute range...
    upper: Decimal | None = None
    range_pct: Decimal | None = None  # ...or a range around the first price seen (anchored once, then fixed)
    stop_pct: Decimal = Decimal("0.03")
    max_lots: int | None = None  # default: all levels
    spacing: str = "geometric"
    max_drawdown_pct: Decimal = Decimal("0.15")

    @classmethod
    def from_mapping(cls, d: Mapping[str, Any]) -> GridConfig:
        d = dict(d)
        unknown = set(d) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown grid config keys: {sorted(unknown)}")
        for k in ("order_notional", "lower", "upper", "range_pct", "stop_pct", "max_drawdown_pct"):
            if d.get(k) is not None:
                d[k] = dec(d[k])
        for k in ("levels", "max_lots"):
            if d.get(k) is not None:
                d[k] = int(d[k])
        d["symbol"] = str(d["symbol"]).upper()
        cfg = cls(**d)
        if (cfg.lower is None) == (cfg.range_pct is None):
            raise ValueError("give either lower+upper or range_pct")
        if cfg.spacing not in ("geometric", "arithmetic"):
            raise ValueError("spacing must be geometric or arithmetic")
        return cfg

    @property
    def version(self) -> str:
        blob = json.dumps({k: str(v) for k, v in asdict(self).items()}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:10]

    @property
    def anchored(self) -> bool:
        return self.lower is not None and self.upper is not None

    def anchor(self, price: Decimal) -> GridConfig:
        """A relative grid becomes absolute around ``price`` (the first price seen; never moved later)."""
        if self.anchored:
            return self
        half = (self.range_pct or Decimal(0)) / 2
        return replace(
            self,
            lower=(price * (1 - half)).quantize(Decimal("0.01")),
            upper=(price * (1 + half)).quantize(Decimal("0.01")),
        )

    def prices(self) -> list[Decimal]:
        lo, hi, n = self.lower, self.upper, self.levels
        if lo is None or hi is None:
            raise ValueError("grid not anchored")
        if self.spacing == "arithmetic":
            step = (hi - lo) / n
            return [(lo + step * i).quantize(Decimal("0.01")) for i in range(n + 1)]
        ratio = (hi / lo) ** (Decimal(1) / n)
        return [(lo * ratio**i).quantize(Decimal("0.01")) for i in range(n + 1)]

    @property
    def stop(self) -> Decimal:
        if self.lower is None:
            raise ValueError("grid not anchored")
        return (self.lower * (1 - self.stop_pct)).quantize(Decimal("0.01"))

    @property
    def lots_cap(self) -> int:
        return min(self.max_lots or self.levels, self.levels)

    def problems(self, limits: RiskLimits) -> list[str]:
        """Why this grid does not fit the risk limits at its worst (empty = fits)."""
        out = []
        if self.lower is None or self.upper is None or self.upper <= self.lower:
            return ["the range needs lower < upper"]
        if self.levels < 2:
            out.append("levels must be >= 2")
        if self.order_notional <= 0:
            out.append("order_notional must be > 0")
        if self.order_notional > limits.max_order_notional:
            out.append(f"order_notional {self.order_notional} > max_order_notional {limits.max_order_notional}")
        if self.symbol not in limits.allowed_symbols and "*" not in limits.allowed_symbols:
            out.append(f"{self.symbol} is not in allowed_symbols")
        lv = self.prices()
        fees = limits.fee_rate * 2
        if min(lv[i + 1] / lv[i] - 1 for i in range(self.levels)) <= fees:
            out.append(f"a grid step must pay more than the round-trip fees ({fees:.2%})")
        # worst case: the lots_cap highest buy levels all filled, then the stop
        losses = sorted(
            ((p - self.stop) / p * self.order_notional + self.order_notional * fees for p in lv[:-1]), reverse=True
        )
        if losses[0] > limits.max_loss_per_trade:
            out.append(f"one lot can lose {losses[0]:.2f} at the stop > max_loss_per_trade {limits.max_loss_per_trade}")
        worst = sum(losses[: self.lots_cap], Decimal(0))
        if worst > limits.max_daily_loss:
            out.append(f"a full stop-out loses {worst:.2f} > max_daily_loss {limits.max_daily_loss}")
        if self.order_notional * self.lots_cap > limits.exposure_cap:
            out.append(f"full inventory {self.order_notional * self.lots_cap} > exposure cap {limits.exposure_cap}")
        return out


@dataclass
class GridBook:
    """Lots held by level, plus the last action awaiting confirmation (an order may be rejected)."""

    lots: dict[int, Decimal] = field(default_factory=dict)
    pending: dict[str, Any] | None = None

    def reconcile(self, held_qty: Decimal) -> None:
        """Make the lots agree with the position the broker/trader actually holds."""
        p, self.pending = self.pending, None
        if p and p["side"] == "buy" and held_qty + QTY_STEP < sum(self.lots.values(), Decimal(0)):
            self.lots.pop(p["level"], None)  # the buy did not go through
        elif p and p["side"] == "sell" and held_qty > sum(self.lots.values(), Decimal(0)) + QTY_STEP:
            self.lots[p["level"]] = dec(p["qty"])  # the sell did not go through
        if held_qty <= 0:
            self.lots.clear()  # stopped out (or never filled)
        while self.lots and sum(self.lots.values(), Decimal(0)) > held_qty + QTY_STEP:
            self.lots.pop(max(self.lots))

    def to_dict(self) -> dict[str, Any]:
        return {"lots": {str(k): str(v) for k, v in self.lots.items()}, "pending": self.pending}

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> GridBook:
        return cls({int(k): dec(v) for k, v in (d.get("lots") or {}).items()}, d.get("pending"))


def decide(cfg: GridConfig, book: GridBook, price: Decimal, limits: RiskLimits) -> TradeProposal | None:
    """One action for this price: sell a lot whose target was reached, else buy the level just crossed."""
    lv = cfg.prices()
    for i in sorted(book.lots):
        if price >= lv[i + 1]:
            book.pending = {"side": "sell", "level": i, "qty": str(book.lots[i])}
            qty = book.lots.pop(i)
            return TradeProposal(
                cfg.symbol, "sell", qty, rationale=f"grid: level {i} target {lv[i + 1]}", proposer=f"grid@{cfg.version}"
            )
    if price < lv[0] or price <= cfg.stop or len(book.lots) >= cfg.lots_cap:
        return None
    # only the level immediately above the price (the one just crossed), and only if not held yet
    i = next((j for j in range(cfg.levels + 1) if lv[j] >= price), cfg.levels)
    if i >= cfg.levels or i in book.lots:
        return None
    qty = (cfg.order_notional / price).quantize(QTY_STEP, rounding=ROUND_DOWN)
    if qty <= 0:
        return None
    book.lots[i] = qty
    book.pending = {"side": "buy", "level": i, "qty": str(qty)}
    return TradeProposal(
        cfg.symbol,
        "buy",
        qty,
        stop_loss=cfg.stop,
        take_profit=lv[i + 1],
        rationale=f"grid: buy level {i} at <= {lv[i]}, sell at {lv[i + 1]}",
        proposer=f"grid@{cfg.version}",
    )


def grid_strategy(cfg: GridConfig, limits: RiskLimits) -> Strategy:
    """The grid as a backtest strategy (anchored on the first bar it sees, if relative)."""
    state: dict[str, Any] = {"cfg": cfg if cfg.anchored else None, "book": GridBook()}

    def strategy(bars: list[Kline], book_state: PortfolioState, lim: RiskLimits, symbol: str) -> TradeProposal | None:
        price = bars[-1].close
        if state["cfg"] is None:
            state["cfg"] = cfg.anchor(price)
        held = book_state.positions.get(symbol)
        state["book"].reconcile(held.qty if held else Decimal(0))
        return decide(state["cfg"], state["book"], price, lim)

    strategy.__name__ = f"grid({cfg.levels},{cfg.version})"
    return strategy


def buy_and_hold(bars: list[Kline], cash: Decimal | str, fee_rate: Decimal) -> dict[str, Any]:
    """The benchmark: all in at the first open, marked to every close."""
    cash = dec(cash)
    qty = cash * (1 - fee_rate) / bars[0].open
    curve = [qty * b.close for b in bars]
    peak, dd = Decimal(0), Decimal(0)
    for eq in curve:
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak if peak else Decimal(0))
    final = curve[-1] * (1 - fee_rate)
    return {
        "strategy": "buy_and_hold",
        "return_pct": str(((final / cash - 1) * 100).quantize(Decimal("0.01"))),
        "max_drawdown_pct": str((dd * 100).quantize(Decimal("0.01"))),
        "trades_closed": 1,
    }


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GridBot:
    """The live/paper loop: one tick = stop check, reconcile, one grid action, auto-kill on drawdown."""

    def __init__(
        self,
        exchange: Exchange,
        *,
        mode: Mode,
        limits: RiskLimits,
        config: GridConfig,
        state_dir: str | Path,
        cash: Decimal | str = "100",
        kill_switch: KillSwitch | None = None,
        approver: Approver = deny_all,
        env: Mapping[str, str] | None = None,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.exchange, self.mode, self.limits, self.clock = exchange, mode, limits, clock
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "state.json"
        self.kill_switch = kill_switch or KillSwitch(self.state_dir / "KILL", env=env)
        self.journal = Journal(self.state_dir / "journal.jsonl")
        raw = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {}
        grid = raw.get("grid") or {}
        self.config = config
        if grid.get("lower") and not config.anchored:  # keep the range anchored on the first run
            self.config = replace(config, lower=dec(grid["lower"]), upper=dec(grid["upper"]))
        self.book = GridBook.from_dict(grid)
        broker = None
        if mode is Mode.PAPER:
            broker = (
                PaperBroker.from_dict(raw["broker"])
                if raw.get("broker")
                else PaperBroker(cash, fee_rate=limits.fee_rate)
            )
        self.trader = Trader(
            exchange,
            mode=mode,
            limits=limits,
            journal=self.journal,
            broker=broker,
            kill_switch=self.kill_switch,
            approver=approver,
            env=env,
        )
        if mode is not Mode.PAPER:
            self.trader._state.positions.update(
                {s: Position(dec(p["qty"]), dec(p["avg_price"])) for s, p in raw.get("positions", {}).items()}
            )
            self.trader._state.realized_today = dec(raw.get("realized_today", "0"))
        self.trader.stops.update({s: dec(v) for s, v in raw.get("stops", {}).items()})
        self.peak = dec(raw["peak"]) if raw.get("peak") else None
        self.day = raw.get("day")

    def _save(self) -> None:
        st = self.trader.state
        data = {
            "mode": self.mode.value,
            "exchange": self.exchange.name,
            "config_version": self.config.version,
            "broker": self.trader.broker.to_dict() if self.trader.broker else None,
            "positions": {s: {"qty": str(p.qty), "avg_price": str(p.avg_price)} for s, p in st.positions.items()},
            "realized_today": str(st.realized_today),
            "stops": {s: str(v) for s, v in self.trader.stops.items()},
            "meta": {},
            "peak": str(self.peak) if self.peak is not None else None,
            "day": self.day,
            "grid": {
                "symbol": self.config.symbol,
                "lower": str(self.config.lower) if self.config.lower is not None else None,
                "upper": str(self.config.upper) if self.config.upper is not None else None,
                "levels": [str(p) for p in self.config.prices()] if self.config.anchored else [],
                "stop": str(self.config.stop) if self.config.anchored else None,
                **self.book.to_dict(),
            },
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    def run_once(self) -> dict[str, Any]:
        as_of = self.clock().isoformat(timespec="seconds")
        sym = self.config.symbol
        summary: dict[str, Any] = {
            "as_of": as_of,
            "version": self.config.version,
            "mode": self.mode.value,
            "strategy": "grid",
            "symbol": sym,
        }
        if self.day != as_of[:10]:
            self.trader.state.realized_today = Decimal(0)
            if self.trader.broker:
                self.trader.broker.new_day()
            self.day = as_of[:10]
        try:
            price = self.exchange.ticker(sym).last
        except ExchangeError as exc:
            self.journal.append("run_error", {"as_of": as_of, "error": str(exc)})
            self._save()
            return {**summary, "error": str(exc)}
        if not self.config.anchored:
            self.config = self.config.anchor(price)
            self.journal.append(
                "grid_anchor", {"symbol": sym, "price": str(price), "levels": [str(p) for p in self.config.prices()]}
            )
        problems = self.config.problems(self.limits)
        if problems:  # fail-closed: a grid that does not fit the limits never trades
            self.journal.append("grid_refused", {"problems": problems})
            self._save()
            return {**summary, "refused": problems}
        summary["exits"] = [o.status for o in self.trader.check_stops({sym: price})]
        held = self.trader.state.positions.get(sym)
        self.book.reconcile(held.qty if held else Decimal(0))
        if self.trader.broker is not None:
            equity = self.trader.broker.equity({sym: price})
            self.peak = max(self.peak or equity, equity)
            if self.peak > 0 and (self.peak - equity) / self.peak >= self.config.max_drawdown_pct:
                if not self.kill_switch.engaged():
                    self.kill_switch.engage(f"auto-kill: grid drawdown from {self.peak:.2f}\n")
                    self.journal.append("auto_kill", {"reason": f"grid drawdown from peak {self.peak:.2f}"})
        proposal = decide(self.config, self.book, price, self.limits)
        if proposal is not None:
            out = self.trader.submit(proposal, price)
            summary["action"] = {
                "side": proposal.side,
                "qty": str(proposal.qty),
                "status": out.status,
                "reasons": out.reasons,
            }
            if out.status not in ("filled", "sent"):
                held = self.trader.state.positions.get(sym)
                self.book.reconcile(held.qty if held else Decimal(0))
        summary["lots"] = {str(k): str(v) for k, v in sorted(self.book.lots.items())}
        summary["price"] = str(price)
        self.journal.append("run", summary)
        self._save()
        return summary

    def run_forever(
        self, every_s: float, *, max_ticks: int | None = None, sleep: Callable[[float], None] = time.sleep
    ) -> int:
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            self.run_once()
            ticks += 1
            if max_ticks is None or ticks < max_ticks:
                sleep(every_s)
        return ticks
