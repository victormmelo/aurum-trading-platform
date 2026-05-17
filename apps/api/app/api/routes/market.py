from __future__ import annotations

from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.schemas import (
    MarketCandleResponse,
    MarketCandlesResponse,
    MarketSnapshotSummary,
    MarketSummaryResponse,
)
from app.db.models import MarketCandle, MarketSnapshot
from app.db.session import get_db_session

router = APIRouter(prefix="/market", tags=["market"])

MarketInterval = Literal["1h", "4h", "1d"]


class MarketReadStore(Protocol):
    def get_latest_snapshot(self, *, environment: str, symbol: str) -> MarketSnapshot | None: ...

    def list_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[MarketCandle]: ...


class SqlAlchemyMarketReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_snapshot(self, *, environment: str, symbol: str) -> MarketSnapshot | None:
        statement = (
            select(MarketSnapshot)
            .where(
                MarketSnapshot.environment == environment,
                MarketSnapshot.symbol == symbol,
            )
            .order_by(MarketSnapshot.captured_at.desc())
            .limit(1)
        )
        return self.session.scalars(statement).first()

    def list_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[MarketCandle]:
        statement = (
            select(MarketCandle)
            .where(
                MarketCandle.environment == environment,
                MarketCandle.symbol == symbol,
                MarketCandle.interval == interval,
            )
            .order_by(MarketCandle.open_time.desc())
            .limit(limit)
        )
        candles = list(self.session.scalars(statement))
        return list(reversed(candles))


def _store(session: Session) -> MarketReadStore:
    return SqlAlchemyMarketReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.get("/summary", response_model=MarketSummaryResponse)
def market_summary(session: Annotated[Session, Depends(get_db_session)]) -> MarketSummaryResponse:
    return get_market_summary(_store(session), environment=_environment(), symbol=_symbol())


@router.get("/candles", response_model=MarketCandlesResponse)
def market_candles(
    session: Annotated[Session, Depends(get_db_session)],
    interval: Annotated[MarketInterval, Query()] = "1h",
    limit: Annotated[int, Query(ge=1, le=500)] = 250,
) -> MarketCandlesResponse:
    return get_market_candles(
        _store(session),
        environment=_environment(),
        symbol=_symbol(),
        interval=interval,
        limit=limit,
    )


def get_market_summary(
    store: MarketReadStore, *, environment: str, symbol: str
) -> MarketSummaryResponse:
    snapshot = store.get_latest_snapshot(environment=environment, symbol=symbol)
    return MarketSummaryResponse(
        environment=environment,
        symbol=symbol,
        snapshot=_snapshot_response(snapshot) if snapshot is not None else None,
    )


def get_market_candles(
    store: MarketReadStore, *, environment: str, symbol: str, interval: str, limit: int
) -> MarketCandlesResponse:
    candles = store.list_candles(
        environment=environment, symbol=symbol, interval=interval, limit=limit
    )
    return MarketCandlesResponse(
        environment=environment,
        symbol=symbol,
        interval=interval,
        candles=[
            MarketCandleResponse.model_validate(candle, from_attributes=True)
            for candle in candles
        ],
    )


def _snapshot_response(snapshot: MarketSnapshot) -> MarketSnapshotSummary:
    return MarketSnapshotSummary.model_validate(snapshot, from_attributes=True)
