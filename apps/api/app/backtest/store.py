from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    BacktestEquityPoint,
    BacktestMetrics,
    BacktestRun,
    BacktestTrade,
)


class BacktestStore(Protocol):
    def create_run(self, run: BacktestRun) -> None: ...
    def update_run_status(
        self,
        run_id: uuid.UUID,
        *,
        status: str,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> None: ...
    def save_trades(self, trades: list[BacktestTrade]) -> None: ...
    def save_equity_points(self, points: list[BacktestEquityPoint]) -> None: ...
    def save_metrics(self, metrics: BacktestMetrics) -> None: ...
    def get_run(self, run_id: uuid.UUID) -> BacktestRun | None: ...
    def list_runs(self, *, environment: str) -> list[BacktestRun]: ...
    def delete_run(self, run_id: uuid.UUID) -> bool: ...
    def get_trades(
        self,
        run_id: uuid.UUID,
        *,
        filter_winner: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[BacktestTrade], int]: ...
    def get_equity_points(
        self, run_id: uuid.UUID, *, max_points: int = 1000
    ) -> list[BacktestEquityPoint]: ...
    def get_runs_by_ids(self, ids: list[uuid.UUID]) -> list[BacktestRun]: ...


class SqlAlchemyBacktestStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, run: BacktestRun) -> None:
        self.session.add(run)
        self.session.flush()

    def update_run_status(
        self,
        run_id: uuid.UUID,
        *,
        status: str,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        run = self.session.get(BacktestRun, run_id)
        if run is None:
            return
        run.status = status
        if error_message is not None:
            run.error_message = error_message
        if completed_at is not None:
            run.completed_at = completed_at
        self.session.flush()

    def save_trades(self, trades: list[BacktestTrade]) -> None:
        for trade in trades:
            self.session.add(trade)
        self.session.flush()

    def save_equity_points(self, points: list[BacktestEquityPoint]) -> None:
        for point in points:
            self.session.add(point)
        self.session.flush()

    def save_metrics(self, metrics: BacktestMetrics) -> None:
        self.session.add(metrics)
        self.session.flush()

    def get_run(self, run_id: uuid.UUID) -> BacktestRun | None:
        return self.session.get(BacktestRun, run_id)

    def list_runs(self, *, environment: str) -> list[BacktestRun]:
        stmt = (
            select(BacktestRun)
            .where(BacktestRun.environment == environment)
            .order_by(BacktestRun.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def delete_run(self, run_id: uuid.UUID) -> bool:
        run = self.session.get(BacktestRun, run_id)
        if run is None:
            return False
        self.session.delete(run)
        self.session.flush()
        return True

    def get_trades(
        self,
        run_id: uuid.UUID,
        *,
        filter_winner: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[BacktestTrade], int]:
        base = select(BacktestTrade).where(BacktestTrade.backtest_run_id == run_id)
        if filter_winner is not None:
            base = base.where(BacktestTrade.is_winner == filter_winner)

        total_result = self.session.execute(
            base.with_only_columns(BacktestTrade.id)
        )
        total = len(list(total_result))

        stmt = base.order_by(BacktestTrade.trade_index.asc()).offset(offset).limit(limit)
        trades = list(self.session.scalars(stmt))
        return trades, total

    def get_equity_points(
        self, run_id: uuid.UUID, *, max_points: int = 1000
    ) -> list[BacktestEquityPoint]:
        stmt = (
            select(BacktestEquityPoint)
            .where(BacktestEquityPoint.backtest_run_id == run_id)
            .order_by(BacktestEquityPoint.timestamp.asc())
        )
        all_points = list(self.session.scalars(stmt))

        if len(all_points) <= max_points:
            return all_points

        # Downsample: pick evenly spaced indices
        step = len(all_points) / max_points
        indices = {int(i * step) for i in range(max_points)}
        indices.add(len(all_points) - 1)
        return [all_points[i] for i in sorted(indices)]

    def get_runs_by_ids(self, ids: list[uuid.UUID]) -> list[BacktestRun]:
        stmt = select(BacktestRun).where(BacktestRun.id.in_(ids))
        return list(self.session.scalars(stmt))
