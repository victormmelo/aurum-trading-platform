# Aurum Trading Platform

Aurum is an operational platform for observing, controlling, and auditing an autonomous BTCUSDT trading robot. The MVP targets Binance Spot Testnet, long-only operation, and a progressive path through local development, paper trading, Testnet validation, and only later controlled Mainnet usage.

The current MVP foundation includes FastAPI backend, Next.js frontend,
PostgreSQL, Redis, Docker Compose, Binance market data, strategy components,
MCP read-only surfaces, and a worker that can run in paper mode or Binance Spot
Testnet mode. Testnet execution is restricted to BTCUSDT, long-only Spot orders,
with Mainnet explicitly blocked.

## Monorepo layout

```text
apps/
  api/           FastAPI backend
  web/           Next.js dashboard
services/
  worker/        Dry-run trading cycle worker
  mcp-server/    Read-only MCP server placeholder
infra/
  docker/        Dockerfiles for local services
scripts/         Local helper scripts
```

## Services

- `api`: FastAPI application with `GET /health`.
- `web`: Next.js operational dashboard with mocked BTCUSDT/Testnet data.
- `postgres`: PostgreSQL 16 for future transactional data.
- `redis`: Redis for future cache, queues, locks, and rate limits.
- `worker`: continuous market reader plus trading cycle. It refreshes
  candles/snapshots, reconciles Binance Spot Testnet portfolio balances when
  credentials are configured, publishes market events, and only runs decision
  cycles when the robot is `running`.
- `mcp-server`: placeholder for read-only agent access.

## Local setup

1. Copy environment defaults:

```bash
cp .env.example .env
```

For real Binance Spot Testnet execution, create Spot Testnet API credentials in
Binance's testnet environment and set only local environment values:

```bash
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_SPOT_BASE_URL=https://testnet.binance.vision/api/v3
AURUM_ENVIRONMENT=testnet
TRADING_SYMBOL=BTCUSDT
```

Do not commit real keys. Mainnet URLs and Mainnet execution remain outside the
MVP.

2. Run with Docker Compose:

```bash
docker compose up --build
```

3. Open the services:

- Web: http://localhost:3000
- API health: http://localhost:8000/health

## Development commands

Backend:

```bash
cd apps/api
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

The Docker Compose worker imports BTCUSDT candles and creates market snapshots
automatically. To backfill manually during local development:

```bash
aurum-import-candles --interval 1h --interval 4h --interval 1d --limit 500
```

Run the continuous worker locally after migrations and service dependencies are
available:

```bash
cd apps/api
. .venv/bin/activate
python ../../services/worker/main.py
```

Private Testnet operations:

```bash
curl -fsS -X POST http://localhost:8000/portfolio/reconcile
curl -fsS -X POST http://localhost:8000/operations/manual-order \
  -H 'content-type: application/json' \
  -d '{"side":"BUY","quote_quantity":"25","reason":"manual testnet validation"}'
curl -fsS -X POST http://localhost:8000/operations/reconcile
```

Manual orders and robot orders use the same `OrderService`, risk checks, audit
log, persistence in `orders`/`order_fills`, and Binance Testnet adapter.
The same private Testnet flows are also exposed in the dashboard: `/portfolio`
has a reconcile action and `/operations` has manual order and order
reconciliation controls.

Collect Testnet validation evidence without mutating service state:

```bash
API_URL=http://localhost:8000 ./scripts/collect-testnet-evidence.sh
```

Use [docs/runbooks/testnet-validation-checklist.md](docs/runbooks/testnet-validation-checklist.md)
as the operational checklist before any higher-risk Testnet validation step.
Use [docs/runbooks/mainnet-readiness-checklist.md](docs/runbooks/mainnet-readiness-checklist.md)
as the mandatory hardening checklist before any future Mainnet promotion. That
checklist does not authorize Mainnet by itself; a dedicated Linear issue and
Slack Canvas decision are still required.

Frontend:

```bash
cd apps/web
npm install
npm run lint
npm run build
npm run dev
```

The frontend toolchain requires Node.js 22 or newer, as declared in
`apps/web/package.json`. Older system Node versions can fail before ESLint or
Next.js start.

Frontend implementation standards:

- Read `DESIGN.md` before changing UI.
- Use TailwindCSS for component styling.
- Keep `apps/web/app/globals.css` limited to Tailwind import, design tokens, and minimal base styles.
- Reuse components from `apps/web/components` before creating new UI patterns.
- Preserve an operational dashboard experience instead of introducing landing-page patterns.

## Agent workflow

Agents working on this repository should follow [AGENTS.md](AGENTS.md). The
Slack Canvas is the central project documentation, the frontend visual
governance Canvas is the durable UI decision, Linear is the source of task
execution state, and frontend work should align with `DESIGN.md`, TailwindCSS,
and reusable components in `apps/web/components`.

## Safety assumptions

- No real Binance credential belongs in this repository.
- Mainnet is out of scope and is explicitly blocked by the execution adapter.
- The MVP is BTCUSDT, Binance Spot Testnet, and long-only Spot behavior.
- Agents and MCP access are read-only until explicit future authorization, audit, and scope controls exist.
