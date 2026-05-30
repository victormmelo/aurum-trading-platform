from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    AuditLog,
    BotRuntimeState,
    DecisionLog,
    MarketSnapshot,
    Order,
    OrderFill,
    PortfolioSnapshot,
    RiskConfig,
)
from app.execution.adapters import ExecutionAdapter, ExecutionRequest, ExecutionResult
from app.strategy.risk import evaluate_risk
from app.strategy.types import RiskConfig as StrategyRiskConfig
from app.strategy.types import RiskResult, RiskState, SignalResult

FINAL_STATUSES = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}
BINANCE_ORDER_STATUSES = {"NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED", "EXPIRED"}


class OrderValidationError(RuntimeError):
    def __init__(self, reason: str, code: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


@dataclass(frozen=True)
class OrderCommand:
    environment: str
    symbol: str
    side: str
    quantity: Decimal | None = None
    quote_quantity: Decimal | None = None
    actor_type: str = "system"
    actor_id: str | None = None
    decision: DecisionLog | None = None
    bot_run_id: uuid.UUID | None = None
    reason: str | None = None


class OrderService:
    def __init__(
        self,
        *,
        session: Session,
        adapter: ExecutionAdapter,
        expected_environment: str,
        expected_symbol: str,
        stale_after_seconds: int,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.expected_environment = expected_environment
        self.expected_symbol = expected_symbol.upper()
        self.stale_after_seconds = stale_after_seconds

    def place_order(self, command: OrderCommand, *, now: datetime | None = None) -> Order:
        submitted_at = now or datetime.now(UTC)
        try:
            self._validate_command(command, now=submitted_at)
            client_order_id = f"aurum-{command.actor_type}-{uuid.uuid4().hex[:24]}"
            request = ExecutionRequest(
                environment=command.environment,
                symbol=command.symbol.upper(),
                side=command.side.upper(),
                order_type="MARKET",
                quantity=command.quantity,
                quote_quantity=command.quote_quantity,
                client_order_id=client_order_id,
            )
            try:
                result = self.adapter.place_order(request)
            except Exception as exc:  # noqa: BLE001
                result = ExecutionResult(
                    adapter=self.adapter.name,
                    external_order_id=None,
                    client_order_id=client_order_id,
                    status="REJECTED",
                    executed_quantity=Decimal("0"),
                    quote_quantity=command.quote_quantity,
                    average_price=None,
                    raw_payload={
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                    fills=[],
                )
            order = self._persist_order(command, result, submitted_at=submitted_at)
            self._audit(
                command,
                action="order.rejected" if order.status == "REJECTED" else "order.submitted",
                entity_id=order.id,
                occurred_at=submitted_at,
                metadata={"adapter": self.adapter.name, "status": order.status},
            )
            return order
        except Exception as exc:
            if isinstance(exc, OrderValidationError):
                self._audit(
                    command,
                    action="order.blocked",
                    entity_id=None,
                    occurred_at=submitted_at,
                    metadata={"code": exc.code, "reason": exc.reason, "adapter": self.adapter.name},
                )
            raise

    def reconcile_open_orders(
        self,
        *,
        environment: str,
        symbol: str,
        now: datetime | None = None,
    ) -> list[Order]:
        reconciled_at = now or datetime.now(UTC)
        statement = (
            select(Order)
            .options(selectinload(Order.fills))
            .where(
                Order.environment == environment,
                Order.symbol == symbol.upper(),
                Order.status.in_(["NEW", "PARTIALLY_FILLED"]),
            )
        )
        orders = list(self.session.scalars(statement))
        updated: list[Order] = []
        for order in orders:
            result = self.adapter.fetch_order(
                symbol=order.symbol,
                external_order_id=order.external_order_id,
                client_order_id=order.client_order_id,
            )
            self._apply_execution_result(order, result, closed_at=reconciled_at)
            updated.append(order)
            self._audit(
                OrderCommand(environment=environment, symbol=symbol, side=order.side),
                action="order.reconciled",
                entity_id=order.id,
                occurred_at=reconciled_at,
                metadata={"adapter": self.adapter.name, "status": order.status},
            )
        return updated

    def _validate_command(self, command: OrderCommand, *, now: datetime) -> None:
        if command.environment != self.expected_environment or command.environment != "testnet":
            raise OrderValidationError(
                "Ambiente inválido para execução Testnet",
                "wrong_environment",
            )
        if self.adapter.name == "binance_mainnet":
            raise OrderValidationError("Mainnet bloqueado no MVP Aurum", "mainnet_blocked")
        if (
            self.adapter.name == "binance_testnet"
            and "testnet.binance.vision" not in self.adapter.client.base_url
        ):
            raise OrderValidationError(
                "Base URL não é Binance Spot Testnet",
                "wrong_binance_base_url",
            )
        if command.symbol.upper() != self.expected_symbol or command.symbol.upper() != "BTCUSDT":
            raise OrderValidationError("Símbolo fora do escopo MVP", "symbol_out_of_scope")
        if command.side.upper() not in {"BUY", "SELL"}:
            raise OrderValidationError("Lado inválido para ordem", "invalid_side")
        if command.quantity is None and command.quote_quantity is None:
            raise OrderValidationError(
                "Ordem precisa de quantidade base ou notional",
                "missing_quantity",
            )
        if command.side.upper() == "SELL" and command.quote_quantity is not None:
            raise OrderValidationError(
                "Venda long-only deve usar quantidade BTC",
                "invalid_sell_quantity",
            )

        runtime = self._runtime(command.environment)
        if runtime is None:
            raise OrderValidationError(
                "Estado operacional do robô não encontrado",
                "missing_runtime_state",
            )
        if runtime.status != "running":
            code = "emergency_stop" if runtime.status == "emergency_stop" else "bot_paused"
            raise OrderValidationError("Robô pausado ou em parada de emergência", code)
        if self.adapter.name == "binance_testnet" and runtime.trading_mode != "testnet":
            raise OrderValidationError("Runtime não está em modo Testnet", "wrong_trading_mode")

        market = self._latest_market(command.environment, command.symbol.upper())
        if market is None:
            raise OrderValidationError("Snapshot de mercado ausente", "missing_market_snapshot")
        if market.captured_at < now - timedelta(seconds=self.stale_after_seconds):
            raise OrderValidationError("Dados de mercado stale", "stale_market_data")

        portfolio = self._latest_portfolio(command.environment, command.symbol.upper())
        if portfolio is None:
            raise OrderValidationError("Snapshot de carteira ausente", "missing_portfolio_snapshot")

        self._validate_balance(command, portfolio)
        self._validate_risk(command, portfolio)

    def _validate_balance(self, command: OrderCommand, portfolio: PortfolioSnapshot) -> None:
        if command.side.upper() == "BUY":
            needed = command.quote_quantity
            if needed is None and command.quantity is not None:
                needed = command.quantity * portfolio.btc_market_price
            if needed is None or needed > portfolio.usdt_balance:
                raise OrderValidationError("Saldo USDT insuficiente", "insufficient_balance")
            return
        quantity = command.quantity or Decimal("0")
        if quantity > portfolio.btc_balance:
            raise OrderValidationError(
                "Saldo BTC insuficiente para venda long-only",
                "insufficient_balance",
            )

    def _validate_risk(self, command: OrderCommand, portfolio: PortfolioSnapshot) -> None:
        risk_config = self.session.scalars(
            select(RiskConfig).where(
                RiskConfig.environment == command.environment,
                RiskConfig.symbol == command.symbol.upper(),
                RiskConfig.is_active.is_(True),
            )
        ).first()
        if risk_config is None:
            raise OrderValidationError("Configuração ativa de risco ausente", "missing_risk_config")
        notional = command.quote_quantity
        if notional is None and command.quantity is not None:
            notional = command.quantity * portfolio.btc_market_price
        signal = SignalResult(
            decision="COMPRA" if command.side.upper() == "BUY" else "VENDA",
            reason=command.reason or "Ordem manual/worker validada",
            reason_payload={"source": command.actor_type},
        )
        result: RiskResult = evaluate_risk(
            signal,
            RiskState(
                bot_status="running",
                daily_pnl_pct=Decimal("0"),
                current_exposure_pct=portfolio.exposure_pct,
                projected_order_notional=notional or Decimal("0"),
                total_equity=portfolio.total_equity,
            ),
            StrategyRiskConfig(
                risk_per_trade_pct=risk_config.risk_per_trade_pct or Decimal("1"),
                daily_loss_limit_pct=risk_config.daily_loss_limit_pct or Decimal("2"),
                max_exposure_pct=risk_config.max_exposure_pct or Decimal("50"),
            ),
        )
        if not result.allowed:
            raise OrderValidationError(
                result.reason,
                str(result.reason_payload.get("code", "risk_blocked")),
            )

    def _persist_order(
        self,
        command: OrderCommand,
        result: ExecutionResult,
        *,
        submitted_at: datetime,
    ) -> Order:
        status = result.status if result.status in BINANCE_ORDER_STATUSES else "REJECTED"
        order = Order(
            environment=command.environment,
            exchange="binance" if self.adapter.name == "binance_testnet" else self.adapter.name,
            symbol=command.symbol.upper(),
            decision_id=command.decision.id if command.decision is not None else None,
            bot_run_id=command.bot_run_id,
            external_order_id=result.external_order_id,
            client_order_id=result.client_order_id,
            side=command.side.upper(),
            order_type="MARKET",
            status=status,
            position_side="LONG",
            requested_quantity=command.quantity or Decimal("0"),
            executed_quantity=result.executed_quantity,
            quote_quantity=result.quote_quantity or command.quote_quantity,
            average_price=result.average_price,
            submitted_at=submitted_at,
            closed_at=submitted_at if status in FINAL_STATUSES else None,
            raw_payload={"adapter": result.adapter, "response": result.raw_payload},
        )
        self.session.add(order)
        self.session.flush()
        self._add_fills(order, result, filled_at=submitted_at)
        return order

    def _apply_execution_result(
        self,
        order: Order,
        result: ExecutionResult,
        *,
        closed_at: datetime,
    ) -> None:
        order.status = result.status if result.status in BINANCE_ORDER_STATUSES else "REJECTED"
        order.executed_quantity = result.executed_quantity
        order.quote_quantity = result.quote_quantity or order.quote_quantity
        order.average_price = result.average_price or order.average_price
        order.raw_payload = {"adapter": result.adapter, "response": result.raw_payload}
        if order.status in FINAL_STATUSES:
            order.closed_at = closed_at
        self._add_fills(order, result, filled_at=closed_at)

    def _add_fills(self, order: Order, result: ExecutionResult, *, filled_at: datetime) -> None:
        existing = {
            fill.external_trade_id
            for fill in order.fills
            if fill.external_trade_id is not None
        }
        for fill in result.fills:
            if fill.external_trade_id is not None and fill.external_trade_id in existing:
                continue
            self.session.add(
                OrderFill(
                    environment=order.environment,
                    exchange=order.exchange,
                    order_id=order.id,
                    external_trade_id=fill.external_trade_id,
                    filled_at=filled_at,
                    price=fill.price,
                    quantity=fill.quantity,
                    quote_quantity=fill.quote_quantity,
                    fee_amount=fill.fee_amount,
                    fee_asset=fill.fee_asset,
                    fee_estimated_usdt=fill.fee_amount if fill.fee_asset == "USDT" else None,
                    raw_payload=fill.raw_payload,
                )
            )

    def _runtime(self, environment: str) -> BotRuntimeState | None:
        return self.session.scalars(
            select(BotRuntimeState).where(BotRuntimeState.environment == environment)
        ).first()

    def _latest_market(self, environment: str, symbol: str) -> MarketSnapshot | None:
        return self.session.scalars(
            select(MarketSnapshot)
            .where(MarketSnapshot.environment == environment, MarketSnapshot.symbol == symbol)
            .order_by(MarketSnapshot.captured_at.desc())
            .limit(1)
        ).first()

    def _latest_portfolio(self, environment: str, symbol: str) -> PortfolioSnapshot | None:
        return self.session.scalars(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.environment == environment, PortfolioSnapshot.symbol == symbol)
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(1)
        ).first()

    def _audit(
        self,
        command: OrderCommand,
        *,
        action: str,
        entity_id: uuid.UUID | None,
        occurred_at: datetime,
        metadata: dict[str, object],
    ) -> None:
        self.session.add(
            AuditLog(
                environment=command.environment,
                actor_type=command.actor_type,
                actor_id=command.actor_id,
                action=action,
                entity_type="order",
                entity_id=entity_id,
                occurred_at=occurred_at,
                metadata_payload={
                    **metadata,
                    "symbol": command.symbol.upper(),
                    "side": command.side.upper(),
                },
            )
        )
