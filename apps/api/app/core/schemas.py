from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str


class BotStatusResponse(BaseModel):
    environment: str
    symbol: str
    status: str
    trading_mode: str
    last_cycle_at: datetime | None
    paused_at: datetime | None
    emergency_stopped_at: datetime | None
    reason: str | None


class BotCommandRequest(BaseModel):
    reason: str | None = None


class MarketSnapshotSummary(BaseModel):
    id: UUID
    captured_at: datetime
    last_price: Decimal
    price_change_pct_24h: Decimal | None
    high_price_24h: Decimal | None
    low_price_24h: Decimal | None
    volume_24h: Decimal | None
    spread_bps: Decimal | None
    volatility_pct: Decimal | None
    trend_1h: str | None
    trend_4h: str | None
    trend_1d: str | None
    indicators: dict
    source_payload: dict


class MarketSummaryResponse(BaseModel):
    environment: str
    symbol: str
    snapshot: MarketSnapshotSummary | None


class MarketCandleResponse(BaseModel):
    id: UUID
    environment: str
    exchange: str
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    quote_volume: Decimal | None
    trade_count: int | None


class MarketCandlesResponse(BaseModel):
    environment: str
    symbol: str
    interval: str
    candles: list[MarketCandleResponse]


class PortfolioSnapshotResponse(BaseModel):
    id: UUID
    captured_at: datetime
    usdt_balance: Decimal
    btc_balance: Decimal
    btc_market_price: Decimal
    btc_market_value: Decimal
    invested_value: Decimal
    average_cost: Decimal
    total_equity: Decimal
    exposure_pct: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_fees_usdt: Decimal
    source_payload: dict


class PositionResponse(BaseModel):
    id: UUID
    asset: str
    side: str
    quantity: Decimal
    average_cost: Decimal
    remaining_cost: Decimal
    realized_pnl: Decimal
    total_fees_usdt: Decimal
    last_reconciled_at: datetime | None


class PortfolioStatusResponse(BaseModel):
    environment: str
    symbol: str
    snapshot: PortfolioSnapshotResponse | None
    position: PositionResponse | None


class OrderResponse(BaseModel):
    id: UUID
    environment: str
    exchange: str
    symbol: str
    decision_id: UUID | None
    bot_run_id: UUID | None
    external_order_id: str | None
    client_order_id: str | None
    side: str
    order_type: str
    status: str
    position_side: str
    requested_quantity: Decimal
    executed_quantity: Decimal
    quote_quantity: Decimal | None
    limit_price: Decimal | None
    average_price: Decimal | None
    submitted_at: datetime | None
    closed_at: datetime | None
    raw_payload: dict


class OrdersResponse(BaseModel):
    environment: str
    symbol: str
    orders: list[OrderResponse]


class OrderFillResponse(BaseModel):
    id: UUID
    environment: str
    exchange: str
    order_id: UUID
    order_decision_id: UUID | None
    order_bot_run_id: UUID | None
    external_trade_id: str | None
    filled_at: datetime
    price: Decimal
    quantity: Decimal
    quote_quantity: Decimal
    fee_amount: Decimal | None
    fee_asset: str | None
    fee_estimated_usdt: Decimal | None
    raw_payload: dict


class OrderFillsResponse(BaseModel):
    environment: str
    symbol: str
    fills: list[OrderFillResponse]


class DecisionLogResponse(BaseModel):
    id: UUID
    environment: str
    symbol: str
    bot_run_id: UUID | None
    strategy_config_id: UUID | None
    risk_config_id: UUID | None
    market_snapshot_id: UUID | None
    decided_at: datetime
    decision: str
    reason: str
    reason_payload: dict
    indicators: dict
    intended_order: dict
    execution_result: dict
    portfolio_state: dict


class DecisionsResponse(BaseModel):
    environment: str
    symbol: str
    decisions: list[DecisionLogResponse]
