from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtest.store import SqlAlchemyBacktestStore
from app.db.models import (
    BacktestEquityPoint as BacktestEquityPointORM,
)
from app.db.models import (
    BacktestMetrics as BacktestMetricsORM,
)
from app.db.models import (
    BacktestRun,
    MarketCandle,
)
from app.db.models import (
    BacktestTrade as BacktestTradeORM,
)
from app.market.binance import BinanceMarketClient
from app.market.importer import import_historical_candles
from app.strategy.backtest import run_multi_trade_backtest
from app.strategy.types import StrategyCandle


def execute_backtest(run_id: uuid.UUID, session: Session) -> None:
    """Background task: backfill candles, run engine, persist results."""
    store = SqlAlchemyBacktestStore(session)
    run = store.get_run(run_id)
    if run is None:
        return

    store.update_run_status(run_id, status="running")

    try:
        _backfill_candles(session, run)

        signal_candles = _load_candles(session, run, interval=run.signal_interval)
        # Regime uses daily candles: SMA-50/200 then represent 50 and 200 real days.
        # Mixing 4h+1d in one list makes SMA periods meaningless (~28 days instead of 200).
        regime_candles = _load_candles(session, run, interval="1d")

        result = run_multi_trade_backtest(
            signal_candles,
            regime_candles,
            initial_cash=run.initial_capital,
            fee_rate=run.fee_rate,
        )

        orm_trades = [
            BacktestTradeORM(
                backtest_run_id=run_id,
                trade_index=t.trade_index,
                entry_time=t.entry_time,
                exit_time=t.exit_time,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                entry_value=t.entry_value,
                exit_value=t.exit_value,
                fees_paid=t.fees_paid,
                pnl_usd=t.pnl_usd,
                return_pct=t.return_pct,
                exit_reason=t.exit_reason,
                is_winner=t.is_winner,
                equity_after=t.equity_after,
            )
            for t in result.trades
        ]
        store.save_trades(orm_trades)

        orm_points = [
            BacktestEquityPointORM(
                backtest_run_id=run_id,
                timestamp=ep.timestamp,
                equity=ep.equity,
                btc_price=ep.btc_price,
                is_in_position=ep.is_in_position,
            )
            for ep in result.equity_points
        ]
        store.save_equity_points(orm_points)

        m = result.metrics
        orm_metrics = BacktestMetricsORM(
            backtest_run_id=run_id,
            total_return_pct=m.total_return_pct,
            total_return_usd=m.total_return_usd,
            final_capital=m.final_capital,
            max_drawdown_pct=m.max_drawdown_pct,
            win_rate_pct=m.win_rate_pct,
            profit_factor=m.profit_factor,
            total_trades=m.total_trades,
            winning_trades=m.winning_trades,
            losing_trades=m.losing_trades,
            avg_win_pct=m.avg_win_pct,
            avg_loss_pct=m.avg_loss_pct,
            sharpe_ratio=m.sharpe_ratio,
            largest_win_pct=m.largest_win_pct,
            largest_loss_pct=m.largest_loss_pct,
            avg_trade_duration_hours=m.avg_trade_duration_hours,
            btc_buy_hold_return_pct=m.btc_buy_hold_return_pct,
        )
        store.save_metrics(orm_metrics)

        store.update_run_status(
            run_id,
            status="completed",
            completed_at=datetime.now(UTC),
        )
        session.commit()

    except Exception as exc:
        session.rollback()
        try:
            store.update_run_status(
                run_id,
                status="failed",
                error_message=str(exc)[:1000],
                completed_at=datetime.now(UTC),
            )
            session.commit()
        except Exception:
            pass


_BINANCE_PUBLIC_BASE_URL = "https://api.binance.com/api/v3"


def _backfill_candles(session: Session, run: BacktestRun) -> None:
    # Always use the public Binance API for market data — Testnet has no historical candles
    client = BinanceMarketClient(_BINANCE_PUBLIC_BASE_URL)
    intervals = _required_intervals(run.signal_interval)
    signal_interval = intervals[0]

    # Advance current based on last_close_time returned by Binance, NOT by querying the DB.
    # Querying the DB would pick up pre-existing worker candles (Testnet, recent dates) and
    # cause the loop to exit after just one iteration, leaving historical data unloaded.
    current = run.start_date
    while current < run.end_date:
        results = import_historical_candles(
            session,
            client,
            environment=run.environment,
            symbol=run.symbol,
            intervals=intervals,
            limit=1000,
            start_time=current,
            end_time=run.end_date,
        )
        signal_result = next((r for r in results if r.interval == signal_interval), None)
        last_close = signal_result.last_close_time if signal_result else None
        if not signal_result or not signal_result.fetched or last_close is None:
            break
        if last_close <= current:
            break
        current = last_close


def _load_candles(session: Session, run: BacktestRun, interval: str) -> list[StrategyCandle]:
    stmt = (
        select(MarketCandle)
        .where(
            MarketCandle.environment == run.environment,
            MarketCandle.symbol == run.symbol,
            MarketCandle.interval == interval,
            MarketCandle.open_time >= run.start_date,
            MarketCandle.close_time <= run.end_date,
        )
        .order_by(MarketCandle.open_time.asc())
    )
    rows = list(session.scalars(stmt))
    return [
        StrategyCandle(
            open_time=row.open_time,
            close_time=row.close_time,
            open_price=row.open_price,
            high_price=row.high_price,
            low_price=row.low_price,
            close_price=row.close_price,
            volume=row.volume,
        )
        for row in rows
    ]


def _required_intervals(signal_interval: str) -> list[str]:
    base = [signal_interval]
    if "1d" not in base:
        base.append("1d")
    return base
