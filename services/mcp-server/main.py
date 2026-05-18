from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

JsonObject = dict[str, Any]

SERVER_NAME = "aurum-mcp-server"
SERVER_VERSION = "0.1.0"
DEFAULT_API_BASE_URL = "http://localhost:8000"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: JsonObject


class AurumApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AurumApiClient:
    def __init__(self, *, base_url: str, bearer_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def get(self, path: str, params: JsonObject | None = None) -> JsonObject:
        query = f"?{urlencode(_clean_params(params or {}))}" if params else ""
        request = Request(f"{self.base_url}{path}{query}", method="GET")
        request.add_header("Accept", "application/json")
        if self.bearer_token:
            request.add_header("Authorization", f"Bearer {self.bearer_token}")

        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise AurumApiError(
                f"Aurum API returned HTTP {exc.code}: {body}", status_code=exc.code
            ) from exc
        except URLError as exc:
            raise AurumApiError(f"Aurum API request failed: {exc.reason}") from exc

        if not payload:
            return {}
        loaded = json.loads(payload)
        return loaded if isinstance(loaded, dict) else {"data": loaded}


def build_tools() -> list[ToolDefinition]:
    read_only_note = "Read-only. Does not place orders or mutate Aurum state."
    return [
        ToolDefinition(
            name="get_market_summary",
            description=f"Return BTCUSDT market summary from Aurum. {read_only_note}",
            input_schema=_object_schema(),
        ),
        ToolDefinition(
            name="get_portfolio_status",
            description=f"Return current Aurum portfolio status. {read_only_note}",
            input_schema=_object_schema(),
        ),
        ToolDefinition(
            name="get_trade_history",
            description=f"Return recent orders and, optionally, fills. {read_only_note}",
            input_schema=_object_schema(
                {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                    "offset": {"type": "integer", "minimum": 0, "default": 0},
                    "side": {"type": "string", "enum": ["BUY", "SELL"]},
                    "status": {
                        "type": "string",
                        "enum": [
                            "NEW",
                            "PARTIALLY_FILLED",
                            "FILLED",
                            "CANCELED",
                            "REJECTED",
                            "EXPIRED",
                        ],
                    },
                    "include_fills": {"type": "boolean", "default": True},
                }
            ),
        ),
        ToolDefinition(
            name="get_decision_log",
            description=f"Return recent bot decision logs. {read_only_note}",
            input_schema=_object_schema(
                {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                    "offset": {"type": "integer", "minimum": 0, "default": 0},
                    "decision": {
                        "type": "string",
                        "enum": ["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"],
                    },
                }
            ),
        ),
        ToolDefinition(
            name="get_risk_status",
            description=(
                "Return bot status, active risk config, and portfolio risk context. "
                f"{read_only_note}"
            ),
            input_schema=_object_schema(),
        ),
        ToolDefinition(
            name="get_strategy_config",
            description=f"Return the active strategy configuration. {read_only_note}",
            input_schema=_object_schema(),
        ),
        ToolDefinition(
            name="explain_last_decision",
            description=(
                "Return a structured explanation of the latest bot decision. "
                f"{read_only_note}"
            ),
            input_schema=_object_schema(),
        ),
    ]


class AurumMcpServer:
    def __init__(self, api_client: AurumApiClient) -> None:
        self.api_client = api_client
        self.tools = {tool.name: tool for tool in build_tools()}

    def handle(self, message: JsonObject) -> JsonObject | None:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}

        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return _result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        if method == "tools/list":
            return _result(
                request_id,
                {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.input_schema,
                        }
                        for tool in self.tools.values()
                    ]
                },
            )
        if method == "tools/call":
            try:
                return _result(request_id, self.call_tool(params))
            except ValueError as exc:
                return _error(request_id, code=-32602, message=str(exc))
            except AurumApiError as exc:
                return _error(request_id, code=-32000, message=str(exc))

        return _error(request_id, code=-32601, message=f"Unsupported MCP method: {method}")

    def call_tool(self, params: JsonObject) -> JsonObject:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in self.tools:
            raise ValueError(f"Tool is not available or not read-only: {name}")
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object")

        handlers = {
            "get_market_summary": self.get_market_summary,
            "get_portfolio_status": self.get_portfolio_status,
            "get_trade_history": self.get_trade_history,
            "get_decision_log": self.get_decision_log,
            "get_risk_status": self.get_risk_status,
            "get_strategy_config": self.get_strategy_config,
            "explain_last_decision": self.explain_last_decision,
        }
        payload = handlers[name](arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
                }
            ],
            "structuredContent": payload,
        }

    def get_market_summary(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, set())
        return self.api_client.get("/market/summary")

    def get_portfolio_status(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, set())
        return self.api_client.get("/portfolio/status")

    def get_trade_history(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, {"limit", "offset", "side", "status", "include_fills"})
        params = {
            "limit": _int_arg(arguments, "limit", default=50, minimum=1, maximum=200),
            "offset": _int_arg(arguments, "offset", default=0, minimum=0),
            "side": _optional_enum(arguments, "side", {"BUY", "SELL"}),
            "status": _optional_enum(
                arguments,
                "status",
                {"NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "EXPIRED"},
            ),
        }
        payload = {"orders": self.api_client.get("/operations/orders", params)}
        if bool(arguments.get("include_fills", True)):
            payload["fills"] = self.api_client.get(
                "/operations/fills",
                {"limit": params["limit"], "offset": params["offset"]},
            )
        return payload

    def get_decision_log(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, {"limit", "offset", "decision"})
        params = {
            "limit": _int_arg(arguments, "limit", default=50, minimum=1, maximum=200),
            "offset": _int_arg(arguments, "offset", default=0, minimum=0),
            "decision": _optional_enum(
                arguments, "decision", {"COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"}
            ),
        }
        return self.api_client.get("/decisions", params)

    def get_risk_status(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, set())
        return {
            "bot": self.api_client.get("/bot/status"),
            "risk_config": self.api_client.get("/configs/risk/active"),
            "portfolio": self.api_client.get("/portfolio/status"),
        }

    def get_strategy_config(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, set())
        return self.api_client.get("/configs/strategy/active")

    def explain_last_decision(self, arguments: JsonObject) -> JsonObject:
        _reject_unknown(arguments, set())
        payload = self.api_client.get("/decisions", {"limit": 1, "offset": 0})
        decisions = payload.get("decisions") or []
        if not decisions:
            return {
                "environment": payload.get("environment"),
                "symbol": payload.get("symbol"),
                "has_decision": False,
                "summary": "No bot decisions are available yet.",
            }

        latest = decisions[0]
        return {
            "environment": latest.get("environment", payload.get("environment")),
            "symbol": latest.get("symbol", payload.get("symbol")),
            "has_decision": True,
            "decision_id": latest.get("id"),
            "bot_run_id": latest.get("bot_run_id"),
            "decided_at": latest.get("decided_at"),
            "decision": latest.get("decision"),
            "summary": _decision_summary(latest),
            "reason": latest.get("reason"),
            "reason_payload": latest.get("reason_payload") or {},
            "indicators": latest.get("indicators") or {},
            "intended_order": latest.get("intended_order") or {},
            "execution_result": latest.get("execution_result") or {},
            "portfolio_state": latest.get("portfolio_state") or {},
        }


def run_stdio_server(server: AurumMcpServer) -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError("JSON-RPC message must be an object")
            response = server.handle(message)
        except Exception as exc:  # noqa: BLE001
            response = _error(None, code=-32700, message=str(exc))

        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def create_server_from_env() -> AurumMcpServer:
    return AurumMcpServer(
        AurumApiClient(
            base_url=os.getenv("AURUM_API_BASE_URL", DEFAULT_API_BASE_URL),
            bearer_token=os.getenv("AURUM_API_BEARER_TOKEN"),
        )
    )


def main() -> None:
    run_stdio_server(create_server_from_env())


def _object_schema(properties: JsonObject | None = None) -> JsonObject:
    return {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }


def _result(request_id: Any, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, *, code: int, message: str) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _clean_params(params: JsonObject) -> JsonObject:
    return {key: value for key, value in params.items() if value is not None}


def _reject_unknown(arguments: JsonObject, allowed: set[str]) -> None:
    unknown = set(arguments) - allowed
    if unknown:
        raise ValueError(f"Unsupported arguments for read-only tool: {', '.join(sorted(unknown))}")


def _int_arg(
    arguments: JsonObject,
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    raw = arguments.get(name, default)
    if not isinstance(raw, int):
        raise ValueError(f"{name} must be an integer")
    if raw < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}")
    if maximum is not None and raw > maximum:
        raise ValueError(f"{name} must be less than or equal to {maximum}")
    return raw


def _optional_enum(arguments: JsonObject, name: str, allowed: set[str]) -> str | None:
    value = arguments.get(name)
    if value is None:
        return None
    if value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return str(value)


def _decision_summary(decision: JsonObject) -> str:
    decision_value = decision.get("decision", "UNKNOWN")
    reason = decision.get("reason") or "No reason was recorded."
    execution = decision.get("execution_result") or {}
    execution_status = execution.get("status", "unknown")
    reason_text = str(reason).rstrip(".")
    return f"{decision_value}: {reason_text}. Execution status: {execution_status}."


if __name__ == "__main__":
    main()
