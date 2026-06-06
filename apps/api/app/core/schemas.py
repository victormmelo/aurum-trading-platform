from datetime import date, datetime
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


class PerformanceDailyPointResponse(BaseModel):
    date: date
    realized_pnl: Decimal
    equity: Decimal | None


class PerformanceSummaryResponse(BaseModel):
    environment: str
    symbol: str
    period: Literal["7d", "30d", "90d", "mtd", "ytd", "all"]
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
    daily: list[PerformanceDailyPointResponse]


class PerformanceTradeResponse(BaseModel):
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


class PerformanceTradesResponse(BaseModel):
    environment: str
    symbol: str
    period: Literal["7d", "30d", "90d", "mtd", "ytd", "all"]
    trades: list[PerformanceTradeResponse]


class ManualOrderRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    quantity: Decimal | None = Field(default=None, gt=0)
    quote_quantity: Decimal | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, max_length=500)
    actor_id: str | None = Field(default="manual", max_length=120)


class OrderActionResponse(BaseModel):
    environment: str
    symbol: str
    order: OrderResponse


class OrderReconciliationResponse(BaseModel):
    environment: str
    symbol: str
    reconciled_orders: list[OrderResponse]


class PortfolioReconciliationResponse(BaseModel):
    environment: str
    symbol: str
    snapshot: PortfolioSnapshotResponse
    position: PositionResponse


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


# --- Backtest schemas ---


class BacktestRunRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Field(gt=0)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=1)
    signal_interval: str = Field(default="1h")


class BacktestMetricsResponse(BaseModel):
    total_return_pct: Decimal
    total_return_usd: Decimal
    final_capital: Decimal
    max_drawdown_pct: Decimal
    win_rate_pct: Decimal
    profit_factor: Decimal | None
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win_pct: Decimal | None
    avg_loss_pct: Decimal | None
    sharpe_ratio: Decimal | None
    largest_win_pct: Decimal | None
    largest_loss_pct: Decimal | None
    avg_trade_duration_hours: Decimal | None
    btc_buy_hold_return_pct: Decimal | None


class BacktestTradeResponse(BaseModel):
    id: UUID
    trade_index: int
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    entry_value: Decimal
    exit_value: Decimal
    fees_paid: Decimal
    pnl_usd: Decimal
    return_pct: Decimal
    exit_reason: str
    is_winner: bool
    equity_after: Decimal


class BacktestEquityPointResponse(BaseModel):
    timestamp: datetime
    equity: Decimal
    btc_price: Decimal | None
    is_in_position: bool


class BacktestRunSummaryResponse(BaseModel):
    id: UUID
    name: str
    environment: str
    symbol: str
    signal_interval: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    fee_rate: Decimal
    strategy_params: dict
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    metrics: BacktestMetricsResponse | None


class BacktestRunDetailResponse(BaseModel):
    id: UUID
    name: str
    environment: str
    symbol: str
    signal_interval: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    fee_rate: Decimal
    strategy_params: dict
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    metrics: BacktestMetricsResponse | None
    equity_points: list[BacktestEquityPointResponse]
    trades: list[BacktestTradeResponse]
    trades_total: int


class BacktestRunsListResponse(BaseModel):
    runs: list[BacktestRunSummaryResponse]


class BacktestTradesPageResponse(BaseModel):
    run_id: UUID
    trades: list[BacktestTradeResponse]
    total: int
    page: int
    page_size: int


class BacktestCompareItemResponse(BaseModel):
    id: UUID
    name: str
    metrics: BacktestMetricsResponse | None
    equity_points: list[BacktestEquityPointResponse]


class BacktestCompareResponse(BaseModel):
    runs: list[BacktestCompareItemResponse]
