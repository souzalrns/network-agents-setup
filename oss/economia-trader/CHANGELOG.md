# Changelog

## 0.1.0 (unreleased, incubating)

- Data contracts v1: `EconomicEvent` (four clocks, look-ahead guard), `TradeProposal`,
  `RiskAssessment`, `OrderIntent`, `Fill`, `SimulationRun`.
- Risk engine: explicit caps (order notional, loss per trade incl. fees, daily loss,
  open positions, exposure, symbol allowlist, limit-price deviation), fail-closed.
- Execution gate: paper / testnet / live ladder, kill switch, no-withdraw key check,
  per-order human approval (`HitlApprover`, hitlwright contract).
- Adapters: Bybit V5 (spot, mainnet + testnet), MEXC Spot V3 (`/order/test` dry run),
  Alpaca (US stocks/ETFs, paper account + live, fractional DAY orders).
- `Credentials` fields are `key_id` / `signing_key`; one shared HMAC-SHA256 request signer.
- Paper broker (fees + slippage), offline backtest with no look-ahead, SMA baseline.
- Hash-chained JSONL journal + `verify-journal`.
- CLI: ticker, backtest, trade, check-key, gate, kill/unkill, verify-journal.
- Whale screen: `FlowPrint` contract + vendor-neutral JSON source; deterministic `ScreenConfig`
  (versioned) with drop reasons; earnings blocked by default; Vol/OI testable both ways.
- Autonomous loop `Runner` (`run --once | --every-min`): exits (stop / take-profit / time), entries
  on the stock, persisted state, no re-entry on the same evidence, auto-kill on drawdown or
  repeated exchange errors. `report`: results per strategy version from the journal.
- `allowed_symbols: ["*"]` explicit opt-in for a screened universe.
- **Adapters now sit on mature libraries** (decision A, `REUSE-AUDIT.md`): `CcxtSpot` (ccxt: Bybit,
  MEXC; precision/lot size, sandbox, MEXC test orders) and `AlpacaPy` (alpaca-py). The hand-written
  HTTP adapters (`bybit.py`, `mexc.py`, `alpaca.py`) are gone. Extras: `[crypto]`, `[stocks]`.
