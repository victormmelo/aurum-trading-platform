from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backtest.service import execute_backtest
from app.backtest.store import SqlAlchemyBacktestStore
from app.core.config import get_settings
from app.core.schemas import (
    BacktestCompareItemResponse,
    BacktestCompareResponse,
    BacktestEquityPointResponse,
    BacktestMetricsResponse,
    BacktestRunDetailResponse,
    BacktestRunRequest,
    BacktestRunsListResponse,
    BacktestRunSummaryResponse,
    BacktestTradeResponse,
    BacktestTradesPageResponse,
)
from app.db.models import (
    BacktestEquityPoint,
    BacktestMetrics,
    BacktestRun,
    BacktestTrade,
)
from app.db.session import get_db_session

router = APIRouter(prefix="/backtest", tags=["backtest"])


def _store(session: Session) -> SqlAlchemyBacktestStore:
    return SqlAlchemyBacktestStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


def _metrics_response(m: BacktestMetrics | None) -> BacktestMetricsResponse | None:
    if m is None:
        return None
    return BacktestMetricsResponse(
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


def _trade_response(t: BacktestTrade) -> BacktestTradeResponse:
    return BacktestTradeResponse(
        id=t.id,
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


def _equity_point_response(ep: BacktestEquityPoint) -> BacktestEquityPointResponse:
    return BacktestEquityPointResponse(
        timestamp=ep.timestamp,
        equity=ep.equity,
        btc_price=ep.btc_price,
        is_in_position=ep.is_in_position,
    )


def _run_summary(run: BacktestRun) -> BacktestRunSummaryResponse:
    return BacktestRunSummaryResponse(
        id=run.id,
        name=run.name,
        environment=run.environment,
        symbol=run.symbol,
        signal_interval=run.signal_interval,
        start_date=run.start_date,
        end_date=run.end_date,
        initial_capital=run.initial_capital,
        fee_rate=run.fee_rate,
        strategy_params=run.strategy_params,
        status=run.status,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
        metrics=_metrics_response(run.metrics),
    )


@router.post("/run", status_code=202)
def create_backtest_run(
    body: BacktestRunRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_db_session)],
) -> BacktestRunSummaryResponse:
    if body.start_date >= body.end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    run = BacktestRun(
        name=body.name,
        environment=_environment(),
        symbol=_symbol(),
        signal_interval=body.signal_interval,
        start_date=body.start_date,
        end_date=body.end_date,
        initial_capital=body.initial_capital,
        fee_rate=body.fee_rate,
        strategy_params={},
        status="pending",
    )
    store = _store(session)
    store.create_run(run)
    session.commit()

    run_id = run.id
    background_tasks.add_task(_run_in_background, run_id)

    return _run_summary(run)


def _run_in_background(run_id: uuid.UUID) -> None:
    from app.db.session import build_session_factory

    factory = build_session_factory()
    with factory() as session:
        execute_backtest(run_id, session)


@router.get("/", response_model=BacktestRunsListResponse)
def list_backtest_runs(
    session: Annotated[Session, Depends(get_db_session)],
) -> BacktestRunsListResponse:
    store = _store(session)
    runs = store.list_runs(environment=_environment())
    return BacktestRunsListResponse(runs=[_run_summary(r) for r in runs])


@router.get("/compare", response_model=BacktestCompareResponse)
def compare_backtest_runs(
    session: Annotated[Session, Depends(get_db_session)],
    ids: Annotated[str, Query(description="Comma-separated run UUIDs")] = "",
) -> BacktestCompareResponse:
    if not ids.strip():
        return BacktestCompareResponse(runs=[])

    try:
        parsed_ids = [uuid.UUID(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID in ids parameter") from None

    store = _store(session)
    runs = store.get_runs_by_ids(parsed_ids)

    items: list[BacktestCompareItemResponse] = []
    for run in runs:
        points = store.get_equity_points(run.id, max_points=500)
        items.append(
            BacktestCompareItemResponse(
                id=run.id,
                name=run.name,
                metrics=_metrics_response(run.metrics),
                equity_points=[_equity_point_response(ep) for ep in points],
            )
        )

    return BacktestCompareResponse(runs=items)


@router.get("/{run_id}", response_model=BacktestRunDetailResponse)
def get_backtest_run(
    run_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> BacktestRunDetailResponse:
    store = _store(session)
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    equity_points = store.get_equity_points(run_id, max_points=1000)
    trades, total = store.get_trades(run_id, offset=(page - 1) * 50, limit=50)

    return BacktestRunDetailResponse(
        id=run.id,
        name=run.name,
        environment=run.environment,
        symbol=run.symbol,
        signal_interval=run.signal_interval,
        start_date=run.start_date,
        end_date=run.end_date,
        initial_capital=run.initial_capital,
        fee_rate=run.fee_rate,
        strategy_params=run.strategy_params,
        status=run.status,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
        metrics=_metrics_response(run.metrics),
        equity_points=[_equity_point_response(ep) for ep in equity_points],
        trades=[_trade_response(t) for t in trades],
        trades_total=total,
    )


@router.get("/{run_id}/trades", response_model=BacktestTradesPageResponse)
def list_backtest_trades(
    run_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    filter: Annotated[Literal["all", "winner", "loser"], Query()] = "all",
) -> BacktestTradesPageResponse:
    store = _store(session)
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    filter_winner: bool | None = None
    if filter == "winner":
        filter_winner = True
    elif filter == "loser":
        filter_winner = False

    offset = (page - 1) * page_size
    trades, total = store.get_trades(
        run_id, filter_winner=filter_winner, offset=offset, limit=page_size
    )

    return BacktestTradesPageResponse(
        run_id=run_id,
        trades=[_trade_response(t) for t in trades],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}/export")
def export_backtest_run(
    run_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    format: Annotated[Literal["json", "csv"], Query()] = "json",
) -> StreamingResponse:
    store = _store(session)
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    trades, _ = store.get_trades(run_id, limit=10000)
    equity_points = store.get_equity_points(run_id, max_points=10000)
    metrics = run.metrics

    safe_name = run.name.replace(" ", "_").lower()[:40]

    if format == "json":
        payload = {
            "_schema_version": "1.0",
            "_description": "Aurum backtest export — compatible with AI agent analysis",
            "run": {
                "id": str(run.id),
                "name": run.name,
                "symbol": run.symbol,
                "signal_interval": run.signal_interval,
                "start_date": run.start_date.isoformat(),
                "end_date": run.end_date.isoformat(),
                "initial_capital_usdt": float(run.initial_capital),
                "fee_rate": float(run.fee_rate),
                "strategy_params": run.strategy_params,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            },
            "metrics": {
                "total_return_pct": float(metrics.total_return_pct) if metrics else None,
                "total_return_usdt": float(metrics.total_return_usd) if metrics else None,
                "final_capital_usdt": float(metrics.final_capital) if metrics else None,
                "max_drawdown_pct": float(metrics.max_drawdown_pct) if metrics else None,
                "win_rate_pct": float(metrics.win_rate_pct) if metrics else None,
                "profit_factor": (
                    float(metrics.profit_factor)
                    if metrics and metrics.profit_factor
                    else None
                ),
                "total_trades": metrics.total_trades if metrics else 0,
                "winning_trades": metrics.winning_trades if metrics else 0,
                "losing_trades": metrics.losing_trades if metrics else 0,
                "sharpe_ratio": (
                    float(metrics.sharpe_ratio)
                    if metrics and metrics.sharpe_ratio
                    else None
                ),
                "avg_trade_duration_hours": (
                    float(metrics.avg_trade_duration_hours)
                    if metrics and metrics.avg_trade_duration_hours
                    else None
                ),
                "btc_buy_hold_return_pct": (
                    float(metrics.btc_buy_hold_return_pct)
                    if metrics and metrics.btc_buy_hold_return_pct
                    else None
                ),
            },
            "equity_curve": [
                {
                    "timestamp": ep.timestamp.isoformat(),
                    "equity_usdt": float(ep.equity),
                    "btc_price_usdt": float(ep.btc_price) if ep.btc_price else None,
                    "in_position": ep.is_in_position,
                }
                for ep in equity_points
            ],
            "trades": [
                {
                    "trade_index": t.trade_index,
                    "entry_time": t.entry_time.isoformat(),
                    "exit_time": t.exit_time.isoformat(),
                    "entry_price_usdt": float(t.entry_price),
                    "exit_price_usdt": float(t.exit_price),
                    "quantity_btc": float(t.quantity),
                    "entry_value_usdt": float(t.entry_value),
                    "exit_value_usdt": float(t.exit_value),
                    "fees_paid_usdt": float(t.fees_paid),
                    "pnl_usdt": float(t.pnl_usd),
                    "return_pct": float(t.return_pct),
                    "exit_reason": t.exit_reason,
                    "is_winner": t.is_winner,
                    "portfolio_equity_after_usdt": float(t.equity_after),
                }
                for t in trades
            ],
        }
        content = json.dumps(payload, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="backtest_{safe_name}.json"'},
        )

    # CSV export
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["# AURUM BACKTEST EXPORT"])
    writer.writerow(["# Run", run.name])
    writer.writerow(["# Period", f"{run.start_date.date()} to {run.end_date.date()}"])
    writer.writerow(["# Initial Capital (USDT)", float(run.initial_capital)])
    writer.writerow(["# Fee Rate", float(run.fee_rate)])
    if metrics:
        writer.writerow(["# Total Return %", float(metrics.total_return_pct)])
        writer.writerow(["# Max Drawdown %", float(metrics.max_drawdown_pct)])
        writer.writerow(["# Win Rate %", float(metrics.win_rate_pct)])
        writer.writerow(["# Total Trades", metrics.total_trades])
        sharpe_val = float(metrics.sharpe_ratio) if metrics.sharpe_ratio else "N/A"
        writer.writerow(["# Sharpe Ratio", sharpe_val])
    writer.writerow([])

    writer.writerow([
        "trade_index", "entry_time", "exit_time", "entry_price_usdt", "exit_price_usdt",
        "quantity_btc", "entry_value_usdt", "exit_value_usdt", "fees_paid_usdt",
        "pnl_usdt", "return_pct", "exit_reason", "is_winner", "equity_after_usdt",
    ])
    for t in trades:
        writer.writerow([
            t.trade_index,
            t.entry_time.isoformat(),
            t.exit_time.isoformat(),
            float(t.entry_price),
            float(t.exit_price),
            float(t.quantity),
            float(t.entry_value),
            float(t.exit_value),
            float(t.fees_paid),
            float(t.pnl_usd),
            float(t.return_pct),
            t.exit_reason,
            t.is_winner,
            float(t.equity_after),
        ])

    content_csv = output.getvalue()
    return StreamingResponse(
        iter([content_csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="backtest_{safe_name}.csv"'},
    )


@router.delete("/{run_id}", status_code=204)
def delete_backtest_run(
    run_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> None:
    store = _store(session)
    deleted = store.delete_run(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    session.commit()
