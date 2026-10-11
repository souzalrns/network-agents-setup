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
from .exchanges.base import Exchange, ExchangeError
from .flow import FlowSource
from .journal import Journal
from .monitors import EventStore
from .paper import PaperBroker
from .risk import Position, RiskLimits
from .safety import Approver, KillSwitch, Mode, deny_all
from .screen import Candidate, ScreenConfig, screen
from .trader import Trader

_EXIT_FIELDS = ("stop_pct", "take_profit_pct", "max_hold_days", "max_new_per_run", "macro_block_hours", "confirm_with")


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
            if k == "confirm_with":
                kw[k] = v
            elif k == "macro_block_hours":
                kw[k] = dec(v) if v is not None else None
            else:
                kw[k] = dec(v) if k in ("stop_pct", "take_profit_pct", "max_drawdown_pct") else int(v)
        return cls(**kw)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def propose(
    candidate: Candidate, price: Decimal, *, config: RunConfig, limits: RiskLimits, extra_evidence: tuple[str, ...] = ()
) -> TradeProposal | None:
    """Turn a screened ticker into a proposal on the *stock* (never the option)."""
    stop = (price * (1 - config.stop_pct)).quantize(Decimal("0.01"))
    qty = size_for_risk(price, stop, limits)
    if qty <= 0:
        return None
    rationale = (
        f"whale flow: {candidate.bullish_pct:.0%} bullish (${candidate.bullish_premium:,.0f} vs "
        f"${candidate.bearish_premium:,.0f}), IVR {candidate.iv_rank}, vol/oi {candidate.vol_oi}, "
        f"largest ${candidate.largest_order:,.0f}"
    )
    return TradeProposal(
        candidate.ticker,
        "buy",
        qty,
        stop_loss=stop,
        take_profit=(price * (1 + config.take_profit_pct)).quantize(Decimal("0.01")),
        rationale=rationale,
        evidence_ids=candidate.print_ids + extra_evidence,
        proposer=f"whale-screen@{config.version}",
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
    ) -> None:
        self.exchange, self.source, self.mode, self.limits, self.config = exchange, source, mode, limits, config
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "state.json"
        self.clock = clock
        self.events = events
        self.analyst = analyst
        if config.confirm_with and analyst is None:
            raise ValueError(f"config.confirm_with={config.confirm_with!r} needs an analyst")
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
        for cand in result.candidates:
            if len(entries) >= self.config.max_new_per_run:
                break
            if cand.ticker in self.trader.state.positions:
                continue
            if set(cand.print_ids) <= self.used_prints:
                continue  # same evidence already traded: wait for new flow
            try:
                price = self.exchange.ticker(cand.ticker).last
            except ExchangeError as exc:
                self.journal.append("error", {"ticker": cand.ticker, "error": str(exc)})
                continue
            extra: tuple[str, ...] = ()
            if self.analyst is not None and self.config.confirm_with:
                op = self.analyst.opinion(cand.ticker, today)
                self.journal.append(
                    "opinion",
                    {
                        "ticker": cand.ticker,
                        "rating": op.rating,
                        "confirms": op.confirms,
                        "evidence": op.evidence_path,
                        "usage": op.usage,
                        "by": self.config.confirm_with,
                    },
                )
                if not op.confirms:
                    entries.append({"ticker": cand.ticker, "status": "vetoed", "reasons": [f"analyst: {op.rating}"]})
                    continue
                extra = (f"opinion:{op.evidence_path}",)
            proposal = propose(cand, price, config=self.config, limits=self.limits, extra_evidence=extra)
            if proposal is None:
                continue
            out = self.trader.submit(proposal, price)
            if out.status in ("filled", "sent"):
                self.used_prints.update(cand.print_ids)
                self.meta[cand.ticker] = {
                    "entry_at": as_of,
                    "take_profit": str(proposal.take_profit),
                    "version": self.config.version,
                }
            entries.append({"ticker": cand.ticker, "status": out.status, "reasons": out.reasons})
        summary["entries"] = entries
        self.journal.append("run", summary)
        self._save()
        return summary

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
