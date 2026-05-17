from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.types import IndicatorSnapshot, StrategyCandle

ONE_HUNDRED = Decimal("100")


def simple_moving_average(values: Sequence[Decimal], period: int) -> Decimal | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None

    window = values[-period:]
    return sum(window) / Decimal(period)


def average_volume(candles: Sequence[StrategyCandle], period: int) -> Decimal | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) <= period:
        return None

    prior_window = candles[-period - 1 : -1]
    return sum(candle.volume for candle in prior_window) / Decimal(period)


def breakout_high(candles: Sequence[StrategyCandle], lookback: int) -> Decimal | None:
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    if len(candles) <= lookback:
        return None

    prior_window = candles[-lookback - 1 : -1]
    return max(candle.high_price for candle in prior_window)


def relative_strength_index(candles: Sequence[StrategyCandle], period: int = 14) -> Decimal | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) <= period:
        return None

    closes = [candle.close_price for candle in candles]
    recent_closes = closes[-period - 1 :]
    gains: list[Decimal] = []
    losses: list[Decimal] = []

    for previous, current in zip(recent_closes, recent_closes[1:], strict=False):
        change = current - previous
        if change >= 0:
            gains.append(change)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(change))

    average_gain = sum(gains) / Decimal(period)
    average_loss = sum(losses) / Decimal(period)

    if average_loss == 0:
        return ONE_HUNDRED

    relative_strength = average_gain / average_loss
    return ONE_HUNDRED - (ONE_HUNDRED / (Decimal("1") + relative_strength))


def average_true_range(candles: Sequence[StrategyCandle], period: int = 14) -> Decimal | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) <= period:
        return None

    recent = candles[-period - 1 :]
    true_ranges: list[Decimal] = []

    for previous, current in zip(recent, recent[1:], strict=False):
        true_ranges.append(
            max(
                current.high_price - current.low_price,
                abs(current.high_price - previous.close_price),
                abs(current.low_price - previous.close_price),
            )
        )

    return sum(true_ranges) / Decimal(period)


def compute_indicator_snapshot(
    candles: Sequence[StrategyCandle],
    *,
    sma_short_period: int = 50,
    sma_long_period: int = 200,
    rsi_period: int = 14,
    atr_period: int = 14,
    volume_average_period: int = 20,
    breakout_lookback: int = 20,
) -> IndicatorSnapshot | None:
    if not candles:
        return None

    closes = [candle.close_price for candle in candles]
    latest = candles[-1]
    atr = average_true_range(candles, atr_period)
    atr_pct = None
    if atr is not None and latest.close_price != 0:
        atr_pct = (atr / latest.close_price) * ONE_HUNDRED

    return IndicatorSnapshot(
        close_price=latest.close_price,
        current_volume=latest.volume,
        sma_50=simple_moving_average(closes, sma_short_period),
        sma_200=simple_moving_average(closes, sma_long_period),
        rsi=relative_strength_index(candles, rsi_period),
        atr=atr,
        atr_pct=atr_pct,
        average_volume=average_volume(candles, volume_average_period),
        breakout_high_20=breakout_high(candles, breakout_lookback),
    )
