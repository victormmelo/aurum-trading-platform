from __future__ import annotations

from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.schemas import (
    OrderFillResponse,
    OrderFillsResponse,
    OrderResponse,
    OrdersResponse,
)
from app.db.models import Order, OrderFill
from app.db.session import get_db_session

router = APIRouter(prefix="/operations", tags=["operations"])

OrderSide = Literal["BUY", "SELL"]
OrderStatus = Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "EXPIRED"]


class OperationsReadStore(Protocol):
    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        side: str | None,
        status: str | None,
    ) -> list[Order]: ...

    def list_fills(
        self, *, environment: str, symbol: str, limit: int, offset: int
    ) -> list[OrderFill]: ...


class SqlAlchemyOperationsReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        side: str | None,
        status: str | None,
    ) -> list[Order]:
        statement = select(Order).where(Order.environment == environment, Order.symbol == symbol)
        if side is not None:
            statement = statement.where(Order.side == side)
        if status is not None:
            statement = statement.where(Order.status == status)
        statement = (
            statement.order_by(Order.submitted_at.desc().nullslast(), Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def list_fills(
        self, *, environment: str, symbol: str, limit: int, offset: int
    ) -> list[OrderFill]:
        statement = (
            select(OrderFill)
            .join(Order)
            .options(selectinload(OrderFill.order))
            .where(OrderFill.environment == environment, Order.symbol == symbol)
            .order_by(OrderFill.filled_at.desc(), OrderFill.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))


def _store(session: Session) -> OperationsReadStore:
    return SqlAlchemyOperationsReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.get("/orders", response_model=OrdersResponse)
def operation_orders(
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    side: Annotated[OrderSide | None, Query()] = None,
    status: Annotated[OrderStatus | None, Query()] = None,
) -> OrdersResponse:
    return get_orders(
        _store(session),
        environment=_environment(),
        symbol=_symbol(),
        limit=limit,
        offset=offset,
        side=side,
        status=status,
    )


@router.get("/fills", response_model=OrderFillsResponse)
def operation_fills(
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OrderFillsResponse:
    return get_fills(
        _store(session), environment=_environment(), symbol=_symbol(), limit=limit, offset=offset
    )


def get_orders(
    store: OperationsReadStore,
    *,
    environment: str,
    symbol: str,
    limit: int,
    offset: int,
    side: str | None,
    status: str | None,
) -> OrdersResponse:
    orders = store.list_orders(
        environment=environment,
        symbol=symbol,
        limit=limit,
        offset=offset,
        side=side,
        status=status,
    )
    return OrdersResponse(
        environment=environment,
        symbol=symbol,
        orders=[OrderResponse.model_validate(order, from_attributes=True) for order in orders],
    )


def get_fills(
    store: OperationsReadStore, *, environment: str, symbol: str, limit: int, offset: int
) -> OrderFillsResponse:
    fills = store.list_fills(environment=environment, symbol=symbol, limit=limit, offset=offset)
    return OrderFillsResponse(
        environment=environment,
        symbol=symbol,
        fills=[_fill_response(fill) for fill in fills],
    )


def _fill_response(fill: OrderFill) -> OrderFillResponse:
    return OrderFillResponse(
        id=fill.id,
        environment=fill.environment,
        exchange=fill.exchange,
        order_id=fill.order_id,
        order_decision_id=fill.order.decision_id if fill.order is not None else None,
        order_bot_run_id=fill.order.bot_run_id if fill.order is not None else None,
        external_trade_id=fill.external_trade_id,
        filled_at=fill.filled_at,
        price=fill.price,
        quantity=fill.quantity,
        quote_quantity=fill.quote_quantity,
        fee_amount=fill.fee_amount,
        fee_asset=fill.fee_asset,
        fee_estimated_usdt=fill.fee_estimated_usdt,
        raw_payload=fill.raw_payload,
    )
