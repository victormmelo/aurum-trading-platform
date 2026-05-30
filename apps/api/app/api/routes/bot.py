from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.bot.control import (
    BotControlStore,
    BotRuntimeStateConflictError,
    BotRuntimeStateNotFoundError,
    SqlAlchemyBotControlStore,
    emergency_stop_bot,
    get_bot_status,
    initialize_bot,
    pause_bot,
    resume_bot,
)
from app.core.config import get_settings
from app.core.schemas import BotCommandRequest, BotStatusResponse
from app.db.session import get_db_session

router = APIRouter(prefix="/bot", tags=["bot"])


def _store(session: Session) -> BotControlStore:
    return SqlAlchemyBotControlStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


def _trading_mode() -> str:
    return get_settings().aurum_environment


def _response(status_value: object) -> BotStatusResponse:
    return BotStatusResponse.model_validate(status_value, from_attributes=True)


def _not_found_error(exc: BotRuntimeStateNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _conflict_error(exc: BotRuntimeStateConflictError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/status", response_model=BotStatusResponse)
def bot_status(session: Annotated[Session, Depends(get_db_session)]) -> BotStatusResponse:
    try:
        return _response(get_bot_status(_store(session), environment=_environment()))
    except BotRuntimeStateNotFoundError as exc:
        raise _not_found_error(exc) from exc


@router.post("/initialize", response_model=BotStatusResponse)
def bot_initialize(
    command: BotCommandRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> BotStatusResponse:
    return _response(
        initialize_bot(
            _store(session),
            environment=_environment(),
            symbol=_symbol(),
            trading_mode=_trading_mode(),
            reason=command.reason,
        )
    )


@router.post("/pause", response_model=BotStatusResponse)
def bot_pause(
    command: BotCommandRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> BotStatusResponse:
    try:
        return _response(
            pause_bot(_store(session), environment=_environment(), reason=command.reason)
        )
    except BotRuntimeStateNotFoundError as exc:
        raise _not_found_error(exc) from exc
    except BotRuntimeStateConflictError as exc:
        raise _conflict_error(exc) from exc


@router.post("/resume", response_model=BotStatusResponse)
def bot_resume(
    command: BotCommandRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> BotStatusResponse:
    try:
        return _response(
            resume_bot(_store(session), environment=_environment(), reason=command.reason)
        )
    except BotRuntimeStateNotFoundError as exc:
        raise _not_found_error(exc) from exc
    except BotRuntimeStateConflictError as exc:
        raise _conflict_error(exc) from exc


@router.post("/emergency-stop", response_model=BotStatusResponse)
def bot_emergency_stop(
    command: BotCommandRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> BotStatusResponse:
    try:
        return _response(
            emergency_stop_bot(_store(session), environment=_environment(), reason=command.reason)
        )
    except BotRuntimeStateNotFoundError as exc:
        raise _not_found_error(exc) from exc
