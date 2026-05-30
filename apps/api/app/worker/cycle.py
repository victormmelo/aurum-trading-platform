from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    BotRun,
    BotRuntimeState,
    DecisionLog,
    MarketCandle,
    MarketSnapshot,
    PortfolioSnapshot,
    Position,
)
from app.db.models import (
    RiskConfig as RiskConfigModel,
)
from app.db.models import (
    StrategyConfig as StrategyConfigModel,
)
from app.execution.factory import execution_adapter_for_mode
from app.execution.service import OrderCommand, OrderService, OrderValidationError
from app.strategy.exits import evaluate_exit_signal
from app.strategy.indicators import compute_indicator_snapshot
from app.strategy.regime import evaluate_regime
from app.strategy.risk import evaluate_risk
from app.strategy.signals import BUY, NO_TRADE, SELL, evaluate_breakout_entry_signal
from app.strategy.sizing import calculate_position_size
from app.strategy.types import (
    ExitPositionState,
    IndicatorSnapshot,
    PositionSizingInput,
    PositionSizingResult,
    RiskConfig,
    RiskResult,
    RiskState,
    SignalResult,
    StrategyCandle,
)

DEFAULT_CANDLE_LIMIT = 250


@dataclass(frozen=True)
class CycleResult:
    bot_run_id: uuid.UUID | None
    decision_id: uuid.UUID | None
    status: str
    decision: str | None
    reason: str


class CycleStore(Protocol):
    def begin_run(self, *, environment: str, symbol: str, started_at: datetime) -> BotRun: ...

    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None: ...

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfigModel | None: ...

    def get_active_risk_config(
        self, *, environment: str, symbol: str
    ) -> RiskConfigModel | None: ...

    def get_recent_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[StrategyCandle]: ...

    def get_latest_portfolio_snapshot(
        self, *, environment: str, symbol: str
    ) -> PortfolioSnapshot | None: ...

    def get_open_position(self, *, environment: str, symbol: str) -> Position | None: ...

    def save_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        captured_at: datetime,
        snapshot: IndicatorSnapshot,
    ) -> MarketSnapshot: ...

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
        strategy_config: StrategyConfigModel | None,
        risk_config: RiskConfigModel | None,
        market_snapshot: MarketSnapshot | None,
    ) -> DecisionLog: ...

    def complete_run(self, bot_run: BotRun, *, finished_at: datetime) -> None: ...

    def fail_run(self, bot_run: BotRun, *, finished_at: datetime, error: str) -> None: ...

    def commit(self) -> None: ...


class SqlAlchemyCycleStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def begin_run(self, *, environment: str, symbol: str, started_at: datetime) -> BotRun:
        bot_run = BotRun(
            environment=environment,
            symbol=symbol,
            started_at=started_at,
            status="started",
            run_payload={"execution_mode": "dry_run"},
        )
        self.session.add(bot_run)
        self.session.flush()
        return bot_run

    def get_runtime_state(self, *, environment: str) -> BotRuntimeState | None:
        statement = select(BotRuntimeState).where(BotRuntimeState.environment == environment)
        return self.session.scalars(statement).first()

    def get_active_strategy_config(
        self, *, environment: str, symbol: str
    ) -> StrategyConfigModel | None:
        statement = select(StrategyConfigModel).where(
            StrategyConfigModel.environment == environment,
            StrategyConfigModel.symbol == symbol,
            StrategyConfigModel.is_active.is_(True),
        )
        return self.session.scalars(statement).first()

    def get_active_risk_config(self, *, environment: str, symbol: str) -> RiskConfigModel | None:
        statement = select(RiskConfigModel).where(
            RiskConfigModel.environment == environment,
            RiskConfigModel.symbol == symbol,
            RiskConfigModel.is_active.is_(True),
        )
        return self.session.scalars(statement).first()

    def get_recent_candles(
        self, *, environment: str, symbol: str, interval: str, limit: int
    ) -> list[StrategyCandle]:
        statement = (
            select(MarketCandle)
            .where(
                MarketCandle.environment == environment,
                MarketCandle.symbol == symbol,
                MarketCandle.interval == interval,
            )
            .order_by(MarketCandle.open_time.desc())
            .limit(limit)
        )
        candles = list(self.session.scalars(statement))
        return [_to_strategy_candle(candle) for candle in reversed(candles)]

    def get_latest_portfolio_snapshot(
        self, *, environment: str, symbol: str
    ) -> PortfolioSnapshot | None:
        statement = (
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.environment == environment,
                PortfolioSnapshot.symbol == symbol,
            )
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(1)
        )
        return self.session.scalars(statement).first()

    def get_open_position(self, *, environment: str, symbol: str) -> Position | None:
        statement = select(Position).where(
            Position.environment == environment,
            Position.symbol == symbol,
            Position.asset == "BTC",
            Position.side == "LONG",
            Position.quantity > 0,
        )
        return self.session.scalars(statement).first()

    def save_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        captured_at: datetime,
        snapshot: IndicatorSnapshot,
    ) -> MarketSnapshot:
        market_snapshot = MarketSnapshot(
            environment=environment,
            exchange="binance",
            symbol=symbol,
            captured_at=captured_at,
            last_price=snapshot.close_price,
            volatility_pct=snapshot.atr_pct,
            indicators=_snapshot_payload(snapshot),
            source_payload={"source": "worker_dry_run"},
        )
        self.session.add(market_snapshot)
        self.session.flush()
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
        strategy_config: StrategyConfigModel | None,
        risk_config: RiskConfigModel | None,
        market_snapshot: MarketSnapshot | None,
    ) -> DecisionLog:
        decision_log = DecisionLog(
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
        self.session.add(decision_log)
        self.session.flush()
        return decision_log

    def complete_run(self, bot_run: BotRun, *, finished_at: datetime) -> None:
        bot_run.finished_at = finished_at
        bot_run.status = "completed"

    def fail_run(self, bot_run: BotRun, *, finished_at: datetime, error: str) -> None:
        bot_run.finished_at = finished_at
        bot_run.status = "failed"
        bot_run.error_message = error

    def commit(self) -> None:
        self.session.commit()


def run_worker_cycle(
    session: Session,
    *,
    environment: str = "testnet",
    symbol: str = "BTCUSDT",
    now: datetime | None = None,
) -> CycleResult:
    from app.core.config import get_settings

    settings = get_settings()
    runtime = SqlAlchemyCycleStore(session).get_runtime_state(environment=environment)
    order_service = None
    if runtime is not None and runtime.trading_mode in {"testnet", "mainnet"}:
        order_service = OrderService(
            session=session,
            adapter=execution_adapter_for_mode(settings, runtime.trading_mode),
            expected_environment=settings.aurum_environment,
            expected_symbol=settings.trading_symbol,
            stale_after_seconds=settings.market_stale_after_seconds,
        )
    return run_dry_run_cycle(
        SqlAlchemyCycleStore(session),
        environment=environment,
        symbol=symbol,
        now=now,
        order_service=order_service,
    )


def run_dry_run_cycle(
    store: CycleStore,
    *,
    environment: str,
    symbol: str,
    now: datetime | None = None,
    order_service: OrderService | None = None,
) -> CycleResult:
    started_at = now or datetime.now(UTC)
    bot_run = store.begin_run(environment=environment, symbol=symbol, started_at=started_at)

    try:
        decision_context = _decide(
            store,
            environment=environment,
            symbol=symbol,
            decided_at=started_at,
        )
        runtime = decision_context.pop("runtime_state")
        trading_mode = _trading_mode(runtime)
        bot_run.run_payload = {
            **(bot_run.run_payload or {}),
            "execution_mode": "dry_run",
            "trading_mode": trading_mode,
        }
        strategy_config = decision_context.get("strategy_config")
        risk_config = decision_context.get("risk_config")
        if isinstance(strategy_config, StrategyConfigModel):
            bot_run.strategy_config_id = strategy_config.id
        if isinstance(risk_config, RiskConfigModel):
            bot_run.risk_config_id = risk_config.id

        decision_log = store.save_decision(bot_run=bot_run, **decision_context)
        if order_service is not None:
            _execute_decision_order(
                order_service,
                bot_run=bot_run,
                decision_log=decision_log,
                trading_mode=trading_mode,
                now=started_at,
            )
        finished_at = now or datetime.now(UTC)
        store.complete_run(bot_run, finished_at=finished_at)

        if isinstance(runtime, BotRuntimeState):
            runtime.last_cycle_at = finished_at

        store.commit()
        return CycleResult(
            bot_run_id=bot_run.id,
            decision_id=decision_log.id,
            status=bot_run.status,
            decision=decision_log.decision,
            reason=decision_log.reason,
        )
    except Exception as exc:  # noqa: BLE001
        finished_at = now or datetime.now(UTC)
        store.fail_run(bot_run, finished_at=finished_at, error=str(exc))
        store.commit()
        return CycleResult(
            bot_run_id=bot_run.id,
            decision_id=None,
            status=bot_run.status,
            decision=None,
            reason=str(exc),
        )


def _decide(
    store: CycleStore,
    *,
    environment: str,
    symbol: str,
    decided_at: datetime,
) -> dict[str, object]:
    runtime = store.get_runtime_state(environment=environment)
    strategy_config = store.get_active_strategy_config(environment=environment, symbol=symbol)
    risk_config = store.get_active_risk_config(environment=environment, symbol=symbol)
    portfolio = store.get_latest_portfolio_snapshot(environment=environment, symbol=symbol)
    position = store.get_open_position(environment=environment, symbol=symbol)

    base_context: dict[str, object] = {
        "environment": environment,
        "symbol": symbol,
        "decided_at": decided_at,
        "strategy_config": strategy_config,
        "risk_config": risk_config,
        "market_snapshot": None,
        "portfolio_state": _portfolio_payload(portfolio, position),
        "runtime_state": runtime,
    }

    if runtime is None:
        return {
            **base_context,
            **_decision_payload(
                decision=NO_TRADE,
                reason="Estado operacional do robô não encontrado",
                reason_payload={"code": "missing_runtime_state"},
                trading_mode=_trading_mode(runtime),
            ),
        }

    if runtime.status != "running":
        return {
            **base_context,
            **_decision_payload(
                decision=NO_TRADE,
                reason="Robô pausado ou em parada de emergência",
                reason_payload={"code": "bot_not_running", "bot_status": runtime.status},
                trading_mode=_trading_mode(runtime),
            ),
        }

    if strategy_config is None or risk_config is None:
        return {
            **base_context,
            **_decision_payload(
                decision=NO_TRADE,
                reason="Configuração ativa de estratégia ou risco não encontrada",
                reason_payload={
                    "code": "missing_active_config",
                    "has_strategy_config": strategy_config is not None,
                    "has_risk_config": risk_config is not None,
                },
                trading_mode=_trading_mode(runtime),
            ),
        }

    signal_candles = store.get_recent_candles(
        environment=environment,
        symbol=symbol,
        interval=strategy_config.signal_timeframe,
        limit=DEFAULT_CANDLE_LIMIT,
    )
    regime_candles = store.get_recent_candles(
        environment=environment,
        symbol=symbol,
        interval=strategy_config.regime_timeframe_primary,
        limit=DEFAULT_CANDLE_LIMIT,
    )
    signal_snapshot = compute_indicator_snapshot(signal_candles)
    regime_snapshot = compute_indicator_snapshot(regime_candles)
    market_snapshot = (
        store.save_market_snapshot(
            environment=environment,
            symbol=symbol,
            captured_at=decided_at,
            snapshot=signal_snapshot,
        )
        if signal_snapshot is not None
        else None
    )

    indicators = {
        "signal": _snapshot_payload(signal_snapshot),
        "regime": _snapshot_payload(regime_snapshot),
    }
    base_context = {**base_context, "market_snapshot": market_snapshot, "indicators": indicators}

    candidate = _candidate_decision(signal_snapshot, regime_snapshot, position, signal_candles)
    final = _apply_sizing_and_risk(
        candidate,
        runtime=runtime,
        risk_config_model=risk_config,
        portfolio=portfolio,
        position=position,
        signal_snapshot=signal_snapshot,
        trading_mode=_trading_mode(runtime),
    )

    return {
        **base_context,
        **_decision_payload(
            decision=final["decision"],
            reason=final["reason"],
            reason_payload=final["reason_payload"],
            indicators=indicators,
            intended_order=final["intended_order"],
            execution_result=final["execution_result"],
            trading_mode=_trading_mode(runtime),
        ),
    }


def _candidate_decision(
    signal_snapshot: IndicatorSnapshot | None,
    regime_snapshot: IndicatorSnapshot | None,
    position: Position | None,
    signal_candles: Sequence[StrategyCandle],
) -> SignalResult:
    if position is not None and position.quantity > 0:
        highest_price = _highest_price_since_loaded(position, signal_candles)
        exit_position = ExitPositionState(
            quantity=position.quantity,
            entry_price=position.average_cost,
            highest_price_since_entry=highest_price,
        )
        return evaluate_exit_signal(signal_snapshot, exit_position)

    regime = evaluate_regime(regime_snapshot)
    return evaluate_breakout_entry_signal(signal_snapshot, regime)


def _apply_sizing_and_risk(
    candidate: SignalResult,
    *,
    runtime: BotRuntimeState,
    risk_config_model: RiskConfigModel,
    portfolio: PortfolioSnapshot | None,
    position: Position | None,
    signal_snapshot: IndicatorSnapshot | None,
    trading_mode: str,
) -> dict[str, object]:
    if candidate.decision == SELL:
        quantity = position.quantity if position is not None else Decimal("0")
        return _final(
            decision=SELL,
            reason=candidate.reason,
            reason_payload=candidate.reason_payload,
            intended_order={
                "execution_mode": "dry_run",
                "trading_mode": trading_mode,
                "side": "SELL",
                "type": "MARKET",
                "quantity": str(quantity),
            },
            trading_mode=trading_mode,
        )

    if candidate.decision != BUY:
        return _final(
            decision=candidate.decision,
            reason=candidate.reason,
            reason_payload=candidate.reason_payload,
            trading_mode=trading_mode,
        )

    if portfolio is None:
        return _final(
            decision=NO_TRADE,
            reason="Snapshot de carteira ausente para sizing e risco",
            reason_payload={"code": "missing_portfolio_snapshot", **candidate.reason_payload},
            trading_mode=trading_mode,
        )

    risk_config = _to_strategy_risk_config(risk_config_model)
    sizing = calculate_position_size(
        PositionSizingInput(
            entry_price=(
                signal_snapshot.close_price if signal_snapshot is not None else Decimal("0")
            ),
            atr=signal_snapshot.atr if signal_snapshot is not None else None,
            available_cash=portfolio.usdt_balance,
            total_equity=portfolio.total_equity,
            current_exposure_notional=portfolio.btc_market_value,
        ),
        risk_config,
    )
    if sizing.quantity <= 0 or sizing.notional <= 0:
        return _final(
            decision=NO_TRADE,
            reason=sizing.reason,
            reason_payload=sizing.reason_payload,
            trading_mode=trading_mode,
        )

    risk = evaluate_risk(
        candidate,
        RiskState(
            bot_status=runtime.status,
            daily_pnl_pct=Decimal("0"),
            current_exposure_pct=portfolio.exposure_pct,
            projected_order_notional=sizing.notional,
            total_equity=portfolio.total_equity,
        ),
        risk_config,
    )
    if not risk.allowed:
        return _final_from_risk(risk, trading_mode=trading_mode)

    return _final_from_risk(
        risk,
        trading_mode=trading_mode,
        sizing=sizing,
        intended_order={
            "execution_mode": "dry_run",
            "trading_mode": trading_mode,
            "side": "BUY",
            "type": "MARKET",
            "quantity": str(sizing.quantity),
            "quote_quantity": str(sizing.notional),
        },
    )


def _final_from_risk(
    risk: RiskResult,
    *,
    trading_mode: str,
    sizing: PositionSizingResult | None = None,
    intended_order: dict[str, object] | None = None,
) -> dict[str, object]:
    reason_payload = risk.reason_payload
    if sizing is not None:
        reason_payload = {**risk.reason_payload, "sizing": sizing.reason_payload}

    return _final(
        decision=risk.decision,
        reason=risk.reason,
        reason_payload=reason_payload,
        intended_order=intended_order,
        trading_mode=trading_mode,
    )


def _final(
    *,
    decision: str,
    reason: str,
    reason_payload: dict[str, object],
    intended_order: dict[str, object] | None = None,
    trading_mode: str,
) -> dict[str, object]:
    return {
        "decision": decision,
        "reason": reason,
        "reason_payload": reason_payload,
        "intended_order": intended_order or {},
        "execution_result": {
            "execution_mode": "dry_run",
            "trading_mode": trading_mode,
            "status": "not_sent",
            "reason": "order_execution_out_of_scope",
        },
    }


def _decision_payload(
    *,
    decision: str,
    reason: str,
    reason_payload: dict[str, object],
    indicators: dict[str, object] | None = None,
    intended_order: dict[str, object] | None = None,
    execution_result: dict[str, object] | None = None,
    trading_mode: str,
) -> dict[str, object]:
    return {
        "decision": decision,
        "reason": reason,
        "reason_payload": reason_payload,
        "indicators": indicators or {},
        "intended_order": intended_order or {},
        "execution_result": execution_result
        or {
            "execution_mode": "dry_run",
            "trading_mode": trading_mode,
            "status": "not_sent",
            "reason": "no_order_intended",
        },
    }


def _execute_decision_order(
    order_service: OrderService,
    *,
    bot_run: BotRun,
    decision_log: DecisionLog,
    trading_mode: str,
    now: datetime,
) -> None:
    intended_order = decision_log.intended_order or {}
    if not intended_order or decision_log.decision not in {BUY, SELL}:
        return
    if trading_mode != "testnet":
        decision_log.execution_result = {
            **(decision_log.execution_result or {}),
            "status": "blocked",
            "reason": (
                "mainnet_execution_blocked"
                if trading_mode == "mainnet"
                else "unsupported_mode"
            ),
        }
        return
    try:
        order = order_service.place_order(
            OrderCommand(
                environment=decision_log.environment,
                symbol=decision_log.symbol,
                side=str(intended_order["side"]),
                quantity=(
                    Decimal(str(intended_order["quantity"]))
                    if intended_order.get("quantity") is not None
                    else None
                ),
                quote_quantity=(
                    Decimal(str(intended_order["quote_quantity"]))
                    if intended_order.get("quote_quantity") is not None
                    else None
                ),
                actor_type="robot",
                actor_id="aurum-worker",
                decision=decision_log,
                bot_run_id=bot_run.id,
                reason=decision_log.reason,
            ),
            now=now,
        )
        decision_log.execution_result = {
            "execution_mode": "binance_testnet",
            "trading_mode": trading_mode,
            "status": "sent",
            "order_id": str(order.id),
            "external_order_id": order.external_order_id,
            "order_status": order.status,
        }
    except OrderValidationError as exc:
        decision_log.execution_result = {
            "execution_mode": "binance_testnet",
            "trading_mode": trading_mode,
            "status": "blocked",
            "code": exc.code,
            "reason": exc.reason,
        }


def _trading_mode(runtime: object) -> str:
    if isinstance(runtime, BotRuntimeState) and runtime.trading_mode:
        return runtime.trading_mode
    return "unknown"


def _to_strategy_risk_config(config: RiskConfigModel) -> RiskConfig:
    return RiskConfig(
        risk_per_trade_pct=config.risk_per_trade_pct or Decimal("1"),
        daily_loss_limit_pct=config.daily_loss_limit_pct or Decimal("2"),
        max_exposure_pct=config.max_exposure_pct or Decimal("50"),
    )


def _to_strategy_candle(candle: MarketCandle) -> StrategyCandle:
    return StrategyCandle(
        open_time=candle.open_time,
        close_time=candle.close_time,
        open_price=candle.open_price,
        high_price=candle.high_price,
        low_price=candle.low_price,
        close_price=candle.close_price,
        volume=candle.volume,
    )


def _snapshot_payload(snapshot: IndicatorSnapshot | None) -> dict[str, object]:
    if snapshot is None:
        return {}

    return {
        "close_price": str(snapshot.close_price),
        "current_volume": str(snapshot.current_volume),
        "sma_50": str(snapshot.sma_50) if snapshot.sma_50 is not None else None,
        "sma_200": str(snapshot.sma_200) if snapshot.sma_200 is not None else None,
        "rsi": str(snapshot.rsi) if snapshot.rsi is not None else None,
        "atr": str(snapshot.atr) if snapshot.atr is not None else None,
        "atr_pct": str(snapshot.atr_pct) if snapshot.atr_pct is not None else None,
        "average_volume": str(snapshot.average_volume)
        if snapshot.average_volume is not None
        else None,
        "breakout_high_20": str(snapshot.breakout_high_20)
        if snapshot.breakout_high_20 is not None
        else None,
    }


def _portfolio_payload(
    portfolio: PortfolioSnapshot | None,
    position: Position | None,
) -> dict[str, object]:
    return {
        "portfolio_snapshot_id": str(portfolio.id) if portfolio is not None else None,
        "position_id": str(position.id) if position is not None else None,
        "usdt_balance": str(portfolio.usdt_balance) if portfolio is not None else None,
        "btc_balance": str(portfolio.btc_balance) if portfolio is not None else None,
        "total_equity": str(portfolio.total_equity) if portfolio is not None else None,
        "exposure_pct": str(portfolio.exposure_pct) if portfolio is not None else None,
        "position_quantity": str(position.quantity) if position is not None else None,
        "position_average_cost": str(position.average_cost) if position is not None else None,
    }


def _highest_price_since_loaded(
    position: Position,
    signal_candles: Sequence[StrategyCandle],
) -> Decimal:
    if not signal_candles:
        return position.average_cost
    return max(position.average_cost, *(candle.high_price for candle in signal_candles))
