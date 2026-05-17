# Aurum Trading Platform

Aurum is an operational platform for observing, controlling, and auditing an autonomous BTCUSDT trading robot. The MVP targets Binance Spot Testnet, long-only operation, and a progressive path through local development, paper trading, Testnet validation, and only later controlled Mainnet usage.

The first cycles create the project foundation: FastAPI backend, Next.js frontend, PostgreSQL, Redis, Docker Compose, Binance read-only market data, the initial operational schema, strategy components, and a dry-run worker cycle. The worker records auditable bot runs and decisions, but it does not submit orders to Binance or require trading credentials.

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
- `worker`: dry-run trading cycle that persists `bot_runs` and `decision_logs`.
- `mcp-server`: placeholder for read-only agent access.

## Local setup

1. Copy environment defaults:

```bash
cp .env.example .env
```

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

Import initial BTCUSDT candles after PostgreSQL migrations are applied:

```bash
aurum-import-candles --interval 1h --interval 4h --interval 1d --limit 500
```

Run one dry-run worker cycle after migrations, configs, runtime state, market data, and a portfolio snapshot exist:

```bash
cd apps/api
. .venv/bin/activate
python ../../services/worker/main.py
```

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

## Agent workflow

Agents working on this repository should follow [AGENTS.md](AGENTS.md). The Slack Canvas is the central project documentation, Linear is the source of task execution state, and frontend work should align with the `npx getdesign@latest add mastercard` design direction.

## Safety assumptions

- No real Binance credential belongs in this repository.
- Mainnet is out of scope for this foundation cycle.
- The MVP starts with BTCUSDT, Binance Spot Testnet, and long-only behavior.
- Agents and MCP access are read-only until explicit future authorization, audit, and scope controls exist.
