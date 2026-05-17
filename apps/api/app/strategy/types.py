from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class StrategyCandle:
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal


@dataclass(frozen=True)
class IndicatorSnapshot:
    close_price: Decimal
    current_volume: Decimal
    sma_50: Decimal | None
    sma_200: Decimal | None
    rsi: Decimal | None
    atr: Decimal | None
    atr_pct: Decimal | None
    average_volume: Decimal | None
    breakout_high_20: Decimal | None


@dataclass(frozen=True)
class RegimeResult:
    allowed: bool
    reason: str
    reason_payload: dict[str, object]


@dataclass(frozen=True)
class SignalResult:
    decision: str
    reason: str
    reason_payload: dict[str, object]


@dataclass(frozen=True)
class ExitPositionState:
    quantity: Decimal
    entry_price: Decimal
    highest_price_since_entry: Decimal


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade_pct: Decimal
    daily_loss_limit_pct: Decimal
    max_exposure_pct: Decimal


@dataclass(frozen=True)
class RiskState:
    bot_status: str
    daily_pnl_pct: Decimal
    current_exposure_pct: Decimal
    projected_order_notional: Decimal
    total_equity: Decimal


@dataclass(frozen=True)
class RiskResult:
    allowed: bool
    decision: str
    reason: str
    reason_payload: dict[str, object]


@dataclass(frozen=True)
class PositionSizingInput:
    entry_price: Decimal
    atr: Decimal | None
    available_cash: Decimal
    total_equity: Decimal
    current_exposure_notional: Decimal = Decimal("0")


@dataclass(frozen=True)
class PositionSizingResult:
    quantity: Decimal
    notional: Decimal
    reason: str
    reason_payload: dict[str, object]


@dataclass(frozen=True)
class BacktestDecision:
    decided_at: datetime
    decision: str
    reason: str
    reason_payload: dict[str, object]


@dataclass(frozen=True)
class BacktestTrade:
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    return_pct: Decimal


@dataclass(frozen=True)
class BacktestMetrics:
    trades: int
    net_return_pct: Decimal
    max_drawdown_pct: Decimal
    win_rate_pct: Decimal
    profit_factor: Decimal | None


@dataclass(frozen=True)
class BacktestResult:
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    decisions: list[BacktestDecision]
