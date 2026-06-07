from decimal import Decimal

from app.strategy.signals import evaluate_breakout_entry_signal
from app.strategy.types import IndicatorSnapshot, RegimeResult


def test_breakout_signal_buys_when_all_filters_pass() -> None:
    result = evaluate_breakout_entry_signal(_snapshot(), _allowed_regime())

    assert result.decision == "COMPRA"
    assert result.reason_payload["code"] == "breakout_entry"


def test_breakout_signal_blocks_when_price_has_not_broken_out() -> None:
    result = evaluate_breakout_entry_signal(
        _snapshot(close_price=Decimal("118")),
        _allowed_regime(),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "no_breakout"


def test_breakout_signal_blocks_exhaustion_candle() -> None:
    # atr=3, multiplier=2.5 → threshold=7.5; true_range=8 > 7.5 → exhaustion
    result = evaluate_breakout_entry_signal(
        _snapshot(current_true_range=Decimal("8")),
        _allowed_regime(),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "exhaustion_candle"


def test_breakout_signal_allows_when_true_range_is_within_limit() -> None:
    # atr=3, multiplier=2.5 → threshold=7.5; true_range=7 ≤ 7.5 → no exhaustion
    result = evaluate_breakout_entry_signal(
        _snapshot(current_true_range=Decimal("7")),
        _allowed_regime(),
    )

    assert result.decision == "COMPRA"


def test_breakout_signal_blocks_when_regime_is_blocked() -> None:
    result = evaluate_breakout_entry_signal(
        _snapshot(),
        RegimeResult(False, "blocked", {"code": "price_below_sma_200"}),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "regime_blocked"


def test_breakout_signal_blocks_missing_breakout_high() -> None:
    result = evaluate_breakout_entry_signal(
        _snapshot(breakout_high_20=None),
        _allowed_regime(),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "missing_breakout_high"


def _allowed_regime() -> RegimeResult:
    return RegimeResult(True, "allowed", {"code": "regime_allowed"})


def _snapshot(
    *,
    close_price: Decimal = Decimal("120"),
    breakout_high_20: Decimal | None = Decimal("119"),
    current_true_range: Decimal | None = Decimal("4"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=Decimal("25"),
        sma_50=Decimal("110"),
        sma_200=Decimal("100"),
        rsi=Decimal("60"),
        atr=Decimal("3"),
        atr_pct=Decimal("2.5"),
        average_volume=Decimal("20"),
        breakout_high_20=breakout_high_20,
        sma_long_prev=Decimal("95"),
        current_true_range=current_true_range,
    )
