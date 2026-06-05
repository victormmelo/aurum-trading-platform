from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.schemas import (
    PerformanceDailyPointResponse,
    PerformanceSummaryResponse,
    PerformanceTradesResponse,
    PerformanceTradeResponse,
)
from app.db.models import Order, OrderFill, PortfolioSnapshot
from app.db.session import get_db_session
from app.performance.service import (
    PerformanceReadStore,
    build_performance_summary,
    build_performance_trades,
)

router = APIRouter(prefix="/performance", tags=["performance"])

PerformancePeriod = Literal["7d", "30d", "90d", "mtd", "ytd", "all"]


class SqlAlchemyPerformanceReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_fills(self, *, environment: str, symbol: str) -> list[OrderFill]:
        statement = (
            select(OrderFill)
            .join(Order)
            .options(selectinload(OrderFill.order))
            .where(OrderFill.environment == environment, Order.symbol == symbol)
            .order_by(OrderFill.filled_at.asc(), OrderFill.created_at.asc())
        )
        return list(self.session.scalars(statement))

    def list_snapshots(self, *, environment: str, symbol: str) -> list[PortfolioSnapshot]:
        statement = (
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.environment == environment,
                PortfolioSnapshot.symbol == symbol,
            )
            .order_by(PortfolioSnapshot.captured_at.asc())
        )
        return list(self.session.scalars(statement))


def _store(session: Session) -> PerformanceReadStore:
    return SqlAlchemyPerformanceReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.get("/summary", response_model=PerformanceSummaryResponse)
def performance_summary(
    session: Annotated[Session, Depends(get_db_session)],
    period: Annotated[PerformancePeriod, Query()] = "30d",
) -> PerformanceSummaryResponse:
    summary = build_performance_summary(
        _store(session),
        environment=_environment(),
        symbol=_symbol(),
        period=period,
    )
    return PerformanceSummaryResponse(
        environment=summary.environment,
        symbol=summary.symbol,
        period=summary.period,
        period_start=summary.period_start,
        period_end=summary.period_end,
        realized_pnl=summary.realized_pnl,
        unrealized_pnl=summary.unrealized_pnl,
        total_pnl=summary.total_pnl,
        initial_equity=summary.initial_equity,
        final_equity=summary.final_equity,
        return_pct=summary.return_pct,
        total_fees_usdt=summary.total_fees_usdt,
        sell_count=summary.sell_count,
        win_rate_pct=summary.win_rate_pct,
        average_win_usdt=summary.average_win_usdt,
        average_loss_usdt=summary.average_loss_usdt,
        largest_win_usdt=summary.largest_win_usdt,
        largest_loss_usdt=summary.largest_loss_usdt,
        max_drawdown_pct=summary.max_drawdown_pct,
        status=summary.status,
        daily=[
            PerformanceDailyPointResponse(
                date=point.date,
                realized_pnl=point.realized_pnl,
                equity=point.equity,
            )
            for point in summary.daily
        ],
    )


@router.get("/trades", response_model=PerformanceTradesResponse)
def performance_trades(
    session: Annotated[Session, Depends(get_db_session)],
    period: Annotated[PerformancePeriod, Query()] = "30d",
) -> PerformanceTradesResponse:
    trades = build_performance_trades(
        _store(session),
        environment=_environment(),
        symbol=_symbol(),
        period=period,
    )
    return PerformanceTradesResponse(
        environment=_environment(),
        symbol=_symbol(),
        period=period,
        trades=[
            PerformanceTradeResponse(
                id=trade.id,
                order_id=trade.order_id,
                decision_id=trade.decision_id,
                bot_run_id=trade.bot_run_id,
                sold_at=trade.sold_at,
                quantity=trade.quantity,
                average_sell_price=trade.average_sell_price,
                average_cost=trade.average_cost,
                gross_proceeds=trade.gross_proceeds,
                cost_basis_reduced=trade.cost_basis_reduced,
                fees_usdt=trade.fees_usdt,
                pnl_usdt=trade.pnl_usdt,
                pnl_pct=trade.pnl_pct,
                source=trade.source,
                status=trade.status,
                fee_estimated=trade.fee_estimated,
            )
            for trade in trades
        ],
    )
