from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.configuration.control import (
    CONFIG_ACTION_ACTIVATE,
    CONFIG_ACTION_CREATE,
    ConfigNotFoundError,
    ConfigVersionConflictError,
    RiskConfigCreate,
    StrategyConfigCreate,
    activate_risk_config,
    activate_strategy_config,
    create_risk_config,
    create_strategy_config,
)
from app.db.models import RiskConfig, StrategyConfig

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_create_strategy_config_creates_inactive_version_and_audit_log() -> None:
    store = FakeConfigStore()

    config = create_strategy_config(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        command=_strategy_create(version=2),
        now=NOW,
    )

    assert config.version == 2
    assert config.is_active is False
    assert store.strategy_configs == [config]
    assert store.audit_logs[0]["action"] == CONFIG_ACTION_CREATE
    assert store.audit_logs[0]["entity_type"] == "strategy_config"
    assert store.audit_logs[0]["metadata_payload"]["version"] == 2
    assert store.commits == 1


def test_create_strategy_config_rejects_duplicate_environment_version() -> None:
    store = FakeConfigStore(strategy_configs=[_strategy_config(version=1)])

    with pytest.raises(ConfigVersionConflictError):
        create_strategy_config(
            store,
            environment="testnet",
            symbol="BTCUSDT",
            command=_strategy_create(version=1),
            now=NOW,
        )

    assert store.audit_logs == []
    assert store.commits == 0


def test_activate_strategy_config_keeps_only_one_active_version() -> None:
    active = _strategy_config(version=1, is_active=True)
    target = _strategy_config(version=2)
    store = FakeConfigStore(strategy_configs=[active, target])

    result = activate_strategy_config(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        config_id=target.id,
        now=NOW,
    )

    assert result == target
    assert active.is_active is False
    assert target.is_active is True
    assert target.activated_at == NOW
    assert store.audit_logs[0]["action"] == CONFIG_ACTION_ACTIVATE
    assert store.audit_logs[0]["metadata_payload"]["previous_active_id"] == str(active.id)
    assert store.audit_logs[0]["metadata_payload"]["new_active_id"] == str(target.id)
    assert store.commits == 1


def test_activate_strategy_config_raises_when_missing() -> None:
    store = FakeConfigStore()

    with pytest.raises(ConfigNotFoundError):
        activate_strategy_config(
            store,
            environment="testnet",
            symbol="BTCUSDT",
            config_id=uuid.uuid4(),
            now=NOW,
        )

    assert store.audit_logs == []
    assert store.commits == 0


def test_create_and_activate_risk_config() -> None:
    store = FakeConfigStore()
    created = create_risk_config(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        command=_risk_create(version=1),
        now=NOW,
    )

    activated = activate_risk_config(
        store,
        environment="testnet",
        symbol="BTCUSDT",
        config_id=created.id,
        now=NOW,
    )

    assert activated.is_active is True
    assert activated.activated_at == NOW
    assert store.audit_logs[0]["entity_type"] == "risk_config"
    assert store.audit_logs[1]["action"] == CONFIG_ACTION_ACTIVATE
    assert store.commits == 2


class FakeConfigStore:
    def __init__(
        self,
        *,
        strategy_configs: list[StrategyConfig] | None = None,
        risk_configs: list[RiskConfig] | None = None,
    ) -> None:
        self.strategy_configs = strategy_configs or []
        self.risk_configs = risk_configs or []
        self.audit_logs: list[dict[str, object]] = []
        self.commits = 0

    def list_strategy_configs(self, *, environment: str, symbol: str) -> list[StrategyConfig]:
        return [
            config
            for config in self.strategy_configs
            if config.environment == environment and config.symbol == symbol
        ]

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfig | None:
        return next(
            (
                config
                for config in self.strategy_configs
                if config.environment == environment
                and config.symbol == symbol
                and config.is_active
            ),
            None,
        )

    def get_strategy_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> StrategyConfig | None:
        return next(
            (
                config
                for config in self.strategy_configs
                if config.id == config_id
                and config.environment == environment
                and config.symbol == symbol
            ),
            None,
        )

    def get_strategy_config_by_version(
        self, *, environment: str, version: int
    ) -> StrategyConfig | None:
        return next(
            (
                config
                for config in self.strategy_configs
                if config.environment == environment and config.version == version
            ),
            None,
        )

    def list_risk_configs(self, *, environment: str, symbol: str) -> list[RiskConfig]:
        return [
            config
            for config in self.risk_configs
            if config.environment == environment and config.symbol == symbol
        ]

    def get_active_risk_config(self, *, environment: str, symbol: str) -> RiskConfig | None:
        return next(
            (
                config
                for config in self.risk_configs
                if config.environment == environment
                and config.symbol == symbol
                and config.is_active
            ),
            None,
        )

    def get_risk_config_by_id(
        self, *, environment: str, symbol: str, config_id: uuid.UUID
    ) -> RiskConfig | None:
        return next(
            (
                config
                for config in self.risk_configs
                if config.id == config_id
                and config.environment == environment
                and config.symbol == symbol
            ),
            None,
        )

    def get_risk_config_by_version(self, *, environment: str, version: int) -> RiskConfig | None:
        return next(
            (
                config
                for config in self.risk_configs
                if config.environment == environment and config.version == version
            ),
            None,
        )

    def add_strategy_config(self, config: StrategyConfig) -> None:
        self.strategy_configs.append(config)

    def add_risk_config(self, config: RiskConfig) -> None:
        self.risk_configs.append(config)

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
        self.audit_logs.append(
            {
                "environment": environment,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "occurred_at": occurred_at,
                "actor_id": actor_id,
                "metadata_payload": metadata_payload,
            }
        )

    def commit(self) -> None:
        self.commits += 1


def _strategy_create(*, version: int) -> StrategyConfigCreate:
    return StrategyConfigCreate(
        version=version,
        name="breakout_trend_v1",
        signal_timeframe="1h",
        regime_timeframe_primary="4h",
        regime_timeframe_secondary="1d",
        parameters={"breakout_lookback": 20},
        created_by="operator",
    )


def _risk_create(*, version: int) -> RiskConfigCreate:
    return RiskConfigCreate(
        version=version,
        name="mvp_risk_v1",
        risk_per_trade_pct=Decimal("1"),
        daily_loss_limit_pct=Decimal("2"),
        max_exposure_pct=Decimal("50"),
        parameters={"atr_stop_multiplier": "2"},
        created_by="operator",
    )


def _strategy_config(*, version: int, is_active: bool = False) -> StrategyConfig:
    return StrategyConfig(
        id=uuid.uuid4(),
        environment="testnet",
        version=version,
        name="breakout_trend_v1",
        symbol="BTCUSDT",
        signal_timeframe="1h",
        regime_timeframe_primary="4h",
        regime_timeframe_secondary="1d",
        parameters={},
        is_active=is_active,
        created_by="operator",
    )


def _risk_config(*, version: int, is_active: bool = False) -> RiskConfig:
    return RiskConfig(
        id=uuid.uuid4(),
        environment="testnet",
        version=version,
        name="mvp_risk_v1",
        symbol="BTCUSDT",
        risk_per_trade_pct=Decimal("1"),
        daily_loss_limit_pct=Decimal("2"),
        max_exposure_pct=Decimal("50"),
        parameters={},
        is_active=is_active,
        created_by="operator",
    )
