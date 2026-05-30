from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.schemas import (
    PortfolioReconciliationResponse,
    PortfolioSnapshotResponse,
    PortfolioStatusResponse,
    PositionResponse,
)
from app.db.models import PortfolioSnapshot, Position
from app.db.session import get_db_session
from app.execution.binance_private import BinanceCredentials, BinancePrivateClient
from app.portfolio.reconciliation import BinancePortfolioReconciler

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PortfolioReadStore(Protocol):
    def get_latest_snapshot(
        self, *, environment: str, symbol: str
    ) -> PortfolioSnapshot | None: ...

    def get_open_position(self, *, environment: str, symbol: str) -> Position | None: ...


class SqlAlchemyPortfolioReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_snapshot(
        self, *, environment: str, symbol: str
    ) -> PortfolioSnapshot | None:
        statement = (
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.environment == environment,
                PortfolioSnapshot.symbol == symbol,
            )
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(1)
        )
        return self.session.scalars(statement).first()

    def get_open_position(self, *, environment: str, symbol: str) -> Position | None:
        statement = (
            select(Position)
            .where(
                Position.environment == environment,
                Position.symbol == symbol,
                Position.asset == "BTC",
                Position.side == "LONG",
                Position.quantity > 0,
            )
            .limit(1)
        )
        return self.session.scalars(statement).first()


def _store(session: Session) -> PortfolioReadStore:
    return SqlAlchemyPortfolioReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.get("/status", response_model=PortfolioStatusResponse)
def portfolio_status(
    session: Annotated[Session, Depends(get_db_session)],
) -> PortfolioStatusResponse:
    return get_portfolio_status(_store(session), environment=_environment(), symbol=_symbol())


@router.post("/reconcile", response_model=PortfolioReconciliationResponse)
def reconcile_portfolio(
    session: Annotated[Session, Depends(get_db_session)],
) -> PortfolioReconciliationResponse:
    settings = get_settings()
    if settings.aurum_environment != "testnet":
        raise HTTPException(status_code=422, detail="Portfolio reconciliation is testnet-only")
    if "testnet.binance.vision" not in settings.binance_spot_base_url:
        raise HTTPException(status_code=422, detail="Binance base URL must be Spot Testnet")
    if not settings.binance_api_key or not settings.binance_api_secret:
        raise HTTPException(
            status_code=503,
            detail="BINANCE_API_KEY and BINANCE_API_SECRET are required",
        )
    client = BinancePrivateClient(
        base_url=settings.binance_spot_base_url,
        credentials=BinanceCredentials(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
        ),
        recv_window_ms=settings.binance_recv_window_ms,
    )
    try:
        result = BinancePortfolioReconciler(client).reconcile(
            session,
            environment=settings.aurum_environment,
            symbol=settings.trading_symbol,
        )
        session.commit()
    except RuntimeError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PortfolioReconciliationResponse(
        environment=settings.aurum_environment,
        symbol=settings.trading_symbol,
        snapshot=PortfolioSnapshotResponse.model_validate(
            result.snapshot, from_attributes=True
        ),
        position=PositionResponse.model_validate(result.position, from_attributes=True),
    )


def get_portfolio_status(
    store: PortfolioReadStore, *, environment: str, symbol: str
) -> PortfolioStatusResponse:
    snapshot = store.get_latest_snapshot(environment=environment, symbol=symbol)
    position = store.get_open_position(environment=environment, symbol=symbol)
    return PortfolioStatusResponse(
        environment=environment,
        symbol=symbol,
        snapshot=(
            PortfolioSnapshotResponse.model_validate(snapshot, from_attributes=True)
            if snapshot is not None
            else None
        ),
        position=(
            PositionResponse.model_validate(position, from_attributes=True)
            if position is not None
            else None
        ),
    )
