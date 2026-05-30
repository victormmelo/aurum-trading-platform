from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.market.refresh import _price_change_pct, _trend, _twenty_four_hour_window

NOW = datetime(2026, 5, 30, 15, 0, tzinfo=UTC)


def test_twenty_four_hour_window_keeps_recent_candles_only() -> None:
    candles = [
        _candle(close_time=NOW - timedelta(hours=25), close_price="90"),
        _candle(close_time=NOW - timedelta(hours=23), close_price="100"),
        _candle(close_time=NOW, close_price="110"),
    ]

    window = _twenty_four_hour_window(candles)

    assert [candle.close_price for candle in window] == [Decimal("100"), Decimal("110")]


def test_price_change_pct_uses_baseline_near_24h() -> None:
    candles = [
        _candle(close_time=NOW - timedelta(hours=25), close_price="90"),
        _candle(close_time=NOW - timedelta(hours=24), close_price="100"),
        _candle(close_time=NOW, close_price="110"),
    ]

    assert _price_change_pct(candles) == Decimal("10.0")


def test_trend_classifies_direction_with_threshold() -> None:
    assert _trend([_candle(close_price="100"), _candle(close_price="101")]) == "alta"
    assert _trend([_candle(close_price="100"), _candle(close_price="99")]) == "baixa"
    assert _trend([_candle(close_price="100"), _candle(close_price="100.05")]) == "lateral"


def _candle(
    *,
    close_time: datetime = NOW,
    close_price: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        close_time=close_time,
        close_price=Decimal(close_price),
        high_price=Decimal(close_price),
        low_price=Decimal(close_price),
        volume=Decimal("1"),
    )
