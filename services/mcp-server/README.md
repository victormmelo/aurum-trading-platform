# Aurum MCP Server

Read-only MCP server for Aurum agents.

The server talks to the existing Aurum API and exposes operational context without direct
database access, Binance credentials, or order execution.

## Run

Start the API first, then run:

```bash
python services/mcp-server/main.py
```

Configuration:

- `AURUM_API_BASE_URL`: upstream API URL. Defaults to `http://localhost:8000`.
- `AURUM_API_BEARER_TOKEN`: optional bearer token forwarded to the upstream API.

## Read-only tools

- `get_market_summary`
- `get_portfolio_status`
- `get_trade_history`
- `get_decision_log`
- `get_risk_status`
- `get_strategy_config`
- `explain_last_decision`

All tools use GET requests against existing API endpoints. Unsupported tool calls and
unknown arguments are rejected.

Future issues will add:

- Bearer token authentication.
- Redis-backed rate limiting.
- Audit logs for agent access.
