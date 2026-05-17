from __future__ import annotations

import base64
import csv
import io
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.schemas import ExportCreateRequest, ExportJobResponse
from app.db.models import DecisionLog, MarketSnapshot, Order, OrderFill, PortfolioSnapshot
from app.db.session import get_db_session

router = APIRouter(prefix="/exports", tags=["exports"])

_EXPORT_JOBS: dict[uuid.UUID, ExportJobResponse] = {}


class ExportReadStore(Protocol):
    def get_latest_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> MarketSnapshot | None: ...

    def get_latest_portfolio_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> PortfolioSnapshot | None: ...

    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        side: str | None,
        status: str | None,
    ) -> list[Order]: ...

    def list_fills(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> list[OrderFill]: ...

    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        decision: str | None,
    ) -> list[DecisionLog]: ...


class SqlAlchemyExportReadStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> MarketSnapshot | None:
        statement = select(MarketSnapshot).where(
            MarketSnapshot.environment == environment,
            MarketSnapshot.symbol == symbol,
        )
        if period_start is not None:
            statement = statement.where(MarketSnapshot.captured_at >= period_start)
        if period_end is not None:
            statement = statement.where(MarketSnapshot.captured_at <= period_end)
        return self.session.scalars(
            statement.order_by(MarketSnapshot.captured_at.desc()).limit(1)
        ).first()

    def get_latest_portfolio_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> PortfolioSnapshot | None:
        statement = select(PortfolioSnapshot).where(
            PortfolioSnapshot.environment == environment,
            PortfolioSnapshot.symbol == symbol,
        )
        if period_start is not None:
            statement = statement.where(PortfolioSnapshot.captured_at >= period_start)
        if period_end is not None:
            statement = statement.where(PortfolioSnapshot.captured_at <= period_end)
        return self.session.scalars(
            statement.order_by(PortfolioSnapshot.captured_at.desc()).limit(1)
        ).first()

    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        side: str | None,
        status: str | None,
    ) -> list[Order]:
        statement = select(Order).where(Order.environment == environment, Order.symbol == symbol)
        if period_start is not None:
            statement = statement.where(Order.created_at >= period_start)
        if period_end is not None:
            statement = statement.where(Order.created_at <= period_end)
        if side is not None:
            statement = statement.where(Order.side == side)
        if status is not None:
            statement = statement.where(Order.status == status)
        return list(
            self.session.scalars(
                statement.order_by(Order.created_at.desc(), Order.id.desc()).limit(500)
            )
        )

    def list_fills(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> list[OrderFill]:
        statement = (
            select(OrderFill)
            .join(Order)
            .options(selectinload(OrderFill.order))
            .where(OrderFill.environment == environment, Order.symbol == symbol)
        )
        if period_start is not None:
            statement = statement.where(OrderFill.filled_at >= period_start)
        if period_end is not None:
            statement = statement.where(OrderFill.filled_at <= period_end)
        return list(
            self.session.scalars(
                statement.order_by(OrderFill.filled_at.desc(), OrderFill.id.desc()).limit(500)
            )
        )

    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        decision: str | None,
    ) -> list[DecisionLog]:
        statement = select(DecisionLog).where(
            DecisionLog.environment == environment,
            DecisionLog.symbol == symbol,
        )
        if period_start is not None:
            statement = statement.where(DecisionLog.decided_at >= period_start)
        if period_end is not None:
            statement = statement.where(DecisionLog.decided_at <= period_end)
        if decision is not None:
            statement = statement.where(DecisionLog.decision == decision)
        return list(
            self.session.scalars(
                statement.order_by(DecisionLog.decided_at.desc(), DecisionLog.id.desc()).limit(500)
            )
        )


def _store(session: Session) -> ExportReadStore:
    return SqlAlchemyExportReadStore(session)


def _environment() -> str:
    return get_settings().aurum_environment


def _symbol() -> str:
    return get_settings().trading_symbol


@router.post("", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
def create_export(
    request: ExportCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ExportJobResponse:
    job = generate_export(_store(session), request, environment=_environment(), symbol=_symbol())
    _EXPORT_JOBS[job.id] = job
    return job


@router.get("/{export_id}", response_model=ExportJobResponse)
def get_export(export_id: uuid.UUID) -> ExportJobResponse:
    job = _EXPORT_JOBS.get(export_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="export not found")
    return job


def generate_export(
    store: ExportReadStore,
    request: ExportCreateRequest,
    *,
    environment: str,
    symbol: str,
    now: datetime | None = None,
) -> ExportJobResponse:
    created_at = now or datetime.now(UTC)
    dataset = _load_dataset(store, request, environment=environment, symbol=symbol)
    filters = request.model_dump(mode="json", exclude={"format"})
    content = _render_content(request.format, dataset, environment=environment, symbol=symbol)
    content_type = _content_type(request.format)
    filename = f"aurum-{symbol.lower()}-{created_at.strftime('%Y%m%d%H%M%S')}.{request.format}"
    return ExportJobResponse(
        id=uuid.uuid4(),
        environment=environment,
        symbol=symbol,
        status="completed",
        format=request.format,
        sections=request.sections,
        content_type=content_type,
        filename=filename,
        created_at=created_at,
        completed_at=created_at,
        filters=filters,
        content=content,
    )


def _load_dataset(
    store: ExportReadStore, request: ExportCreateRequest, *, environment: str, symbol: str
) -> dict[str, object]:
    dataset: dict[str, object] = {}
    if "market" in request.sections:
        dataset["market"] = store.get_latest_market_snapshot(
            environment=environment,
            symbol=symbol,
            period_start=request.period_start,
            period_end=request.period_end,
        )
    if "portfolio" in request.sections:
        dataset["portfolio"] = store.get_latest_portfolio_snapshot(
            environment=environment,
            symbol=symbol,
            period_start=request.period_start,
            period_end=request.period_end,
        )
    if "operations" in request.sections:
        dataset["orders"] = store.list_orders(
            environment=environment,
            symbol=symbol,
            period_start=request.period_start,
            period_end=request.period_end,
            side=request.order_side,
            status=request.order_status,
        )
        dataset["fills"] = store.list_fills(
            environment=environment,
            symbol=symbol,
            period_start=request.period_start,
            period_end=request.period_end,
        )
    if "decisions" in request.sections:
        dataset["decisions"] = store.list_decisions(
            environment=environment,
            symbol=symbol,
            period_start=request.period_start,
            period_end=request.period_end,
            decision=request.decision,
        )
    return dataset


def _render_content(
    format_: str, dataset: dict[str, object], *, environment: str, symbol: str
) -> str:
    if format_ == "csv":
        return _render_csv(dataset)
    text = _render_text(dataset, environment=environment, symbol=symbol)
    if format_ == "pdf":
        return base64.b64encode(text.encode("utf-8")).decode("ascii")
    return text


def _render_csv(dataset: dict[str, object]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "field", "value"])
    market = dataset.get("market")
    if market is not None:
        _write_fields(
            writer,
            "market",
            market,
            ["captured_at", "last_price", "trend_1h", "trend_4h", "trend_1d"],
        )
    portfolio = dataset.get("portfolio")
    if portfolio is not None:
        _write_fields(
            writer,
            "portfolio",
            portfolio,
            [
                "captured_at",
                "usdt_balance",
                "btc_balance",
                "total_equity",
                "realized_pnl",
                "unrealized_pnl",
            ],
        )
    for order in dataset.get("orders", []):
        writer.writerow(["order", "id", getattr(order, "id", "")])
        _write_fields(
            writer,
            "order",
            order,
            ["side", "status", "requested_quantity", "executed_quantity", "average_price"],
        )
    for fill in dataset.get("fills", []):
        writer.writerow(["fill", "id", getattr(fill, "id", "")])
        _write_fields(
            writer, "fill", fill, ["filled_at", "price", "quantity", "fee_amount", "fee_asset"]
        )
    for decision in dataset.get("decisions", []):
        writer.writerow(["decision", "id", getattr(decision, "id", "")])
        _write_fields(writer, "decision", decision, ["decided_at", "decision", "reason"])
    return output.getvalue()


def _render_text(dataset: dict[str, object], *, environment: str, symbol: str) -> str:
    lines = ["Aurum export report", f"Environment: {environment}", f"Symbol: {symbol}", ""]
    market = dataset.get("market")
    lines.append("Market")
    if market is None:
        lines.append("- No market snapshot in selected scope.")
    else:
        lines.append(f"- Last price: {_value(getattr(market, 'last_price', None))}")
        lines.append(f"- Captured at: {_value(getattr(market, 'captured_at', None))}")
    portfolio = dataset.get("portfolio")
    lines.append("")
    lines.append("Portfolio")
    if portfolio is None:
        lines.append("- No portfolio snapshot in selected scope.")
    else:
        lines.append(f"- Total equity: {_value(getattr(portfolio, 'total_equity', None))}")
        lines.append(f"- BTC balance: {_value(getattr(portfolio, 'btc_balance', None))}")
        lines.append(f"- Unrealized PnL: {_value(getattr(portfolio, 'unrealized_pnl', None))}")
    lines.append("")
    lines.append(f"Orders: {len(dataset.get('orders', []))}")
    lines.append(f"Fills: {len(dataset.get('fills', []))}")
    decisions = dataset.get("decisions", [])
    lines.append(f"Decisions: {len(decisions)}")
    for decision in decisions[:20]:
        lines.append(
            f"- {_value(getattr(decision, 'decided_at', None))} "
            f"{_value(getattr(decision, 'decision', None))}: "
            f"{_value(getattr(decision, 'reason', None))}"
        )
    return "\n".join(lines) + "\n"


def _write_fields(writer: csv.writer, section: str, row: object, fields: list[str]) -> None:
    for field in fields:
        writer.writerow([section, field, _value(getattr(row, field, None))])


def _value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _content_type(format_: str) -> str:
    if format_ == "csv":
        return "text/csv"
    if format_ == "pdf":
        return "application/pdf"
    return "text/plain"
