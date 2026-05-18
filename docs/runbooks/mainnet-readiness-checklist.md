# Mainnet readiness checklist

Use this checklist before any future Aurum promotion from Binance Spot Testnet
to Binance Spot Mainnet. This document is a hardening and go-live control. It
does not authorize Mainnet execution by itself, and it does not change the
current MVP scope: BTCUSDT, long-only, no leverage, and no Mainnet order
execution.

Every item must be reviewed with evidence before any real capital is exposed.
If any required control is missing, untested, stale, or disputed, Mainnet
promotion must stop until the issue is resolved and documented.

## Mandatory scope gates

- Mainnet remains out of scope until a dedicated Linear issue and Slack Canvas
  decision explicitly authorize a controlled go-live.
- The approved trading scope is Binance Spot only, BTCUSDT only, long-only, and
  no leverage.
- Backtest, paper trading, and Binance Spot Testnet validation must all be
  completed and reviewed before any real capital is used.
- The Testnet validation evidence from
  `docs/runbooks/testnet-validation-checklist.md` must be current for the
  release candidate being promoted.
- Any change to trading rules, risk rules, promotion criteria, architecture,
  security posture, MCP permissions, or operational ownership must be reflected
  in the Slack Canvas before go-live.

## Environment segregation

- Testnet and Mainnet must use separate environment variables, credentials,
  database schemas or namespaces, Redis keys, logs, dashboards, and evidence
  bundles.
- Operators must be able to identify the active environment from API responses,
  dashboard views, worker logs, audit rows, and evidence reports.
- Mainnet configuration must never be enabled by changing a default value in
  shared code. It must require explicit deployment-time configuration.
- `AURUM_ENVIRONMENT`, Binance base URLs, trading symbol, and execution mode
  must be captured in the go-live evidence bundle.
- No Testnet token, database, queue, cache namespace, or audit stream may be
  reused for Mainnet.

## Secrets and credentials

- No real Binance API key, Binance API secret, MCP token, production key, or
  operational secret may be committed to the repository.
- Mainnet secrets must be stored in an approved secret manager or encrypted
  deployment secret store, not in source files, shell history, local notes, or
  plain-text runbooks.
- Secret rotation and revocation steps must be documented and tested before
  go-live.
- Binance credentials must use minimum required permissions for Spot trading and
  must not include futures, margin, withdrawal, or leverage permissions.
- Binance IP restriction must be enabled wherever the deployment environment
  supports stable egress IPs.
- A sensitive-pattern scan must be run against tracked source before go-live,
  and any match must block promotion until reviewed and remediated.

## Strategy and risk validation

- Backtests must include fees, conservative slippage, drawdown, win rate,
  profit factor, Sharpe or equivalent risk-adjusted metric, and versioned
  strategy assumptions.
- Paper trading must prove that signal generation, position accounting,
  decision logs, portfolio snapshots, and PnL calculations remain reproducible.
- Binance Spot Testnet must validate order intent, order lifecycle handling,
  fills, fees, portfolio reconciliation, audit logs, and failure handling.
- Risk limits must be configured and reviewed for max position exposure, daily
  loss, stop behavior, stale market data, API instability, and balance
  inconsistency.
- Promotion must be rejected if backtest, paper trading, and Testnet evidence do
  not support the same strategy version and risk configuration.

## Operational controls

- Emergency stop must be implemented independently from the strategy and tested
  before go-live.
- Pause and resume actions must require an operator reason and must write audit
  evidence.
- Worker locking must prevent concurrent trading cycles in the same
  environment.
- The system must block new orders when market data is stale, Binance APIs are
  unstable, balances cannot be reconciled, risk limits are exceeded, or the bot
  is paused or in emergency stop.
- Mainnet order submission must be behind an explicit execution-mode control
  and must not be reachable from dry-run, paper, or Testnet paths.
- A rollback plan must identify the commands, owners, credentials, and expected
  evidence for pausing the bot, disabling workers, revoking tokens, rotating
  credentials, and preserving logs.

## Audit and reconciliation

- Configuration changes, token operations, pause and resume actions, emergency
  stop events, order submissions, fills, fees, exports, and MCP accesses must be
  auditable.
- Audit records must include environment, actor, action, target entity, time,
  status, and relevant metadata without exposing secrets.
- Orders and fills must be reconcilable between Aurum records and Binance
  records before any Mainnet operation starts.
- Portfolio snapshots must reconcile USDT, BTC, invested value, market value,
  exposure, realized PnL, unrealized PnL, and fees.
- The go-live evidence bundle must include database checks for orders, fills,
  decision logs, bot runs, audit logs, MCP access logs, and portfolio snapshots.

## MCP and agent access

- MCP and agent access must remain read-only until a future issue explicitly
  adds scoped write behavior, token controls, rate limits, and audit controls.
- Agents must not send orders, alter strategy settings, alter risk settings,
  rotate credentials, or change runtime state unless future authorization
  defines those scopes and confirmation requirements.
- MCP tokens must be scoped, expiring, revocable, hashed at rest, and rate
  limited per token.
- MCP responses, logs, and audit rows must never expose Binance credentials,
  token secrets, token hashes, or operational secrets.
- Any move beyond read-only MCP access requires an updated Slack Canvas decision
  and separate Linear implementation scope.

## No-go criteria

Mainnet promotion must be blocked if any of these conditions are true:

- Backtest, paper trading, or Testnet validation is missing, stale, or tied to a
  different strategy or risk version.
- The bot can submit Mainnet orders without explicit Mainnet deployment
  configuration.
- Emergency stop, pause, audit, reconciliation, or rollback evidence is missing.
- Binance credentials have broad permissions, withdrawal access, futures,
  margin, leverage, or no practical IP restriction where one is available.
- MCP or agent access can mutate trading state without approved scopes, rate
  limits, token controls, and audit coverage.
- Any committed source contains real credentials, Mainnet secrets, or
  accidental Mainnet defaults.

## Final sign-off

Before any controlled Mainnet go-live, confirm:

- Linear contains the explicit go-live issue or milestone authorizing the work.
- The Slack Canvas contains the durable decision for scope, risk limits,
  promotion criteria, security controls, MCP permissions, and rollback.
- Evidence for backtest, paper trading, Testnet, audit, reconciliation,
  emergency stop, secrets, and rollback has been reviewed.
- The first Mainnet run is limited to the approved symbol, direction, capital
  cap, risk configuration, and operator window.
- The sign-off states that this checklist was satisfied; it must not state that
  Mainnet is authorized by this checklist alone.
