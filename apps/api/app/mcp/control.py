from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import McpAccessLog, McpToken

ALLOWED_MCP_SCOPES = {
    "read:market",
    "read:portfolio",
    "read:trades",
    "read:decisions",
    "read:config",
    "read:reports",
}

READ_ONLY_MCP_TOOLS = [
    "get_market_summary",
    "get_portfolio_status",
    "get_trade_history",
    "get_decision_log",
    "get_risk_status",
    "get_strategy_config",
    "explain_last_decision",
]


class McpTokenNotFoundError(Exception):
    """Raised when the requested MCP token does not exist."""


class McpTokenInvalidError(Exception):
    """Raised when an MCP bearer token is invalid, revoked, expired, or underscoped."""


class McpScopeError(Exception):
    """Raised when a requested MCP scope is outside the MVP read-only allowlist."""


@dataclass(frozen=True)
class McpTokenCreate:
    name: str
    agent_name: str | None
    scopes: list[str]
    expires_at: datetime | None


@dataclass(frozen=True)
class McpTokenCreated:
    token: McpToken
    secret: str


@dataclass(frozen=True)
class McpAccessLogCreate:
    token_id: uuid.UUID | None
    agent_name: str | None
    resource: str
    arguments: dict[str, object]
    status: str
    status_code: int | None
    error_message: str | None
    latency_ms: int | None


class McpStore(Protocol):
    def list_tokens(self, *, environment: str) -> list[McpToken]: ...

    def get_token_by_id(self, *, environment: str, token_id: uuid.UUID) -> McpToken | None: ...

    def get_token_by_hash(self, *, token_hash: str) -> McpToken | None: ...

    def add_token(self, token: McpToken) -> None: ...

    def add_access_log(self, access_log: McpAccessLog) -> None: ...

    def list_access_logs(
        self,
        *,
        environment: str,
        limit: int,
        offset: int,
        status: str | None,
        resource: str | None,
    ) -> list[McpAccessLog]: ...

    def commit(self) -> None: ...


class SqlAlchemyMcpStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tokens(self, *, environment: str) -> list[McpToken]:
        statement = (
            select(McpToken)
            .where(McpToken.environment == environment)
            .order_by(McpToken.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get_token_by_id(self, *, environment: str, token_id: uuid.UUID) -> McpToken | None:
        statement = select(McpToken).where(
            McpToken.environment == environment,
            McpToken.id == token_id,
        )
        return self.session.scalars(statement).first()

    def get_token_by_hash(self, *, token_hash: str) -> McpToken | None:
        statement = select(McpToken).where(McpToken.token_hash == token_hash)
        return self.session.scalars(statement).first()

    def add_token(self, token: McpToken) -> None:
        self.session.add(token)
        self.session.flush()

    def add_access_log(self, access_log: McpAccessLog) -> None:
        self.session.add(access_log)
        self.session.flush()

    def list_access_logs(
        self,
        *,
        environment: str,
        limit: int,
        offset: int,
        status: str | None,
        resource: str | None,
    ) -> list[McpAccessLog]:
        statement = select(McpAccessLog).where(McpAccessLog.environment == environment)
        if status is not None:
            statement = statement.where(McpAccessLog.status == status)
        if resource is not None:
            statement = statement.where(McpAccessLog.resource == resource)
        statement = statement.order_by(
            McpAccessLog.occurred_at.desc(),
            McpAccessLog.id.desc(),
        ).limit(limit).offset(offset)
        return list(self.session.scalars(statement))

    def commit(self) -> None:
        self.session.commit()


def create_mcp_token(
    store: McpStore,
    *,
    environment: str,
    command: McpTokenCreate,
) -> McpTokenCreated:
    _validate_scopes(command.scopes)
    secret = f"aurum_mcp_{secrets.token_urlsafe(32)}"
    token = McpToken(
        environment=environment,
        name=command.name,
        agent_name=command.agent_name,
        token_hash=hash_mcp_token(secret),
        scopes=sorted(set(command.scopes)),
        status="active",
        expires_at=command.expires_at,
    )
    store.add_token(token)
    store.commit()
    return McpTokenCreated(token=token, secret=secret)


def list_mcp_tokens(store: McpStore, *, environment: str) -> list[McpToken]:
    return store.list_tokens(environment=environment)


def revoke_mcp_token(
    store: McpStore,
    *,
    environment: str,
    token_id: uuid.UUID,
    now: datetime | None = None,
) -> McpToken:
    token = store.get_token_by_id(environment=environment, token_id=token_id)
    if token is None:
        raise McpTokenNotFoundError(f"Token MCP não encontrado para ambiente {environment}")

    occurred_at = now or datetime.now(UTC)
    token.status = "revoked"
    token.revoked_at = occurred_at
    store.commit()
    return token


def validate_mcp_token(
    store: McpStore,
    *,
    bearer_token: str,
    required_scopes: list[str],
    resource: str,
    now: datetime | None = None,
) -> McpToken:
    _validate_scopes(required_scopes)
    token = store.get_token_by_hash(token_hash=hash_mcp_token(bearer_token))
    if token is None:
        raise McpTokenInvalidError("Token MCP inválido")
    if token.status != "active":
        raise McpTokenInvalidError("Token MCP revogado ou inativo")

    checked_at = now or datetime.now(UTC)
    if token.expires_at is not None and token.expires_at <= checked_at:
        token.status = "expired"
        store.commit()
        raise McpTokenInvalidError("Token MCP expirado")

    missing = sorted(set(required_scopes) - set(token.scopes or []))
    if missing:
        raise McpTokenInvalidError(
            f"Escopo MCP insuficiente para {resource}: {', '.join(missing)}"
        )

    token.last_used_at = checked_at
    store.commit()
    return token


def record_mcp_access(
    store: McpStore,
    *,
    environment: str,
    command: McpAccessLogCreate,
    now: datetime | None = None,
) -> McpAccessLog:
    access_log = McpAccessLog(
        environment=environment,
        token_id=command.token_id,
        agent_name=command.agent_name,
        resource=command.resource,
        arguments=command.arguments,
        status=command.status,
        status_code=command.status_code,
        error_message=command.error_message,
        latency_ms=command.latency_ms,
        occurred_at=now or datetime.now(UTC),
    )
    store.add_access_log(access_log)
    store.commit()
    return access_log


def list_mcp_access_logs(
    store: McpStore,
    *,
    environment: str,
    limit: int,
    offset: int,
    status: str | None,
    resource: str | None,
) -> list[McpAccessLog]:
    return store.list_access_logs(
        environment=environment,
        limit=limit,
        offset=offset,
        status=status,
        resource=resource,
    )


def hash_mcp_token(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _validate_scopes(scopes: list[str]) -> None:
    unknown = sorted(set(scopes) - ALLOWED_MCP_SCOPES)
    if unknown:
        raise McpScopeError(f"Escopos MCP fora do MVP read-only: {', '.join(unknown)}")
