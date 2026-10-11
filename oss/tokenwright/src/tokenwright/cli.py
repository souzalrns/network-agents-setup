"""tokenwright CLI: total a ledger's cost, or check a projected call against a cap.

    tokenwright cost  <ledger.jsonl> --prices prices.json [--cap USD]
    tokenwright check --spent USD --in N --out M --model NAME --prices prices.json --cap USD

`prices.json` is ``{model: {usd_per_1m_input, usd_per_1m_output}}``. `cost` prints the
USD spent (exit 1 if a `--cap` is given and already crossed). `check` exits 0 if the
projected call fits the cap, 1 if it would exceed, 2 if the model has no price.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import (
    BudgetExceeded,
    CostUnknown,
    __version__,
    estimate_cost_usd,
    guard_next_call,
    ledger_cost_usd,
    prices_from_mapping,
)


def _load_prices(path: str):
    return prices_from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tokenwright", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"tokenwright {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cost", help="Total the USD cost of a token-usage ledger")
    c.add_argument("ledger")
    c.add_argument("--prices", required=True)
    c.add_argument("--cap", type=float)

    k = sub.add_parser("check", help="Check a projected call against a cap (projective guard)")
    k.add_argument("--spent", type=float, default=0.0)
    k.add_argument("--in", dest="tin", type=int, required=True)
    k.add_argument("--out", dest="tout", type=int, required=True)
    k.add_argument("--model", required=True)
    k.add_argument("--prices", required=True)
    k.add_argument("--cap", type=float, required=True)

    args = ap.parse_args(argv)

    if args.cmd == "cost":
        try:
            spent = ledger_cost_usd(args.ledger, _load_prices(args.prices))
        except CostUnknown as e:
            print(f"cost_unknown: {e}", file=sys.stderr)
            return 2
        print(f"{spent:.6f}")
        if args.cap is not None and spent > args.cap:
            print(f"over cap: {spent:.6f} > {args.cap:.6f}", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "check":
        prices = _load_prices(args.prices)
        try:
            projected = guard_next_call(
                args.spent,
                projected_in=args.tin,
                projected_out=args.tout,
                model=args.model,
                prices=prices,
                cap_usd=args.cap,
            )
        except CostUnknown as e:
            print(f"cost_unknown: {e}", file=sys.stderr)
            return 2
        except BudgetExceeded as e:
            print(str(e), file=sys.stderr)
            return 1
        est = estimate_cost_usd(args.tin, args.tout, args.model, prices)
        print(f"ok: next {projected:.6f} USD (this call {est:.6f}); spent+next within cap {args.cap:.6f}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
