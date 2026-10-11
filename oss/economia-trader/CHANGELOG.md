# Changelog

## 0.1.0 (unreleased, incubating)

- Data contracts v1: `EconomicEvent` (four clocks, look-ahead guard), `TradeProposal`,
  `RiskAssessment`, `OrderIntent`, `Fill`, `SimulationRun`.
- Risk engine: explicit caps (order notional, loss per trade incl. fees, daily loss,
  open positions, exposure, symbol allowlist, limit-price deviation), fail-closed.
- Execution gate: paper / testnet / live ladder, kill switch, no-withdraw key check,
  per-order human approval (`HitlApprover`, hitlwright contract).
- Adapters: Bybit V5 (spot, mainnet + testnet), MEXC Spot V3 (`/order/test` dry run).
- Paper broker (fees + slippage), offline backtest with no look-ahead, SMA baseline.
- Hash-chained JSONL journal + `verify-journal`.
- CLI: ticker, backtest, trade, check-key, gate, kill/unkill, verify-journal.
