"""economia-trader CLI.

    economia-trader ticker   --exchange bybit --symbol BTCUSDT
    economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limits limits.json
    economia-trader check-key --exchange bybit --mode testnet          # needs <EX>_API_KEY/SECRET
    economia-trader trade    --exchange bybit --mode paper --symbol BTCUSDT --side buy --qty 0.001 \\
                             --stop 60000 --limits limits.json
    economia-trader gate     --mode live                               # what would block an order now
    economia-trader kill [--reason ...] | unkill                       # the kill switch
    economia-trader verify-journal .economia-trader/journal.jsonl

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
from .journal import Journal, verify
from .paper import PaperBroker
from .risk import RiskLimits
from .safety import ExecutionBlocked, HitlApprover, KillSwitch, Mode, deny_all, gate_report
from .trader import Trader

STATE_DIR = Path(".economia-trader")


def _limits(path: str) -> RiskLimits:
    return RiskLimits.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


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

    if args.cmd == "verify-journal":
        errors = verify(args.path)
        for e in errors:
            print(f"BROKEN {e}", file=sys.stderr)
        print("journal: " + ("intact" if not errors else f"{len(errors)} breaks"))
        return 1 if errors else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
