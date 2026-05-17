from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.indicators import compute_indicator_snapshot
from app.strategy.regime import evaluate_regime
from app.strategy.signals import BUY, NO_TRADE, evaluate_breakout_entry_signal
from app.strategy.types import (
    BacktestDecision,
    BacktestMetrics,
    BacktestResult,
    BacktestTrade,
    StrategyCandle,
)

ONE_HUNDRED = Decimal("100")


def run_breakout_backtest(
    signal_candles: Sequence[StrategyCandle],
    regime_candles: Sequence[StrategyCandle],
    *,
    initial_cash: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0"),
) -> BacktestResult:
    if not signal_candles:
        return BacktestResult(
            metrics=BacktestMetrics(
                trades=0,
                net_return_pct=Decimal("0"),
                max_drawdown_pct=Decimal("0"),
                win_rate_pct=Decimal("0"),
                profit_factor=None,
            ),
            trades=[],
            decisions=[],
        )

    cash = initial_cash
    quantity = Decimal("0")
    entry_price: Decimal | None = None
    entry_time = None
    decisions: list[BacktestDecision] = []
    trades: list[BacktestTrade] = []
    equity_curve: list[Decimal] = []

    for index, candle in enumerate(signal_candles):
        signal_history = signal_candles[: index + 1]
        regime_history = [item for item in regime_candles if item.close_time <= candle.close_time]

        signal_snapshot = compute_indicator_snapshot(signal_history)
        regime_snapshot = compute_indicator_snapshot(regime_history)
        regime = evaluate_regime(regime_snapshot)
        signal = evaluate_breakout_entry_signal(signal_snapshot, regime)

        if quantity == 0 and signal.decision == BUY:
            gross_cash = cash * (Decimal("1") - fee_rate)
            quantity = gross_cash / candle.close_price
            entry_price = candle.close_price
            entry_time = candle.close_time
            cash = Decimal("0")
            decisions.append(
                BacktestDecision(
                    decided_at=candle.close_time,
                    decision=BUY,
                    reason=signal.reason,
                    reason_payload=signal.reason_payload,
                )
            )
        else:
            decision = "MANTER_POSICAO" if quantity > 0 else NO_TRADE
            decisions.append(
                BacktestDecision(
                    decided_at=candle.close_time,
                    decision=decision,
                    reason=signal.reason if decision == NO_TRADE else "Posição long mantida",
                    reason_payload=signal.reason_payload
                    if decision == NO_TRADE
                    else {"code": "holding_position"},
                )
            )

        equity_curve.append(cash + quantity * candle.close_price)

    last = signal_candles[-1]
    if quantity > 0 and entry_price is not None and entry_time is not None:
        gross_exit_value = quantity * last.close_price
        cash = gross_exit_value * (Decimal("1") - fee_rate)
        pnl = cash - initial_cash
        trades.append(
            BacktestTrade(
                entry_time=entry_time,
                exit_time=last.close_time,
                entry_price=entry_price,
                exit_price=last.close_price,
                quantity=quantity,
                pnl=pnl,
                return_pct=(pnl / initial_cash) * ONE_HUNDRED,
            )
        )
        equity_curve[-1] = cash

    return BacktestResult(
        metrics=_calculate_metrics(initial_cash, cash, trades, equity_curve),
        trades=trades,
        decisions=decisions,
    )


def _calculate_metrics(
    initial_cash: Decimal,
    final_cash: Decimal,
    trades: Sequence[BacktestTrade],
    equity_curve: Sequence[Decimal],
) -> BacktestMetrics:
    net_return_pct = ((final_cash - initial_cash) / initial_cash) * ONE_HUNDRED
    max_drawdown_pct = _max_drawdown_pct(equity_curve)
    winning_trades = [trade for trade in trades if trade.pnl > 0]
    losing_trades = [trade for trade in trades if trade.pnl < 0]
    win_rate_pct = Decimal("0")
    if trades:
        win_rate_pct = Decimal(len(winning_trades)) / Decimal(len(trades)) * ONE_HUNDRED
    total_profit = sum((trade.pnl for trade in winning_trades), Decimal("0"))
    total_loss = abs(sum((trade.pnl for trade in losing_trades), Decimal("0")))
    profit_factor = None if total_loss == 0 else total_profit / total_loss

    return BacktestMetrics(
        trades=len(trades),
        net_return_pct=net_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        win_rate_pct=win_rate_pct,
        profit_factor=profit_factor,
    )


def _max_drawdown_pct(equity_curve: Sequence[Decimal]) -> Decimal:
    if not equity_curve:
        return Decimal("0")

    peak = equity_curve[0]
    max_drawdown = Decimal("0")
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        if peak == 0:
            continue
        drawdown = (peak - equity) / peak * ONE_HUNDRED
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown
