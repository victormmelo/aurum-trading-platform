from sqlalchemy import CheckConstraint

from app.db import models  # noqa: F401
from app.db.base import Base


def test_operational_schema_tables_are_registered() -> None:
    expected_tables = {
        "audit_logs",
        "bot_runs",
        "bot_runtime_state",
        "decision_logs",
        "market_candles",
        "market_snapshots",
        "order_fills",
        "orders",
        "portfolio_snapshots",
        "positions",
        "risk_configs",
        "strategy_configs",
    }

    assert set(Base.metadata.tables) == expected_tables


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
