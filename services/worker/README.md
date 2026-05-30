# Aurum Worker

This directory contains the entrypoint for the continuous market and trading
cycle worker.

The worker runs continuously under Docker Compose. Every market poll it imports
recent BTCUSDT candles from Binance Spot Testnet, persists new candles, creates a
market snapshot, and publishes a Redis event for the web/API realtime stream.
When the robot runtime state is `running`, it executes the decision cycle and
persists `bot_runs` and `decision_logs`. If runtime `trading_mode` is `paper`,
orders remain dry-run intents. If runtime `trading_mode` is `testnet`, the worker
uses the same central `OrderService` and Binance Spot Testnet adapter used by
manual orders.

Current scope:

- Binance Spot Testnet by default.
- BTCUSDT only.
- Long-only decisions.
- Market data updates even while the robot is paused.
- Paper mode keeps order intent only.
- Testnet mode can submit real Spot Testnet orders after risk, runtime,
  environment, symbol, balance, and market freshness validation.
- Mainnet mode is blocked by the execution adapter.

Useful environment variables:

- `MARKET_POLL_SECONDS`: market refresh interval, default `30`.
- `WORKER_CYCLE_SECONDS`: dry-run decision interval, default `60`.
- `MARKET_BACKFILL_LIMIT`: candles fetched per interval on refresh, default `500`.
- `BINANCE_API_KEY`: Binance Spot Testnet API key, required for Testnet private
  account/order operations.
- `BINANCE_API_SECRET`: Binance Spot Testnet API secret, required for signed
  private endpoints.
- `BINANCE_RECV_WINDOW_MS`: signed request receive window, default `5000`.
- `MARKET_STALE_AFTER_SECONDS`: maximum market snapshot age before execution is
  blocked, default `300`.

The worker reconciles Binance Spot Testnet account balances into
`portfolio_snapshots` before a Testnet decision cycle when private credentials
are configured. Open orders can also be reconciled through
`POST /operations/reconcile`.
