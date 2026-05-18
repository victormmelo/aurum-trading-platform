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
- `AURUM_MCP_AUTH_ENABLED`: enables API-backed MCP token validation. Defaults to `true`.
- `AURUM_MCP_BEARER_TOKEN`: required when MCP auth is enabled. Create this token through
  `POST /mcp/tokens`; the API stores only its SHA-256 hash.

The MCP server validates the token and required read-only scopes through
`POST /mcp/auth/validate` before every tool call. It records each successful or failed tool call
through `POST /mcp/audit-log`, including token ID, agent, resource, allowed arguments, status, and
latency.

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

Token scopes are mapped per tool:

- `read:market`: `get_market_summary`
- `read:portfolio`: `get_portfolio_status`
- `read:trades`: `get_trade_history`
- `read:decisions`: `get_decision_log`, `explain_last_decision`
- `read:config`: `get_strategy_config`
- `read:portfolio` and `read:config`: `get_risk_status`

Future issues may add Redis-backed rate limiting and a dashboard page for token management. The UI
work remains blocked until the backend MCP contracts are available.
