"""The autonomous loop: screen -> propose -> risk -> gate -> order, plus exits and auto-kill.

One ``run_once`` is one tick (e.g. every morning before the open, or every 4h). It is safe to
schedule from cron/systemd: all state lives in ``<state_dir>/state.json`` and every decision in
the journal. Exits run before entries; the kill switch stops both.

Auto-kill engages the kill switch (a human must ``unkill``) when:
- equity falls ``max_drawdown_pct`` below its peak (paper; live equity needs reconciliation), or
- ``max_errors_in_row`` consecutive ticks fail to reach the exchange.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from .backtest import size_for_risk
from .contracts import TradeProposal, dec
from .exchanges.base import INTERVALS, Exchange, ExchangeError
from .flow import FlowSource
from .journal import Journal
from .monitors import EventStore
from .paper import PaperBroker
from .predictions import odds_block
from .risk import Position, RiskLimits
from .safety import Approver, KillSwitch, Mode, deny_all
from .screen import Candidate, ScreenConfig, screen
from .signals import Idea, insider_clusters, sentiment_veto
from .trader import Trader

_EXIT_FIELDS = (
    "stop_pct",
    "take_profit_pct",
    "max_hold_days",
    "max_new_per_run",
    "macro_block_hours",
    "confirm_with",
    "use_flow",
    "insider_signal",
    "insider_window_days",
    "insider_min_count",
    "insider_min_value",
    "sentiment_veto",
    "sentiment_lookback_hours",
    "max_negative_news_share",
    "min_social_bullish_pct",
    "forecast_confirm",
    "forecast_interval",
    "forecast_lookback",
    "forecast_horizon",
    "forecast_min_expected_return",
    "forecast_min_up_share",
    "odds_block",
)
_DEC = (
    "stop_pct",
    "take_profit_pct",
    "max_drawdown_pct",
    "insider_min_value",
    "sentiment_lookback_hours",
    "max_negative_news_share",
    "min_social_bullish_pct",
    "forecast_min_expected_return",
    "forecast_min_up_share",
)
_BOOL = ("use_flow", "insider_signal", "sentiment_veto", "forecast_confirm")
_STR = ("confirm_with", "forecast_interval")
ANALYSTS = ("tradingagents", "ai-hedge-fund")


@dataclass(frozen=True)
class RunConfig:
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    stop_pct: Decimal = Decimal("0.08")
    take_profit_pct: Decimal = Decimal("0.16")
    max_hold_days: int = 15
    max_new_per_run: int = 1
    max_drawdown_pct: Decimal = Decimal("0.15")
    max_errors_in_row: int = 3
    macro_block_hours: Decimal | None = Decimal("24")  # no new entries this close to CPI/NFP/FOMC...; None = off
    confirm_with: str | None = None  # "tradingagents": an LLM analyst must confirm each entry
    use_flow: bool = True  # ideas from the whale screen (options flow)
    insider_signal: bool = False  # ideas from SEC Form 4 insider-buying clusters (events store)
    insider_window_days: int = 10
    insider_min_count: int = 2
    insider_min_value: Decimal = Decimal("100000")
    sentiment_veto: bool = False  # skip entries with mostly negative news / weak social sentiment
    sentiment_lookback_hours: Decimal = Decimal("48")
    max_negative_news_share: Decimal = Decimal("0.6")
    min_social_bullish_pct: Decimal = Decimal("30")
    forecast_confirm: bool = False  # Kronos must forecast a rise before an entry (P-68; never an idea source, P-69)
    forecast_interval: str = "1d"
    forecast_lookback: int = 400  # bars sent to the model (Kronos-small reads at most 512)
    forecast_horizon: int = 5  # bars ahead
    forecast_min_expected_return: Decimal = Decimal("0.01")
    forecast_min_up_share: Decimal = Decimal("0.6")
    # Polymarket odds (read-only): no new entries while a matching market is at/above the threshold,
    # e.g. {"recession": "0.5"}; empty = off. Stored sorted, so the version hash is stable.
    odds_block: tuple[tuple[str, Decimal], ...] = ()

    @property
    def analysts(self) -> tuple[str, ...]:
        return tuple(self.confirm_with.split("+")) if self.confirm_with else ()

    @property
    def version(self) -> str:
        """Strategy version = screen + exits. Stamped on every proposal for per-version results."""
        exits = {k: str(getattr(self, k)) for k in _EXIT_FIELDS}
        blob = json.dumps({"screen": self.screen.version, "exits": exits}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:10]

    @classmethod
    def from_mapping(cls, d: dict[str, Any]) -> RunConfig:
        d = dict(d)
        kw: dict[str, Any] = {"screen": ScreenConfig.from_mapping(d.pop("screen", {}))}
        unknown = set(d) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown run config keys: {sorted(unknown)}")
        for k, v in d.items():
            if k in _STR:
                kw[k] = v
            elif k == "odds_block":
                kw[k] = tuple(sorted((str(pat), dec(p)) for pat, p in dict(v).items()))
            elif k == "macro_block_hours":
                kw[k] = dec(v) if v is not None else None
            elif k in _BOOL:
                kw[k] = bool(v)
            else:
                kw[k] = dec(v) if k in _DEC else int(v)
        cfg = cls(**kw)
        bad = sorted(set(cfg.analysts) - set(ANALYSTS))
        if bad:
            raise ValueError(f"confirm_with: unknown analysts {bad}; use {ANALYSTS} joined by '+'")
        if any(not (0 < p <= 1) for _, p in cfg.odds_block):
            raise ValueError("odds_block probabilities must be in (0, 1]")
        if cfg.forecast_interval not in INTERVALS:
            raise ValueError(f"forecast_interval must be one of {INTERVALS}")
        return cfg


def _now() -> datetime:
    return datetime.now(timezone.utc)


def idea_from_flow(c: Candidate) -> Idea:
    rationale = (
        f"whale flow: {c.bullish_pct:.0%} bullish (${c.bullish_premium:,.0f} vs ${c.bearish_premium:,.0f}), "
        f"IVR {c.iv_rank}, vol/oi {c.vol_oi}, largest ${c.largest_order:,.0f}"
    )
    return Idea(c.ticker, "flow", c.print_ids, rationale, c.bullish_premium)


def merge_ideas(ideas: list[Idea]) -> list[Idea]:
    """One idea per ticker; when several screens agree, evidence and rationale are combined."""
    out: dict[str, Idea] = {}
    for i in ideas:
        if i.ticker in out:
            o = out[i.ticker]
            out[i.ticker] = Idea(
                i.ticker,
                f"{o.source}+{i.source}",
                tuple(sorted(set(o.evidence_ids + i.evidence_ids))),
                f"{o.rationale} | {i.rationale}",
                o.score + i.score,
            )
        else:
            out[i.ticker] = i
    return sorted(out.values(), key=lambda x: ("+" in x.source, x.score), reverse=True)


def propose(
    idea: Idea, price: Decimal, *, config: RunConfig, limits: RiskLimits, extra_evidence: tuple[str, ...] = ()
) -> TradeProposal | None:
    """Turn an idea into a proposal on the *stock* (never the option)."""
    stop = (price * (1 - config.stop_pct)).quantize(Decimal("0.01"))
    qty = size_for_risk(price, stop, limits)
    if qty <= 0:
        return None
    return TradeProposal(
        idea.ticker,
        "buy",
        qty,
        stop_loss=stop,
        take_profit=(price * (1 + config.take_profit_pct)).quantize(Decimal("0.01")),
        rationale=idea.rationale,
        evidence_ids=idea.evidence_ids + extra_evidence,
        proposer=f"{'whale-screen' if idea.source == 'flow' else idea.source}@{config.version}",
    )


class Runner:
    def __init__(
        self,
        exchange: Exchange,
        source: FlowSource,
        *,
        mode: Mode,
        limits: RiskLimits,
        config: RunConfig,
        state_dir: str | Path,
        cash: Decimal | str = "100",
        kill_switch: KillSwitch | None = None,
        approver: Approver = deny_all,
        env: Mapping[str, str] | None = None,
        clock: Callable[[], datetime] = _now,
        events: EventStore | None = None,
        analyst: Any = None,
        forecaster: Any = None,
    ) -> None:
        self.exchange, self.source, self.mode, self.limits, self.config = exchange, source, mode, limits, config
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "state.json"
        self.clock = clock
        self.events = events
        # One analyst or several ("tradingagents+ai-hedge-fund"): each must confirm, in order.
        self.analysts: list[Any] = list(analyst) if isinstance(analyst, (list, tuple)) else [analyst] * bool(analyst)
        self.forecaster = forecaster  # a forecast.ForecastConfirmer
        if config.confirm_with and not self.analysts:
            raise ValueError(f"config.confirm_with={config.confirm_with!r} needs an analyst")
        if config.forecast_confirm and forecaster is None:
            raise ValueError("config.forecast_confirm needs a forecaster (forecast.ForecastConfirmer)")
        self.kill_switch = kill_switch or KillSwitch(self.state_dir / "KILL", env=env)
        self.journal = Journal(self.state_dir / "journal.jsonl")
        st = self._load(cash)
        self.trader = Trader(
            exchange,
            mode=mode,
            limits=limits,
            journal=self.journal,
            broker=st["broker"],
            kill_switch=self.kill_switch,
            approver=approver,
            env=env,
        )
        if mode is not Mode.PAPER:
            self.trader._state.positions.update(st["positions"])
            self.trader._state.realized_today = st["realized_today"]
        self.trader.stops.update(st["stops"])
        self.meta: dict[str, dict[str, Any]] = st["meta"]
        self.peak = st["peak"]
        self.day = st["day"]
        self.errors_in_row = st["errors_in_row"]
        self.used_prints: set[str] = st["used_prints"]

    # ---- state ----

    def _load(self, cash: Decimal | str) -> dict[str, Any]:
        raw: dict[str, Any] = {}
        if self.state_path.exists():
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        broker = None
        if self.mode is Mode.PAPER:
            broker = PaperBroker.from_dict(raw["broker"]) if raw.get("broker") else PaperBroker(cash)
        return {
            "broker": broker,
            "positions": {s: Position(dec(p["qty"]), dec(p["avg_price"])) for s, p in raw.get("positions", {}).items()},
            "realized_today": dec(raw.get("realized_today", "0")),
            "stops": {s: dec(v) for s, v in raw.get("stops", {}).items()},
            "meta": raw.get("meta", {}),
            "peak": dec(raw["peak"]) if raw.get("peak") else None,
            "day": raw.get("day"),
            "errors_in_row": int(raw.get("errors_in_row", 0)),
            "used_prints": set(raw.get("used_prints", [])),
        }

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
            "meta": self.meta,
            "peak": str(self.peak) if self.peak is not None else None,
            "day": self.day,
            "errors_in_row": self.errors_in_row,
            "used_prints": sorted(self.used_prints),
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    # ---- one tick ----

    def run_once(self) -> dict[str, Any]:
        now = self.clock()
        as_of = now.isoformat(timespec="seconds")
        summary: dict[str, Any] = {"as_of": as_of, "version": self.config.version, "mode": self.mode.value}
        today = as_of[:10]
        if self.day != today:
            self.trader.state.realized_today = Decimal(0)
            self.day = today

        held = list(self.trader.state.positions)
        try:
            marks = {s: self.exchange.ticker(s).last for s in held}
            self.errors_in_row = 0
        except ExchangeError as exc:
            self.errors_in_row += 1
            self.journal.append("run_error", {"as_of": as_of, "error": str(exc), "in_row": self.errors_in_row})
            if self.errors_in_row >= self.config.max_errors_in_row:
                self._auto_kill(f"{self.errors_in_row} ticks in a row without the exchange")
            self._save()
            return {**summary, "error": str(exc)}

        summary["exits"] = self._exits(marks, now)
        summary["auto_kill"] = self._check_drawdown(marks)

        result = screen(self.source.prints(as_of), self.config.screen, as_of)
        summary["screen"] = {
            "candidates": [c.ticker for c in result.candidates],
            "dropped": len(result.dropped),
            "prints": result.prints_kept,
        }
        ideas = [idea_from_flow(c) for c in result.candidates] if self.config.use_flow else []
        all_events = self.events.all() if self.events is not None else []
        if self.config.insider_signal:
            clusters = insider_clusters(
                all_events,
                as_of,
                window_days=self.config.insider_window_days,
                min_insiders=self.config.insider_min_count,
                min_value=self.config.insider_min_value,
            )
            summary["insiders"] = [i.ticker for i in clusters]
            ideas += clusters
        ideas = merge_ideas(ideas)
        entries: list[dict[str, Any]] = []
        if self.events is not None and self.config.macro_block_hours is not None:
            near = self.events.high_impact_within(as_of, float(self.config.macro_block_hours))
            if near:
                summary["macro_block"] = sorted({e["payload"]["name"] for e in near})
                summary["entries"] = []
                self.journal.append("macro_block", {"as_of": as_of, "releases": summary["macro_block"]})
                self.journal.append("run", summary)
                self._save()
                return summary
        if self.events is not None and self.config.odds_block:
            odds = odds_block(all_events, as_of, self.config.odds_block)
            if odds:
                summary["odds_block"] = odds
                summary["entries"] = []
                self.journal.append("odds_block", {"as_of": as_of, "reasons": odds})
                self.journal.append("run", summary)
                self._save()
                return summary
        for cand in ideas:
            if len(entries) >= self.config.max_new_per_run:
                break
            if cand.ticker in self.trader.state.positions:
                continue
            if set(cand.evidence_ids) <= self.used_prints:
                continue  # same evidence already traded: wait for new evidence
            if self.config.sentiment_veto:
                veto = sentiment_veto(
                    all_events,
                    cand.ticker,
                    as_of,
                    lookback_hours=float(self.config.sentiment_lookback_hours),
                    max_negative_share=float(self.config.max_negative_news_share),
                    min_bullish_pct=float(self.config.min_social_bullish_pct),
                )
                if veto:
                    self.journal.append("sentiment_veto", {"ticker": cand.ticker, "reasons": veto})
                    entries.append({"ticker": cand.ticker, "status": "vetoed", "reasons": veto})
                    continue
            try:
                price = self.exchange.ticker(cand.ticker).last
            except ExchangeError as exc:
                self.journal.append("error", {"ticker": cand.ticker, "error": str(exc)})
                continue
            extra: tuple[str, ...] = ()
            if self.config.forecast_confirm:
                veto = self._forecast_veto(cand.ticker, today)
                if veto:
                    entries.append({"ticker": cand.ticker, "status": "vetoed", "reasons": [veto]})
                    continue
            if self.config.confirm_with:
                veto, extra = self._second_opinions(cand.ticker, today)
                if veto:
                    entries.append({"ticker": cand.ticker, "status": "vetoed", "reasons": [veto]})
                    continue
            proposal = propose(cand, price, config=self.config, limits=self.limits, extra_evidence=extra)
            if proposal is None:
                continue
            out = self.trader.submit(proposal, price)
            if out.status in ("filled", "sent"):
                self.used_prints.update(cand.evidence_ids)
                self.meta[cand.ticker] = {
                    "entry_at": as_of,
                    "take_profit": str(proposal.take_profit),
                    "version": self.config.version,
                    "source": cand.source,
                }
            entries.append({"ticker": cand.ticker, "status": out.status, "reasons": out.reasons})
        summary["entries"] = entries
        self.journal.append("run", summary)
        self._save()
        return summary

    def _second_opinions(self, ticker: str, day: str) -> tuple[str | None, tuple[str, ...]]:
        """Ask each analyst in turn; the first that does not confirm vetoes (the rest are not paid for)."""
        evidence: list[str] = []
        for an in self.analysts:
            by = getattr(an, "name", self.config.confirm_with)
            op = an.opinion(ticker, day)
            self.journal.append(
                "opinion",
                {
                    "ticker": ticker,
                    "rating": op.rating,
                    "confirms": op.confirms,
                    "evidence": op.evidence_path,
                    "usage": op.usage,
                    "by": by,
                },
            )
            if not op.confirms:
                return f"analyst {by}: {op.rating}", ()
            evidence.append(f"opinion:{op.evidence_path}")
        return None, tuple(evidence)

    def _forecast_veto(self, ticker: str, day: str) -> str | None:
        """Ask the forecaster (Kronos) on recent bars; anything but a confirmed rise is a veto (fail-closed)."""
        try:
            bars = self.exchange.klines(ticker, self.config.forecast_interval, self.config.forecast_lookback)
            op = self.forecaster.opinion(ticker, bars, day)
        except Exception as exc:  # a broken model must block the entry, not the tick
            self.journal.append("forecast", {"ticker": ticker, "rating": "ERROR", "confirms": False, "error": str(exc)})
            return f"forecast: ERROR ({type(exc).__name__})"
        self.journal.append(
            "forecast",
            {
                "ticker": ticker,
                "rating": op.rating,
                "confirms": op.confirms,
                "expected_return": op.expected_return,
                "up_share": op.up_share,
                "detail": op.detail,
                "by": getattr(self.forecaster, "name", "kronos"),
            },
        )
        return None if op.confirms else f"forecast: {op.rating} ({op.detail})"

    def _exits(self, marks: dict[str, Decimal], now: datetime) -> list[dict[str, Any]]:
        out = [
            {"proposal_id": o.proposal_id, "status": o.status, "why": "stop"} for o in self.trader.check_stops(marks)
        ]
        for sym, meta in list(self.meta.items()):
            held = self.trader.state.positions.get(sym)
            if not held:
                self.meta.pop(sym, None)
                continue
            why = None
            if meta.get("take_profit") and marks.get(sym, Decimal(0)) >= dec(meta["take_profit"]):
                why = "take-profit"
            elif now - datetime.fromisoformat(meta["entry_at"]) >= timedelta(days=self.config.max_hold_days):
                why = "time-exit"
            if why:
                res = self.trader.submit(TradeProposal(sym, "sell", held.qty, rationale=why, proposer=why), marks[sym])
                out.append({"ticker": sym, "status": res.status, "why": why})
                if res.status in ("filled", "sent"):
                    self.meta.pop(sym, None)
        return out

    def _check_drawdown(self, marks: dict[str, Decimal]) -> str | None:
        if self.trader.broker is None:
            return None  # live equity needs reconciliation with the exchange (next step)
        equity = self.trader.broker.equity(marks)
        self.peak = max(self.peak or equity, equity)
        if self.peak > 0 and (self.peak - equity) / self.peak >= self.config.max_drawdown_pct:
            return self._auto_kill(f"drawdown {(self.peak - equity) / self.peak:.1%} from peak {self.peak:.2f}")
        return None

    def _auto_kill(self, reason: str) -> str:
        if not self.kill_switch.engaged():
            self.kill_switch.engage(f"auto-kill: {reason}\n")
            self.journal.append("auto_kill", {"reason": reason})
        return reason

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
