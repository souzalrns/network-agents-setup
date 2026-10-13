"""Smoke L3 (testnet): compra -> stop na exchange -> reconcile -> saída sem venda dupla.

Corre SÓ em testnet: precisa de ECONOMIA_TRADER_ALLOW_TESTNET=1 e das chaves de TESTE no ambiente.
Uso: python smoke_testnet.py bybit BTCUSDT 0.0002 limits.json /tmp/et-smoke
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

from economia_trader import RiskLimits, TradeProposal, Trader
from economia_trader.exchanges import make_exchange
from economia_trader.journal import Journal, verify
from economia_trader.safety import KillSwitch, Mode


def smoke(exchange_name, symbol, qty, limits_path, out_dir, *, client=None, env=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ex = make_exchange(exchange_name, Mode.TESTNET, client=client, env=env)  # nunca mainnet
    limits = RiskLimits.from_mapping(json.loads(Path(limits_path).read_text()))
    t = Trader(
        ex,
        mode=Mode.TESTNET,
        limits=limits,
        journal=Journal(out / "journal.jsonl"),
        kill_switch=KillSwitch(out / "KILL", env=env or {}),
        env=env,
    )
    t.verify_key()  # recusa chave com levantamento
    qty = Decimal(qty)
    last = ex.ticker(symbol).last
    stop = (last * Decimal("0.97")).quantize(Decimal("0.01"))
    checks = {}

    buy = t.submit(TradeProposal(symbol, "buy", qty, stop_loss=stop, rationale="smoke testnet", proposer="smoke"))
    t.reconcile()
    checks["1_buy_filled_by_exchange"] = bool(t.state.positions.get(symbol))
    checks["2_stop_on_exchange"] = symbol in t.exchange_stops
    checks["3_position_matches_exchange"] = not t.sync_positions([symbol])
    if not checks["1_buy_filled_by_exchange"]:  # blocked by the gate/risk, or not filled: stop here
        print(json.dumps({"checks": checks, "buy": buy.status, "reasons": buy.reasons}, indent=2))
        return False

    sell = t.submit(
        TradeProposal(symbol, "sell", t.state.positions[symbol].qty, rationale="smoke exit", proposer="smoke")
    )
    t.reconcile()
    entries = [json.loads(line) for line in (out / "journal.jsonl").read_text().splitlines()]
    kinds = [e["kind"] for e in entries]
    sells = [e for e in entries if e["kind"] == "order" and (e.get("payload") or {}).get("side") == "sell"]
    checks["4_stop_cancelled_before_sell"] = "stop_cancelled" in kinds
    checks["5_flat_after_exit"] = symbol not in t.state.positions and symbol not in t.exchange_stops
    checks["6_one_sell_and_flat_on_exchange"] = len(sells) == 1 and ex.position_qty(symbol) == 0
    checks["7_journal_chain_ok"] = verify(out / "journal.jsonl") == []
    print(json.dumps({"checks": checks, "buy": buy.status, "sell": sell.status, "journal_kinds": kinds}, indent=2))
    return all(checks.values())


if __name__ == "__main__":
    sys.exit(0 if smoke(*sys.argv[1:6]) else 1)
