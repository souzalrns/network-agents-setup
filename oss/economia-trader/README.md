# economia-trader

An auditable trading core for AI agents. **Agents propose; a deterministic risk engine and an
execution gate decide; every step lands in a hash-chained journal.** Paper by default, Bybit
testnet when you flip one switch, and real orders only behind a kill switch, a key that
provably cannot withdraw, and a human approval *per order*.

It is not "another trading bot" and it ships no alpha. It is the part every LLM trading agent
skips: the layer that makes sure the model **cannot** lose more than you said, cannot touch
withdrawals, and has to explain itself.

```
EconomicEvent ──► analyst (rule / human / LLM) ──► TradeProposal
                                                       │
                              risk.assess (no LLM) ◄───┘   explicit caps, fail-closed
                                                       │
                       safety.authorize ◄──────────────┘   kill switch · mode locks · HITL
                                                       │
                PaperBroker │ Bybit testnet │ Bybit/MEXC live
                                                       │
                              Journal (SHA-256 chain) ◄┘   why, on what, when
```

Zero runtime dependencies (stdlib HTTP + HMAC). Python ≥ 3.10.

## Install

```bash
pip install -e oss/economia-trader            # incubating in this repo; not on PyPI yet
pip install -e 'oss/economia-trader[hitl]'    # + hitlwright for per-order live approvals
```

## The ladder (each rung needs the one before)

| Rung | What happens | What unlocks it |
|---|---|---|
| **paper** | Simulated fills against real public prices (fees + slippage, conservative) | default |
| **testnet** | Bybit testnet orders (test funds). MEXC has no testnet: `/api/v3/order/test` validates only | `ECONOMIA_TRADER_ALLOW_TESTNET=1` + `BYBIT_API_KEY`/`BYBIT_API_SECRET` (testnet key) |
| **live** | Real orders on Bybit mainnet / MEXC spot | `ECONOMIA_TRADER_LIVE=I_ACCEPT_REAL_LOSSES` **and** `check-key` passes (trade yes, withdraw **no**) **and** a human approves *that* order |

Every rung is stopped by the kill switch (`economia-trader kill`, or `ECONOMIA_TRADER_KILL=1`)
and by any risk rule that fails.

## Risk limits are explicit (no money defaults)

```json
{
  "max_order_notional": "50",
  "max_loss_per_trade": "2",
  "max_daily_loss": "5",
  "max_open_positions": 1,
  "allowed_symbols": ["BTCUSDT", "ETHUSDT"]
}
```

A `buy` without a stop-loss is refused. The loss at the stop (including fees on both sides)
must fit `max_loss_per_trade` *and* what is left of today's `max_daily_loss`. After the daily
cap is hit, only exits pass. Spot, long-only, no leverage in v0.1.

## CLI

```bash
economia-trader ticker   --exchange bybit --symbol BTCUSDT
economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limits limits.json
economia-trader trade    --mode paper --symbol BTCUSDT --side buy --qty 0.0005 --stop 60000 --limits limits.json
economia-trader check-key --exchange bybit --mode testnet
economia-trader gate --mode live          # which locks are open right now
economia-trader kill --reason "drill"     # blocks every new order, all modes
economia-trader verify-journal .economia-trader/journal.jsonl
```

Live approvals use the [hitlwright](../hitlwright) contract: the first attempt writes a request
under `.economia-trader/approvals/<client_order_id>/`; a human answers with
`hitlwright decide <dir> <id> --response approve --by user:you`; the next attempt goes through.

## Use from an agent

```python
from economia_trader import Journal, Mode, PaperBroker, RiskLimits, TradeProposal, Trader
from economia_trader.exchanges import make_exchange

trader = Trader(make_exchange("bybit", Mode.PAPER), mode=Mode.PAPER,
                limits=RiskLimits.from_mapping(...), broker=PaperBroker("1000"),
                journal=Journal(".economia-trader/journal.jsonl"))
outcome = trader.submit(TradeProposal("BTCUSDT", "buy", "0.0005", stop_loss="60000",
                                      rationale="CPI surprise, see e1", evidence_ids=("e1",),
                                      proposer="macro-analyst"))
outcome.status   # filled | sent | rejected | blocked | error  (+ reasons)
```

The agent never holds a key and never calls an exchange: it only builds `TradeProposal`s.

## With Bybit's official MCP / Skill

Bybit publishes an official MCP server ([bybit-exchange/trading-mcp](https://github.com/bybit-exchange/trading-mcp),
MIT) and an official agent Skill ([bybit-exchange/skills](https://github.com/bybit-exchange/skills), MIT).
They give a *conversational* agent the whole Bybit API (hundreds of tools). economia-trader
is the *autonomous* path. Use both, for different jobs:

- **MCP for research and inspection**, on a **read-only key** or on **testnet**
  (`examples/bybit-trading-mcp.testnet.mcp.json`, version pinned).
- **economia-trader for any order an agent originates**, so it passes the risk engine, the
  gate and the journal. Never give the MCP a trade-enabled mainnet key in an autonomous loop.

## What v0.1 does not do (yet)

- Reconcile positions with the exchange's own fills (testnet/live book acknowledged orders
  locally, at the assessed price); exchange-side stop orders (stops are client-side).
- Lot-size/precision rounding per instrument (the exchange rejects a bad qty; paper does not).
- Futures, margin, leverage, shorting. MEXC futures order API is not available to retail keys.

Not financial advice. Trading can lose all the capital you put in.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
