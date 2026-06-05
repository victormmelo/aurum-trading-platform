from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

from app.db.models import OrderFill, PortfolioSnapshot

PerformancePeriod = Literal["7d", "30d", "90d", "mtd", "ytd", "all"]

ONE_HUNDRED = Decimal("100")
ZERO = Decimal("0")


@dataclass(frozen=True)
class PerformanceTrade:
    id: UUID
    order_id: UUID
    decision_id: UUID | None
    bot_run_id: UUID | None
    sold_at: datetime
    quantity: Decimal
    average_sell_price: Decimal
    average_cost: Decimal
    gross_proceeds: Decimal
    cost_basis_reduced: Decimal
    fees_usdt: Decimal
    pnl_usdt: Decimal
    pnl_pct: Decimal | None
    source: str
    status: str
    fee_estimated: bool


@dataclass(frozen=True)
class PerformanceDailyPoint:
    date: date
    realized_pnl: Decimal
    equity: Decimal | None


@dataclass(frozen=True)
class PerformanceSummary:
    environment: str
    symbol: str
    period: PerformancePeriod
    period_start: datetime | None
    period_end: datetime
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    initial_equity: Decimal | None
    final_equity: Decimal | None
    return_pct: Decimal | None
    total_fees_usdt: Decimal
    sell_count: int
    win_rate_pct: Decimal
    average_win_usdt: Decimal | None
    average_loss_usdt: Decimal | None
    largest_win_usdt: Decimal | None
    largest_loss_usdt: Decimal | None
    max_drawdown_pct: Decimal
    status: Literal["lucrando", "perdendo", "sem_amostra_suficiente", "atencao"]
    daily: list[PerformanceDailyPoint]


class PerformanceReadStore(Protocol):
    def list_fills(self, *, environment: str, symbol: str) -> list[OrderFill]: ...

    def list_snapshots(
        self, *, environment: str, symbol: str
    ) -> list[PortfolioSnapshot]: ...


def build_performance_summary(
    store: PerformanceReadStore,
    *,
    environment: str,
    symbol: str,
    period: PerformancePeriod,
    now: datetime | None = None,
) -> PerformanceSummary:
    period_end = now or datetime.now(UTC)
    period_start = period_start_for(period, period_end)
    fills = store.list_fills(environment=environment, symbol=symbol)
    snapshots = store.list_snapshots(environment=environment, symbol=symbol)
    trades = build_average_cost_trades(fills)
    period_trades = _filter_trades(trades, period_start, period_end)
    period_fills = _filter_fills(fills, period_start, period_end)

    latest_snapshot = snapshots[-1] if snapshots else None
    initial_snapshot = _initial_snapshot(snapshots, period_start)
    final_snapshot = _final_snapshot(snapshots, period_end)
    initial_equity = initial_snapshot.total_equity if initial_snapshot is not None else None
    final_equity = final_snapshot.total_equity if final_snapshot is not None else None
    realized_pnl = sum((trade.pnl_usdt for trade in period_trades), ZERO)
    unrealized_pnl = latest_snapshot.unrealized_pnl if latest_snapshot is not None else ZERO
    total_pnl = realized_pnl + unrealized_pnl
    wins = [trade.pnl_usdt for trade in period_trades if trade.pnl_usdt > 0]
    losses = [trade.pnl_usdt for trade in period_trades if trade.pnl_usdt < 0]

    return PerformanceSummary(
        environment=environment,
        symbol=symbol,
        period=period,
        period_start=period_start,
        period_end=period_end,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        total_pnl=total_pnl,
        initial_equity=initial_equity,
        final_equity=final_equity,
        return_pct=_return_pct(initial_equity, final_equity),
        total_fees_usdt=sum((_fee_usdt(fill)[0] for fill in period_fills), ZERO),
        sell_count=len(period_trades),
        win_rate_pct=(
            Decimal(len(wins)) / Decimal(len(period_trades)) * ONE_HUNDRED
            if period_trades
            else ZERO
        ),
        average_win_usdt=sum(wins, ZERO) / Decimal(len(wins)) if wins else None,
        average_loss_usdt=sum(losses, ZERO) / Decimal(len(losses)) if losses else None,
        largest_win_usdt=max(wins) if wins else None,
        largest_loss_usdt=min(losses) if losses else None,
        max_drawdown_pct=_max_drawdown_pct(_period_snapshots(snapshots, period_start, period_end)),
        status=_performance_status(len(period_trades), total_pnl),
        daily=_daily_points(period_trades, snapshots, period_start, period_end),
    )


def build_performance_trades(
    store: PerformanceReadStore,
    *,
    environment: str,
    symbol: str,
    period: PerformancePeriod,
    now: datetime | None = None,
) -> list[PerformanceTrade]:
    period_end = now or datetime.now(UTC)
    period_start = period_start_for(period, period_end)
    trades = build_average_cost_trades(store.list_fills(environment=environment, symbol=symbol))
    return list(reversed(_filter_trades(trades, period_start, period_end)))


def build_average_cost_trades(fills: list[OrderFill]) -> list[PerformanceTrade]:
    quantity = ZERO
    cost_basis = ZERO
    trades: list[PerformanceTrade] = []

    for fill in sorted(fills, key=lambda item: (item.filled_at, str(item.id))):
        order = fill.order
        if order is None:
            continue
        side = order.side.upper()
        fill_fee_usdt, fee_estimated = _fee_usdt(fill)
        if side == "BUY":
            quantity += fill.quantity
            cost_basis += fill.quote_quantity + fill_fee_usdt
            continue
        if side != "SELL":
            continue

        average_cost = cost_basis / quantity if quantity > 0 else ZERO
        sold_quantity = min(fill.quantity, quantity) if quantity > 0 else fill.quantity
        cost_basis_reduced = average_cost * sold_quantity
        gross_proceeds = fill.quote_quantity
        pnl_usdt = gross_proceeds - cost_basis_reduced - fill_fee_usdt
        pnl_pct = (pnl_usdt / cost_basis_reduced * ONE_HUNDRED) if cost_basis_reduced > 0 else None
        if quantity > 0:
            quantity -= sold_quantity
            cost_basis -= cost_basis_reduced
            if quantity <= 0:
                quantity = ZERO
                cost_basis = ZERO

        trades.append(
            PerformanceTrade(
                id=fill.id,
                order_id=fill.order_id,
                decision_id=order.decision_id,
                bot_run_id=order.bot_run_id,
                sold_at=fill.filled_at,
                quantity=fill.quantity,
                average_sell_price=fill.price,
                average_cost=average_cost,
                gross_proceeds=gross_proceeds,
                cost_basis_reduced=cost_basis_reduced,
                fees_usdt=fill_fee_usdt,
                pnl_usdt=pnl_usdt,
                pnl_pct=pnl_pct,
                source="robô" if order.decision_id is not None else "manual",
                status=order.status,
                fee_estimated=fee_estimated,
            )
        )
    return trades


def period_start_for(period: PerformancePeriod, now: datetime) -> datetime | None:
    if period == "7d":
        return now - timedelta(days=7)
    if period == "30d":
        return now - timedelta(days=30)
    if period == "90d":
        return now - timedelta(days=90)
    if period == "mtd":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "ytd":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def _fee_usdt(fill: OrderFill) -> tuple[Decimal, bool]:
    if fill.fee_estimated_usdt is not None:
        return fill.fee_estimated_usdt, fill.fee_asset not in {None, "USDT"}
    if fill.fee_amount is None:
        return ZERO, False
    if fill.fee_asset == "USDT":
        return fill.fee_amount, False
    if fill.fee_asset == "BTC":
        return fill.fee_amount * fill.price, True
    return ZERO, False


def _filter_trades(
    trades: list[PerformanceTrade], period_start: datetime | None, period_end: datetime
) -> list[PerformanceTrade]:
    return [
        trade
        for trade in trades
        if (period_start is None or trade.sold_at >= period_start) and trade.sold_at <= period_end
    ]


def _filter_fills(
    fills: list[OrderFill], period_start: datetime | None, period_end: datetime
) -> list[OrderFill]:
    return [
        fill
        for fill in fills
        if (period_start is None or fill.filled_at >= period_start) and fill.filled_at <= period_end
    ]


def _period_snapshots(
    snapshots: list[PortfolioSnapshot], period_start: datetime | None, period_end: datetime
) -> list[PortfolioSnapshot]:
    return [
        snapshot
        for snapshot in snapshots
        if (period_start is None or snapshot.captured_at >= period_start)
        and snapshot.captured_at <= period_end
    ]


def _initial_snapshot(
    snapshots: list[PortfolioSnapshot], period_start: datetime | None
) -> PortfolioSnapshot | None:
    if not snapshots:
        return None
    if period_start is None:
        return snapshots[0]
    before_or_at = [snapshot for snapshot in snapshots if snapshot.captured_at <= period_start]
    if before_or_at:
        return before_or_at[-1]
    in_period = [snapshot for snapshot in snapshots if snapshot.captured_at >= period_start]
    return in_period[0] if in_period else None


def _final_snapshot(
    snapshots: list[PortfolioSnapshot], period_end: datetime
) -> PortfolioSnapshot | None:
    candidates = [snapshot for snapshot in snapshots if snapshot.captured_at <= period_end]
    return candidates[-1] if candidates else None


def _return_pct(initial_equity: Decimal | None, final_equity: Decimal | None) -> Decimal | None:
    if initial_equity is None or final_equity is None or initial_equity <= 0:
        return None
    return (final_equity - initial_equity) / initial_equity * ONE_HUNDRED


def _max_drawdown_pct(snapshots: list[PortfolioSnapshot]) -> Decimal:
    peak: Decimal | None = None
    max_drawdown = ZERO
    for snapshot in snapshots:
        equity = snapshot.total_equity
        if peak is None or equity > peak:
            peak = equity
        if peak is None or peak <= 0:
            continue
        drawdown = (peak - equity) / peak * ONE_HUNDRED
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def _daily_points(
    trades: list[PerformanceTrade],
    snapshots: list[PortfolioSnapshot],
    period_start: datetime | None,
    period_end: datetime,
) -> list[PerformanceDailyPoint]:
    realized_by_day: defaultdict[date, Decimal] = defaultdict(lambda: ZERO)
    for trade in trades:
        realized_by_day[trade.sold_at.date()] += trade.pnl_usdt

    snapshots_by_day: dict[date, Decimal] = {}
    for snapshot in _period_snapshots(snapshots, period_start, period_end):
        snapshots_by_day[snapshot.captured_at.date()] = snapshot.total_equity

    days = sorted(set(realized_by_day) | set(snapshots_by_day))
    return [
        PerformanceDailyPoint(
            date=day,
            realized_pnl=realized_by_day[day],
            equity=snapshots_by_day.get(day),
        )
        for day in days
    ]


def _performance_status(
    sell_count: int, total_pnl: Decimal
) -> Literal["lucrando", "perdendo", "sem_amostra_suficiente", "atencao"]:
    if sell_count == 0:
        return "sem_amostra_suficiente"
    if total_pnl > 0:
        return "lucrando"
    if total_pnl < 0:
        return "perdendo"
    return "atencao"
