"""economia-trader CLI.

    economia-trader ticker   --exchange bybit --symbol BTCUSDT
    economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limits limits.json
    economia-trader check-key --exchange bybit --mode testnet          # needs <EX>_API_KEY/SECRET
    economia-trader trade    --exchange bybit --mode paper --symbol BTCUSDT --side buy --qty 0.001 \\
                             --stop 60000 --limits limits.json
    economia-trader gate     --mode live                               # what would block an order now
    economia-trader kill [--reason ...] | unkill                       # the kill switch
    economia-trader verify-journal .economia-trader/journal.jsonl
    economia-trader screen --flow-file flow.json [--config run.json] [--as-of ISO]
    economia-trader run    --exchange alpaca --mode paper --flow-file flow.json --limits limits.json \
                           [--config run.json] [--cash 100] [--every-min 240 | --once]
    economia-trader report [--journal .economia-trader/journal.jsonl]
    economia-trader monitor [--news AAPL,MSFT] [--macro] [--calendar-file fomc.json] [--days 14]
    economia-trader dashboard [--state-dir .economia-trader] [--out dashboard.html] [--refresh 60]
    economia-trader office --url http://127.0.0.1:19000 --join-key KEY [--every-s 10 | --once]

Paper is the default everywhere. Testnet and live need the environment locks in ``safety``.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import __version__
from .backtest import run_backtest, sma_cross
from .contracts import TradeProposal, dec
from .exchanges import EXCHANGES, make_exchange
from .exchanges.base import INTERVALS, ExchangeError, Kline
from .flow import JsonFileFlowSource
from .journal import Journal, verify
from .paper import PaperBroker
from .report import report
from .risk import RiskLimits
from .runner import RunConfig, Runner
from .safety import ExecutionBlocked, HitlApprover, KillSwitch, Mode, deny_all, gate_report
from .screen import screen
from .trader import Trader

STATE_DIR = Path(".economia-trader")


def _limits(path: str) -> RiskLimits:
    return RiskLimits.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def _run_config(path: str | None) -> RunConfig:
    return RunConfig.from_mapping(json.loads(Path(path).read_text(encoding="utf-8"))) if path else RunConfig()


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="economia-trader", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"economia-trader {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def ex_args(p: argparse.ArgumentParser, mode: bool = False) -> None:
        p.add_argument("--exchange", choices=EXCHANGES, default="bybit")
        if mode:
            p.add_argument("--mode", choices=[m.value for m in Mode], default="paper")

    p = sub.add_parser("ticker", help="Last/bid/ask from public market data (no key)")
    ex_args(p)
    p.add_argument("--symbol", required=True)

    p = sub.add_parser("backtest", help="Replay the baseline strategy over public klines (paper)")
    ex_args(p)
    p.add_argument("--symbol", required=True)
    p.add_argument("--interval", choices=INTERVALS, default="1h")
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--limits", required=True, help="JSON risk limits (see examples/limits.example.json)")
    p.add_argument("--cash", default="1000")
    p.add_argument("--fast", type=int, default=10)
    p.add_argument("--slow", type=int, default=30)
    p.add_argument("--klines-file", help="Use saved klines JSON instead of fetching")

    p = sub.add_parser("check-key", help="Verify the API key: read+trade, never withdraw")
    ex_args(p, mode=True)

    p = sub.add_parser("trade", help="Send one proposal through risk -> gate -> order")
    ex_args(p, mode=True)
    p.add_argument("--symbol", required=True)
    p.add_argument("--side", choices=["buy", "sell"], required=True)
    p.add_argument("--qty", required=True)
    p.add_argument("--stop", help="stop-loss price (required for buy)")
    p.add_argument("--limit-price", help="limit price (default: market)")
    p.add_argument("--limits", required=True)
    p.add_argument("--cash", default="1000", help="paper cash")
    p.add_argument("--journal", default=str(STATE_DIR / "journal.jsonl"))
    p.add_argument("--approvals", default=str(STATE_DIR / "approvals"), help="hitlwright dir for live approvals")

    p = sub.add_parser("gate", help="Show which locks are open for a mode")
    p.add_argument("--mode", choices=[m.value for m in Mode], default="live")

    p = sub.add_parser("kill", help="Engage the kill switch (blocks every new order)")
    p.add_argument("--reason", default="")
    sub.add_parser("unkill", help="Release the kill switch")

    p = sub.add_parser("verify-journal", help="Check the journal's hash chain")
    p.add_argument("path")

    p = sub.add_parser("screen", help="Run the whale screen over a flow file and show candidates + drops")
    p.add_argument("--flow-file", required=True)
    p.add_argument("--config", help="run config JSON (see examples/run.example.json)")
    p.add_argument("--as-of", help="ISO time (default: now, UTC)")

    p = sub.add_parser("run", help="The autonomous loop: exits, screen, entries, auto-kill")
    ex_args(p, mode=True)
    p.add_argument("--flow-file", required=True, help="flow export, refreshed by your data job")
    p.add_argument("--limits", required=True)
    p.add_argument("--config")
    p.add_argument("--cash", default="100", help="paper starting cash (first run only)")
    p.add_argument("--state-dir", default=str(STATE_DIR))
    p.add_argument("--approvals", default=str(STATE_DIR / "approvals"))
    p.add_argument("--events", help="events.jsonl from `monitor` (default: <state-dir>/events.jsonl if present)")
    p.add_argument("--ta-config", help="TradingAgents config overrides JSON (when config.confirm_with=tradingagents)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="one tick (for cron / systemd timers)")
    g.add_argument("--every-min", type=float, help="loop forever, one tick every N minutes")

    p = sub.add_parser("monitor", help="Fetch news and macro releases (OpenBB) into events.jsonl")
    p.add_argument("--news", help="comma-separated tickers")
    p.add_argument("--macro", action="store_true", help="BLS release calendar (CPI, jobs, PPI, ...)")
    p.add_argument("--calendar-file", help="hand-kept releases JSON (e.g. FOMC days)")
    p.add_argument("--days", type=int, default=14, help="macro calendar window ahead")
    p.add_argument("--events", default=str(STATE_DIR / "events.jsonl"))

    p = sub.add_parser("dashboard", help="Static HTML page with positions, results, events, opinions")
    p.add_argument("--state-dir", default=str(STATE_DIR))
    p.add_argument("--out", default=str(STATE_DIR / "dashboard.html"))
    p.add_argument("--refresh", type=int, help="auto-reload every N seconds")

    p = sub.add_parser("office", help="Push agent states to a Star-Office-UI (pixel office)")
    p.add_argument("--url", required=True, help="Star-Office-UI base URL")
    p.add_argument("--join-key", required=True)
    p.add_argument("--state-dir", default=str(STATE_DIR))
    og = p.add_mutually_exclusive_group()
    og.add_argument("--once", action="store_true")
    og.add_argument("--every-s", type=float, default=10.0)

    p = sub.add_parser("report", help="Results per strategy version, from the journal")
    p.add_argument("--journal", default=str(STATE_DIR / "journal.jsonl"))

    args = ap.parse_args(argv)
    try:
        return _run(args)
    except (ExchangeError, ExecutionBlocked, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace) -> int:
    if args.cmd == "ticker":
        t = make_exchange(args.exchange, Mode.PAPER).ticker(args.symbol)
        _print({"exchange": args.exchange, "symbol": t.symbol, "last": t.last, "bid": t.bid, "ask": t.ask})
        return 0

    if args.cmd == "backtest":
        limits = _limits(args.limits)
        if args.klines_file:
            raw = json.loads(Path(args.klines_file).read_text(encoding="utf-8"))
            bars = [Kline(int(r[0]), dec(r[1]), dec(r[2]), dec(r[3]), dec(r[4]), dec(r[5])) for r in raw]
        else:
            bars = make_exchange(args.exchange, Mode.PAPER).klines(args.symbol, args.interval, args.limit)
        run = run_backtest(
            bars,
            sma_cross(args.fast, args.slow),
            symbol=args.symbol.upper(),
            limits=limits,
            cash=args.cash,
            exchange_name=args.exchange,
        )
        _print({"bars": len(bars), **run.summary()})
        return 0

    if args.cmd == "check-key":
        mode = Mode(args.mode)
        if mode is Mode.PAPER:
            print("error: check-key needs --mode testnet|live (paper uses no key)", file=sys.stderr)
            return 2
        check = make_exchange(args.exchange, mode).check_key()
        _print(
            {
                "safe_for_trading": check.safe_for_trading,
                "can_trade": check.can_trade,
                "can_withdraw": check.can_withdraw,
                "read_only": check.read_only,
                "detail": check.detail,
            }
        )
        return 0 if check.safe_for_trading else 1

    if args.cmd == "trade":
        mode = Mode(args.mode)
        exchange = make_exchange(args.exchange, mode)
        trader = Trader(
            exchange,
            mode=mode,
            limits=_limits(args.limits),
            journal=Journal(args.journal),
            broker=PaperBroker(args.cash) if mode is Mode.PAPER else None,
            approver=HitlApprover(args.approvals) if mode is Mode.LIVE else deny_all,
        )
        if mode is not Mode.PAPER:
            trader.verify_key()
        proposal = TradeProposal(
            args.symbol.upper(),
            args.side,
            Decimal(args.qty),
            stop_loss=Decimal(args.stop) if args.stop else None,
            entry_price=Decimal(args.limit_price) if args.limit_price else None,
            rationale="manual (cli)",
            proposer="cli",
        )
        out = trader.submit(proposal)
        _print(
            {
                "status": out.status,
                "proposal_id": out.proposal_id,
                "reasons": out.reasons,
                "fill": out.fill,
                "order": out.order,
            }
        )
        return 0 if out.status in ("filled", "sent") else 1

    if args.cmd == "gate":
        _print(gate_report(Mode(args.mode), kill_switch=KillSwitch()))
        return 0

    if args.cmd == "kill":
        KillSwitch().engage(args.reason)
        print("kill switch ENGAGED")
        return 0

    if args.cmd == "unkill":
        KillSwitch().release()
        print("kill switch released")
        return 0

    if args.cmd == "screen":
        from datetime import datetime, timezone

        cfg = _run_config(args.config)
        as_of = args.as_of or datetime.now(timezone.utc).isoformat(timespec="seconds")
        res = screen(JsonFileFlowSource(args.flow_file).prints(as_of), cfg.screen, as_of)
        _print(
            {
                "as_of": as_of,
                "version": cfg.version,
                "prints_seen": res.prints_seen,
                "prints_kept": res.prints_kept,
                "candidates": [c.__dict__ for c in res.candidates],
                "dropped": res.dropped,
            }
        )
        return 0

    if args.cmd == "monitor":
        from datetime import datetime, timedelta, timezone

        from .monitors import (
            EventStore,
            load_calendar_file,
            macro_events,
            news_events,
            openbb_company_news,
            openbb_macro_calendar,
        )

        store, added = EventStore(args.events), {}
        if args.news:
            added["news"] = store.add(news_events(openbb_company_news([t.strip() for t in args.news.split(",")])))
        if args.macro:
            today = datetime.now(timezone.utc).date()
            rows = openbb_macro_calendar(today.isoformat(), (today + timedelta(days=args.days)).isoformat())
            added["macro"] = store.add(macro_events(rows))
        if args.calendar_file:
            added["calendar_file"] = store.add(macro_events(load_calendar_file(args.calendar_file), source="manual"))
        _print({"events_file": args.events, "added": added})
        return 0

    if args.cmd == "run":
        from .monitors import EventStore

        mode = Mode(args.mode)
        cfg = _run_config(args.config)
        events_path = Path(args.events) if args.events else Path(args.state_dir) / "events.jsonl"
        analyst = None
        if cfg.confirm_with == "tradingagents":
            from .analysts import TradingAgentsAnalyst

            ta_cfg = json.loads(Path(args.ta_config).read_text(encoding="utf-8")) if args.ta_config else {}
            analyst = TradingAgentsAnalyst(config=ta_cfg, evidence_dir=Path(args.state_dir) / "evidence")
        runner = Runner(
            make_exchange(args.exchange, mode),
            JsonFileFlowSource(args.flow_file),
            mode=mode,
            limits=_limits(args.limits),
            config=cfg,
            state_dir=args.state_dir,
            cash=args.cash,
            kill_switch=KillSwitch(Path(args.state_dir) / "KILL"),
            approver=HitlApprover(args.approvals) if mode is Mode.LIVE else deny_all,
            events=EventStore(events_path) if (args.events or events_path.exists()) else None,
            analyst=analyst,
        )
        if mode is not Mode.PAPER:
            runner.trader.verify_key()
        if args.every_min:
            runner.run_forever(args.every_min * 60)
        else:
            _print(runner.run_once())
        return 0

    if args.cmd == "dashboard":
        from .dashboard import build_html

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_html(args.state_dir, refresh_s=args.refresh), encoding="utf-8")
        print(f"dashboard: {out}")
        return 0

    if args.cmd == "office":
        import time

        from .office import OfficeBridge

        sd = Path(args.state_dir)
        bridge = OfficeBridge(args.url, args.join_key, sd / "office.json")
        while True:
            sent = bridge.sync(sd / "journal.jsonl", sd / "events.jsonl")
            if args.once:
                print(f"office: {sent} updates")
                return 0
            time.sleep(args.every_s)

    if args.cmd == "report":
        _print(report(args.journal))
        return 0

    if args.cmd == "verify-journal":
        errors = verify(args.path)
        for e in errors:
            print(f"BROKEN {e}", file=sys.stderr)
        print("journal: " + ("intact" if not errors else f"{len(errors)} breaks"))
        return 1 if errors else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
