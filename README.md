# Aurum Trading Platform

Aurum is an operational platform for observing, controlling, and auditing an autonomous BTCUSDT trading robot. The MVP targets Binance Spot Testnet, long-only operation, and a progressive path through local development, paper trading, Testnet validation, and only later controlled Mainnet usage.

The first cycle creates the project foundation: FastAPI backend, Next.js frontend, PostgreSQL, Redis, Docker Compose, and placeholders for worker and MCP services. It does not implement live trading, Binance credentials, a full database schema, or a functional MCP server yet.

## Monorepo layout

```text
apps/
  api/           FastAPI backend
  web/           Next.js dashboard
services/
  worker/        Trading and market worker placeholder
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
- `worker`: placeholder for market and trading cycles.
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

Frontend:

```bash
cd apps/web
npm install
npm run lint
npm run build
npm run dev
```

## Agent workflow

Agents working on this repository should follow [AGENTS.md](AGENTS.md). The Slack Canvas is the central project documentation, Linear is the source of task execution state, and frontend work should align with the `npx getdesign@latest add mastercard` design direction.

## Safety assumptions

- No real Binance credential belongs in this repository.
- Mainnet is out of scope for this foundation cycle.
- The MVP starts with BTCUSDT, Binance Spot Testnet, and long-only behavior.
- Agents and MCP access are read-only until explicit future authorization, audit, and scope controls exist.
