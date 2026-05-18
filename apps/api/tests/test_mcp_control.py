from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models import McpAccessLog, McpToken
from app.mcp.control import (
    McpAccessLogCreate,
    McpScopeError,
    McpTokenCreate,
    McpTokenInvalidError,
    create_mcp_token,
    hash_mcp_token,
    list_mcp_access_logs,
    list_mcp_tokens,
    record_mcp_access,
    revoke_mcp_token,
    validate_mcp_token,
)

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_create_mcp_token_returns_secret_once_and_stores_hash_only() -> None:
    store = FakeMcpStore()

    created = create_mcp_token(
        store,
        environment="testnet",
        command=McpTokenCreate(
            name="Codex",
            agent_name="codex",
            scopes=["read:market", "read:decisions"],
            expires_at=None,
        ),
    )

    assert created.secret.startswith("aurum_mcp_")
    assert created.token.token_hash == hash_mcp_token(created.secret)
    assert created.secret != created.token.token_hash
    assert created.token.scopes == ["read:decisions", "read:market"]
    assert list_mcp_tokens(store, environment="testnet") == [created.token]
    assert store.commits == 1


def test_create_mcp_token_rejects_non_read_only_scope() -> None:
    with pytest.raises(McpScopeError):
        create_mcp_token(
            FakeMcpStore(),
            environment="testnet",
            command=McpTokenCreate(
                name="bad",
                agent_name=None,
                scopes=["trade:orders"],
                expires_at=None,
            ),
        )


def test_validate_mcp_token_updates_last_used_and_checks_scope() -> None:
    secret = "aurum_mcp_secret"
    token = _token(secret=secret, scopes=["read:market"])
    store = FakeMcpStore(tokens=[token])

    validated = validate_mcp_token(
        store,
        bearer_token=secret,
        required_scopes=["read:market"],
        resource="get_market_summary",
        now=NOW,
    )

    assert validated is token
    assert token.last_used_at == NOW
    assert store.commits == 1


def test_validate_mcp_token_rejects_invalid_revoked_expired_and_underscoped() -> None:
    secret = "aurum_mcp_secret"

    with pytest.raises(McpTokenInvalidError, match="inválido"):
        validate_mcp_token(
            FakeMcpStore(),
            bearer_token=secret,
            required_scopes=["read:market"],
            resource="get_market_summary",
            now=NOW,
        )

    with pytest.raises(McpTokenInvalidError, match="revogado"):
        validate_mcp_token(
            FakeMcpStore(tokens=[_token(secret=secret, status="revoked")]),
            bearer_token=secret,
            required_scopes=["read:market"],
            resource="get_market_summary",
            now=NOW,
        )

    expired = _token(secret=secret, expires_at=NOW - timedelta(seconds=1))
    expired_store = FakeMcpStore(tokens=[expired])
    with pytest.raises(McpTokenInvalidError, match="expirado"):
        validate_mcp_token(
            expired_store,
            bearer_token=secret,
            required_scopes=["read:market"],
            resource="get_market_summary",
            now=NOW,
        )
    assert expired.status == "expired"

    with pytest.raises(McpTokenInvalidError, match="Escopo MCP insuficiente"):
        validate_mcp_token(
            FakeMcpStore(tokens=[_token(secret=secret, scopes=["read:market"])]),
            bearer_token=secret,
            required_scopes=["read:portfolio"],
            resource="get_portfolio_status",
            now=NOW,
        )


def test_revoke_mcp_token_and_record_access_log() -> None:
    token = _token(secret="aurum_mcp_secret")
    store = FakeMcpStore(tokens=[token])

    revoked = revoke_mcp_token(store, environment="testnet", token_id=token.id, now=NOW)

    assert revoked.status == "revoked"
    assert revoked.revoked_at == NOW

    access_log = record_mcp_access(
        store,
        environment="testnet",
        command=McpAccessLogCreate(
            token_id=token.id,
            agent_name="codex",
            resource="get_market_summary",
            arguments={},
            status="success",
            status_code=200,
            error_message=None,
            latency_ms=12,
        ),
        now=NOW,
    )

    assert access_log in store.access_logs
    assert access_log.resource == "get_market_summary"
    assert access_log.latency_ms == 12


def test_list_mcp_access_logs_filters_and_paginates() -> None:
    first = _access_log(resource="get_market_summary", status="success", occurred_at=NOW)
    second = _access_log(
        resource="get_portfolio_status",
        status="error",
        occurred_at=NOW + timedelta(seconds=1),
    )
    store = FakeMcpStore(access_logs=[first, second])

    assert list_mcp_access_logs(
        store,
        environment="testnet",
        limit=10,
        offset=0,
        status=None,
        resource=None,
    ) == [second, first]
    assert list_mcp_access_logs(
        store,
        environment="testnet",
        limit=10,
        offset=0,
        status="error",
        resource=None,
    ) == [second]


class FakeMcpStore:
    def __init__(
        self,
        tokens: list[McpToken] | None = None,
        access_logs: list[McpAccessLog] | None = None,
    ) -> None:
        self.tokens = tokens or []
        self.access_logs = access_logs or []
        self.commits = 0

    def list_tokens(self, *, environment: str) -> list[McpToken]:
        return [token for token in self.tokens if token.environment == environment]

    def get_token_by_id(self, *, environment: str, token_id: uuid.UUID) -> McpToken | None:
        return next(
            (
                token
                for token in self.tokens
                if token.environment == environment and token.id == token_id
            ),
            None,
        )

    def get_token_by_hash(self, *, token_hash: str) -> McpToken | None:
        return next((token for token in self.tokens if token.token_hash == token_hash), None)

    def add_token(self, token: McpToken) -> None:
        self.tokens.append(token)

    def add_access_log(self, access_log: McpAccessLog) -> None:
        self.access_logs.append(access_log)

    def list_access_logs(
        self,
        *,
        environment: str,
        limit: int,
        offset: int,
        status: str | None,
        resource: str | None,
    ) -> list[McpAccessLog]:
        logs = [
            access_log
            for access_log in self.access_logs
            if access_log.environment == environment
        ]
        if status is not None:
            logs = [access_log for access_log in logs if access_log.status == status]
        if resource is not None:
            logs = [access_log for access_log in logs if access_log.resource == resource]
        logs.sort(key=lambda access_log: access_log.occurred_at, reverse=True)
        return logs[offset : offset + limit]

    def commit(self) -> None:
        self.commits += 1


def _token(
    *,
    secret: str,
    scopes: list[str] | None = None,
    status: str = "active",
    expires_at: datetime | None = None,
) -> McpToken:
    return McpToken(
        id=uuid.uuid4(),
        environment="testnet",
        name="Codex",
        agent_name="codex",
        token_hash=hash_mcp_token(secret),
        scopes=scopes or ["read:market"],
        status=status,
        expires_at=expires_at,
    )


def _access_log(*, resource: str, status: str, occurred_at: datetime) -> McpAccessLog:
    return McpAccessLog(
        id=uuid.uuid4(),
        environment="testnet",
        token_id=None,
        agent_name="codex",
        resource=resource,
        arguments={},
        status=status,
        status_code=200 if status == "success" else 403,
        error_message=None,
        latency_ms=12,
        occurred_at=occurred_at,
    )
