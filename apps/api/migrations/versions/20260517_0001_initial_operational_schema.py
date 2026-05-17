"""initial operational schema

Revision ID: 20260517_0001
Revises:
Create Date: 2026-05-17 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260517_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)
jsonb_type = postgresql.JSONB(astext_type=sa.Text())


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "bot_runtime_state",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("trading_mode", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_cycle_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("emergency_stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pause_reason", sa.Text(), nullable=True),
        sa.Column(
            "state_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('running', 'paused', 'emergency_stop')",
            name=op.f("ck_bot_runtime_state_bot_runtime_state_status"),
        ),
        sa.CheckConstraint(
            "trading_mode in ('paper', 'testnet', 'mainnet')",
            name=op.f("ck_bot_runtime_state_bot_runtime_state_trading_mode"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bot_runtime_state")),
        sa.UniqueConstraint("environment", name="uq_bot_runtime_state_environment"),
    )

    op.create_table(
        "strategy_configs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("signal_timeframe", sa.String(length=12), nullable=False),
        sa.Column("regime_timeframe_primary", sa.String(length=12), nullable=False),
        sa.Column("regime_timeframe_secondary", sa.String(length=12), nullable=False),
        sa.Column("parameters", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_strategy_configs")),
        sa.UniqueConstraint(
            "environment", "version", name="uq_strategy_configs_environment_version"
        ),
    )
    op.create_index(
        "ix_strategy_configs_one_active_per_environment",
        "strategy_configs",
        ["environment"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "risk_configs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("risk_per_trade_pct", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("daily_loss_limit_pct", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("max_exposure_pct", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("parameters", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_configs")),
        sa.UniqueConstraint("environment", "version", name="uq_risk_configs_environment_version"),
    )
    op.create_index(
        "ix_risk_configs_one_active_per_environment",
        "risk_configs",
        ["environment"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "market_candles",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("interval", sa.String(length=12), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("high_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("low_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("volume", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("quote_volume", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("trade_count", sa.Integer(), nullable=True),
        sa.Column(
            "source_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_candles")),
        sa.UniqueConstraint(
            "exchange", "symbol", "interval", "open_time", name="uq_market_candles_source_window"
        ),
    )

    op.create_table(
        "market_snapshots",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("price_change_pct_24h", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("high_price_24h", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("low_price_24h", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("volume_24h", sa.Numeric(precision=28, scale=12), nullable=True),
        sa.Column("spread_bps", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("volatility_pct", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("trend_1h", sa.String(length=32), nullable=True),
        sa.Column("trend_4h", sa.String(length=32), nullable=True),
        sa.Column("trend_1d", sa.String(length=32), nullable=True),
        sa.Column("indicators", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "source_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_snapshots")),
    )

    op.create_table(
        "bot_runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("strategy_config_id", uuid_type, nullable=True),
        sa.Column("risk_config_id", uuid_type, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("run_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status in ('started', 'completed', 'failed', 'skipped')",
            name=op.f("ck_bot_runs_bot_runs_status"),
        ),
        sa.ForeignKeyConstraint(
            ["risk_config_id"],
            ["risk_configs.id"],
            name=op.f("fk_bot_runs_risk_config_id_risk_configs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["strategy_config_id"],
            ["strategy_configs.id"],
            name=op.f("fk_bot_runs_strategy_config_id_strategy_configs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bot_runs")),
    )

    op.create_table(
        "decision_logs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("bot_run_id", uuid_type, nullable=True),
        sa.Column("strategy_config_id", uuid_type, nullable=True),
        sa.Column("risk_config_id", uuid_type, nullable=True),
        sa.Column("market_snapshot_id", uuid_type, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "reason_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("indicators", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "intended_order", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "execution_result", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "portfolio_state", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "decision in ('COMPRA', 'VENDA', 'MANTER_POSICAO', 'NAO_OPERAR')",
            name=op.f("ck_decision_logs_decision_logs_decision"),
        ),
        sa.ForeignKeyConstraint(
            ["bot_run_id"],
            ["bot_runs.id"],
            name=op.f("fk_decision_logs_bot_run_id_bot_runs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["market_snapshot_id"],
            ["market_snapshots.id"],
            name=op.f("fk_decision_logs_market_snapshot_id_market_snapshots"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["risk_config_id"],
            ["risk_configs.id"],
            name=op.f("fk_decision_logs_risk_config_id_risk_configs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["strategy_config_id"],
            ["strategy_configs.id"],
            name=op.f("fk_decision_logs_strategy_config_id_strategy_configs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_logs")),
    )

    op.create_table(
        "orders",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("decision_id", uuid_type, nullable=True),
        sa.Column("bot_run_id", uuid_type, nullable=True),
        sa.Column("external_order_id", sa.String(length=120), nullable=True),
        sa.Column("client_order_id", sa.String(length=120), nullable=True),
        sa.Column("side", sa.String(length=12), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("position_side", sa.String(length=12), nullable=False),
        sa.Column("requested_quantity", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("executed_quantity", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("quote_quantity", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("limit_price", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("average_price", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("side in ('BUY', 'SELL')", name=op.f("ck_orders_orders_side")),
        sa.CheckConstraint(
            "position_side = 'LONG'", name=op.f("ck_orders_orders_position_side_long_only")
        ),
        sa.CheckConstraint(
            "status in ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED')",
            name=op.f("ck_orders_orders_status"),
        ),
        sa.ForeignKeyConstraint(
            ["bot_run_id"],
            ["bot_runs.id"],
            name=op.f("fk_orders_bot_run_id_bot_runs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["decision_logs.id"],
            name=op.f("fk_orders_decision_id_decision_logs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint(
            "exchange", "external_order_id", name="uq_orders_exchange_external_order_id"
        ),
    )

    op.create_table(
        "order_fills",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("order_id", uuid_type, nullable=False),
        sa.Column("external_trade_id", sa.String(length=120), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("quote_quantity", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("fee_amount", sa.Numeric(precision=28, scale=12), nullable=True),
        sa.Column("fee_asset", sa.String(length=24), nullable=True),
        sa.Column("fee_estimated_usdt", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("raw_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_fills_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_fills")),
        sa.UniqueConstraint(
            "exchange", "external_trade_id", name="uq_order_fills_exchange_trade_id"
        ),
    )

    op.create_table(
        "positions",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("asset", sa.String(length=24), nullable=False),
        sa.Column("side", sa.String(length=12), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("remaining_cost", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("total_fees_usdt", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("side = 'LONG'", name=op.f("ck_positions_positions_side_long_only")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_positions")),
        sa.UniqueConstraint(
            "environment", "symbol", "asset", "side", name="uq_positions_open_position"
        ),
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("usdt_balance", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("btc_balance", sa.Numeric(precision=28, scale=12), nullable=False),
        sa.Column("btc_market_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("btc_market_value", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("invested_value", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("total_equity", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("exposure_pct", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("total_fees_usdt", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column(
            "source_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_portfolio_snapshots")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=True),
        sa.Column("entity_id", uuid_type, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "metadata_payload", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("portfolio_snapshots")
    op.drop_table("positions")
    op.drop_table("order_fills")
    op.drop_table("orders")
    op.drop_table("decision_logs")
    op.drop_table("bot_runs")
    op.drop_table("market_snapshots")
    op.drop_table("market_candles")
    op.drop_index("ix_risk_configs_one_active_per_environment", table_name="risk_configs")
    op.drop_table("risk_configs")
    op.drop_index("ix_strategy_configs_one_active_per_environment", table_name="strategy_configs")
    op.drop_table("strategy_configs")
    op.drop_table("bot_runtime_state")
