from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import decisions as decisions_routes
from app.api.routes import market as market_routes
from app.api.routes import operations as operations_routes
from app.api.routes import portfolio as portfolio_routes
from app.db.session import get_db_session
from app.main import create_app

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_market_summary_endpoint_returns_empty_shape(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    original_get_market_summary = market_routes.get_market_summary

    def summary(store, environment, symbol):  # noqa: ANN001
        assert environment == "testnet"
        assert symbol == "BTCUSDT"
        return original_get_market_summary(
            _MarketStore(snapshot=None, candles=[]), environment=environment, symbol=symbol
        )

    monkeypatch.setattr(market_routes, "get_market_summary", summary)

    response = client.get("/market/summary")

    assert response.status_code == 200
    assert response.json() == {
        "environment": "testnet",
        "symbol": "BTCUSDT",
        "snapshot": None,
    }


def test_market_candles_endpoint_passes_interval_and_limit(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    candle_id = uuid.uuid4()
    original_get_market_candles = market_routes.get_market_candles

    def candles(store, environment, symbol, interval, limit):  # noqa: ANN001
        assert interval == "4h"
        assert limit == 2
        candle = SimpleNamespace(
            id=candle_id,
            environment=environment,
            exchange="binance",
            symbol=symbol,
            interval=interval,
            open_time=NOW,
            close_time=NOW,
            open_price=Decimal("100"),
            high_price=Decimal("110"),
            low_price=Decimal("90"),
            close_price=Decimal("105"),
            volume=Decimal("1.5"),
            quote_volume=Decimal("157.5"),
            trade_count=42,
        )
        return original_get_market_candles(
            _MarketStore(snapshot=None, candles=[candle]),
            environment=environment,
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

    monkeypatch.setattr(market_routes, "get_market_candles", candles)

    response = client.get("/market/candles?interval=4h&limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["interval"] == "4h"
    assert payload["candles"][0]["id"] == str(candle_id)
    assert payload["candles"][0]["close_price"] == "105"


def test_market_candles_rejects_unsupported_interval() -> None:
    response = _client().get("/market/candles?interval=15m")

    assert response.status_code == 422


def test_market_stream_endpoint_returns_sse_events(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    async def stream():  # noqa: ANN202
        yield "event: snapshot\ndata: {}\n\n"
        yield "event: heartbeat\ndata: {}\n\n"

    monkeypatch.setattr(market_routes, "_market_event_stream", stream)

    response = client.get("/market/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: snapshot" in response.text
    assert "event: heartbeat" in response.text


def test_portfolio_status_endpoint_returns_empty_state(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    original_get_portfolio_status = portfolio_routes.get_portfolio_status

    monkeypatch.setattr(
        portfolio_routes,
        "get_portfolio_status",
        lambda store, environment, symbol: original_get_portfolio_status(
            _PortfolioStore(snapshot=None, position=None), environment=environment, symbol=symbol
        ),
    )

    response = client.get("/portfolio/status")

    assert response.status_code == 200
    assert response.json() == {
        "environment": "testnet",
        "symbol": "BTCUSDT",
        "snapshot": None,
        "position": None,
    }


def test_portfolio_status_endpoint_returns_snapshot_and_position(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    snapshot_id = uuid.uuid4()
    position_id = uuid.uuid4()
    original_get_portfolio_status = portfolio_routes.get_portfolio_status

    snapshot = SimpleNamespace(
        id=snapshot_id,
        captured_at=NOW,
        usdt_balance=Decimal("1000"),
        btc_balance=Decimal("0.01"),
        btc_market_price=Decimal("100000"),
        btc_market_value=Decimal("1000"),
        invested_value=Decimal("950"),
        average_cost=Decimal("95000"),
        total_equity=Decimal("2000"),
        exposure_pct=Decimal("50"),
        realized_pnl=Decimal("10"),
        unrealized_pnl=Decimal("50"),
        total_fees_usdt=Decimal("1.25"),
        source_payload={"source": "test"},
    )
    position = SimpleNamespace(
        id=position_id,
        asset="BTC",
        side="LONG",
        quantity=Decimal("0.01"),
        average_cost=Decimal("95000"),
        remaining_cost=Decimal("950"),
        realized_pnl=Decimal("10"),
        total_fees_usdt=Decimal("1.25"),
        last_reconciled_at=NOW,
    )

    monkeypatch.setattr(
        portfolio_routes,
        "get_portfolio_status",
        lambda store, environment, symbol: original_get_portfolio_status(
            _PortfolioStore(snapshot=snapshot, position=position),
            environment=environment,
            symbol=symbol,
        ),
    )

    response = client.get("/portfolio/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot"]["id"] == str(snapshot_id)
    assert payload["snapshot"]["total_equity"] == "2000"
    assert payload["position"]["id"] == str(position_id)
    assert payload["position"]["side"] == "LONG"


def test_orders_endpoint_passes_filters(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    order_id = uuid.uuid4()
    decision_id = uuid.uuid4()
    original_get_orders = operations_routes.get_orders

    def orders(store, environment, symbol, limit, offset, side, status):  # noqa: ANN001
        assert limit == 10
        assert offset == 5
        assert side == "BUY"
        assert status == "FILLED"
        order = SimpleNamespace(
            id=order_id,
            environment=environment,
            exchange="binance",
            symbol=symbol,
            decision_id=decision_id,
            bot_run_id=None,
            external_order_id="123",
            client_order_id="aurum-123",
            side=side,
            order_type="MARKET",
            status=status,
            position_side="LONG",
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            quote_quantity=Decimal("1000"),
            limit_price=None,
            average_price=Decimal("100000"),
            submitted_at=NOW,
            closed_at=NOW,
            raw_payload={"raw": True},
        )
        return original_get_orders(
            _OperationsStore(orders=[order], fills=[]),
            environment=environment,
            symbol=symbol,
            limit=limit,
            offset=offset,
            side=side,
            status=status,
        )

    monkeypatch.setattr(operations_routes, "get_orders", orders)

    response = client.get("/operations/orders?side=BUY&status=FILLED&limit=10&offset=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["orders"][0]["id"] == str(order_id)
    assert payload["orders"][0]["decision_id"] == str(decision_id)


def test_fills_endpoint_preserves_order_links(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    order_id = uuid.uuid4()
    decision_id = uuid.uuid4()
    bot_run_id = uuid.uuid4()
    original_get_fills = operations_routes.get_fills
    fill = SimpleNamespace(
        id=uuid.uuid4(),
        environment="testnet",
        exchange="binance",
        order_id=order_id,
        order=SimpleNamespace(decision_id=decision_id, bot_run_id=bot_run_id),
        external_trade_id="trade-1",
        filled_at=NOW,
        price=Decimal("100000"),
        quantity=Decimal("0.01"),
        quote_quantity=Decimal("1000"),
        fee_amount=Decimal("0.00001"),
        fee_asset="BTC",
        fee_estimated_usdt=Decimal("1"),
        raw_payload={},
    )

    monkeypatch.setattr(
        operations_routes,
        "get_fills",
        lambda store, environment, symbol, limit, offset: original_get_fills(
            _OperationsStore(orders=[], fills=[fill]),
            environment=environment,
            symbol=symbol,
            limit=limit,
            offset=offset,
        ),
    )

    response = client.get("/operations/fills")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fills"][0]["order_id"] == str(order_id)
    assert payload["fills"][0]["order_decision_id"] == str(decision_id)
    assert payload["fills"][0]["order_bot_run_id"] == str(bot_run_id)


def test_manual_order_endpoint_returns_persisted_order(monkeypatch) -> None:  # noqa: ANN001
    session = _FakeSession()
    client = _client(session)
    order_id = uuid.uuid4()

    order = SimpleNamespace(
        id=order_id,
        environment="testnet",
        exchange="binance",
        symbol="BTCUSDT",
        decision_id=None,
        bot_run_id=None,
        external_order_id="12345",
        client_order_id="aurum-manual",
        side="BUY",
        order_type="MARKET",
        status="FILLED",
        position_side="LONG",
        requested_quantity=Decimal("0"),
        executed_quantity=Decimal("0.00025"),
        quote_quantity=Decimal("25"),
        limit_price=None,
        average_price=Decimal("100000"),
        submitted_at=NOW,
        closed_at=NOW,
        raw_payload={"adapter": "binance_testnet"},
    )

    monkeypatch.setattr(
        operations_routes,
        "_order_service",
        lambda session, trading_mode: _FakeOrderService(order),
    )

    response = client.post(
        "/operations/manual-order",
        json={"side": "BUY", "quote_quantity": "25", "reason": "test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "testnet"
    assert payload["symbol"] == "BTCUSDT"
    assert payload["order"]["id"] == str(order_id)
    assert payload["order"]["status"] == "FILLED"
    assert session.commits == 1


def test_order_reconcile_endpoint_returns_updated_orders(monkeypatch) -> None:  # noqa: ANN001
    session = _FakeSession()
    client = _client(session)
    order_id = uuid.uuid4()
    order = SimpleNamespace(
        id=order_id,
        environment="testnet",
        exchange="binance",
        symbol="BTCUSDT",
        decision_id=None,
        bot_run_id=None,
        external_order_id="12345",
        client_order_id="aurum-manual",
        side="BUY",
        order_type="MARKET",
        status="FILLED",
        position_side="LONG",
        requested_quantity=Decimal("0"),
        executed_quantity=Decimal("0.00025"),
        quote_quantity=Decimal("25"),
        limit_price=None,
        average_price=Decimal("100000"),
        submitted_at=NOW,
        closed_at=NOW,
        raw_payload={},
    )

    monkeypatch.setattr(
        operations_routes,
        "_order_service",
        lambda session, trading_mode: _FakeOrderService(order),
    )

    response = client.post("/operations/reconcile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["reconciled_orders"][0]["id"] == str(order_id)
    assert session.commits == 1


def test_portfolio_reconcile_endpoint_returns_snapshot_and_position(monkeypatch) -> None:  # noqa: ANN001
    session = _FakeSession()
    client = _client(session)
    snapshot_id = uuid.uuid4()
    position_id = uuid.uuid4()
    snapshot = SimpleNamespace(
        id=snapshot_id,
        captured_at=NOW,
        usdt_balance=Decimal("500"),
        btc_balance=Decimal("0.01"),
        btc_market_price=Decimal("100000"),
        btc_market_value=Decimal("1000"),
        invested_value=Decimal("950"),
        average_cost=Decimal("95000"),
        total_equity=Decimal("1500"),
        exposure_pct=Decimal("66.666667"),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("50"),
        total_fees_usdt=Decimal("0"),
        source_payload={"source": "binance_spot_testnet_account"},
    )
    position = SimpleNamespace(
        id=position_id,
        asset="BTC",
        side="LONG",
        quantity=Decimal("0.01"),
        average_cost=Decimal("95000"),
        remaining_cost=Decimal("950"),
        realized_pnl=Decimal("0"),
        total_fees_usdt=Decimal("0"),
        last_reconciled_at=NOW,
    )

    monkeypatch.setattr(
        portfolio_routes,
        "get_settings",
        lambda: SimpleNamespace(
            aurum_environment="testnet",
            trading_symbol="BTCUSDT",
            binance_spot_base_url="https://testnet.binance.vision/api/v3",
            binance_api_key="key",
            binance_api_secret="secret",
            binance_recv_window_ms=5000,
        ),
    )
    monkeypatch.setattr(
        portfolio_routes,
        "BinancePortfolioReconciler",
        lambda client: _FakePortfolioReconciler(snapshot, position),
    )

    response = client.post("/portfolio/reconcile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot"]["id"] == str(snapshot_id)
    assert payload["position"]["id"] == str(position_id)
    assert session.commits == 1


def test_decisions_endpoint_passes_filter_and_preserves_links(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    bot_run_id = uuid.uuid4()
    strategy_config_id = uuid.uuid4()
    risk_config_id = uuid.uuid4()
    market_snapshot_id = uuid.uuid4()
    original_get_decisions = decisions_routes.get_decisions

    def decisions(store, environment, symbol, limit, offset, decision):  # noqa: ANN001
        assert decision == "NAO_OPERAR"
        row = SimpleNamespace(
            id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            bot_run_id=bot_run_id,
            strategy_config_id=strategy_config_id,
            risk_config_id=risk_config_id,
            market_snapshot_id=market_snapshot_id,
            decided_at=NOW,
            decision=decision,
            reason="Regime bloqueado",
            reason_payload={"regime": "blocked"},
            indicators={"rsi": 45},
            intended_order={},
            execution_result={"execution_mode": "dry_run"},
            portfolio_state={},
        )
        return original_get_decisions(
            _DecisionsStore(decisions=[row]),
            environment=environment,
            symbol=symbol,
            limit=limit,
            offset=offset,
            decision=decision,
        )

    monkeypatch.setattr(decisions_routes, "get_decisions", decisions)

    response = client.get("/decisions?decision=NAO_OPERAR")

    assert response.status_code == 200
    payload = response.json()
    assert payload["decisions"][0]["bot_run_id"] == str(bot_run_id)
    assert payload["decisions"][0]["strategy_config_id"] == str(strategy_config_id)
    assert payload["decisions"][0]["risk_config_id"] == str(risk_config_id)
    assert payload["decisions"][0]["market_snapshot_id"] == str(market_snapshot_id)


def _client(session: object | None = None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session if session is not None else object()
    return TestClient(app)


@dataclass
class _MarketStore:
    snapshot: object | None
    candles: list[object]

    def get_latest_snapshot(self, *, environment: str, symbol: str) -> object | None:
        return self.snapshot

    def list_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[object]:
        return self.candles


@dataclass
class _PortfolioStore:
    snapshot: object | None
    position: object | None

    def get_latest_snapshot(self, *, environment: str, symbol: str) -> object | None:
        return self.snapshot

    def get_open_position(self, *, environment: str, symbol: str) -> object | None:
        return self.position


@dataclass
class _OperationsStore:
    orders: list[object]
    fills: list[object]

    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        side: str | None,
        status: str | None,
    ) -> list[object]:
        return self.orders

    def list_fills(
        self, *, environment: str, symbol: str, limit: int, offset: int
    ) -> list[object]:
        return self.fills


@dataclass
class _DecisionsStore:
    decisions: list[object]

    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        limit: int,
        offset: int,
        decision: str | None,
    ) -> list[object]:
        return self.decisions


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class _FakeOrderService:
    def __init__(self, order: object) -> None:
        self.order = order

    def place_order(self, command, *, now=None):  # noqa: ANN001, ANN201, ARG002
        return self.order

    def reconcile_open_orders(self, *, environment, symbol):  # noqa: ANN001, ANN201, ARG002
        return [self.order]


class _FakePortfolioReconciler:
    def __init__(self, snapshot: object, position: object) -> None:
        self.snapshot = snapshot
        self.position = position

    def reconcile(self, session, *, environment, symbol):  # noqa: ANN001, ANN201, ARG002
        return SimpleNamespace(snapshot=self.snapshot, position=self.position)
