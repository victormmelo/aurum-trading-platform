from sqlalchemy import CheckConstraint

from app.db import models  # noqa: F401
from app.db.base import Base


def test_operational_schema_tables_are_registered() -> None:
    expected_tables = {
        "audit_logs",
        "backtest_equity_points",
        "backtest_metrics",
        "backtest_runs",
        "backtest_trades",
        "bot_runs",
        "bot_runtime_state",
        "decision_logs",
        "market_candles",
        "market_snapshots",
        "mcp_access_logs",
        "mcp_tokens",
        "order_fills",
        "orders",
        "portfolio_snapshots",
        "positions",
        "risk_configs",
        "strategy_configs",
    }

    assert set(Base.metadata.tables) == expected_tables


def test_mcp_token_schema_stores_only_token_hash_and_read_only_scopes() -> None:
    mcp_tokens = Base.metadata.tables["mcp_tokens"]

    assert "token_hash" in mcp_tokens.columns
    assert "token" not in mcp_tokens.columns
    assert "secret" not in mcp_tokens.columns
    assert "scopes" in mcp_tokens.columns


def test_decision_log_accepts_only_mvp_decisions() -> None:
    decision_logs = Base.metadata.tables["decision_logs"]
    constraints = {
        constraint.name: str(constraint.sqltext)
        for constraint in decision_logs.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert constraints["ck_decision_logs_decision_logs_decision"] == (
        "decision in ('COMPRA', 'VENDA', 'MANTER_POSICAO', 'NAO_OPERAR')"
    )


def test_order_and_position_schema_preserve_long_only_scope() -> None:
    orders = Base.metadata.tables["orders"]
    positions = Base.metadata.tables["positions"]

    order_constraints = {
        constraint.name: str(constraint.sqltext)
        for constraint in orders.constraints
        if isinstance(constraint, CheckConstraint)
    }
    position_constraints = {
        constraint.name: str(constraint.sqltext)
        for constraint in positions.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert order_constraints["ck_orders_orders_position_side_long_only"] == "position_side = 'LONG'"
    assert position_constraints["ck_positions_positions_side_long_only"] == "side = 'LONG'"
