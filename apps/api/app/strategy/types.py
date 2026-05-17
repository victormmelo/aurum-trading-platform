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

