from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import configs as config_routes
from app.configuration.control import ConfigNotFoundError, ConfigVersionConflictError
from app.db.session import get_db_session
from app.main import create_app

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_strategy_configs_endpoint_lists_versions(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    config_id = uuid.uuid4()

    monkeypatch.setattr(
        config_routes,
        "list_strategy_configs",
        lambda store, environment, symbol: [
            _strategy_config(config_id=config_id, environment=environment, symbol=symbol)
        ],
    )

    response = client.get("/configs/strategy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "testnet"
    assert payload["symbol"] == "BTCUSDT"
    assert payload["configs"][0]["id"] == str(config_id)
    assert payload["configs"][0]["version"] == 1
    assert payload["configs"][0]["is_active"] is False


def test_active_strategy_config_endpoint_returns_null(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    monkeypatch.setattr(
        config_routes,
        "get_active_strategy_config",
        lambda store, environment, symbol: None,
    )

    response = client.get("/configs/strategy/active")

    assert response.status_code == 200
    assert response.json() is None


def test_create_strategy_config_endpoint_returns_201(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def create(store, environment, symbol, command):  # noqa: ANN001
        assert environment == "testnet"
        assert symbol == "BTCUSDT"
        assert command.version == 2
        assert command.created_by == "operator"
        return _strategy_config(
            config_id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            version=command.version,
            created_by=command.created_by,
        )

    monkeypatch.setattr(config_routes, "create_strategy_config", create)

    response = client.post(
        "/configs/strategy",
        json={
            "version": 2,
            "name": "breakout_trend_v2",
            "parameters": {"breakout_lookback": 30},
            "created_by": "operator",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["version"] == 2
    assert payload["created_by"] == "operator"
    assert payload["is_active"] is False


def test_create_strategy_config_endpoint_returns_409(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def conflict(store, environment, symbol, command):  # noqa: ANN001
        raise ConfigVersionConflictError("duplicate")

    monkeypatch.setattr(config_routes, "create_strategy_config", conflict)

    response = client.post("/configs/strategy", json={"version": 1})

    assert response.status_code == 409
    assert response.json() == {"detail": "duplicate"}


def test_create_strategy_config_endpoint_rejects_invalid_payload() -> None:
    response = _client().post("/configs/strategy", json={"version": 0})

    assert response.status_code == 422


def test_activate_strategy_config_endpoint_returns_404(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def missing(store, environment, symbol, config_id):  # noqa: ANN001
        raise ConfigNotFoundError("missing")

    monkeypatch.setattr(config_routes, "activate_strategy_config", missing)

    response = client.post(f"/configs/strategy/{uuid.uuid4()}/activate")

    assert response.status_code == 404
    assert response.json() == {"detail": "missing"}


def test_risk_configs_endpoint_lists_versions(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    config_id = uuid.uuid4()

    monkeypatch.setattr(
        config_routes,
        "list_risk_configs",
        lambda store, environment, symbol: [
            _risk_config(config_id=config_id, environment=environment, symbol=symbol)
        ],
    )

    response = client.get("/configs/risk")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configs"][0]["id"] == str(config_id)
    assert payload["configs"][0]["risk_per_trade_pct"] == "1"
    assert payload["configs"][0]["max_exposure_pct"] == "50"


def test_active_risk_config_endpoint_returns_active_version(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    config_id = uuid.uuid4()
    monkeypatch.setattr(
        config_routes,
        "get_active_risk_config",
        lambda store, environment, symbol: _risk_config(
            config_id=config_id,
            environment=environment,
            symbol=symbol,
            is_active=True,
        ),
    )

    response = client.get("/configs/risk/active")

    assert response.status_code == 200
    assert response.json()["id"] == str(config_id)
    assert response.json()["is_active"] is True


def test_create_risk_config_endpoint_returns_201(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def create(store, environment, symbol, command):  # noqa: ANN001
        assert command.version == 2
        assert command.risk_per_trade_pct == Decimal("1.5")
        return _risk_config(
            config_id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            version=command.version,
            risk_per_trade_pct=command.risk_per_trade_pct,
        )

    monkeypatch.setattr(config_routes, "create_risk_config", create)

    response = client.post(
        "/configs/risk",
        json={
            "version": 2,
            "risk_per_trade_pct": "1.5",
            "daily_loss_limit_pct": "2",
            "max_exposure_pct": "50",
        },
    )

    assert response.status_code == 201
    assert response.json()["version"] == 2
    assert response.json()["risk_per_trade_pct"] == "1.5"


def test_activate_risk_config_endpoint_returns_active_config(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    config_id = uuid.uuid4()

    def activate(store, environment, symbol, config_id):  # noqa: ANN001
        return _risk_config(
            config_id=config_id,
            environment=environment,
            symbol=symbol,
            is_active=True,
            activated_at=NOW,
        )

    monkeypatch.setattr(config_routes, "activate_risk_config", activate)

    response = client.post(f"/configs/risk/{config_id}/activate")

    assert response.status_code == 200
    assert response.json()["id"] == str(config_id)
    assert response.json()["is_active"] is True
    assert response.json()["activated_at"] == "2026-05-17T20:00:00Z"


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()
    return TestClient(app)


def _strategy_config(
    *,
    config_id: uuid.UUID,
    environment: str,
    symbol: str,
    version: int = 1,
    is_active: bool = False,
    created_by: str | None = "system",
    activated_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=config_id,
        environment=environment,
        version=version,
        name="breakout_trend_v1",
        symbol=symbol,
        signal_timeframe="1h",
        regime_timeframe_primary="4h",
        regime_timeframe_secondary="1d",
        parameters={"breakout_lookback": 20},
        is_active=is_active,
        created_by=created_by,
        activated_at=activated_at,
        created_at=None,
        updated_at=None,
    )


def _risk_config(
    *,
    config_id: uuid.UUID,
    environment: str,
    symbol: str,
    version: int = 1,
    is_active: bool = False,
    created_by: str | None = "system",
    activated_at: datetime | None = None,
    risk_per_trade_pct: Decimal = Decimal("1"),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=config_id,
        environment=environment,
        version=version,
        name="mvp_risk_v1",
        symbol=symbol,
        risk_per_trade_pct=risk_per_trade_pct,
        daily_loss_limit_pct=Decimal("2"),
        max_exposure_pct=Decimal("50"),
        parameters={"atr_stop_multiplier": "2"},
        is_active=is_active,
        created_by=created_by,
        activated_at=activated_at,
        created_at=None,
        updated_at=None,
    )
