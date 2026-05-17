from __future__ import annotations

from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.schemas import DecisionLogResponse, DecisionsResponse
from app.db.models import DecisionLog
from app.db.session import get_db_session

router = APIRouter(prefix="/decisions", tags=["decisions"])

DecisionValue = Literal["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"]


class DecisionsReadStore(Protocol):
    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        decision: str | None,
    ) -> list[DecisionLog]: ...


class SqlAlchemyDecisionsReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        decision: str | None,
    ) -> list[DecisionLog]:
        statement = select(DecisionLog).where(
            DecisionLog.environment == environment,
            DecisionLog.symbol == symbol,
        )
        if decision is not None:
            statement = statement.where(DecisionLog.decision == decision)
        statement = (
            statement.order_by(DecisionLog.decided_at.desc(), DecisionLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))


def _store(session: Session) -> DecisionsReadStore:
    return SqlAlchemyDecisionsReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.get("", response_model=DecisionsResponse)
def decisions(
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    decision: Annotated[DecisionValue | None, Query()] = None,
) -> DecisionsResponse:
    return get_decisions(
        _store(session),
        environment=_environment(),
        symbol=_symbol(),
        limit=limit,
        offset=offset,
        decision=decision,
    )


def get_decisions(
    store: DecisionsReadStore,
    *,
    environment: str,
    symbol: str,
    limit: int,
    offset: int,
    decision: str | None,
) -> DecisionsResponse:
    rows = store.list_decisions(
        environment=environment,
        symbol=symbol,
        limit=limit,
        offset=offset,
        decision=decision,
    )
    return DecisionsResponse(
        environment=environment,
        symbol=symbol,
        decisions=[
            DecisionLogResponse.model_validate(row, from_attributes=True) for row in rows
        ],
    )
