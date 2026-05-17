# Aurum Worker

This directory contains the entrypoint for the dry-run trading cycle worker.

The current worker executes a single audit-oriented cycle by default. It loads the
runtime state, active strategy and risk configs, recent BTCUSDT candles, portfolio
state, and open position data, then persists a `bot_runs` row and one
`decision_logs` row without sending any order to Binance.

Current scope:

- Binance Spot Testnet by default.
- BTCUSDT only.
- Long-only decisions.
- Dry-run order intent only; no real order submission.

Future issues will add:

- Trading cycle locks through Redis.
- Paper/Testnet execution adapters.
- Pause/resume API endpoints.
- Fill, fee, and reconciliation handling.
