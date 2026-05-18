from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import mcp as mcp_routes
from app.db.session import get_db_session
from app.main import create_app
from app.mcp.control import McpTokenInvalidError

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_create_mcp_token_returns_secret_once_without_hash(monkeypatch) -> None:  # noqa: ANN001
    token_id = uuid.uuid4()
    client = _client()

    def create(store, environment, command):  # noqa: ANN001
        assert environment == "testnet"
        assert command.scopes == ["read:market"]
        return SimpleNamespace(
            token=_token(token_id=token_id, scopes=["read:market"]),
            secret="aurum_mcp_secret",
        )

    monkeypatch.setattr(mcp_routes, "create_mcp_token", create)

    response = client.post(
        "/mcp/tokens",
        json={"name": "Codex", "agent_name": "codex", "scopes": ["read:market"]},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["token"] == "aurum_mcp_secret"
    assert payload["id"] == str(token_id)
    assert "token_hash" not in payload


def test_mcp_status_returns_read_only_capabilities() -> None:
    client = _client()

    response = client.get("/mcp/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "testnet"
    assert "read:market" in payload["allowed_scopes"]
    assert "get_market_summary" in payload["tools"]


def test_list_mcp_tokens_never_exposes_secret_or_hash(monkeypatch) -> None:  # noqa: ANN001
    token_id = uuid.uuid4()
    client = _client()
    monkeypatch.setattr(
        mcp_routes,
        "list_mcp_tokens",
        lambda store, environment: [_token(token_id=token_id, scopes=["read:market"])],
    )

    response = client.get("/mcp/tokens")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tokens"][0]["id"] == str(token_id)
    assert "token" not in payload["tokens"][0]
    assert "token_hash" not in payload["tokens"][0]


def test_revoke_mcp_token_endpoint(monkeypatch) -> None:  # noqa: ANN001
    token_id = uuid.uuid4()
    client = _client()

    def revoke(store, environment, token_id):  # noqa: ANN001
        return _token(token_id=token_id, scopes=["read:market"], status="revoked")

    monkeypatch.setattr(mcp_routes, "revoke_mcp_token", revoke)

    response = client.post(f"/mcp/tokens/{token_id}/revoke")

    assert response.status_code == 200
    assert response.json()["status"] == "revoked"


def test_validate_mcp_token_endpoint_requires_bearer_and_scope(monkeypatch) -> None:  # noqa: ANN001
    token_id = uuid.uuid4()
    client = _client()

    def validate(store, bearer_token, required_scopes, resource):  # noqa: ANN001
        assert bearer_token == "aurum_mcp_secret"
        assert required_scopes == ["read:market"]
        assert resource == "get_market_summary"
        return _token(token_id=token_id, scopes=["read:market"])

    monkeypatch.setattr(mcp_routes, "validate_mcp_token", validate)

    missing = client.post(
        "/mcp/auth/validate",
        json={"resource": "get_market_summary", "required_scopes": ["read:market"]},
    )
    assert missing.status_code == 401

    response = client.post(
        "/mcp/auth/validate",
        headers={"Authorization": "Bearer aurum_mcp_secret"},
        json={"resource": "get_market_summary", "required_scopes": ["read:market"]},
    )

    assert response.status_code == 200
    assert response.json()["token_id"] == str(token_id)


def test_validate_mcp_token_endpoint_blocks_insufficient_scope(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def validate(store, bearer_token, required_scopes, resource):  # noqa: ANN001
        raise McpTokenInvalidError("Escopo MCP insuficiente")

    monkeypatch.setattr(mcp_routes, "validate_mcp_token", validate)

    response = client.post(
        "/mcp/auth/validate",
        headers={"Authorization": "Bearer aurum_mcp_secret"},
        json={"resource": "get_portfolio_status", "required_scopes": ["read:portfolio"]},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Escopo MCP insuficiente"}


def test_create_mcp_audit_log_endpoint(monkeypatch) -> None:  # noqa: ANN001
    token_id = uuid.uuid4()
    log_id = uuid.uuid4()
    client = _client()

    def record(store, environment, command):  # noqa: ANN001
        assert environment == "testnet"
        assert command.token_id == token_id
        assert command.status == "success"
        return SimpleNamespace(
            id=log_id,
            environment=environment,
            token_id=command.token_id,
            agent_name=command.agent_name,
            resource=command.resource,
            arguments=command.arguments,
            status=command.status,
            status_code=command.status_code,
            error_message=command.error_message,
            latency_ms=command.latency_ms,
            occurred_at=NOW,
            created_at=None,
        )

    monkeypatch.setattr(mcp_routes, "record_mcp_access", record)

    response = client.post(
        "/mcp/audit-log",
        json={
            "token_id": str(token_id),
            "agent_name": "codex",
            "resource": "get_market_summary",
            "arguments": {},
            "status": "success",
            "status_code": 200,
            "latency_ms": 10,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(log_id)


def test_list_mcp_audit_log_endpoint(monkeypatch) -> None:  # noqa: ANN001
    log_id = uuid.uuid4()
    client = _client()

    def list_logs(store, environment, limit, offset, status, resource):  # noqa: ANN001
        assert environment == "testnet"
        assert limit == 25
        assert offset == 5
        assert status == "success"
        assert resource == "get_market_summary"
        return [
            SimpleNamespace(
                id=log_id,
                environment=environment,
                token_id=None,
                agent_name="codex",
                resource=resource,
                arguments={},
                status=status,
                status_code=200,
                error_message=None,
                latency_ms=10,
                occurred_at=NOW,
                created_at=None,
            )
        ]

    monkeypatch.setattr(mcp_routes, "list_mcp_access_logs", list_logs)

    response = client.get(
        "/mcp/audit-log?limit=25&offset=5&status=success&resource=get_market_summary"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "testnet"
    assert payload["logs"][0]["id"] == str(log_id)


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()
    return TestClient(app)


def _token(
    *,
    token_id: uuid.UUID,
    scopes: list[str],
    status: str = "active",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=token_id,
        environment="testnet",
        name="Codex",
        agent_name="codex",
        scopes=scopes,
        status=status,
        expires_at=None,
        revoked_at=NOW if status == "revoked" else None,
        last_used_at=None,
        created_at=None,
        updated_at=None,
    )
