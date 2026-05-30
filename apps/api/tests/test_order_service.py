from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.db.models import (
    AuditLog,
    BotRuntimeState,
    MarketSnapshot,
    Order,
    OrderFill,
    PortfolioSnapshot,
    RiskConfig,
)
from app.execution.adapters import ExecutionFill, ExecutionResult
from app.execution.service import OrderCommand, OrderService, OrderValidationError

NOW = datetime(2026, 5, 30, 12, 0, tzinfo=UTC)


def test_order_service_places_manual_testnet_order_and_persists_order_fill_and_audit() -> None:
    session = valid_session()
    service = OrderService(
        session=session,
        adapter=FakeAdapter(),
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    order = service.place_order(
        OrderCommand(
            environment="testnet",
            symbol="BTCUSDT",
            side="BUY",
            quote_quantity=Decimal("100"),
            actor_type="manual",
            actor_id="victor",
            reason="manual test",
        ),
        now=NOW,
    )

    assert isinstance(order, Order)
    assert order.status == "FILLED"
    assert order.external_order_id == "12345"
    assert order.client_order_id.startswith("aurum-manual-")
    assert order.executed_quantity == Decimal("0.001")
    assert order.average_price == Decimal("100000")
    assert any(isinstance(item, OrderFill) for item in session.added)
    audits = [item for item in session.added if isinstance(item, AuditLog)]
    assert audits[0].action == "order.submitted"
    assert audits[0].actor_type == "manual"


def test_order_service_blocks_when_bot_is_paused_and_audits_block() -> None:
    session = valid_session(runtime_status="paused")
    service = OrderService(
        session=session,
        adapter=FakeAdapter(),
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    with pytest.raises(OrderValidationError) as exc:
        service.place_order(
            OrderCommand(
                environment="testnet",
                symbol="BTCUSDT",
                side="BUY",
                quote_quantity=Decimal("100"),
                actor_type="manual",
            ),
            now=NOW,
        )

    assert exc.value.code == "bot_paused"
    audits = [item for item in session.added if isinstance(item, AuditLog)]
    assert audits[0].action == "order.blocked"
    assert audits[0].metadata_payload["code"] == "bot_paused"


def test_order_service_blocks_stale_market_data() -> None:
    session = valid_session(market_captured_at=NOW - timedelta(minutes=10))
    service = OrderService(
        session=session,
        adapter=FakeAdapter(),
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    with pytest.raises(OrderValidationError) as exc:
        service.place_order(
            OrderCommand(
                environment="testnet",
                symbol="BTCUSDT",
                side="BUY",
                quote_quantity=Decimal("100"),
            ),
            now=NOW,
        )

    assert exc.value.code == "stale_market_data"


def test_order_service_blocks_insufficient_balance() -> None:
    session = valid_session(usdt_balance=Decimal("50"))
    service = OrderService(
        session=session,
        adapter=FakeAdapter(),
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    with pytest.raises(OrderValidationError) as exc:
        service.place_order(
            OrderCommand(
                environment="testnet",
                symbol="BTCUSDT",
                side="BUY",
                quote_quantity=Decimal("100"),
            ),
            now=NOW,
        )

    assert exc.value.code == "insufficient_balance"


def test_order_service_blocks_symbol_out_of_scope_before_adapter_call() -> None:
    session = valid_session()
    adapter = FakeAdapter()
    service = OrderService(
        session=session,
        adapter=adapter,
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    with pytest.raises(OrderValidationError) as exc:
        service.place_order(
            OrderCommand(
                environment="testnet",
                symbol="ETHUSDT",
                side="BUY",
                quote_quantity=Decimal("100"),
            ),
            now=NOW,
        )

    assert exc.value.code == "symbol_out_of_scope"
    assert adapter.requests == []


def test_order_service_persists_rejected_order_when_adapter_fails() -> None:
    session = valid_session()
    service = OrderService(
        session=session,
        adapter=FailingAdapter(),
        expected_environment="testnet",
        expected_symbol="BTCUSDT",
        stale_after_seconds=300,
    )

    order = service.place_order(
        OrderCommand(
            environment="testnet",
            symbol="BTCUSDT",
            side="BUY",
            quote_quantity=Decimal("100"),
            actor_type="manual",
            actor_id="victor",
        ),
        now=NOW,
    )

    assert order.status == "REJECTED"
    assert order.executed_quantity == Decimal("0")
    assert order.quote_quantity == Decimal("100")
    assert order.raw_payload["response"]["error_type"] == "RuntimeError"
    audits = [item for item in session.added if isinstance(item, AuditLog)]
    assert audits[0].action == "order.rejected"
    assert audits[0].entity_id == order.id


def valid_session(
    *,
    runtime_status: str = "running",
    market_captured_at: datetime = NOW,
    usdt_balance: Decimal = Decimal("1000"),
) -> FakeSession:
    return FakeSession(
        scalars=[
            BotRuntimeState(
                environment="testnet",
                status=runtime_status,
                trading_mode="testnet",
                symbol="BTCUSDT",
            ),
            MarketSnapshot(
                environment="testnet",
                symbol="BTCUSDT",
                captured_at=market_captured_at,
                last_price=Decimal("100000"),
                indicators={},
                source_payload={},
            ),
            PortfolioSnapshot(
                environment="testnet",
                captured_at=NOW,
                symbol="BTCUSDT",
                usdt_balance=usdt_balance,
                btc_balance=Decimal("0.01"),
                btc_market_price=Decimal("100000"),
                btc_market_value=Decimal("1000"),
                invested_value=Decimal("0"),
                average_cost=Decimal("0"),
                total_equity=usdt_balance + Decimal("1000"),
                exposure_pct=Decimal("10"),
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                total_fees_usdt=Decimal("0"),
                source_payload={},
            ),
            RiskConfig(
                environment="testnet",
                version=1,
                symbol="BTCUSDT",
                risk_per_trade_pct=Decimal("1"),
                daily_loss_limit_pct=Decimal("2"),
                max_exposure_pct=Decimal("80"),
                parameters={},
                is_active=True,
            ),
        ]
    )


class FakeAdapter:
    name = "binance_testnet"

    def __init__(self) -> None:
        self.client = type(
            "Client",
            (),
            {"base_url": "https://testnet.binance.vision/api/v3"},
        )()
        self.requests = []

    def place_order(self, request):  # noqa: ANN001, ANN201
        self.requests.append(request)
        return ExecutionResult(
            adapter=self.name,
            external_order_id="12345",
            client_order_id=request.client_order_id,
            status="FILLED",
            executed_quantity=Decimal("0.001"),
            quote_quantity=Decimal("100"),
            average_price=Decimal("100000"),
            raw_payload={"orderId": 12345, "status": "FILLED"},
            fills=[
                ExecutionFill(
                    external_trade_id="999",
                    price=Decimal("100000"),
                    quantity=Decimal("0.001"),
                    quote_quantity=Decimal("100"),
                    fee_amount=Decimal("0.1"),
                    fee_asset="USDT",
                    raw_payload={"id": 999},
                )
            ],
        )

    def fetch_order(self, *, symbol, external_order_id, client_order_id):  # noqa: ANN001, ANN201, ARG002
        raise AssertionError("not used")


class FailingAdapter(FakeAdapter):
    def place_order(self, request):  # noqa: ANN001, ANN201, ARG002
        raise RuntimeError("binance rejected")


class FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def first(self):  # noqa: ANN201
        return self.value


class FakeSession:
    def __init__(self, *, scalars: list) -> None:
        self._scalars = scalars
        self.added = []
        self.flushes = 0

    def scalars(self, statement):  # noqa: ANN001, ANN201, ARG002
        return FakeScalarResult(self._scalars.pop(0))

    def add(self, value) -> None:  # noqa: ANN001
        if isinstance(value, Order) and value.id is None:
            value.id = uuid.uuid4()
        self.added.append(value)

    def flush(self) -> None:
        self.flushes += 1
