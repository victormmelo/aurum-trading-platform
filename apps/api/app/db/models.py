from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

UUID_PK = UUID(as_uuid=True)
MONEY = Numeric(precision=28, scale=10)
PERCENT = Numeric(precision=12, scale=6)
PRICE = Numeric(precision=28, scale=10)
QUANTITY = Numeric(precision=28, scale=12)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BotRuntimeState(TimestampMixin, Base):
    __tablename__ = "bot_runtime_state"
    __table_args__ = (
        CheckConstraint(
            "status in ('running', 'paused', 'emergency_stop')",
            name="bot_runtime_state_status",
        ),
        CheckConstraint(
            "trading_mode in ('paper', 'testnet', 'mainnet')",
            name="bot_runtime_state_trading_mode",
        ),
        UniqueConstraint("environment", name="uq_bot_runtime_state_environment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    trading_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="paused")
    last_cycle_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    emergency_stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pause_reason: Mapped[str | None] = mapped_column(Text)
    state_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class StrategyConfig(TimestampMixin, Base):
    __tablename__ = "strategy_configs"
    __table_args__ = (
        UniqueConstraint("environment", "version", name="uq_strategy_configs_environment_version"),
        Index(
            "ix_strategy_configs_one_active_per_environment",
            "environment",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="breakout_trend_v1")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    signal_timeframe: Mapped[str] = mapped_column(String(12), nullable=False, default="1h")
    regime_timeframe_primary: Mapped[str] = mapped_column(String(12), nullable=False, default="4h")
    regime_timeframe_secondary: Mapped[str] = mapped_column(
        String(12), nullable=False, default="1d"
    )
    parameters: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str | None] = mapped_column(String(120))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RiskConfig(TimestampMixin, Base):
    __tablename__ = "risk_configs"
    __table_args__ = (
        UniqueConstraint("environment", "version", name="uq_risk_configs_environment_version"),
        Index(
            "ix_risk_configs_one_active_per_environment",
            "environment",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="mvp_risk_v1")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    risk_per_trade_pct: Mapped[Decimal | None] = mapped_column(PERCENT)
    daily_loss_limit_pct: Mapped[Decimal | None] = mapped_column(PERCENT)
    max_exposure_pct: Mapped[Decimal | None] = mapped_column(PERCENT)
    parameters: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str | None] = mapped_column(String(120))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MarketCandle(Base):
    __tablename__ = "market_candles"
    __table_args__ = (
        UniqueConstraint(
            "exchange", "symbol", "interval", "open_time", name="uq_market_candles_source_window"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    exchange: Mapped[str] = mapped_column(String(32), nullable=False, default="binance")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    interval: Mapped[str] = mapped_column(String(12), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    high_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    low_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    close_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    volume: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    quote_volume: Mapped[Decimal | None] = mapped_column(MONEY)
    trade_count: Mapped[int | None] = mapped_column(Integer)
    source_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    exchange: Mapped[str] = mapped_column(String(32), nullable=False, default="binance")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    price_change_pct_24h: Mapped[Decimal | None] = mapped_column(PERCENT)
    high_price_24h: Mapped[Decimal | None] = mapped_column(PRICE)
    low_price_24h: Mapped[Decimal | None] = mapped_column(PRICE)
    volume_24h: Mapped[Decimal | None] = mapped_column(QUANTITY)
    spread_bps: Mapped[Decimal | None] = mapped_column(PERCENT)
    volatility_pct: Mapped[Decimal | None] = mapped_column(PERCENT)
    trend_1h: Mapped[str | None] = mapped_column(String(32))
    trend_4h: Mapped[str | None] = mapped_column(String(32))
    trend_1d: Mapped[str | None] = mapped_column(String(32))
    indicators: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BotRun(Base):
    __tablename__ = "bot_runs"
    __table_args__ = (
        CheckConstraint(
            "status in ('started', 'completed', 'failed', 'skipped')", name="bot_runs_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    strategy_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("strategy_configs.id", ondelete="SET NULL")
    )
    risk_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("risk_configs.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="started")
    error_message: Mapped[str | None] = mapped_column(Text)
    run_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    decisions: Mapped[list[DecisionLog]] = relationship(back_populates="bot_run")


class DecisionLog(Base):
    __tablename__ = "decision_logs"
    __table_args__ = (
        CheckConstraint(
            "decision in ('COMPRA', 'VENDA', 'MANTER_POSICAO', 'NAO_OPERAR')",
            name="decision_logs_decision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    bot_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("bot_runs.id", ondelete="SET NULL")
    )
    strategy_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("strategy_configs.id", ondelete="SET NULL")
    )
    risk_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("risk_configs.id", ondelete="SET NULL")
    )
    market_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("market_snapshots.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    indicators: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    intended_order: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    execution_result: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    portfolio_state: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    bot_run: Mapped[BotRun | None] = relationship(back_populates="decisions")
    orders: Mapped[list[Order]] = relationship(back_populates="decision")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("side in ('BUY', 'SELL')", name="orders_side"),
        CheckConstraint(
            "status in ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED')",
            name="orders_status",
        ),
        CheckConstraint("position_side = 'LONG'", name="orders_position_side_long_only"),
        UniqueConstraint(
            "exchange", "external_order_id", name="uq_orders_exchange_external_order_id"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    exchange: Mapped[str] = mapped_column(String(32), nullable=False, default="binance")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    decision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("decision_logs.id", ondelete="SET NULL")
    )
    bot_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("bot_runs.id", ondelete="SET NULL")
    )
    external_order_id: Mapped[str | None] = mapped_column(String(120))
    client_order_id: Mapped[str | None] = mapped_column(String(120))
    side: Mapped[str] = mapped_column(String(12), nullable=False)
    order_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    position_side: Mapped[str] = mapped_column(String(12), nullable=False, default="LONG")
    requested_quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    executed_quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False, default=0)
    quote_quantity: Mapped[Decimal | None] = mapped_column(MONEY)
    limit_price: Mapped[Decimal | None] = mapped_column(PRICE)
    average_price: Mapped[Decimal | None] = mapped_column(PRICE)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    decision: Mapped[DecisionLog | None] = relationship(back_populates="orders")
    fills: Mapped[list[OrderFill]] = relationship(back_populates="order")


class OrderFill(Base):
    __tablename__ = "order_fills"
    __table_args__ = (
        UniqueConstraint("exchange", "external_trade_id", name="uq_order_fills_exchange_trade_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    exchange: Mapped[str] = mapped_column(String(32), nullable=False, default="binance")
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    external_trade_id: Mapped[str | None] = mapped_column(String(120))
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    quote_quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    fee_amount: Mapped[Decimal | None] = mapped_column(QUANTITY)
    fee_asset: Mapped[str | None] = mapped_column(String(24))
    fee_estimated_usdt: Mapped[Decimal | None] = mapped_column(MONEY)
    raw_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped[Order] = relationship(back_populates="fills")


class Position(TimestampMixin, Base):
    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint("side = 'LONG'", name="positions_side_long_only"),
        UniqueConstraint(
            "environment", "symbol", "asset", "side", name="uq_positions_open_position"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    asset: Mapped[str] = mapped_column(String(24), nullable=False, default="BTC")
    side: Mapped[str] = mapped_column(String(12), nullable=False, default="LONG")
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False, default=0)
    average_cost: Mapped[Decimal] = mapped_column(PRICE, nullable=False, default=0)
    remaining_cost: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    total_fees_usdt: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(24), nullable=False, default="BTCUSDT")
    usdt_balance: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    btc_balance: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False, default=0)
    btc_market_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False, default=0)
    btc_market_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    invested_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    average_cost: Mapped[Decimal] = mapped_column(PRICE, nullable=False, default=0)
    total_equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    exposure_pct: Mapped[Decimal] = mapped_column(PERCENT, nullable=False, default=0)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    unrealized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    total_fees_usdt: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    source_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="testnet")
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(120))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID_PK)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
