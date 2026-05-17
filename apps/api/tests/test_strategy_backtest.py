from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.strategy.backtest import run_breakout_backtest
from app.strategy.types import StrategyCandle


def test_backtest_generates_closed_trade_and_decisions() -> None:
    candles = _backtest_fixture()

    result = run_breakout_backtest(candles, candles)

    assert result.metrics.trades == 1
    assert result.trades[0].entry_price == Decimal("101")
    assert result.trades[0].exit_price == Decimal("103")
    assert result.metrics.net_return_pct > 0
    assert any(decision.decision == "COMPRA" for decision in result.decisions)
    assert any(decision.decision == "NAO_OPERAR" for decision in result.decisions)


def test_backtest_returns_empty_metrics_without_candles() -> None:
    result = run_breakout_backtest([], [])

    assert result.metrics.trades == 0
    assert result.metrics.net_return_pct == Decimal("0")
    assert result.decisions == []


def _backtest_fixture() -> list[StrategyCandle]:
    closes = [Decimal("90")] * 185
    closes += [
        Decimal("100"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("90"),
        Decimal("94"),
        Decimal("95"),
        Decimal("101"),
        Decimal("103"),
    ]
    candles: list[StrategyCandle] = []
    for index, close in enumerate(closes):
        volume = Decimal("50") if close in {Decimal("101"), Decimal("103")} else Decimal("10")
        candles.append(_candle(index, close, volume=volume))
    return candles


def _candle(index: int, close: Decimal, *, volume: Decimal) -> StrategyCandle:
    opened_at = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=index)
    return StrategyCandle(
        open_time=opened_at,
        close_time=opened_at + timedelta(hours=1),
        open_price=close,
        high_price=close,
        low_price=close,
        close_price=close,
        volume=volume,
    )
