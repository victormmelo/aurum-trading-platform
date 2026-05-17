from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes import bot as bot_routes
from app.bot.control import BotRuntimeStateConflictError, BotRuntimeStateNotFoundError, BotStatus
from app.db.session import get_db_session
from app.main import create_app

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_get_bot_status_endpoint(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    monkeypatch.setattr(
        bot_routes,
        "get_bot_status",
        lambda store, environment: _status(status="running", reason=None),
    )

    response = client.get("/bot/status")

    assert response.status_code == 200
    assert response.json() == {
        "environment": "testnet",
        "symbol": "BTCUSDT",
        "status": "running",
        "trading_mode": "testnet",
        "last_cycle_at": None,
        "paused_at": None,
        "emergency_stopped_at": None,
        "reason": None,
    }


def test_get_bot_status_endpoint_returns_404(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def missing_runtime(store, environment):  # noqa: ANN001
        raise BotRuntimeStateNotFoundError("missing")

    monkeypatch.setattr(bot_routes, "get_bot_status", missing_runtime)

    response = client.get("/bot/status")

    assert response.status_code == 404
    assert response.json() == {"detail": "missing"}


def test_pause_endpoint_returns_status(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def pause(store, environment, reason):  # noqa: ANN001
        assert reason == "manual pause"
        return _status(status="paused", paused_at=NOW, reason=reason)

    monkeypatch.setattr(bot_routes, "pause_bot", pause)

    response = client.post("/bot/pause", json={"reason": "manual pause"})

    assert response.status_code == 200
    assert response.json()["status"] == "paused"
    assert response.json()["paused_at"] == "2026-05-17T20:00:00Z"
    assert response.json()["reason"] == "manual pause"


def test_resume_endpoint_returns_409_for_emergency_stop(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def conflict(store, environment, reason):  # noqa: ANN001
        raise BotRuntimeStateConflictError("emergency stop")

    monkeypatch.setattr(bot_routes, "resume_bot", conflict)

    response = client.post("/bot/resume", json={"reason": "resume"})

    assert response.status_code == 409
    assert response.json() == {"detail": "emergency stop"}


def test_emergency_stop_endpoint_returns_status(monkeypatch) -> None:  # noqa: ANN001
    client = _client()

    def emergency_stop(store, environment, reason):  # noqa: ANN001
        assert reason == "risk breach"
        return _status(status="emergency_stop", emergency_stopped_at=NOW, reason=reason)

    monkeypatch.setattr(bot_routes, "emergency_stop_bot", emergency_stop)

    response = client.post("/bot/emergency-stop", json={"reason": "risk breach"})

    assert response.status_code == 200
    assert response.json()["status"] == "emergency_stop"
    assert response.json()["emergency_stopped_at"] == "2026-05-17T20:00:00Z"
    assert response.json()["reason"] == "risk breach"


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()
    return TestClient(app)


def _status(
    *,
    status: str,
    reason: str | None,
    paused_at: datetime | None = None,
    emergency_stopped_at: datetime | None = None,
) -> BotStatus:
    return BotStatus(
        environment="testnet",
        symbol="BTCUSDT",
        status=status,
        trading_mode="testnet",
        last_cycle_at=None,
        paused_at=paused_at,
        emergency_stopped_at=emergency_stopped_at,
        reason=reason,
    )
