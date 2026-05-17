from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.configuration.control import (
    ConfigNotFoundError,
    ConfigStore,
    ConfigVersionConflictError,
    RiskConfigCreate,
    SqlAlchemyConfigStore,
    StrategyConfigCreate,
    activate_risk_config,
    activate_strategy_config,
    create_risk_config,
    create_strategy_config,
    get_active_risk_config,
    get_active_strategy_config,
    list_risk_configs,
    list_strategy_configs,
)
from app.core.config import get_settings
from app.core.schemas import (
    RiskConfigCreateRequest,
    RiskConfigResponse,
    RiskConfigsResponse,
    StrategyConfigCreateRequest,
    StrategyConfigResponse,
    StrategyConfigsResponse,
)
from app.db.session import get_db_session

router = APIRouter(prefix="/configs", tags=["configs"])


def _store(session: Session) -> ConfigStore:
    return SqlAlchemyConfigStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


def _not_found_error(exc: ConfigNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _conflict_error(exc: ConfigVersionConflictError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/strategy", response_model=StrategyConfigsResponse)
def strategy_configs(
    session: Annotated[Session, Depends(get_db_session)],
) -> StrategyConfigsResponse:
    environment = _environment()
    symbol = _symbol()
    configs = list_strategy_configs(_store(session), environment=environment, symbol=symbol)
    return StrategyConfigsResponse(
        environment=environment,
        symbol=symbol,
        configs=[
            StrategyConfigResponse.model_validate(config, from_attributes=True)
            for config in configs
        ],
    )


@router.get("/strategy/active", response_model=StrategyConfigResponse | None)
def active_strategy_config(
    session: Annotated[Session, Depends(get_db_session)],
) -> StrategyConfigResponse | None:
    config = get_active_strategy_config(
        _store(session), environment=_environment(), symbol=_symbol()
    )
    return (
        StrategyConfigResponse.model_validate(config, from_attributes=True)
        if config is not None
        else None
    )


@router.post(
    "/strategy",
    response_model=StrategyConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_strategy_config_endpoint(
    request: StrategyConfigCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> StrategyConfigResponse:
    try:
        config = create_strategy_config(
            _store(session),
            environment=_environment(),
            symbol=_symbol(),
            command=StrategyConfigCreate(**request.model_dump()),
        )
    except ConfigVersionConflictError as exc:
        raise _conflict_error(exc) from exc
    return StrategyConfigResponse.model_validate(config, from_attributes=True)


@router.post("/strategy/{config_id}/activate", response_model=StrategyConfigResponse)
def activate_strategy_config_endpoint(
    config_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> StrategyConfigResponse:
    try:
        config = activate_strategy_config(
            _store(session),
            environment=_environment(),
            symbol=_symbol(),
            config_id=config_id,
        )
    except ConfigNotFoundError as exc:
        raise _not_found_error(exc) from exc
    return StrategyConfigResponse.model_validate(config, from_attributes=True)


@router.get("/risk", response_model=RiskConfigsResponse)
def risk_configs(session: Annotated[Session, Depends(get_db_session)]) -> RiskConfigsResponse:
    environment = _environment()
    symbol = _symbol()
    configs = list_risk_configs(_store(session), environment=environment, symbol=symbol)
    return RiskConfigsResponse(
        environment=environment,
        symbol=symbol,
        configs=[
            RiskConfigResponse.model_validate(config, from_attributes=True) for config in configs
        ],
    )


@router.get("/risk/active", response_model=RiskConfigResponse | None)
def active_risk_config(
    session: Annotated[Session, Depends(get_db_session)],
) -> RiskConfigResponse | None:
    config = get_active_risk_config(_store(session), environment=_environment(), symbol=_symbol())
    return (
        RiskConfigResponse.model_validate(config, from_attributes=True)
        if config is not None
        else None
    )


@router.post(
    "/risk",
    response_model=RiskConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_risk_config_endpoint(
    request: RiskConfigCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> RiskConfigResponse:
    try:
        config = create_risk_config(
            _store(session),
            environment=_environment(),
            symbol=_symbol(),
            command=RiskConfigCreate(**request.model_dump()),
        )
    except ConfigVersionConflictError as exc:
        raise _conflict_error(exc) from exc
    return RiskConfigResponse.model_validate(config, from_attributes=True)


@router.post("/risk/{config_id}/activate", response_model=RiskConfigResponse)
def activate_risk_config_endpoint(
    config_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> RiskConfigResponse:
    try:
        config = activate_risk_config(
            _store(session),
            environment=_environment(),
            symbol=_symbol(),
            config_id=config_id,
        )
    except ConfigNotFoundError as exc:
        raise _not_found_error(exc) from exc
    return RiskConfigResponse.model_validate(config, from_attributes=True)
