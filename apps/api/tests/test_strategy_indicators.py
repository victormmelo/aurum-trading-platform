from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.strategy.indicators import (
    average_true_range,
    breakout_high,
    compute_indicator_snapshot,
    relative_strength_index,
    simple_moving_average,
)
from app.strategy.types import StrategyCandle


def test_indicator_snapshot_calculates_mvp_values() -> None:
    candles = [_candle(index, Decimal(index), volume=Decimal("10")) for index in range(1, 202)]

    snapshot = compute_indicator_snapshot(candles)

    assert snapshot is not None
    assert snapshot.close_price == Decimal("201")
    assert snapshot.sma_50 == Decimal("176.5")
    assert snapshot.sma_200 == Decimal("101.5")
    assert snapshot.average_volume == Decimal("10")
    assert snapshot.breakout_high_20 == Decimal("201")
    assert snapshot.rsi == Decimal("100")
    assert snapshot.atr == Decimal("2")


def test_indicators_return_none_when_history_is_insufficient() -> None:
    candles = [_candle(index, Decimal(index)) for index in range(1, 10)]

    assert simple_moving_average([candle.close_price for candle in candles], 50) is None
    assert relative_strength_index(candles) is None
    assert average_true_range(candles) is None
    assert breakout_high(candles, 20) is None


def _candle(index: int, close: Decimal, *, volume: Decimal = Decimal("1")) -> StrategyCandle:
    opened_at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
    return StrategyCandle(
        open_time=opened_at,
        close_time=opened_at + timedelta(hours=1),
        open_price=close,
        high_price=close + Decimal("1"),
        low_price=close - Decimal("1"),
        close_price=close,
        volume=volume,
    )
