# economia-trader

An auditable trading core for AI agents. **Agents propose; a deterministic risk engine and an
execution gate decide; every step lands in a hash-chained journal.** Crypto (Bybit, MEXC) and
US stocks/ETFs (Alpaca). Paper by default, Bybit testnet or the Alpaca paper account when you
flip one switch, and real orders only behind a kill switch, a key that
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
     PaperBroker │ Bybit testnet · Alpaca paper acct │ Bybit · MEXC · Alpaca live
                                                       │
                              Journal (SHA-256 chain) ◄┘   why, on what, when
```

Zero-dependency core. Exchanges come from mature libraries as extras: **ccxt** (crypto) and
**alpaca-py** (stocks). Python ≥ 3.10.

## Install

```bash
pip install -e 'oss/economia-trader[crypto]'   # Bybit / MEXC via ccxt
pip install -e 'oss/economia-trader[stocks]'   # Alpaca via alpaca-py (official SDK)
pip install -e 'oss/economia-trader[data]'     # news + macro calendar via OpenBB (lean)
pip install -e 'oss/economia-trader[hitl]'     # + hitlwright for per-order live approvals
pip install 'git+https://github.com/TauricResearch/TradingAgents@1394a3f'   # LLM analysts (optional)
```

## The ladder (each rung needs the one before)

| Rung | What happens | What unlocks it |
|---|---|---|
| **paper** | Simulated fills against real public prices (fees + slippage, conservative) | default |
| **testnet** | Bybit testnet orders (test funds); Alpaca **paper account** (broker-side simulation). MEXC has no testnet: `/api/v3/order/test` validates only | `ECONOMIA_TRADER_ALLOW_TESTNET=1` + `BYBIT_API_KEY`/`BYBIT_API_SECRET` (testnet key) or `ALPACA_API_KEY`/`ALPACA_SECRET_KEY` (paper keys) |
| **live** | Real orders on Bybit mainnet / MEXC spot / Alpaca | `ECONOMIA_TRADER_LIVE=I_ACCEPT_REAL_LOSSES` **and** `check-key` passes (trade yes, withdraw **no**) **and** a human approves *that* order |

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

## With Alpaca's official MCP (stocks)

[alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) (MIT) defaults to
the paper account (`ALPACA_PAPER_TRADE=true`) and filters tools with `ALPACA_TOOLSETS`. Same
split as Bybit: give the MCP `ALPACA_TOOLSETS=stock-data,news,assets,account` for research, and
route every agent-originated order through economia-trader. Alpaca market data needs a key even
for paper, so the paper rung reads the same `ALPACA_API_KEY`/`ALPACA_SECRET_KEY` (the env names
the official MCP uses).

## Autonomous loop: the whale screen (institutional options flow)

`economia-trader run` is one tick of the autonomous loop: exits first (stop, take-profit,
time), then a deterministic screen over institutional options flow, then at most N new entries
on the **stock** (never the option), each through risk, gate and journal. State lives in
`<state-dir>/state.json`, so a cron/systemd timer can run `--once` every morning; `--every-min`
loops in-process. Auto-kill engages the kill switch on a drawdown from peak or on repeated
exchange errors. The same evidence (flow print ids) is never traded twice.

```bash
economia-trader screen --flow-file flow.json --config examples/run.example.json   # candidates + why others dropped
economia-trader run --exchange alpaca --mode paper --flow-file flow.json \
  --limits examples/limits.stocks.example.json --config examples/run.example.json --once
economia-trader report        # results per strategy version (config hash), from the journal
```

Every config has a `version` (hash of filters + exits) stamped on each proposal, so tuning is
measured per version instead of remembered. `flow.json` is vendor-neutral
(`examples/flow.example.json`); `available_at` keeps the screen from seeing the future.

## News, macro and LLM analysts (reused, not rebuilt)

- `economia-trader monitor`: company news and the BLS release calendar through **OpenBB**
  (`[data]` extra, lean: core + news + bls), plus a hand-kept file for FOMC days. Everything
  becomes `EconomicEvent`s in `events.jsonl`.
- **Macro block:** with a high-impact release (CPI, jobs, FOMC, ...) within `macro_block_hours`,
  a tick opens nothing new (exits still run).
- **LLM second opinion:** with `"confirm_with": "tradingagents"`, each screened candidate goes
  through **TradingAgents** (analysts, bull/bear debate, risk discussion). Only Buy/Overweight lets
  it reach the risk engine; the analyst never orders. Runs per day are capped, tokens per model are
  journaled, and the reports are kept as evidence.

See `docs/initiatives/economia-trader/AGENTS-AND-MONITORS.md`.

## More evidence: insiders (SEC), FinBERT, Adanos

`monitor --insiders --sec-identity "Name email"` pulls SEC Form 4 open-market trades
(**edgartools**); `insider_signal` turns clusters of insider buying into ideas next to the options
flow. `monitor --finbert` scores headlines locally (**FinBERT**); `monitor --adanos` adds social
sentiment (**Adanos**, optional key). With `sentiment_veto`, mostly-negative news or weak social
bullishness skips an entry. Every source is credited separately in `report`. See
`docs/initiatives/economia-trader/SIGNALS-OSINT.md`.

## Forecast confirm (Kronos)

With `"forecast_confirm": true`, every entry must also be confirmed by **Kronos**
([shiyu-coder/Kronos](https://github.com/shiyu-coder/Kronos) @ `67b630e`, code MIT), a foundation model for
candlesticks: seeded sample paths over the next `forecast_horizon` bars must show a mean rise of at least
`forecast_min_expected_return` with at least `forecast_min_up_share` of the paths up. It only confirms or
vetoes (never an idea source), fails closed, and is versioned. Prove it first with an A/B backtest:

```bash
git clone https://github.com/shiyu-coder/Kronos ~/ext/Kronos && git -C ~/ext/Kronos checkout 67b630e
pip install -e 'oss/economia-trader[forecast]'
economia-trader backtest --symbol BTCUSDT --interval 1d --limit 1000 --limits limits.json \
  --forecast kronos --kronos-repo ~/ext/Kronos      # sem_previsao vs com_previsao
```

See `docs/initiatives/economia-trader/FORECAST-KRONOS.md`.

## See it: dashboard, pixel office, traces

- `economia-trader dashboard [--refresh 60]`: one static HTML page (no server, light/dark,
  phone-friendly) built from `state.json`, `journal.jsonl` and `events.jsonl`. It shows positions,
  results per version, upcoming macro releases, analyst opinions, rejections, blocks and kills,
  news, and the last decisions. `--openstock-url http://localhost:3000` links every ticker to its
  page in an **OpenStock** instance (charts, heatmap, news), used as-is, side by side (AGPL-3.0:
  linking by URL creates no obligation; do not copy its code here).
- `economia-trader office --url http://127.0.0.1:19000 --join-key KEY`: the agents (monitor,
  screen, analyst, risk, executor) appear as characters in **Star-Office-UI** and move with the
  journal. Code MIT, art **non-commercial**: personal use only, unless you replace the art.
  It runs as a separate process, so the trader never waits on the visual layer.
- **Langfuse** (optional, `[tracing]` extra): set `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` and
  every TradingAgents step is traced (prompts, tools, tokens, latency).

## What v0.1 does not do (yet)

- Reconcile positions with the exchange's own fills (testnet/live book acknowledged orders
  locally, at the assessed price); exchange-side stop orders (stops are client-side).
- Futures, margin, leverage, shorting, options. MEXC futures order API is not available to retail keys.
- US-market rules on stocks: use a **cash** account (no pattern-day-trader rule) and mind settlement.

Not financial advice. Trading can lose all the capital you put in.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
