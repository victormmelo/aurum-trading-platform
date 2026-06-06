from __future__ import annotations

import math
from bisect import bisect_right
from collections import deque
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from app.strategy.exits import evaluate_exit_signal
from app.strategy.indicators import compute_indicator_snapshot
from app.strategy.regime import evaluate_regime
from app.strategy.signals import BUY, NO_TRADE, SELL, evaluate_breakout_entry_signal
from app.strategy.types import (
    BacktestDecision,
    BacktestMetrics,
    BacktestResult,
    BacktestTrade,
    EquityPoint,
    ExitPositionState,
    FullBacktestMetrics,
    FullBacktestResult,
    FullBacktestTrade,
    StrategyCandle,
)

ONE_HUNDRED = Decimal("100")

# Sliding window large enough for SMA-200, ATR-14, RSI-14, volume-20, breakout-20
_INDICATOR_WINDOW = 252


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


def run_multi_trade_backtest(
    signal_candles: Sequence[StrategyCandle],
    regime_candles: Sequence[StrategyCandle],
    *,
    initial_cash: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0.001"),
) -> FullBacktestResult:
    """Multi-trade backtest engine supporting multiple open/close cycles."""
    if not signal_candles:
        return FullBacktestResult(
            metrics=_empty_full_metrics(initial_cash),
            trades=[],
            equity_points=[],
        )

    regime_sorted = sorted(regime_candles, key=lambda c: c.close_time)
    regime_close_times = [c.close_time for c in regime_sorted]

    signal_window: deque[StrategyCandle] = deque(maxlen=_INDICATOR_WINDOW)

    cash = initial_cash
    quantity = Decimal("0")
    entry_price: Decimal | None = None
    entry_time = None
    entry_cash = Decimal("0")
    entry_fee_paid = Decimal("0")
    highest_price = Decimal("0")

    trades: list[FullBacktestTrade] = []
    equity_points: list[EquityPoint] = []
    trade_index = 0

    for candle in signal_candles:
        signal_window.append(candle)

        cutoff = bisect_right(regime_close_times, candle.close_time)
        regime_window = regime_sorted[max(0, cutoff - _INDICATOR_WINDOW) : cutoff]

        signal_snapshot = compute_indicator_snapshot(list(signal_window))
        regime_snapshot = compute_indicator_snapshot(regime_window)
        regime = evaluate_regime(regime_snapshot)

        if quantity == 0:
            signal = evaluate_breakout_entry_signal(signal_snapshot, regime)
            if signal.decision == BUY:
                entry_fee_paid = cash * fee_rate
                invested = cash - entry_fee_paid
                quantity = invested / candle.close_price
                entry_price = candle.close_price
                entry_time = candle.close_time
                entry_cash = cash
                highest_price = candle.close_price
                cash = Decimal("0")
        else:
            if candle.close_price > highest_price:
                highest_price = candle.close_price

            position_state = ExitPositionState(
                quantity=quantity,
                entry_price=entry_price,  # type: ignore[arg-type]
                highest_price_since_entry=highest_price,
            )
            exit_signal = evaluate_exit_signal(signal_snapshot, position_state)

            if exit_signal.decision == SELL:
                (
                    trade_index, cash, quantity,
                    entry_price, entry_time,
                    entry_cash, entry_fee_paid, highest_price,
                ) = _close_position(
                    candle=candle,
                    quantity=quantity,
                    entry_price=entry_price,  # type: ignore[arg-type]
                    entry_time=entry_time,  # type: ignore[arg-type]
                    entry_cash=entry_cash,
                    entry_fee_paid=entry_fee_paid,
                    fee_rate=fee_rate,
                    exit_reason=str(exit_signal.reason_payload.get("code", "unknown")),
                    trade_index=trade_index,
                    trades=trades,
                )

        current_equity = cash + quantity * candle.close_price
        equity_points.append(
            EquityPoint(
                timestamp=candle.close_time,
                equity=current_equity,
                btc_price=candle.close_price,
                is_in_position=quantity > 0,
            )
        )

    # Close any open position at the end of the period
    if quantity > 0 and entry_price is not None and entry_time is not None and equity_points:
        last_candle = signal_candles[-1]
        gross = quantity * last_candle.close_price
        exit_fee = gross * fee_rate
        net = gross - exit_fee
        fees_paid = entry_fee_paid + exit_fee
        pnl_usd = net - entry_cash
        return_pct = (pnl_usd / entry_cash) * ONE_HUNDRED if entry_cash else Decimal("0")

        trades.append(
            FullBacktestTrade(
                trade_index=trade_index,
                entry_time=entry_time,
                exit_time=last_candle.close_time,
                entry_price=entry_price,
                exit_price=last_candle.close_price,
                quantity=quantity,
                entry_value=entry_cash,
                exit_value=net,
                fees_paid=fees_paid,
                pnl_usd=pnl_usd,
                return_pct=return_pct,
                exit_reason="end_of_period",
                is_winner=pnl_usd > 0,
                equity_after=net,
            )
        )
        cash = net
        last_ep = equity_points[-1]
        equity_points[-1] = EquityPoint(
            timestamp=last_ep.timestamp,
            equity=cash,
            btc_price=last_ep.btc_price,
            is_in_position=False,
        )

    metrics = _calculate_full_metrics(
        initial_cash=initial_cash,
        final_cash=cash,
        trades=trades,
        equity_points=equity_points,
        first_close=signal_candles[0].close_price,
        last_close=signal_candles[-1].close_price,
    )

    return FullBacktestResult(metrics=metrics, trades=trades, equity_points=equity_points)


def _close_position(
    *,
    candle: StrategyCandle,
    quantity: Decimal,
    entry_price: Decimal,
    entry_time,
    entry_cash: Decimal,
    entry_fee_paid: Decimal,
    fee_rate: Decimal,
    exit_reason: str,
    trade_index: int,
    trades: list[FullBacktestTrade],
) -> tuple:
    gross = quantity * candle.close_price
    exit_fee = gross * fee_rate
    net = gross - exit_fee
    fees_paid = entry_fee_paid + exit_fee
    pnl_usd = net - entry_cash
    return_pct = (pnl_usd / entry_cash) * ONE_HUNDRED if entry_cash else Decimal("0")

    trades.append(
        FullBacktestTrade(
            trade_index=trade_index,
            entry_time=entry_time,
            exit_time=candle.close_time,
            entry_price=entry_price,
            exit_price=candle.close_price,
            quantity=quantity,
            entry_value=entry_cash,
            exit_value=net,
            fees_paid=fees_paid,
            pnl_usd=pnl_usd,
            return_pct=return_pct,
            exit_reason=exit_reason,
            is_winner=pnl_usd > 0,
            equity_after=net,
        )
    )

    return trade_index + 1, net, Decimal("0"), None, None, Decimal("0"), Decimal("0"), Decimal("0")


def _calculate_full_metrics(
    *,
    initial_cash: Decimal,
    final_cash: Decimal,
    trades: list[FullBacktestTrade],
    equity_points: list[EquityPoint],
    first_close: Decimal,
    last_close: Decimal,
) -> FullBacktestMetrics:
    total_return_usd = final_cash - initial_cash
    total_return_pct = (
        (total_return_usd / initial_cash) * ONE_HUNDRED if initial_cash else Decimal("0")
    )
    max_drawdown_pct = _max_drawdown_pct([ep.equity for ep in equity_points])

    winners = [t for t in trades if t.is_winner]
    losers = [t for t in trades if not t.is_winner]
    total = len(trades)

    win_rate_pct = (Decimal(len(winners)) / Decimal(total)) * ONE_HUNDRED if total else Decimal("0")

    total_profit = sum((t.pnl_usd for t in winners), Decimal("0"))
    total_loss = abs(sum((t.pnl_usd for t in losers), Decimal("0")))
    profit_factor = total_profit / total_loss if total_loss > 0 else None

    avg_win_pct = (
        sum((t.return_pct for t in winners), Decimal("0")) / Decimal(len(winners))
        if winners
        else None
    )
    avg_loss_pct = (
        sum((t.return_pct for t in losers), Decimal("0")) / Decimal(len(losers))
        if losers
        else None
    )

    largest_win_pct = max((t.return_pct for t in winners), default=None)
    largest_loss_pct = min((t.return_pct for t in losers), default=None)

    avg_duration_hours: Decimal | None = None
    if trades:
        total_hours = sum(
            (t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades
        )
        avg_duration_hours = Decimal(str(round(total_hours / len(trades), 6)))

    sharpe = _compute_daily_sharpe(equity_points)

    btc_buy_hold: Decimal | None = None
    if first_close and first_close > 0:
        btc_buy_hold = ((last_close - first_close) / first_close) * ONE_HUNDRED

    return FullBacktestMetrics(
        total_return_pct=total_return_pct,
        total_return_usd=total_return_usd,
        final_capital=final_cash,
        max_drawdown_pct=max_drawdown_pct,
        win_rate_pct=win_rate_pct,
        profit_factor=profit_factor,
        total_trades=total,
        winning_trades=len(winners),
        losing_trades=len(losers),
        avg_win_pct=avg_win_pct,
        avg_loss_pct=avg_loss_pct,
        sharpe_ratio=sharpe,
        largest_win_pct=largest_win_pct,
        largest_loss_pct=largest_loss_pct,
        avg_trade_duration_hours=avg_duration_hours,
        btc_buy_hold_return_pct=btc_buy_hold,
    )


def _compute_daily_sharpe(equity_points: Sequence[EquityPoint]) -> Decimal | None:
    if len(equity_points) < 2:
        return None

    daily: dict[date, Decimal] = {}
    for ep in equity_points:
        daily[ep.timestamp.date()] = ep.equity

    sorted_equities = [daily[d] for d in sorted(daily.keys())]
    if len(sorted_equities) < 2:
        return None

    daily_returns: list[float] = []
    for prev, curr in zip(sorted_equities, sorted_equities[1:], strict=False):
        if prev == 0:
            continue
        daily_returns.append(float(curr - prev) / float(prev))

    if len(daily_returns) < 2:
        return None

    n = len(daily_returns)
    mean_r = sum(daily_returns) / n
    variance = sum((r - mean_r) ** 2 for r in daily_returns) / n
    std_r = math.sqrt(variance)
    if std_r == 0:
        return None

    sharpe = mean_r / std_r * math.sqrt(252)
    return Decimal(str(round(sharpe, 6)))


def _empty_full_metrics(initial_cash: Decimal) -> FullBacktestMetrics:
    return FullBacktestMetrics(
        total_return_pct=Decimal("0"),
        total_return_usd=Decimal("0"),
        final_capital=initial_cash,
        max_drawdown_pct=Decimal("0"),
        win_rate_pct=Decimal("0"),
        profit_factor=None,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        avg_win_pct=None,
        avg_loss_pct=None,
        sharpe_ratio=None,
        largest_win_pct=None,
        largest_loss_pct=None,
        avg_trade_duration_hours=None,
        btc_buy_hold_return_pct=None,
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
