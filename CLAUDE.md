# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Aurum is an operational platform for observing, controlling, and auditing an autonomous BTCUSDT trading robot. MVP scope is fixed: Binance Spot Testnet, BTCUSDT, long-only, no leverage, no Mainnet execution. Mainnet is explicitly blocked at the execution adapter level.

## Source of truth

- **Slack Canvas** (product & technical decisions): https://rvxsolutions.slack.com/docs/T0B4MRY2N8Y/F0B562EFLJU
- **Frontend visual governance Canvas**: https://rvxsolutions.slack.com/docs/T0B4MRY2N8Y/F0B460FPCEB
- **Linear** (task execution state): https://linear.app/victormmelo/project/aurum-trading-plataforma-robo-btc-0ec902f0dca8

Before implementing anything meaningful, read the relevant Slack Canvas sections and the matching Linear issue. Only change architecture, schemas, security model, or dashboard requirements by also updating the Slack Canvas.

## Commands

### Backend (apps/api)

```bash
cd apps/api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_health.py

# Run a single test by name
pytest tests/test_bot_control.py::test_function_name

# Lint
ruff check .
ruff format .

# Dev server (requires postgres + redis running)
python -m alembic upgrade head
uvicorn app.main:app --reload

# Backfill candles manually
aurum-import-candles --interval 1h --interval 4h --interval 1d --limit 500

# Run the worker locally
python ../../services/worker/main.py
```

### Frontend (apps/web, requires Node.js 22+)

```bash
cd apps/web
npm install
npm run dev      # dev server at localhost:3000
npm run build
npm run lint
```

### Docker Compose (all services)

```bash
cp .env.example .env   # fill in BINANCE_API_KEY/SECRET for Testnet execution
docker compose up --build
# Web: http://localhost:3000
# API: http://localhost:8000/health
# API docs: http://localhost:8000/docs
```

### Testnet validation

```bash
API_URL=http://localhost:8000 ./scripts/collect-testnet-evidence.sh
```

## Architecture

### Monorepo layout

```
apps/api/          FastAPI backend + all domain logic
apps/web/          Next.js 15 operational dashboard
services/worker/   Continuous market polling + decision cycle (runs as separate process/container)
services/mcp-server/  Read-only MCP server (future)
infra/docker/      Dockerfiles
```

### How services connect

The **worker** (`services/worker/main.py`) runs independently and drives two loops:
1. **Market loop** (~30s): fetches candles from Binance, writes `Candle` + `MarketSnapshot` to Postgres, publishes a Redis event (`aurum:market:snapshots`).
2. **Decision loop** (~60s, only when bot status is `running`): loads active `StrategyConfig` + `RiskConfig`, generates a `Decision`, and when in testnet mode submits orders via `OrderService` → Binance Spot Testnet adapter.

The **API** (`apps/api/app/main.py`) is pure read/write over the same Postgres database — it does not run the strategy. The **web** dashboard reads from the API over HTTP.

Both manual orders (via `/operations/manual-order`) and robot orders use the same `OrderService`, risk checks, audit log, and Binance adapter.

### Backend domain layout (apps/api/app/)

| Package | Responsibility |
|---|---|
| `api/routes/` | 11 FastAPI route modules (bot, market, portfolio, operations, decisions, configs, performance, exports, mcp, health) |
| `db/` | SQLAlchemy ORM models (`models.py`) and session factory |
| `core/` | Pydantic settings, shared schemas |
| `market/` | Binance public client, candle import, snapshot refresh |
| `execution/` | Binance private client, order execution adapter (blocks Mainnet) |
| `strategy/` | Signal generation, regime detection, risk sizing, backtest |
| `portfolio/` | Balance reconciliation against Binance |
| `bot/` | Bot state transitions (running/paused/emergency_stop) |
| `worker/` | Decision cycle orchestration (called by `services/worker/`) |
| `performance/` | P&L calculation, trade history |
| `configuration/` | Strategy/risk config versioning |
| `mcp/` | MCP token management, rate limiting, audit log |

### Key database models

Models live in `apps/api/app/db/models.py`. Critical ones:

- `BotRuntimeState` — singleton bot control record; `status` ∈ {running, paused, emergency_stop}, `trading_mode` ∈ {paper, testnet, mainnet}
- `StrategyConfig` / `RiskConfig` — versioned configs, one active per environment
- `Candle` — OHLCV for 1h/4h/1d intervals
- `MarketSnapshot` — computed indicators + trend state, consumed by the decision cycle
- `Decision` — every buy/sell/hold/noop with reasoning, linked to optional `Order`
- `Order` / `OrderFill` — full execution audit trail
- `PortfolioSnapshot` / `Position` — account state snapshots
- `McpToken` / `McpAccessLog` — agent authentication + access audit

Numeric precision: money/price uses `Numeric(28,10)`, quantity uses `Numeric(28,12)`.

Migrations are in `apps/api/migrations/` (Alembic). Always run `alembic upgrade head` before starting the API or worker locally.

### Frontend architecture (apps/web/)

- **Next.js 15 App Router** with React 19; all pages are in `app/` directories.
- **API client**: `lib/api.ts` — all backend calls go through `fetchApi`/`postApi`; type definitions live here too.
- **Shared components**: `components/app-shell.tsx` (topbar + sidebar layout), `components/ui.tsx` (all reusable primitives). Search here before creating new UI patterns.
- **Design tokens**: defined in `app/globals.css` via TailwindCSS v4 `@theme`. Do not add CSS modules or component-level CSS files.

## Frontend design conventions

Read `DESIGN.md` before changing any UI. Key rules:

- Primary color: `#107e59` (RVX green) — sidebar, primary buttons, active states.
- Dashboard background: `color-mix(in srgb, var(--primary) 8%, white)` (light green tint).
- Typography: Poppins (body), Geist Mono (code).
- Cards: `rounded-xl border border-border bg-card shadow-sm`, padding `p-5 md:p-6`.
- Buttons: primary uses `bg-primary text-primary-foreground`, `rounded-md`, min height `h-10`.
- Badges: `rounded-md text-xs font-medium`; use semantic color tokens (success/warning/destructive).
- No decorative gradients, no hero/marketing patterns, no landing-page chrome.
- `rounded-full` only for circles (avatars, status dots, counters).
- Reuse: `AppShell`, `Panel`, `PanelHeader`, `MetricCard`, `StatusPill`, `Notice`, `PrimaryButton`, `IconTextButton`, `LabeledInput`.

## Engineering guardrails

- Prefer small, issue-scoped changes. No broad refactors unless explicitly requested.
- Run `ruff check .` before committing backend changes; run `npm run lint` for frontend.
- Add or update tests when behavior changes; run the narrowest meaningful test suite for the change.
- Never commit Binance credentials, MCP tokens, or any operational secrets. Only `.env.example` is committed.
- Preserve MVP scope (Testnet, BTCUSDT, long-only) unless Slack Canvas + Linear explicitly authorize otherwise.
- MCP and agent access are read-only until future authorization + audit controls exist.
