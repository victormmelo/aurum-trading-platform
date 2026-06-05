from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.db.models import Order, OrderFill, PortfolioSnapshot
from app.performance.service import (
    build_average_cost_trades,
    build_performance_summary,
    build_performance_trades,
)

NOW = datetime(2026, 6, 5, 12, 0, tzinfo=UTC)


def test_average_cost_trades_realizes_partial_sell_profit() -> None:
    fills = [
        _fill("BUY", NOW - timedelta(days=4), quantity="0.010", price="100", quote="1.00"),
        _fill("BUY", NOW - timedelta(days=3), quantity="0.010", price="120", quote="1.20"),
        _fill(
            "SELL",
            NOW - timedelta(days=2),
            quantity="0.015",
            price="130",
            quote="1.95",
            fee_amount="0.01",
            fee_asset="USDT",
        ),
    ]

    trades = build_average_cost_trades(fills)

    assert len(trades) == 1
    assert trades[0].average_cost == Decimal("110.00")
    assert trades[0].cost_basis_reduced == Decimal("1.65000")
    assert trades[0].pnl_usdt == Decimal("0.29000")
    assert trades[0].source == "manual"


def test_average_cost_trades_realizes_loss_and_estimates_btc_fee() -> None:
    decision_id = uuid.uuid4()
    fills = [
        _fill("BUY", NOW - timedelta(days=4), quantity="0.020", price="100", quote="2.00"),
        _fill(
            "SELL",
            NOW - timedelta(days=1),
            quantity="0.020",
            price="90",
            quote="1.80",
            fee_amount="0.0001",
            fee_asset="BTC",
            decision_id=decision_id,
        ),
    ]

    trades = build_average_cost_trades(fills)

    assert len(trades) == 1
    assert trades[0].average_cost == Decimal("100")
    assert trades[0].fees_usdt == Decimal("0.0090")
    assert trades[0].pnl_usdt == Decimal("-0.2090")
    assert trades[0].fee_estimated is True
    assert trades[0].source == "robô"


def test_performance_summary_period_without_sells_keeps_open_pnl_visible() -> None:
    store = FakePerformanceStore(
        fills=[
            _fill("BUY", NOW - timedelta(days=20), quantity="0.010", price="100", quote="1.00")
        ],
        snapshots=[
            _snapshot(NOW - timedelta(days=8), total_equity="1000", unrealized_pnl="10"),
            _snapshot(NOW - timedelta(days=1), total_equity="1030", unrealized_pnl="30"),
        ],
    )

    summary = build_performance_summary(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        period="7d",
        now=NOW,
    )

    assert summary.sell_count == 0
    assert summary.realized_pnl == Decimal("0")
    assert summary.unrealized_pnl == Decimal("30")
    assert summary.total_pnl == Decimal("30")
    assert summary.status == "sem_amostra_suficiente"


def test_performance_summary_all_period_and_trade_filtering() -> None:
    old_sell = _fill("SELL", NOW - timedelta(days=100), quantity="0.010", price="130", quote="1.30")
    recent_sell = _fill("SELL", NOW - timedelta(days=1), quantity="0.010", price="140", quote="1.40")
    store = FakePerformanceStore(
        fills=[
            _fill("BUY", NOW - timedelta(days=120), quantity="0.020", price="100", quote="2.00"),
            old_sell,
            recent_sell,
        ],
        snapshots=[
            _snapshot(NOW - timedelta(days=120), total_equity="1000", unrealized_pnl="0"),
            _snapshot(NOW - timedelta(days=1), total_equity="1040", unrealized_pnl="0"),
        ],
    )

    all_summary = build_performance_summary(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        period="all",
        now=NOW,
    )
    recent_trades = build_performance_trades(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        period="30d",
        now=NOW,
    )

    assert all_summary.sell_count == 2
    assert all_summary.realized_pnl == Decimal("0.70")
    assert all_summary.return_pct == Decimal("4.00")
    assert len(recent_trades) == 1
    assert recent_trades[0].id == recent_sell.id


class FakePerformanceStore:
    def __init__(self, *, fills: list[OrderFill], snapshots: list[PortfolioSnapshot]) -> None:
        self.fills = fills
        self.snapshots = snapshots

    def list_fills(self, *, environment: str, symbol: str) -> list[OrderFill]:
        assert environment == "testnet"
        assert symbol == "BTCUSDT"
        return self.fills

    def list_snapshots(self, *, environment: str, symbol: str) -> list[PortfolioSnapshot]:
        assert environment == "testnet"
        assert symbol == "BTCUSDT"
        return self.snapshots


def _fill(
    side: str,
    filled_at: datetime,
    *,
    quantity: str,
    price: str,
    quote: str,
    fee_amount: str | None = None,
    fee_asset: str | None = None,
    decision_id: uuid.UUID | None = None,
) -> OrderFill:
    order = Order(
        id=uuid.uuid4(),
        environment="testnet",
        exchange="binance",
        symbol="BTCUSDT",
        decision_id=decision_id,
        bot_run_id=None,
        external_order_id=str(uuid.uuid4()),
        client_order_id=f"aurum-test-{uuid.uuid4().hex[:8]}",
        side=side,
        order_type="MARKET",
        status="FILLED",
        position_side="LONG",
        requested_quantity=Decimal(quantity),
        executed_quantity=Decimal(quantity),
        quote_quantity=Decimal(quote),
        average_price=Decimal(price),
        submitted_at=filled_at,
        closed_at=filled_at,
        raw_payload={},
    )
    fill = OrderFill(
        id=uuid.uuid4(),
        environment="testnet",
        exchange="binance",
        order_id=order.id,
        external_trade_id=str(uuid.uuid4()),
        filled_at=filled_at,
        price=Decimal(price),
        quantity=Decimal(quantity),
        quote_quantity=Decimal(quote),
        fee_amount=Decimal(fee_amount) if fee_amount is not None else None,
        fee_asset=fee_asset,
        fee_estimated_usdt=None,
        raw_payload={},
    )
    fill.order = order
    return fill


def _snapshot(
    captured_at: datetime, *, total_equity: str, unrealized_pnl: str
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        id=uuid.uuid4(),
        environment="testnet",
        captured_at=captured_at,
        symbol="BTCUSDT",
        usdt_balance=Decimal("0"),
        btc_balance=Decimal("0"),
        btc_market_price=Decimal("0"),
        btc_market_value=Decimal("0"),
        invested_value=Decimal("0"),
        average_cost=Decimal("0"),
        total_equity=Decimal(total_equity),
        exposure_pct=Decimal("0"),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal(unrealized_pnl),
        total_fees_usdt=Decimal("0"),
        source_payload={},
    )
