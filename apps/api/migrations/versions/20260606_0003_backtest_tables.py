"""backtest tables

Revision ID: 20260606_0003
Revises: 20260517_0002
Create Date: 2026-06-06 00:03:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260606_0003"
down_revision: str | None = "20260517_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)
jsonb_type = postgresql.JSONB(astext_type=sa.Text())
money_type = sa.Numeric(precision=28, scale=10)
percent_type = sa.Numeric(precision=12, scale=6)
price_type = sa.Numeric(precision=28, scale=10)
quantity_type = sa.Numeric(precision=28, scale=12)


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("signal_interval", sa.String(length=12), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("initial_capital", money_type, nullable=False),
        sa.Column("fee_rate", percent_type, nullable=False),
        sa.Column(
            "strategy_params",
            jsonb_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('pending', 'running', 'completed', 'failed')",
            name="backtest_runs_status",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_runs")),
    )

    op.create_table(
        "backtest_trades",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("backtest_run_id", uuid_type, nullable=False),
        sa.Column("trade_index", sa.Integer(), nullable=False),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entry_price", price_type, nullable=False),
        sa.Column("exit_price", price_type, nullable=False),
        sa.Column("quantity", quantity_type, nullable=False),
        sa.Column("entry_value", money_type, nullable=False),
        sa.Column("exit_value", money_type, nullable=False),
        sa.Column("fees_paid", money_type, nullable=False),
        sa.Column("pnl_usd", money_type, nullable=False),
        sa.Column("return_pct", percent_type, nullable=False),
        sa.Column("exit_reason", sa.String(length=64), nullable=False),
        sa.Column("is_winner", sa.Boolean(), nullable=False),
        sa.Column("equity_after", money_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["backtest_run_id"],
            ["backtest_runs.id"],
            name=op.f("fk_backtest_trades_backtest_run_id_backtest_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_trades")),
    )
    op.create_index(
        "ix_backtest_trades_run_index",
        "backtest_trades",
        ["backtest_run_id", "trade_index"],
    )

    op.create_table(
        "backtest_equity_points",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("backtest_run_id", uuid_type, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("equity", money_type, nullable=False),
        sa.Column("btc_price", price_type, nullable=True),
        sa.Column("is_in_position", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(
            ["backtest_run_id"],
            ["backtest_runs.id"],
            name=op.f("fk_backtest_equity_points_backtest_run_id_backtest_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_equity_points")),
    )
    op.create_index(
        "ix_backtest_equity_points_run_ts",
        "backtest_equity_points",
        ["backtest_run_id", "timestamp"],
    )

    op.create_table(
        "backtest_metrics",
        sa.Column("backtest_run_id", uuid_type, nullable=False),
        sa.Column("total_return_pct", percent_type, nullable=False),
        sa.Column("total_return_usd", money_type, nullable=False),
        sa.Column("final_capital", money_type, nullable=False),
        sa.Column("max_drawdown_pct", percent_type, nullable=False),
        sa.Column("win_rate_pct", percent_type, nullable=False),
        sa.Column("profit_factor", percent_type, nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=False),
        sa.Column("winning_trades", sa.Integer(), nullable=False),
        sa.Column("losing_trades", sa.Integer(), nullable=False),
        sa.Column("avg_win_pct", percent_type, nullable=True),
        sa.Column("avg_loss_pct", percent_type, nullable=True),
        sa.Column("sharpe_ratio", percent_type, nullable=True),
        sa.Column("largest_win_pct", percent_type, nullable=True),
        sa.Column("largest_loss_pct", percent_type, nullable=True),
        sa.Column("avg_trade_duration_hours", percent_type, nullable=True),
        sa.Column("btc_buy_hold_return_pct", percent_type, nullable=True),
        sa.ForeignKeyConstraint(
            ["backtest_run_id"],
            ["backtest_runs.id"],
            name=op.f("fk_backtest_metrics_backtest_run_id_backtest_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("backtest_run_id", name=op.f("pk_backtest_metrics")),
    )


def downgrade() -> None:
    op.drop_table("backtest_metrics")
    op.drop_index("ix_backtest_equity_points_run_ts", table_name="backtest_equity_points")
    op.drop_table("backtest_equity_points")
    op.drop_index("ix_backtest_trades_run_index", table_name="backtest_trades")
    op.drop_table("backtest_trades")
    op.drop_table("backtest_runs")
