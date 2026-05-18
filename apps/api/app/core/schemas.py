from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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


class StrategyConfigCreateRequest(BaseModel):
    version: int = Field(ge=1)
    name: str = "breakout_trend_v1"
    signal_timeframe: str = "1h"
    regime_timeframe_primary: str = "4h"
    regime_timeframe_secondary: str = "1d"
    parameters: dict = Field(default_factory=dict)
    created_by: str | None = "system"


class StrategyConfigResponse(BaseModel):
    id: UUID
    environment: str
    version: int
    name: str
    symbol: str
    signal_timeframe: str
    regime_timeframe_primary: str
    regime_timeframe_secondary: str
    parameters: dict
    is_active: bool
    created_by: str | None
    activated_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StrategyConfigsResponse(BaseModel):
    environment: str
    symbol: str
    configs: list[StrategyConfigResponse]


class RiskConfigCreateRequest(BaseModel):
    version: int = Field(ge=1)
    name: str = "mvp_risk_v1"
    risk_per_trade_pct: Decimal | None = None
    daily_loss_limit_pct: Decimal | None = None
    max_exposure_pct: Decimal | None = None
    parameters: dict = Field(default_factory=dict)
    created_by: str | None = "system"


class RiskConfigResponse(BaseModel):
    id: UUID
    environment: str
    version: int
    name: str
    symbol: str
    risk_per_trade_pct: Decimal | None
    daily_loss_limit_pct: Decimal | None
    max_exposure_pct: Decimal | None
    parameters: dict
    is_active: bool
    created_by: str | None
    activated_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RiskConfigsResponse(BaseModel):
    environment: str
    symbol: str
    configs: list[RiskConfigResponse]


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


ExportFormat = Literal["csv", "txt", "pdf"]
ExportSection = Literal["market", "portfolio", "operations", "decisions"]


class ExportCreateRequest(BaseModel):
    format: ExportFormat
    sections: list[ExportSection] = Field(
        default_factory=lambda: ["market", "portfolio", "operations", "decisions"]
    )
    period_start: datetime | None = None
    period_end: datetime | None = None
    decision: Literal["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"] | None = None
    order_side: Literal["BUY", "SELL"] | None = None
    order_status: (
        Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "EXPIRED"] | None
    ) = None


class ExportJobResponse(BaseModel):
    id: UUID
    environment: str
    symbol: str
    status: Literal["completed"]
    format: ExportFormat
    sections: list[ExportSection]
    content_type: str
    filename: str
    created_at: datetime
    completed_at: datetime
    filters: dict
    content: str


McpScope = Literal[
    "read:market",
    "read:portfolio",
    "read:trades",
    "read:decisions",
    "read:config",
    "read:reports",
]


class McpTokenCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    agent_name: str | None = Field(default=None, max_length=120)
    scopes: list[McpScope] = Field(min_length=1)
    expires_at: datetime | None = None


class McpTokenResponse(BaseModel):
    id: UUID
    environment: str
    name: str
    agent_name: str | None
    scopes: list[McpScope]
    status: str
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class McpTokenCreateResponse(McpTokenResponse):
    token: str


class McpTokensResponse(BaseModel):
    environment: str
    tokens: list[McpTokenResponse]


class McpTokenValidateRequest(BaseModel):
    required_scopes: list[McpScope] = Field(min_length=1)
    resource: str = Field(min_length=1, max_length=120)


class McpTokenValidateResponse(BaseModel):
    token_id: UUID
    environment: str
    agent_name: str | None
    scopes: list[McpScope]


class McpAccessLogCreateRequest(BaseModel):
    token_id: UUID | None = None
    agent_name: str | None = Field(default=None, max_length=120)
    resource: str = Field(min_length=1, max_length=120)
    arguments: dict = Field(default_factory=dict)
    status: Literal["success", "error", "blocked"]
    status_code: int | None = None
    error_message: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)


class McpAccessLogResponse(BaseModel):
    id: UUID
    environment: str
    token_id: UUID | None
    agent_name: str | None
    resource: str
    arguments: dict
    status: str
    status_code: int | None
    error_message: str | None
    latency_ms: int | None
    occurred_at: datetime
    created_at: datetime | None = None


class McpAccessLogsResponse(BaseModel):
    environment: str
    logs: list[McpAccessLogResponse]


class McpStatusResponse(BaseModel):
    environment: str
    auth_enabled: bool
    allowed_scopes: list[McpScope]
    tools: list[str]
