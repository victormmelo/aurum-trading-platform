from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.strategy.backtest import run_multi_trade_backtest
from app.strategy.types import StrategyCandle


def _candle(
    index: int,
    close: Decimal,
    *,
    volume: Decimal,
    high: Decimal | None = None,
) -> StrategyCandle:
    opened_at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
    return StrategyCandle(
        open_time=opened_at,
        close_time=opened_at + timedelta(hours=1),
        open_price=close,
        high_price=high if high is not None else close,
        low_price=close,
        close_price=close,
        volume=volume,
    )


def _entry_fixture() -> list[StrategyCandle]:
    """203 candles that trigger one BUY signal; same as the legacy backtest fixture."""
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


def test_multi_trade_empty_candles_returns_empty_result() -> None:
    result = run_multi_trade_backtest([], [])

    assert result.metrics.total_trades == 0
    assert result.metrics.total_return_pct == Decimal("0")
    assert result.trades == []
    assert result.equity_points == []


def test_multi_trade_buys_and_closes_at_end_of_period() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    assert result.metrics.total_trades == 1
    trade = result.trades[0]
    assert trade.entry_price == Decimal("101")
    assert trade.exit_price == Decimal("103")
    assert trade.exit_reason == "end_of_period"
    assert trade.pnl_usd > 0
    assert trade.is_winner is True


def test_multi_trade_equity_points_cover_all_candles() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    assert len(result.equity_points) == len(candles)


def test_multi_trade_equity_starts_at_initial_cash() -> None:
    candles = _entry_fixture()
    initial = Decimal("5000")

    result = run_multi_trade_backtest(candles, candles, initial_cash=initial)

    assert result.equity_points[0].equity == initial


def test_multi_trade_fee_rate_reduces_pnl() -> None:
    candles = _entry_fixture()

    result_no_fee = run_multi_trade_backtest(candles, candles, fee_rate=Decimal("0"))
    result_with_fee = run_multi_trade_backtest(candles, candles, fee_rate=Decimal("0.001"))

    assert result_no_fee.metrics.total_return_pct > result_with_fee.metrics.total_return_pct
    assert result_no_fee.trades[0].fees_paid == Decimal("0")
    assert result_with_fee.trades[0].fees_paid > 0


def test_multi_trade_metrics_are_positive_on_winning_trade() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    m = result.metrics
    assert m.total_return_pct > 0
    assert m.win_rate_pct == Decimal("100")
    assert m.winning_trades == 1
    assert m.losing_trades == 0
    assert m.final_capital > Decimal("10000")


def test_multi_trade_trade_index_is_sequential() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    for expected_idx, trade in enumerate(result.trades):
        assert trade.trade_index == expected_idx


def test_multi_trade_entry_value_equals_invested_cash() -> None:
    candles = _entry_fixture()
    initial = Decimal("10000")
    fee_rate = Decimal("0.001")

    result = run_multi_trade_backtest(candles, candles, initial_cash=initial, fee_rate=fee_rate)

    trade = result.trades[0]
    assert trade.entry_value == initial


def test_multi_trade_pnl_matches_equity_delta() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    total_pnl = sum(t.pnl_usd for t in result.trades)
    assert abs(result.metrics.total_return_usd - total_pnl) < Decimal("0.0001")


def test_multi_trade_btc_buy_hold_calculated() -> None:
    candles = _entry_fixture()

    result = run_multi_trade_backtest(candles, candles)

    assert result.metrics.btc_buy_hold_return_pct is not None
    # BTC goes from 90 to 103: ~14.4% gain
    assert result.metrics.btc_buy_hold_return_pct > Decimal("10")
