from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def test_mcp_initialize_and_tool_list_expose_read_only_tools() -> None:
    server = _mcp().AurumMcpServer(_ApiClientStub())

    initialize = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert initialize["result"]["serverInfo"]["name"] == "aurum-mcp-server"
    tool_names = {tool["name"] for tool in tools["result"]["tools"]}
    assert tool_names == {
        "get_market_summary",
        "get_portfolio_status",
        "get_trade_history",
        "get_decision_log",
        "get_risk_status",
        "get_strategy_config",
        "explain_last_decision",
    }


def test_get_market_summary_calls_existing_read_api_contract() -> None:
    client = _ApiClientStub()
    server = _mcp().AurumMcpServer(client)

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_market_summary", "arguments": {}},
        }
    )

    assert client.calls == [("/market/summary", None)]
    assert response["result"]["structuredContent"] == {
        "environment": "testnet",
        "symbol": "BTCUSDT",
        "snapshot": None,
    }
    assert json.loads(response["result"]["content"][0]["text"])["symbol"] == "BTCUSDT"


def test_get_trade_history_uses_orders_and_fills_filters() -> None:
    client = _ApiClientStub()
    server = _mcp().AurumMcpServer(client)

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_trade_history",
                "arguments": {
                    "limit": 10,
                    "offset": 5,
                    "side": "BUY",
                    "status": "FILLED",
                },
            },
        }
    )

    assert client.calls == [
        (
            "/operations/orders",
            {"limit": 10, "offset": 5, "side": "BUY", "status": "FILLED"},
        ),
        ("/operations/fills", {"limit": 10, "offset": 5}),
    ]
    assert response["result"]["structuredContent"]["orders"]["orders"] == []
    assert response["result"]["structuredContent"]["fills"]["fills"] == []


def test_get_decision_log_validates_decision_filter() -> None:
    server = _mcp().AurumMcpServer(_ApiClientStub())

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_decision_log",
                "arguments": {"decision": "SHORT", "limit": 10},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "decision must be one of" in response["error"]["message"]


def test_unknown_tools_are_blocked_as_not_read_only() -> None:
    server = _mcp().AurumMcpServer(_ApiClientStub())

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "pause_bot", "arguments": {"reason": "manual"}},
        }
    )

    assert response["error"] == {
        "code": -32602,
        "message": "Tool is not available or not read-only: pause_bot",
    }


def test_get_risk_status_combines_status_config_and_portfolio() -> None:
    client = _ApiClientStub()
    server = _mcp().AurumMcpServer(client)

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_risk_status", "arguments": {}},
        }
    )

    assert client.calls == [
        ("/bot/status", None),
        ("/configs/risk/active", None),
        ("/portfolio/status", None),
    ]
    assert response["result"]["structuredContent"]["bot"]["trading_mode"] == "testnet"


def test_auth_enabled_validates_scope_and_writes_audit_log() -> None:
    client = _ApiClientStub()
    server = _mcp().AurumMcpServer(
        client,
        mcp_bearer_token="aurum_mcp_secret",
        auth_required=True,
    )

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_market_summary", "arguments": {}},
        }
    )

    assert response["result"]["structuredContent"]["symbol"] == "BTCUSDT"
    assert client.post_calls[0] == (
        "/mcp/auth/validate",
        {
            "resource": "get_market_summary",
            "required_scopes": ["read:market"],
        },
        "aurum_mcp_secret",
    )
    assert client.post_calls[1][0] == "/mcp/audit-log"
    assert client.post_calls[1][1]["token_id"] == "token-1"
    assert client.post_calls[1][1]["resource"] == "get_market_summary"
    assert client.post_calls[1][1]["status"] == "success"


def test_auth_enabled_blocks_missing_mcp_bearer_token() -> None:
    server = _mcp().AurumMcpServer(_ApiClientStub(), auth_required=True)

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_market_summary", "arguments": {}},
        }
    )

    assert response["error"]["code"] == -32000
    assert "AURUM_MCP_BEARER_TOKEN is required" in response["error"]["message"]


def test_auth_enabled_writes_error_audit_log_for_insufficient_scope() -> None:
    client = _ApiClientStub(validate_error=True)
    server = _mcp().AurumMcpServer(
        client,
        mcp_bearer_token="aurum_mcp_secret",
        auth_required=True,
    )

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_portfolio_status", "arguments": {}},
        }
    )

    assert response["error"]["code"] == -32000
    assert client.post_calls[1][0] == "/mcp/audit-log"
    assert client.post_calls[1][1]["status"] == "error"
    assert client.post_calls[1][1]["resource"] == "get_portfolio_status"


def test_explain_last_decision_returns_structured_summary() -> None:
    server = _mcp().AurumMcpServer(_ApiClientStub())

    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "explain_last_decision", "arguments": {}},
        }
    )

    payload = response["result"]["structuredContent"]
    assert payload["has_decision"] is True
    assert payload["decision"] == "NAO_OPERAR"
    assert payload["summary"] == "NAO_OPERAR: Robô pausado. Execution status: not_sent."


def _mcp() -> Any:
    path = (
        Path(__file__).resolve().parents[3]
        / "services"
        / "mcp-server"
        / "main.py"
    )
    spec = importlib.util.spec_from_file_location("aurum_mcp_server", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _ApiClientStub:
    def __init__(self, *, validate_error: bool = False) -> None:
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.post_calls: list[tuple[str, dict[str, object], str | None]] = []
        self.validate_error = validate_error

    def get(self, path: str, params: dict[str, object] | None = None) -> dict[str, object]:
        self.calls.append((path, params))
        responses: dict[str, dict[str, object]] = {
            "/market/summary": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "snapshot": None,
            },
            "/portfolio/status": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "snapshot": None,
                "position": None,
            },
            "/operations/orders": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "orders": [],
            },
            "/operations/fills": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "fills": [],
            },
            "/decisions": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "decisions": [
                    {
                        "id": "decision-1",
                        "environment": "testnet",
                        "symbol": "BTCUSDT",
                        "bot_run_id": "run-1",
                        "decided_at": "2026-05-17T20:00:00Z",
                        "decision": "NAO_OPERAR",
                        "reason": "Robô pausado",
                        "reason_payload": {"code": "bot_not_running"},
                        "indicators": {},
                        "intended_order": {},
                        "execution_result": {"status": "not_sent"},
                        "portfolio_state": {},
                    }
                ],
            },
            "/bot/status": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "status": "running",
                "trading_mode": "testnet",
                "last_cycle_at": None,
                "paused_at": None,
                "emergency_stopped_at": None,
                "reason": None,
            },
            "/configs/risk/active": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "version": 1,
                "parameters": {},
            },
            "/configs/strategy/active": {
                "environment": "testnet",
                "symbol": "BTCUSDT",
                "version": 1,
                "parameters": {},
            },
        }
        return responses[path]

    def post(
        self,
        path: str,
        payload: dict[str, object],
        *,
        bearer_token: str | None = None,
    ) -> dict[str, object]:
        self.post_calls.append((path, payload, bearer_token))
        if path == "/mcp/auth/validate":
            if self.validate_error:
                error_cls = sys.modules["aurum_mcp_server"].AurumApiError
                raise error_cls(
                    "Aurum API returned HTTP 403: insufficient scope",
                    status_code=403,
                )
            return {
                "token_id": "token-1",
                "environment": "testnet",
                "agent_name": "codex",
                "scopes": payload["required_scopes"],
            }
        if path == "/mcp/audit-log":
            return {
                "id": "log-1",
                "environment": "testnet",
                **payload,
            }
        raise AssertionError(f"Unexpected POST path: {path}")
