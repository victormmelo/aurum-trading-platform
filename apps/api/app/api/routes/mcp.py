from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.schemas import (
    McpAccessLogCreateRequest,
    McpAccessLogResponse,
    McpAccessLogsResponse,
    McpStatusResponse,
    McpTokenCreateRequest,
    McpTokenCreateResponse,
    McpTokenResponse,
    McpTokensResponse,
    McpTokenValidateRequest,
    McpTokenValidateResponse,
)
from app.db.session import get_db_session
from app.mcp.control import (
    ALLOWED_MCP_SCOPES,
    READ_ONLY_MCP_TOOLS,
    McpAccessLogCreate,
    McpScopeError,
    McpStore,
    McpTokenCreate,
    McpTokenInvalidError,
    McpTokenNotFoundError,
    SqlAlchemyMcpStore,
    create_mcp_token,
    list_mcp_access_logs,
    list_mcp_tokens,
    record_mcp_access,
    revoke_mcp_token,
    validate_mcp_token,
)

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _store(session: Session) -> McpStore:
    return SqlAlchemyMcpStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


@router.get("/status", response_model=McpStatusResponse)
def mcp_status() -> McpStatusResponse:
    settings = get_settings()
    return McpStatusResponse(
        environment=settings.aurum_environment,
        auth_enabled=True,
        allowed_scopes=sorted(ALLOWED_MCP_SCOPES),
        tools=READ_ONLY_MCP_TOOLS,
    )


@router.post(
    "/tokens",
    response_model=McpTokenCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mcp_token_endpoint(
    request: McpTokenCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> McpTokenCreateResponse:
    try:
        created = create_mcp_token(
            _store(session),
            environment=_environment(),
            command=McpTokenCreate(**request.model_dump()),
        )
    except McpScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    payload = McpTokenResponse.model_validate(created.token, from_attributes=True).model_dump()
    return McpTokenCreateResponse(**payload, token=created.secret)


@router.get("/tokens", response_model=McpTokensResponse)
def mcp_tokens(session: Annotated[Session, Depends(get_db_session)]) -> McpTokensResponse:
    environment = _environment()
    return McpTokensResponse(
        environment=environment,
        tokens=[
            McpTokenResponse.model_validate(token, from_attributes=True)
            for token in list_mcp_tokens(_store(session), environment=environment)
        ],
    )


@router.post("/tokens/{token_id}/revoke", response_model=McpTokenResponse)
def revoke_mcp_token_endpoint(
    token_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> McpTokenResponse:
    try:
        token = revoke_mcp_token(_store(session), environment=_environment(), token_id=token_id)
    except McpTokenNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return McpTokenResponse.model_validate(token, from_attributes=True)


@router.post("/auth/validate", response_model=McpTokenValidateResponse)
def validate_mcp_token_endpoint(
    request: McpTokenValidateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> McpTokenValidateResponse:
    bearer_token = _bearer_token(authorization)
    try:
        token = validate_mcp_token(
            _store(session),
            bearer_token=bearer_token,
            required_scopes=list(request.required_scopes),
            resource=request.resource,
        )
    except McpScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except McpTokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return McpTokenValidateResponse(
        token_id=token.id,
        environment=token.environment,
        agent_name=token.agent_name,
        scopes=token.scopes,
    )


@router.post(
    "/audit-log",
    response_model=McpAccessLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mcp_access_log_endpoint(
    request: McpAccessLogCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> McpAccessLogResponse:
    access_log = record_mcp_access(
        _store(session),
        environment=_environment(),
        command=McpAccessLogCreate(**request.model_dump()),
    )
    return McpAccessLogResponse.model_validate(access_log, from_attributes=True)


@router.get("/audit-log", response_model=McpAccessLogsResponse)
def mcp_access_logs(
    session: Annotated[Session, Depends(get_db_session)],
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    resource: str | None = None,
) -> McpAccessLogsResponse:
    bounded_limit = min(max(limit, 1), 100)
    bounded_offset = max(offset, 0)
    environment = _environment()
    return McpAccessLogsResponse(
        environment=environment,
        logs=[
            McpAccessLogResponse.model_validate(access_log, from_attributes=True)
            for access_log in list_mcp_access_logs(
                _store(session),
                environment=environment,
                limit=bounded_limit,
                offset=bounded_offset,
                status=status,
                resource=resource,
            )
        ],
    )


def _bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token ausente")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token ausente")
    return token
