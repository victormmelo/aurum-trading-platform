from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, RiskConfig, StrategyConfig

CONFIG_ACTION_CREATE = "config.create"
CONFIG_ACTION_ACTIVATE = "config.activate"


class ConfigNotFoundError(Exception):
    """Raised when a requested configuration version does not exist."""


class ConfigVersionConflictError(Exception):
    """Raised when a configuration version already exists."""


@dataclass(frozen=True)
class StrategyConfigCreate:
    version: int
    name: str
    signal_timeframe: str
    regime_timeframe_primary: str
    regime_timeframe_secondary: str
    parameters: dict
    created_by: str | None


@dataclass(frozen=True)
class RiskConfigCreate:
    version: int
    name: str
    risk_per_trade_pct: Decimal | None
    daily_loss_limit_pct: Decimal | None
    max_exposure_pct: Decimal | None
    parameters: dict
    created_by: str | None


class ConfigStore(Protocol):
    def list_strategy_configs(self, *, environment: str, symbol: str) -> list[StrategyConfig]: ...

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfig | None: ...

    def get_strategy_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> StrategyConfig | None: ...

    def get_strategy_config_by_version(
        self, *, environment: str, version: int
    ) -> StrategyConfig | None: ...

    def list_risk_configs(self, *, environment: str, symbol: str) -> list[RiskConfig]: ...

    def get_active_risk_config(self, *, environment: str, symbol: str) -> RiskConfig | None: ...

    def get_risk_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> RiskConfig | None: ...

    def get_risk_config_by_version(
        self, *, environment: str, version: int
    ) -> RiskConfig | None: ...

    def add_strategy_config(self, config: StrategyConfig) -> None: ...

    def add_risk_config(self, config: RiskConfig) -> None: ...

    def save_audit_log(
        self,
        *,
        environment: str,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        occurred_at: datetime,
        actor_id: str | None,
        metadata_payload: dict[str, object],
    ) -> None: ...

    def commit(self) -> None: ...


class SqlAlchemyConfigStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_strategy_configs(self, *, environment: str, symbol: str) -> list[StrategyConfig]:
        statement = (
            select(StrategyConfig)
            .where(StrategyConfig.environment == environment, StrategyConfig.symbol == symbol)
            .order_by(StrategyConfig.version.desc())
        )
        return list(self.session.scalars(statement))

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfig | None:
        statement = select(StrategyConfig).where(
            StrategyConfig.environment == environment,
            StrategyConfig.symbol == symbol,
            StrategyConfig.is_active.is_(True),
        )
        return self.session.scalars(statement).first()

    def get_strategy_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> StrategyConfig | None:
        statement = select(StrategyConfig).where(
            StrategyConfig.id == config_id,
            StrategyConfig.environment == environment,
            StrategyConfig.symbol == symbol,
        )
        return self.session.scalars(statement).first()

    def get_strategy_config_by_version(
        self, *, environment: str, version: int
    ) -> StrategyConfig | None:
        statement = select(StrategyConfig).where(
            StrategyConfig.environment == environment,
            StrategyConfig.version == version,
        )
        return self.session.scalars(statement).first()

    def list_risk_configs(self, *, environment: str, symbol: str) -> list[RiskConfig]:
        statement = (
            select(RiskConfig)
            .where(RiskConfig.environment == environment, RiskConfig.symbol == symbol)
            .order_by(RiskConfig.version.desc())
        )
        return list(self.session.scalars(statement))

    def get_active_risk_config(self, *, environment: str, symbol: str) -> RiskConfig | None:
        statement = select(RiskConfig).where(
            RiskConfig.environment == environment,
            RiskConfig.symbol == symbol,
            RiskConfig.is_active.is_(True),
        )
        return self.session.scalars(statement).first()

    def get_risk_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> RiskConfig | None:
        statement = select(RiskConfig).where(
            RiskConfig.id == config_id,
            RiskConfig.environment == environment,
            RiskConfig.symbol == symbol,
        )
        return self.session.scalars(statement).first()

    def get_risk_config_by_version(self, *, environment: str, version: int) -> RiskConfig | None:
        statement = select(RiskConfig).where(
            RiskConfig.environment == environment,
            RiskConfig.version == version,
        )
        return self.session.scalars(statement).first()

    def add_strategy_config(self, config: StrategyConfig) -> None:
        self.session.add(config)
        self.session.flush()

    def add_risk_config(self, config: RiskConfig) -> None:
        self.session.add(config)
        self.session.flush()

    def save_audit_log(
        self,
        *,
        environment: str,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        occurred_at: datetime,
        actor_id: str | None,
        metadata_payload: dict[str, object],
    ) -> None:
        self.session.add(
            AuditLog(
                environment=environment,
                actor_type="system",
                actor_id=actor_id or "system",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                occurred_at=occurred_at,
                metadata_payload=metadata_payload,
            )
        )

    def commit(self) -> None:
        self.session.commit()


def list_strategy_configs(
    store: ConfigStore, *, environment: str, symbol: str
) -> list[StrategyConfig]:
    return store.list_strategy_configs(environment=environment, symbol=symbol)


def get_active_strategy_config(
    store: ConfigStore, *, environment: str, symbol: str
) -> StrategyConfig | None:
    return store.get_active_strategy_config(environment=environment, symbol=symbol)


def create_strategy_config(
    store: ConfigStore,
    *,
    environment: str,
    symbol: str,
    command: StrategyConfigCreate,
    now: datetime | None = None,
) -> StrategyConfig:
    if store.get_strategy_config_by_version(environment=environment, version=command.version):
        raise ConfigVersionConflictError(
            f"Configuração de estratégia versão {command.version} já existe em {environment}"
        )

    occurred_at = now or datetime.now(UTC)
    config = StrategyConfig(
        id=uuid.uuid4(),
        environment=environment,
        version=command.version,
        name=command.name,
        symbol=symbol,
        signal_timeframe=command.signal_timeframe,
        regime_timeframe_primary=command.regime_timeframe_primary,
        regime_timeframe_secondary=command.regime_timeframe_secondary,
        parameters=command.parameters,
        is_active=False,
        created_by=command.created_by or "system",
    )
    store.add_strategy_config(config)
    _audit_config_change(
        store,
        environment=environment,
        action=CONFIG_ACTION_CREATE,
        entity_type="strategy_config",
        entity_id=config.id,
        occurred_at=occurred_at,
        actor_id=config.created_by,
        metadata_payload=_strategy_payload(config),
    )
    store.commit()
    return config


def activate_strategy_config(
    store: ConfigStore,
    *,
    environment: str,
    symbol: str,
    config_id: uuid.UUID,
    actor_id: str | None = "system",
    now: datetime | None = None,
) -> StrategyConfig:
    config = store.get_strategy_config_by_id(
        environment=environment, symbol=symbol, config_id=config_id
    )
    if config is None:
        raise ConfigNotFoundError(f"Configuração de estratégia {config_id} não encontrada")

    occurred_at = now or datetime.now(UTC)
    previous_active = store.get_active_strategy_config(environment=environment, symbol=symbol)
    previous_active_id = previous_active.id if previous_active is not None else None
    if previous_active is not None and previous_active.id != config.id:
        previous_active.is_active = False

    config.is_active = True
    config.activated_at = occurred_at
    _audit_config_change(
        store,
        environment=environment,
        action=CONFIG_ACTION_ACTIVATE,
        entity_type="strategy_config",
        entity_id=config.id,
        occurred_at=occurred_at,
        actor_id=actor_id,
        metadata_payload={
            "previous_active_id": str(previous_active_id) if previous_active_id else None,
            "new_active_id": str(config.id),
            "version": config.version,
            "symbol": config.symbol,
        },
    )
    store.commit()
    return config


def list_risk_configs(store: ConfigStore, *, environment: str, symbol: str) -> list[RiskConfig]:
    return store.list_risk_configs(environment=environment, symbol=symbol)


def get_active_risk_config(
    store: ConfigStore, *, environment: str, symbol: str
) -> RiskConfig | None:
    return store.get_active_risk_config(environment=environment, symbol=symbol)


def create_risk_config(
    store: ConfigStore,
    *,
    environment: str,
    symbol: str,
    command: RiskConfigCreate,
    now: datetime | None = None,
) -> RiskConfig:
    if store.get_risk_config_by_version(environment=environment, version=command.version):
        raise ConfigVersionConflictError(
            f"Configuração de risco versão {command.version} já existe em {environment}"
        )

    occurred_at = now or datetime.now(UTC)
    config = RiskConfig(
        id=uuid.uuid4(),
        environment=environment,
        version=command.version,
        name=command.name,
        symbol=symbol,
        risk_per_trade_pct=command.risk_per_trade_pct,
        daily_loss_limit_pct=command.daily_loss_limit_pct,
        max_exposure_pct=command.max_exposure_pct,
        parameters=command.parameters,
        is_active=False,
        created_by=command.created_by or "system",
    )
    store.add_risk_config(config)
    _audit_config_change(
        store,
        environment=environment,
        action=CONFIG_ACTION_CREATE,
        entity_type="risk_config",
        entity_id=config.id,
        occurred_at=occurred_at,
        actor_id=config.created_by,
        metadata_payload=_risk_payload(config),
    )
    store.commit()
    return config


def activate_risk_config(
    store: ConfigStore,
    *,
    environment: str,
    symbol: str,
    config_id: uuid.UUID,
    actor_id: str | None = "system",
    now: datetime | None = None,
) -> RiskConfig:
    config = store.get_risk_config_by_id(
        environment=environment, symbol=symbol, config_id=config_id
    )
    if config is None:
        raise ConfigNotFoundError(f"Configuração de risco {config_id} não encontrada")

    occurred_at = now or datetime.now(UTC)
    previous_active = store.get_active_risk_config(environment=environment, symbol=symbol)
    previous_active_id = previous_active.id if previous_active is not None else None
    if previous_active is not None and previous_active.id != config.id:
        previous_active.is_active = False

    config.is_active = True
    config.activated_at = occurred_at
    _audit_config_change(
        store,
        environment=environment,
        action=CONFIG_ACTION_ACTIVATE,
        entity_type="risk_config",
        entity_id=config.id,
        occurred_at=occurred_at,
        actor_id=actor_id,
        metadata_payload={
            "previous_active_id": str(previous_active_id) if previous_active_id else None,
            "new_active_id": str(config.id),
            "version": config.version,
            "symbol": config.symbol,
        },
    )
    store.commit()
    return config


def _audit_config_change(
    store: ConfigStore,
    *,
    environment: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    occurred_at: datetime,
    actor_id: str | None,
    metadata_payload: dict[str, object],
) -> None:
    store.save_audit_log(
        environment=environment,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        occurred_at=occurred_at,
        actor_id=actor_id,
        metadata_payload=metadata_payload,
    )


def _strategy_payload(config: StrategyConfig) -> dict[str, object]:
    return {
        "version": config.version,
        "name": config.name,
        "symbol": config.symbol,
        "signal_timeframe": config.signal_timeframe,
        "regime_timeframe_primary": config.regime_timeframe_primary,
        "regime_timeframe_secondary": config.regime_timeframe_secondary,
        "parameters": dict(config.parameters),
        "is_active": config.is_active,
    }


def _risk_payload(config: RiskConfig) -> dict[str, object]:
    return {
        "version": config.version,
        "name": config.name,
        "symbol": config.symbol,
        "risk_per_trade_pct": str(config.risk_per_trade_pct)
        if config.risk_per_trade_pct is not None
        else None,
        "daily_loss_limit_pct": str(config.daily_loss_limit_pct)
        if config.daily_loss_limit_pct is not None
        else None,
        "max_exposure_pct": str(config.max_exposure_pct)
        if config.max_exposure_pct is not None
        else None,
        "parameters": dict(config.parameters),
        "is_active": config.is_active,
    }
