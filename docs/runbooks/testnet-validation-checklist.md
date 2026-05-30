# Testnet validation checklist

Use this checklist before any operational step that increases risk beyond the
current MVP foundation. It validates the Aurum Testnet environment and collects
minimum evidence that the system remains observable, auditable, and restricted to
the approved scope.

## Mandatory scope

- Environment is `testnet` through `AURUM_ENVIRONMENT=testnet`.
- Trading symbol is `BTCUSDT` through `TRADING_SYMBOL=BTCUSDT`.
- Binance integration uses Spot Testnet:
  `BINANCE_SPOT_BASE_URL=https://testnet.binance.vision/api/v3`.
- The robot remains long-only, with no leverage and no Mainnet execution.
- Worker cycles may run in paper mode or Testnet mode. Paper mode persists only
  dry-run intents. Testnet mode may submit real Spot Testnet orders only through
  the central `OrderService`.
- Manual and robot orders must use the same validation, audit, persistence, and
  reconciliation path.
- MCP and agent access remain read-only unless a future issue explicitly adds
  scoped write behavior, rate limits, and audit controls.

## Prerequisites

- `.env` exists and is based on `.env.example`.
- `BINANCE_API_KEY` and `BINANCE_API_SECRET` are set locally only when validating
  private Testnet account/order flows.
- No real Binance API key, API secret, MCP token, production key, or operational
  secret is committed to the repository.
- Docker Compose services for PostgreSQL, Redis, API, and any service under test
  are healthy enough for the validation step being executed.
- PostgreSQL migrations have been applied to the target database.
- The API is reachable at the selected `API_URL`, usually
  `http://localhost:8000`.
- Redis is reachable by the API and services using `REDIS_URL`.
- BTCUSDT candles have been imported for the required intervals before worker
  validation:

```bash
cd apps/api
aurum-import-candles --interval 1h --interval 4h --interval 1d --limit 500
```

## Evidence collection

Run the read-only evidence collector and save the Markdown output with the
validation notes:

```bash
API_URL=http://localhost:8000 ./scripts/collect-testnet-evidence.sh
```

The collector must not execute POST requests, import candles, run the worker,
create exports, pause or resume the robot, or write audit records. It only reads
local service state and read-only API endpoints.

Attach or retain the following minimum evidence:

- Timestamp and git working tree status.
- `docker compose ps` output.
- API responses for `GET /health`, `GET /bot/status`, `GET /market/summary`,
  `GET /market/candles`, `GET /decisions`, `GET /mcp/status`, and
  `GET /mcp/audit-log`.
- Sensitive-pattern scan output confirming there are no real Binance
  credentials, Mainnet base URLs, or leverage configuration in tracked source.
- SQL evidence listed below for data, worker, and audit validation.
- Worker run logs when manually executing a dry-run cycle.

## API validation

Validate these read-only endpoints against the same `API_URL`:

```bash
curl -fsS "$API_URL/health"
curl -fsS "$API_URL/bot/status"
curl -fsS "$API_URL/market/summary"
curl -fsS "$API_URL/market/candles?interval=1h&limit=5"
curl -fsS "$API_URL/decisions?limit=5"
curl -fsS "$API_URL/mcp/status"
curl -fsS "$API_URL/mcp/audit-log?limit=5"
```

Acceptance criteria:

- `/health` returns `status: ok`.
- API responses report `environment: testnet` wherever environment is present.
- Market and decision responses report `symbol: BTCUSDT` wherever symbol is
  present.
- Missing optional operational data is acceptable during early setup, but the
  endpoint itself must respond predictably.
- MCP status and audit-log endpoints must not expose token secrets or hashes.

Dashboard acceptance criteria:

- `/portfolio` renders the latest Binance-backed wallet snapshot and exposes a
  reconcile action backed by `POST /portfolio/reconcile`.
- `/operations` renders orders/fills and exposes manual order and reconciliation
  actions backed by `POST /operations/manual-order` and
  `POST /operations/reconcile`.
- Dashboard mutations must show success or failure feedback without exposing
  Binance credentials.

## Private Testnet validation

Only run this section with Binance Spot Testnet credentials. The base URL must
remain `https://testnet.binance.vision/api/v3`.

Reconcile the Binance Spot Testnet account into Aurum:

```bash
curl -fsS -X POST "$API_URL/portfolio/reconcile"
curl -fsS "$API_URL/portfolio/status"
```

Acceptance criteria:

- The response reports `environment: testnet` and `symbol: BTCUSDT`.
- `source_payload.source` is `binance_spot_testnet_account`.
- BTC and USDT balances match the Binance Spot Testnet account at validation
  time.
- No secret values appear in the response or logs.

Submit a small manual order after confirming the runtime state is `running`,
active risk config exists, portfolio is reconciled, and market data is fresh:

```bash
curl -fsS -X POST "$API_URL/operations/manual-order" \
  -H 'content-type: application/json' \
  -d '{"side":"BUY","quote_quantity":"25","reason":"manual testnet validation"}'
```

Then reconcile open orders/fills:

```bash
curl -fsS -X POST "$API_URL/operations/reconcile"
curl -fsS "$API_URL/operations/orders?limit=10"
curl -fsS "$API_URL/operations/fills?limit=10"
```

Acceptance criteria:

- Manual order is blocked unless runtime is `running`, environment is `testnet`,
  symbol is `BTCUSDT`, market data is fresh, balance is sufficient, and risk
  limits allow it.
- Persisted order status is one of `NEW`, `PARTIALLY_FILLED`, `FILLED`,
  `CANCELED`, `REJECTED`, or `EXPIRED`.
- If Binance rejects or the signed submission fails after local validation, an
  `orders` row with `status = 'REJECTED'` must remain available for audit.
- Binance fills are persisted in `order_fills` when returned by Testnet.
- `audit_logs` includes `order.submitted`, `order.blocked`, or
  `order.rejected`, or `order.reconciled` events as applicable.
- Mainnet remains blocked and no Mainnet URL appears in tracked source.

## Data validation

Confirm imported candle coverage for Testnet BTCUSDT:

```bash
docker compose exec postgres psql -U aurum -d aurum -c "
select environment, symbol, interval, count(*) as candles, max(close_time) as latest_close
from market_candles
where environment = 'testnet' and symbol = 'BTCUSDT'
group by environment, symbol, interval
order by interval;
"
```

Acceptance criteria:

- Rows exist for intervals `1h`, `4h`, and `1d`.
- Every row is `environment = 'testnet'` and `symbol = 'BTCUSDT'`.
- `latest_close` is recent enough for the validation window being tested.

## Worker validation

Run one worker cycle only after runtime state, active strategy config, active
risk config, market candles, fresh market snapshot, and portfolio state are
present:

```bash
cd apps/api
python ../../services/worker/main.py
```

Then collect database evidence:

```bash
docker compose exec postgres psql -U aurum -d aurum -c "
select id, environment, symbol, status, run_payload, started_at, finished_at, error_message
from bot_runs
where environment = 'testnet' and symbol = 'BTCUSDT'
order by started_at desc
limit 5;
"

docker compose exec postgres psql -U aurum -d aurum -c "
select id, environment, symbol, decision, reason, intended_order, execution_result, decided_at
from decision_logs
where environment = 'testnet' and symbol = 'BTCUSDT'
order by decided_at desc
limit 5;
"
```

Acceptance criteria:

- A `bot_runs` row is created for `environment = 'testnet'` and
  `symbol = 'BTCUSDT'`.
- The run payload includes the active trading mode.
- A `decision_logs` row is created for the run.
- The decision is one of `COMPRA`, `VENDA`, `MANTER_POSICAO`, or `NAO_OPERAR`.
- In paper mode, `execution_result.execution_mode` is `dry_run` and no Binance
  order is submitted.
- In Testnet mode, any allowed `COMPRA`/`VENDA` must create an `orders` row and
  use `execution_result.execution_mode = binance_testnet`.
- If execution is blocked, the decision log must explain the block code and
  reason.

## Audit validation

Confirm configuration and MCP audit evidence where applicable:

```bash
docker compose exec postgres psql -U aurum -d aurum -c "
select environment, actor_type, action, entity_type, occurred_at, metadata_payload
from audit_logs
where environment = 'testnet'
order by occurred_at desc
limit 10;
"

docker compose exec postgres psql -U aurum -d aurum -c "
select environment, agent_name, resource, status, status_code, occurred_at
from mcp_access_logs
where environment = 'testnet'
order by occurred_at desc
limit 10;
"
```

Acceptance criteria:

- Configuration changes, token operations, and MCP accesses are auditable when
  those flows are exercised.
- Audit evidence stays in `testnet`.
- Token secrets are never shown in API responses, SQL evidence, logs, or files.

## Final sign-off

Before marking the Testnet validation complete, confirm:

- The evidence collector output has been reviewed.
- API, database, Redis, candle import, worker dry-run, decision logs, and audit
  evidence have been captured or explicitly marked not applicable with a reason.
- No committed source points execution to Binance Mainnet.
- No committed source contains real Binance credentials or operational secrets.
- The current validation does not authorize Mainnet, leverage, short positions,
  or real order execution.
