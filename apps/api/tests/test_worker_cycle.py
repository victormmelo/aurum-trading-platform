from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.db.models import (
    BotRun,
    BotRuntimeState,
    DecisionLog,
    MarketSnapshot,
    PortfolioSnapshot,
    Position,
    RiskConfig,
    StrategyConfig,
)
from app.strategy.types import (
    IndicatorSnapshot,
    PositionSizingResult,
    RegimeResult,
    RiskResult,
    SignalResult,
    StrategyCandle,
)
from app.worker import cycle
from app.worker.cycle import run_dry_run_cycle

NOW = datetime(2026, 5, 17, 19, 0, tzinfo=UTC)


def test_worker_cycle_records_no_trade_when_bot_is_paused() -> None:
    store = FakeStore(runtime=BotRuntimeState(environment="testnet", status="paused"))

    result = run_dry_run_cycle(store, environment="testnet", symbol="BTCUSDT", now=NOW)

    assert result.status == "completed"
    assert result.decision == "NAO_OPERAR"
    assert len(store.runs) == 1
    assert len(store.decisions) == 1
    assert store.decisions[0].reason_payload["code"] == "bot_not_running"
    assert store.commits == 1


def test_worker_cycle_records_no_trade_without_active_configs() -> None:
    store = FakeStore(runtime=BotRuntimeState(environment="testnet", status="running"))

    result = run_dry_run_cycle(store, environment="testnet", symbol="BTCUSDT", now=NOW)

    assert result.status == "completed"
    assert result.decision == "NAO_OPERAR"
    assert store.decisions[0].reason_payload == {
        "code": "missing_active_config",
        "has_strategy_config": False,
        "has_risk_config": False,
    }


def test_worker_cycle_persists_buy_decision_in_dry_run(monkeypatch) -> None:  # noqa: ANN001
    store = FakeStore(
        runtime=BotRuntimeState(environment="testnet", status="running"),
        strategy_config=_strategy_config(),
        risk_config=_risk_config(),
        portfolio=_portfolio_snapshot(),
        candles_by_interval={"1h": [_candle()], "4h": [_candle()]},
    )

    monkeypatch.setattr(cycle, "compute_indicator_snapshot", lambda candles: _snapshot())
    monkeypatch.setattr(
        cycle,
        "evaluate_regime",
        lambda snapshot: RegimeResult(True, "Regime permitido", {"code": "regime_allowed"}),
    )
    monkeypatch.setattr(
        cycle,
        "evaluate_breakout_entry_signal",
        lambda snapshot, regime: SignalResult(
            "COMPRA",
            "Breakout confirmado",
            {"code": "breakout_entry"},
        ),
    )
    monkeypatch.setattr(
        cycle,
        "calculate_position_size",
        lambda sizing_input, config: PositionSizingResult(
            quantity=Decimal("0.05"),
            notional=Decimal("500"),
            reason="Sizing calculado",
            reason_payload={"code": "position_size_calculated"},
        ),
    )
    monkeypatch.setattr(
        cycle,
        "evaluate_risk",
        lambda candidate, state, config: RiskResult(
            True,
            candidate.decision,
            "Risco permite nova compra",
            {"code": "risk_allowed"},
        ),
    )

    result = run_dry_run_cycle(store, environment="testnet", symbol="BTCUSDT", now=NOW)

    assert result.status == "completed"
    assert result.decision == "COMPRA"
    assert len(store.market_snapshots) == 1
    assert len(store.decisions) == 1
    assert store.runs[0].strategy_config_id == store.strategy_config.id
    assert store.runs[0].risk_config_id == store.risk_config.id
    decision = store.decisions[0]
    assert decision.indicators["signal"]["rsi"] == "60"
    assert decision.intended_order == {
        "mode": "dry_run",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.05",
        "quote_quantity": "500",
    }
    assert decision.execution_result["status"] == "not_sent"
    assert decision.market_snapshot_id == store.market_snapshots[0].id


def test_worker_cycle_marks_run_failed_when_cycle_raises() -> None:
    store = FakeStore(runtime_error=RuntimeError("boom"))

    result = run_dry_run_cycle(store, environment="testnet", symbol="BTCUSDT", now=NOW)

    assert result.status == "failed"
    assert result.decision is None
    assert store.runs[0].status == "failed"
    assert store.runs[0].error_message == "boom"
    assert store.decisions == []
    assert store.commits == 1


class FakeStore:
    def __init__(
        self,
        *,
        runtime: BotRuntimeState | None = None,
        strategy_config: StrategyConfig | None = None,
        risk_config: RiskConfig | None = None,
        portfolio: PortfolioSnapshot | None = None,
        position: Position | None = None,
        candles_by_interval: dict[str, list[StrategyCandle]] | None = None,
        runtime_error: Exception | None = None,
    ) -> None:
        self.runtime = runtime
        self.strategy_config = strategy_config
        self.risk_config = risk_config
        self.portfolio = portfolio
        self.position = position
        self.candles_by_interval = candles_by_interval or {}
        self.runtime_error = runtime_error
        self.runs: list[BotRun] = []
        self.decisions: list[DecisionLog] = []
        self.market_snapshots: list[MarketSnapshot] = []
        self.commits = 0

    def begin_run(self, *, environment: str, symbol: str, started_at: datetime) -> BotRun:
        run = BotRun(
            id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            started_at=started_at,
            status="started",
        )
        self.runs.append(run)
        return run

    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None:
        if self.runtime_error is not None:
            raise self.runtime_error
        return self.runtime

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfig | None:
        return self.strategy_config

    def get_active_risk_config(self, *, environment: str, symbol: str) -> RiskConfig | None:
        return self.risk_config

    def get_recent_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[StrategyCandle]:
        return self.candles_by_interval.get(interval, [])

    def get_latest_portfolio_snapshot(
        self, *, environment: str, symbol: str
    ) -> PortfolioSnapshot | None:
        return self.portfolio

    def get_open_position(self, *, environment: str, symbol: str) -> Position | None:
        return self.position

    def save_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        captured_at: datetime,
        snapshot: IndicatorSnapshot,
    ) -> MarketSnapshot:
        market_snapshot = MarketSnapshot(
            id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            captured_at=captured_at,
            last_price=snapshot.close_price,
            indicators={},
            source_payload={},
        )
        self.market_snapshots.append(market_snapshot)
        return market_snapshot

    def save_decision(
        self,
        *,
        bot_run: BotRun,
        environment: str,
        symbol: str,
        decided_at: datetime,
        decision: str,
        reason: str,
        reason_payload: dict[str, object],
        indicators: dict[str, object],
        intended_order: dict[str, object],
        execution_result: dict[str, object],
        portfolio_state: dict[str, object],
        strategy_config: StrategyConfig | None,
        risk_config: RiskConfig | None,
        market_snapshot: MarketSnapshot | None,
    ) -> DecisionLog:
        decision_log = DecisionLog(
            id=uuid.uuid4(),
            environment=environment,
            symbol=symbol,
            bot_run_id=bot_run.id,
            strategy_config_id=strategy_config.id if strategy_config is not None else None,
            risk_config_id=risk_config.id if risk_config is not None else None,
            market_snapshot_id=market_snapshot.id if market_snapshot is not None else None,
            decided_at=decided_at,
            decision=decision,
            reason=reason,
            reason_payload=reason_payload,
            indicators=indicators,
            intended_order=intended_order,
            execution_result=execution_result,
            portfolio_state=portfolio_state,
        )
        self.decisions.append(decision_log)
        return decision_log

    def complete_run(self, bot_run: BotRun, *, finished_at: datetime) -> None:
        bot_run.finished_at = finished_at
        bot_run.status = "completed"

    def fail_run(self, bot_run: BotRun, *, finished_at: datetime, error: str) -> None:
        bot_run.finished_at = finished_at
        bot_run.status = "failed"
        bot_run.error_message = error

    def commit(self) -> None:
        self.commits += 1


def _strategy_config() -> StrategyConfig:
    return StrategyConfig(
        id=uuid.uuid4(),
        environment="testnet",
        version=1,
        symbol="BTCUSDT",
        signal_timeframe="1h",
        regime_timeframe_primary="4h",
        regime_timeframe_secondary="1d",
        parameters={},
        is_active=True,
    )


def _risk_config() -> RiskConfig:
    return RiskConfig(
        id=uuid.uuid4(),
        environment="testnet",
        version=1,
        symbol="BTCUSDT",
        risk_per_trade_pct=Decimal("1"),
        daily_loss_limit_pct=Decimal("2"),
        max_exposure_pct=Decimal("50"),
        parameters={},
        is_active=True,
    )


def _portfolio_snapshot() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        id=uuid.uuid4(),
        environment="testnet",
        captured_at=NOW,
        symbol="BTCUSDT",
        usdt_balance=Decimal("10000"),
        btc_balance=Decimal("0"),
        btc_market_price=Decimal("100000"),
        btc_market_value=Decimal("0"),
        invested_value=Decimal("0"),
        average_cost=Decimal("0"),
        total_equity=Decimal("10000"),
        exposure_pct=Decimal("0"),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        total_fees_usdt=Decimal("0"),
        source_payload={},
    )


def _snapshot() -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=Decimal("100000"),
        current_volume=Decimal("20"),
        sma_50=Decimal("95000"),
        sma_200=Decimal("90000"),
        rsi=Decimal("60"),
        atr=Decimal("1000"),
        atr_pct=Decimal("1"),
        average_volume=Decimal("10"),
        breakout_high_20=Decimal("99000"),
    )


def _candle() -> StrategyCandle:
    return StrategyCandle(
        open_time=NOW - timedelta(hours=1),
        close_time=NOW,
        open_price=Decimal("99000"),
        high_price=Decimal("100000"),
        low_price=Decimal("98000"),
        close_price=Decimal("100000"),
        volume=Decimal("20"),
    )
