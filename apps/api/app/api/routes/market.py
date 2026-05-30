from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from redis import asyncio as aioredis
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
from app.db.session import get_db_session, get_session_factory

router = APIRouter(prefix="/market", tags=["market"])

MarketInterval = Literal["1h", "4h", "1d"]
MARKET_CHANNEL = "aurum:market:snapshots"
HEARTBEAT_SECONDS = 15


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


@router.get("/stream")
async def market_stream() -> StreamingResponse:
    return StreamingResponse(
        _market_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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


async def _market_event_stream() -> AsyncIterator[str]:
    settings = get_settings()
    yield _sse("snapshot", _latest_summary_json())

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    try:
        await pubsub.subscribe(MARKET_CHANNEL)
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=HEARTBEAT_SECONDS,
            )
            if message is None:
                yield _sse("heartbeat", "{}")
                continue
            yield _sse("snapshot", _latest_summary_json())
    except asyncio.CancelledError:
        raise
    except Exception:
        while True:
            yield _sse("snapshot", _latest_summary_json())
            await asyncio.sleep(HEARTBEAT_SECONDS)
    finally:
        await pubsub.close()
        await redis_client.aclose()


def _latest_summary_json() -> str:
    settings = get_settings()
    session_factory = get_session_factory()
    with session_factory() as session:
        summary = get_market_summary(
            SqlAlchemyMarketReadStore(session),
            environment=settings.aurum_environment,
            symbol=settings.trading_symbol,
        )
    return summary.model_dump_json()


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
