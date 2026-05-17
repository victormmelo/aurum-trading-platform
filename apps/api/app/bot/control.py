from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, BotRuntimeState

BOT_ACTION_PAUSE = "bot.pause"
BOT_ACTION_RESUME = "bot.resume"
BOT_ACTION_EMERGENCY_STOP = "bot.emergency_stop"


class BotRuntimeStateNotFoundError(Exception):
    """Raised when no runtime state exists for the requested environment."""


class BotRuntimeStateConflictError(Exception):
    """Raised when a requested state transition is not allowed."""


@dataclass(frozen=True)
class BotStatus:
    environment: str
    symbol: str
    status: str
    trading_mode: str
    last_cycle_at: datetime | None
    paused_at: datetime | None
    emergency_stopped_at: datetime | None
    reason: str | None


class BotControlStore(Protocol):
    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None: ...

    def save_audit_log(
        self,
        *,
        environment: str,
        action: str,
        entity_id: object,
        occurred_at: datetime,
        metadata_payload: dict[str, object],
    ) -> None: ...

    def commit(self) -> None: ...


class SqlAlchemyBotControlStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None:
        statement = select(BotRuntimeState).where(BotRuntimeState.environment == environment)
        return self.session.scalars(statement).first()

    def save_audit_log(
        self,
        *,
        environment: str,
        action: str,
        entity_id: object,
        occurred_at: datetime,
        metadata_payload: dict[str, object],
    ) -> None:
        self.session.add(
            AuditLog(
                environment=environment,
                actor_type="system",
                actor_id="system",
                action=action,
                entity_type="bot_runtime_state",
                entity_id=entity_id,
                occurred_at=occurred_at,
                metadata_payload=metadata_payload,
            )
        )

    def commit(self) -> None:
        self.session.commit()


def get_bot_status(store: BotControlStore, *, environment: str) -> BotStatus:
    runtime = _require_runtime(store, environment=environment)
    return _to_status(runtime)


def pause_bot(
    store: BotControlStore,
    *,
    environment: str,
    reason: str | None = None,
    now: datetime | None = None,
) -> BotStatus:
    runtime = _require_runtime(store, environment=environment)
    if runtime.status == "emergency_stop":
        raise BotRuntimeStateConflictError("Robô em parada de emergência não pode ser pausado")

    occurred_at = now or datetime.now(UTC)
    previous = _state_payload(runtime)

    runtime.status = "paused"
    runtime.paused_at = occurred_at
    runtime.pause_reason = reason

    _audit_transition(
        store,
        runtime=runtime,
        action=BOT_ACTION_PAUSE,
        occurred_at=occurred_at,
        previous=previous,
        reason=reason,
    )
    store.commit()
    return _to_status(runtime)


def resume_bot(
    store: BotControlStore,
    *,
    environment: str,
    reason: str | None = None,
    now: datetime | None = None,
) -> BotStatus:
    runtime = _require_runtime(store, environment=environment)
    if runtime.status == "emergency_stop":
        raise BotRuntimeStateConflictError("Robô em parada de emergência não pode ser retomado")

    occurred_at = now or datetime.now(UTC)
    previous = _state_payload(runtime)

    runtime.status = "running"
    runtime.paused_at = None
    runtime.pause_reason = None

    _audit_transition(
        store,
        runtime=runtime,
        action=BOT_ACTION_RESUME,
        occurred_at=occurred_at,
        previous=previous,
        reason=reason,
    )
    store.commit()
    return _to_status(runtime)


def emergency_stop_bot(
    store: BotControlStore,
    *,
    environment: str,
    reason: str | None = None,
    now: datetime | None = None,
) -> BotStatus:
    runtime = _require_runtime(store, environment=environment)
    occurred_at = now or datetime.now(UTC)
    previous = _state_payload(runtime)

    runtime.status = "emergency_stop"
    runtime.emergency_stopped_at = occurred_at
    runtime.pause_reason = reason

    _audit_transition(
        store,
        runtime=runtime,
        action=BOT_ACTION_EMERGENCY_STOP,
        occurred_at=occurred_at,
        previous=previous,
        reason=reason,
    )
    store.commit()
    return _to_status(runtime)


def _require_runtime(store: BotControlStore, *, environment: str) -> BotRuntimeState:
    runtime = store.get_runtime_state(environment=environment)
    if runtime is None:
        raise BotRuntimeStateNotFoundError(
            f"Estado operacional do robô não encontrado para ambiente {environment}"
        )
    return runtime


def _audit_transition(
    store: BotControlStore,
    *,
    runtime: BotRuntimeState,
    action: str,
    occurred_at: datetime,
    previous: Mapping[str, object],
    reason: str | None,
) -> None:
    store.save_audit_log(
        environment=runtime.environment,
        action=action,
        entity_id=runtime.id,
        occurred_at=occurred_at,
        metadata_payload={
            "previous_state": dict(previous),
            "new_state": _state_payload(runtime),
            "reason": reason,
        },
    )


def _state_payload(runtime: BotRuntimeState) -> dict[str, object]:
    return {
        "status": runtime.status,
        "trading_mode": runtime.trading_mode,
        "symbol": runtime.symbol,
        "last_cycle_at": runtime.last_cycle_at.isoformat()
        if runtime.last_cycle_at is not None
        else None,
        "paused_at": runtime.paused_at.isoformat() if runtime.paused_at is not None else None,
        "emergency_stopped_at": runtime.emergency_stopped_at.isoformat()
        if runtime.emergency_stopped_at is not None
        else None,
        "reason": runtime.pause_reason,
    }


def _to_status(runtime: BotRuntimeState) -> BotStatus:
    return BotStatus(
        environment=runtime.environment,
        symbol=runtime.symbol,
        status=runtime.status,
        trading_mode=runtime.trading_mode,
        last_cycle_at=runtime.last_cycle_at,
        paused_at=runtime.paused_at,
        emergency_stopped_at=runtime.emergency_stopped_at,
        reason=runtime.pause_reason,
    )
