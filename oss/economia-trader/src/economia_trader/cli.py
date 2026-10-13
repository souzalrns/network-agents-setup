"""economia-trader CLI.

    economia-trader ticker   --exchange bybit --symbol BTCUSDT
    economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limits limits.json \\
                             [--forecast kronos --kronos-repo PATH]       # A/B with vs without the forecast
    economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limits limits.json \\
                             --strategy grid --grid-config grid.json   # grid vs sma_cross vs buy-and-hold
    economia-trader grid     --exchange bybit --config grid.json --limits limits.json --once   # paper
    economia-trader tune     --exchange bybit --symbol BTCUSDT --interval 1h --limit 1000 --limits limits.json \\
                             --space tune.grid.json --out grid.tuned.json   # walk-forward, nothing traded
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
    economia-trader monitor [--news AAPL,MSFT] [--macro] [--calendar-file fomc.json] [--days 14] [--polymarket]
    economia-trader export-klines --exchange alpaca --symbols SPY,QQQ --interval 1d --out data.csv   # FinRL
    economia-trader dashboard [--state-dir .economia-trader] [--out dashboard.html] [--refresh 60]
    economia-trader alerts --state-dir .economia-trader [--once | --every-min 5 | --test]   # Telegram/webhook/email
    economia-trader office --url http://127.0.0.1:19000 --join-key KEY [--every-s 10 | --once]

Paper is the default everywhere. Testnet and live need the environment locks in ``safety``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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


def _kronos(args: argparse.Namespace, cfg: RunConfig) -> Any:
    from .forecast import confirmer_for, kronos_forecaster

    if not args.kronos_repo:
        raise SystemExit("error: the forecast confirm needs --kronos-repo (git clone shiyu-coder/Kronos)")
    fc = kronos_forecaster(args.kronos_repo, model=args.kronos_model, device=args.kronos_device)
    return confirmer_for(fc, cfg)


def _analysts(args: argparse.Namespace, cfg: RunConfig) -> list[Any]:
    """``confirm_with`` = "tradingagents", "ai-hedge-fund" or both joined by "+" (each must confirm)."""
    from . import analysts as an

    evidence = Path(args.state_dir) / "evidence"
    out: list[Any] = []
    for name in cfg.analysts:
        if name == "tradingagents":
            ta_cfg = json.loads(Path(args.ta_config).read_text(encoding="utf-8")) if args.ta_config else {}
            out.append(an.TradingAgentsAnalyst(config=ta_cfg, evidence_dir=evidence))
        else:
            if not args.aihf_python:
                raise SystemExit("error: ai-hedge-fund needs --aihf-python (the python of its venv, pipx install aihf)")
            kw = json.loads(Path(args.aihf_config).read_text(encoding="utf-8")) if args.aihf_config else {}
            out.append(
                an.AiHedgeFundAnalyst(bridge=an.subprocess_bridge(args.aihf_python), evidence_dir=evidence, **kw)
            )
    return out


def _watcher(state_dir: str | Path, errors_after: int = 3) -> Any:
    import os

    from .alerts import AlertWatcher, senders_from_env

    senders = senders_from_env(os.environ)
    if not senders:
        print(
            "warning: no alert channel configured (ECONOMIA_TRADER_ALERT_*); alerts go to alerts.jsonl only",
            file=sys.stderr,
        )
    return AlertWatcher(state_dir, senders, errors_after=errors_after, env=os.environ)


def _tick(loop: Any, args: argparse.Namespace, watcher: Any) -> None:
    """--once / --every-min for the run and grid loops, with alerts checked after every tick."""
    if args.every_min:

        def pause(seconds: float) -> None:
            if watcher is not None:
                watcher.check()
            time.sleep(seconds)  # nosemgrep  (pacing between ticks)

        loop.run_forever(args.every_min * 60, sleep=pause)
        return
    _print(loop.run_once())
    if watcher is not None:
        watcher.check()


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

    def kronos_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--kronos-repo", help="checkout of shiyu-coder/Kronos @ 67b630e (forecast confirm)")
        p.add_argument("--kronos-model", default="NeoQuasar/Kronos-small")
        p.add_argument("--kronos-device", default="cpu")

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
    p.add_argument("--forecast", choices=["kronos"], help="A/B: same strategy with vs without the forecast confirm")
    p.add_argument("--config", help="run config JSON: forecast_horizon / thresholds for --forecast")
    p.add_argument("--strategy", choices=["sma", "grid"], default="sma")
    p.add_argument("--grid-config", help="grid config JSON (see examples/grid.example.json) for --strategy grid")
    kronos_args(p)

    p = sub.add_parser("tune", help="Walk-forward parameter search on history (paper); nothing is traded")
    ex_args(p)
    p.add_argument("--symbol", required=True)
    p.add_argument("--interval", choices=INTERVALS, default="1h")
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--klines-file", help="Use saved klines JSON instead of fetching (reproducible)")
    p.add_argument("--save-klines", help="Save the fetched klines JSON here (to re-run on the same data)")
    p.add_argument("--limits", required=True)
    p.add_argument("--cash", default="1000")
    p.add_argument("--space", required=True, help="JSON {strategy, base, search} (see examples/tune.grid.example.json)")
    p.add_argument("--folds", type=int, default=4)
    p.add_argument("--dd-weight", default="0.5", help="score = return%% - dd_weight * max drawdown%%")
    p.add_argument("--min-trades", type=int, default=3, help="out-of-sample trades needed to accept")
    p.add_argument("--min-edge", default="0.1", help="score points the pick must win by, out of sample")
    p.add_argument("--out", help="write the chosen config here, only if it is accepted")
    p.add_argument("--log", default=str(STATE_DIR / "tune.jsonl"), help="append the full result here")

    p = sub.add_parser("grid", help="The bounded spot grid loop (crypto): paper by default")
    ex_args(p, mode=True)
    p.add_argument("--config", required=True, help="grid config JSON (see examples/grid.example.json)")
    p.add_argument("--limits", required=True)
    p.add_argument("--cash", default="100", help="paper starting cash (first run only)")
    p.add_argument("--state-dir", default=str(STATE_DIR / "grid"))
    p.add_argument("--approvals", default=str(STATE_DIR / "approvals"))
    p.add_argument("--alerts", action="store_true", help="after each tick, send new alerts (see `alerts`)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="one tick (for cron / systemd timers)")
    g.add_argument("--every-min", type=float, help="loop forever, one tick every N minutes")

    p = sub.add_parser("alerts", help="Send alerts (auto-kill, grid refused, errors in a row) from a state dir")
    p.add_argument("--state-dir", default=str(STATE_DIR))
    p.add_argument("--errors-after", type=int, default=3, help="alert after N errors with no good tick")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="scan once (cron)")
    g.add_argument("--every-min", type=float, help="keep watching, every N minutes")
    g.add_argument("--test", action="store_true", help="send one test alert to every configured channel")

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
    p.add_argument("--aihf-python", help="python of ai-hedge-fund's own venv (confirm_with includes ai-hedge-fund)")
    p.add_argument("--aihf-config", help="ai-hedge-fund analyst options JSON (personas, model, thresholds)")
    p.add_argument("--alerts", action="store_true", help="after each tick, send new alerts (see `alerts`)")
    kronos_args(p)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="one tick (for cron / systemd timers)")
    g.add_argument("--every-min", type=float, help="loop forever, one tick every N minutes")

    p = sub.add_parser("monitor", help="Fetch news and macro releases (OpenBB) into events.jsonl")
    p.add_argument("--news", help="comma-separated tickers")
    p.add_argument("--macro", action="store_true", help="BLS release calendar (CPI, jobs, PPI, ...)")
    p.add_argument("--calendar-file", help="hand-kept releases JSON (e.g. FOMC days)")
    p.add_argument("--days", type=int, default=14, help="macro calendar window ahead")
    p.add_argument("--insiders", action="store_true", help="SEC Form 4 open-market trades (edgartools)")
    p.add_argument("--insider-days", type=int, default=3, help="Form 4 filings from the last N days")
    p.add_argument("--sec-identity", help='SEC contact, "Name email" (required by EDGAR for --insiders)')
    p.add_argument("--finbert", action="store_true", help="score stored news with FinBERT ([nlp] extra)")
    p.add_argument("--adanos", help="comma-separated tickers; needs ADANOS_API_KEY (Reddit/X/news/Polymarket)")
    p.add_argument("--polymarket", action="store_true", help="macro odds from Polymarket (read-only, no key)")
    p.add_argument("--pm-keywords", help="comma-separated question keywords (default: fed, rates, recession, cpi...)")
    p.add_argument("--pm-min-volume", type=float, default=50_000, help="ignore markets below this volume (USD)")
    p.add_argument("--events", default=str(STATE_DIR / "events.jsonl"))

    p = sub.add_parser("export-klines", help="Klines as CSV for research tools (FinRL); nothing is traded")
    ex_args(p)
    p.add_argument("--symbols", required=True, help="comma-separated symbols")
    p.add_argument("--interval", choices=INTERVALS, default="1d")
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--format", choices=["finrl"], default="finrl")
    p.add_argument("--out", required=True)

    p = sub.add_parser("dashboard", help="Static HTML page with positions, results, events, opinions")
    p.add_argument("--state-dir", default=str(STATE_DIR))
    p.add_argument("--out", default=str(STATE_DIR / "dashboard.html"))
    p.add_argument("--refresh", type=int, help="auto-reload every N seconds")
    p.add_argument("--openstock-url", help="link tickers to an OpenStock instance (e.g. http://localhost:3000)")

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

        def bt(strategy: Any) -> dict[str, Any]:
            run = run_backtest(
                bars, strategy, symbol=args.symbol.upper(), limits=limits, cash=args.cash, exchange_name=args.exchange
            )
            return run.summary()

        if args.strategy == "grid":
            from .grid import GridConfig, buy_and_hold, grid_strategy

            if not args.grid_config:
                print("error: --strategy grid needs --grid-config", file=sys.stderr)
                return 2
            gcfg = GridConfig.from_mapping(json.loads(Path(args.grid_config).read_text(encoding="utf-8")))
            anchored = gcfg.anchor(bars[0].close)  # a relative grid anchors on the first bar (no look-ahead)
            problems = anchored.problems(limits)
            if problems:
                _print({"refused": problems, "levels": [str(p) for p in anchored.prices()], "stop": str(anchored.stop)})
                return 2
            grid = bt(grid_strategy(anchored, limits))
            sma = bt(sma_cross(args.fast, args.slow))
            hold = buy_and_hold(bars, args.cash, limits.fee_rate)
            _print(
                {
                    "bars": len(bars),
                    "levels": [str(p) for p in anchored.prices()],
                    "stop": str(anchored.stop),
                    "grid": grid,
                    "sma_cross": sma,
                    "buy_and_hold": hold,
                    "comparacao": {
                        k: {"grid": grid.get(k), "sma_cross": sma.get(k), "buy_and_hold": hold.get(k)}
                        for k in ("return_pct", "max_drawdown_pct", "trades_closed")
                    },
                }
            )
            return 0

        base = bt(sma_cross(args.fast, args.slow))
        if not args.forecast:
            _print({"bars": len(bars), **base})
            return 0
        from .forecast import compare_summaries, with_forecast_confirm

        cfg = _run_config(args.config)
        test = bt(with_forecast_confirm(sma_cross(args.fast, args.slow), _kronos(args, cfg)))
        cmp = compare_summaries(base, test)
        _print({"bars": len(bars), "sem_previsao": base, "com_previsao": test, "comparacao": cmp})
        return 0

    if args.cmd == "tune":
        from .tune import walk_forward

        space = json.loads(Path(args.space).read_text(encoding="utf-8"))
        if args.klines_file:
            raw = json.loads(Path(args.klines_file).read_text(encoding="utf-8"))
            bars = [Kline(int(r[0]), dec(r[1]), dec(r[2]), dec(r[3]), dec(r[4]), dec(r[5])) for r in raw]
        else:
            bars = make_exchange(args.exchange, Mode.PAPER).klines(args.symbol, args.interval, args.limit)
            if args.save_klines:
                rows = [
                    [b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close), str(b.volume)] for b in bars
                ]
                Path(args.save_klines).write_text(json.dumps(rows), encoding="utf-8")
        result = walk_forward(
            bars,
            kind=space.get("strategy", "grid"),
            base=space["base"],
            search=space.get("search") or {},
            limits=_limits(args.limits),
            symbol=args.symbol.upper(),
            cash=args.cash,
            folds=args.folds,
            dd_weight=args.dd_weight,
            min_trades=args.min_trades,
            min_edge=args.min_edge,
            exchange=args.exchange,
        )
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "interval": args.interval, **result}
        Path(args.log).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.log).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        if result["accepted"] and args.out:
            Path(args.out).write_text(json.dumps(result["verdict"]["params"], indent=2) + "\n", encoding="utf-8")
        _print(
            {
                "accepted": result["accepted"],
                "reasons": result["reasons"],
                "chosen": (result["verdict"] or {}).get("params"),
                "config_hash": result.get("config_hash"),
                "out_of_sample": (result["verdict"] or {}).get("oos"),
                "current_config_out_of_sample": (result["verdict"] or {}).get("baseline_oos"),
                "overfit_gap": (result["verdict"] or {}).get("overfit_gap"),
                "notes": (result["verdict"] or {}).get("notes"),
                "bars": result["bars"],
                "bars_hash": result["bars_hash"],
                "written": args.out if result["accepted"] and args.out else None,
                "log": args.log,
            }
        )
        return 0 if result["accepted"] else 1

    if args.cmd == "grid":
        from .grid import GridBot, GridConfig

        mode = Mode(args.mode)
        gcfg = GridConfig.from_mapping(json.loads(Path(args.config).read_text(encoding="utf-8")))
        bot = GridBot(
            make_exchange(args.exchange, mode),
            mode=mode,
            limits=_limits(args.limits),
            config=gcfg,
            state_dir=args.state_dir,
            cash=args.cash,
            kill_switch=KillSwitch(Path(args.state_dir) / "KILL"),
            approver=HitlApprover(args.approvals) if mode is Mode.LIVE else deny_all,
        )
        if mode is not Mode.PAPER:
            bot.trader.verify_key()
        _tick(bot, args, _watcher(args.state_dir) if args.alerts else None)
        return 0

    if args.cmd == "alerts":
        watcher = _watcher(args.state_dir, args.errors_after)
        if args.test:
            _print(watcher.test())
            return 0
        if args.every_min:
            while True:
                watcher.check()
                time.sleep(args.every_min * 60)
        _print({"sent": watcher.check()})
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
        if args.insiders:
            from .signals import edgar_insider_trades, insider_events

            if not args.sec_identity:
                print('error: --insiders needs --sec-identity "Name email" (SEC rule)', file=sys.stderr)
                return 2
            today = datetime.now(timezone.utc).date()
            start = (today - timedelta(days=args.insider_days)).isoformat()
            rows = edgar_insider_trades(start, today.isoformat(), identity=args.sec_identity)
            added["insiders"] = store.add(insider_events(rows))
        if args.finbert:
            from .signals import finbert_scorer, news_sentiment_events

            scored = {e["payload"].get("news_id") for e in store.all() if e.get("kind") == "news_sentiment"}
            todo = [e for e in store.all() if e.get("kind") == "news" and e["id"] not in scored]
            added["news_sentiment"] = store.add(news_sentiment_events(todo, finbert_scorer()))
        if args.adanos:
            import os

            from .signals import adanos_compare, social_sentiment_events

            key = os.environ.get("ADANOS_API_KEY")
            if not key:
                print("error: --adanos needs ADANOS_API_KEY in the environment", file=sys.stderr)
                return 2
            rows = adanos_compare([t.strip().upper() for t in args.adanos.split(",")], api_key=key)
            added["social_sentiment"] = store.add(social_sentiment_events(rows))
        if args.polymarket:
            from .predictions import DEFAULT_KEYWORDS, gamma_markets, prediction_events

            kws = [k.strip() for k in args.pm_keywords.split(",")] if args.pm_keywords else DEFAULT_KEYWORDS
            evs = prediction_events(gamma_markets(), keywords=kws, min_volume=args.pm_min_volume)
            added["prediction_market"] = store.add(evs)
        _print({"events_file": args.events, "added": added})
        return 0

    if args.cmd == "export-klines":
        from .research import finrl_rows, write_csv

        ex = make_exchange(args.exchange, Mode.PAPER)
        series = {
            s.strip().upper(): ex.klines(s.strip().upper(), args.interval, args.limit) for s in args.symbols.split(",")
        }
        n = write_csv(args.out, finrl_rows(series))
        _print({"out": args.out, "rows": n, "symbols": sorted(series), "format": args.format})
        return 0

    if args.cmd == "run":
        from .monitors import EventStore

        mode = Mode(args.mode)
        cfg = _run_config(args.config)
        events_path = Path(args.events) if args.events else Path(args.state_dir) / "events.jsonl"
        analyst = _analysts(args, cfg)
        forecaster = _kronos(args, cfg) if cfg.forecast_confirm else None
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
            forecaster=forecaster,
        )
        if mode is not Mode.PAPER:
            runner.trader.verify_key()
        _tick(runner, args, _watcher(args.state_dir) if args.alerts else None)
        return 0

    if args.cmd == "dashboard":
        from .dashboard import build_html

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            build_html(args.state_dir, refresh_s=args.refresh, openstock_url=args.openstock_url), encoding="utf-8"
        )
        print(f"dashboard: {out}")
        return 0

    if args.cmd == "office":
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
