from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.bot.control import (
    BOT_ACTION_EMERGENCY_STOP,
    BOT_ACTION_PAUSE,
    BOT_ACTION_RESUME,
    BotRuntimeStateConflictError,
    BotRuntimeStateNotFoundError,
    emergency_stop_bot,
    get_bot_status,
    pause_bot,
    resume_bot,
)
from app.db.models import BotRuntimeState

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_get_bot_status_returns_runtime_state() -> None:
    runtime = _runtime(status="running", trading_mode="paper")
    store = FakeBotControlStore(runtime)

    status = get_bot_status(store, environment="testnet")

    assert status.environment == "testnet"
    assert status.symbol == "BTCUSDT"
    assert status.status == "running"
    assert status.trading_mode == "paper"


def test_get_bot_status_raises_when_runtime_state_is_missing() -> None:
    store = FakeBotControlStore(None)

    with pytest.raises(BotRuntimeStateNotFoundError):
        get_bot_status(store, environment="testnet")


def test_pause_bot_updates_state_and_writes_audit_log() -> None:
    runtime = _runtime(status="running")
    store = FakeBotControlStore(runtime)

    status = pause_bot(store, environment="testnet", reason="manual pause", now=NOW)

    assert status.status == "paused"
    assert status.paused_at == NOW
    assert status.reason == "manual pause"
    assert store.commits == 1
    assert store.audit_logs[0]["action"] == BOT_ACTION_PAUSE
    assert store.audit_logs[0]["metadata_payload"] == {
        "previous_state": {
            "status": "running",
            "trading_mode": "testnet",
            "symbol": "BTCUSDT",
            "last_cycle_at": None,
            "paused_at": None,
            "emergency_stopped_at": None,
            "reason": None,
        },
        "new_state": {
            "status": "paused",
            "trading_mode": "testnet",
            "symbol": "BTCUSDT",
            "last_cycle_at": None,
            "paused_at": NOW.isoformat(),
            "emergency_stopped_at": None,
            "reason": "manual pause",
        },
        "reason": "manual pause",
    }


def test_resume_bot_updates_state_and_writes_audit_log() -> None:
    runtime = _runtime(status="paused", paused_at=NOW, pause_reason="manual pause")
    store = FakeBotControlStore(runtime)

    status = resume_bot(store, environment="testnet", reason="operator resume", now=NOW)

    assert status.status == "running"
    assert status.paused_at is None
    assert status.reason is None
    assert store.commits == 1
    assert store.audit_logs[0]["action"] == BOT_ACTION_RESUME
    assert store.audit_logs[0]["metadata_payload"]["reason"] == "operator resume"
    assert store.audit_logs[0]["metadata_payload"]["previous_state"]["status"] == "paused"
    assert store.audit_logs[0]["metadata_payload"]["new_state"]["status"] == "running"


def test_resume_bot_rejects_emergency_stop() -> None:
    runtime = _runtime(status="emergency_stop")
    store = FakeBotControlStore(runtime)

    with pytest.raises(BotRuntimeStateConflictError):
        resume_bot(store, environment="testnet", reason="unsafe", now=NOW)

    assert runtime.status == "emergency_stop"
    assert store.audit_logs == []
    assert store.commits == 0


def test_pause_bot_rejects_emergency_stop() -> None:
    runtime = _runtime(status="emergency_stop")
    store = FakeBotControlStore(runtime)

    with pytest.raises(BotRuntimeStateConflictError):
        pause_bot(store, environment="testnet", reason="unsafe", now=NOW)

    assert runtime.status == "emergency_stop"
    assert store.audit_logs == []
    assert store.commits == 0


def test_emergency_stop_bot_updates_state_and_writes_audit_log() -> None:
    runtime = _runtime(status="running")
    store = FakeBotControlStore(runtime)

    status = emergency_stop_bot(store, environment="testnet", reason="risk breach", now=NOW)

    assert status.status == "emergency_stop"
    assert status.emergency_stopped_at == NOW
    assert status.reason == "risk breach"
    assert store.commits == 1
    assert store.audit_logs[0]["action"] == BOT_ACTION_EMERGENCY_STOP
    assert store.audit_logs[0]["metadata_payload"]["new_state"]["status"] == "emergency_stop"


class FakeBotControlStore:
    def __init__(self, runtime: BotRuntimeState | None) -> None:
        self.runtime = runtime
        self.audit_logs: list[dict[str, object]] = []
        self.commits = 0

    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None:
        return self.runtime if self.runtime and self.runtime.environment == environment else None

    def save_audit_log(
        self,
        *,
        environment: str,
        action: str,
        entity_id: object,
        occurred_at: datetime,
        metadata_payload: dict[str, object],
    ) -> None:
        self.audit_logs.append(
            {
                "environment": environment,
                "action": action,
                "entity_id": entity_id,
                "occurred_at": occurred_at,
                "metadata_payload": metadata_payload,
            }
        )

    def commit(self) -> None:
        self.commits += 1


def _runtime(
    *,
    status: str,
    trading_mode: str = "testnet",
    paused_at: datetime | None = None,
    pause_reason: str | None = None,
) -> BotRuntimeState:
    return BotRuntimeState(
        id=uuid.uuid4(),
        environment="testnet",
        trading_mode=trading_mode,
        symbol="BTCUSDT",
        status=status,
        paused_at=paused_at,
        pause_reason=pause_reason,
        state_payload={},
    )
