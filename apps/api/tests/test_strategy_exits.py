from decimal import Decimal

from app.strategy.exits import evaluate_exit_signal
from app.strategy.types import ExitPositionState, IndicatorSnapshot, RegimeResult


def test_exit_signal_sells_when_regime_turns_off() -> None:
    regime = RegimeResult(False, "regime off", {"code": "sma_200_slope_negative"})
    result = evaluate_exit_signal(_snapshot(), _position(), regime)

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "regime_exit"


def test_exit_signal_sells_when_atr_stop_is_hit() -> None:
    # entry=100, atr=3, multiplier=2.5 → stop=92.5; close=92 ≤ 92.5
    result = evaluate_exit_signal(
        _snapshot(close_price=Decimal("92")),
        _position(),
    )

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "atr_stop"


def test_exit_signal_sells_when_trailing_stop_is_hit() -> None:
    # highest=120, atr=3, trailing_mult=3.0 → trailing=111; close=111 ≤ 111
    result = evaluate_exit_signal(_snapshot(close_price=Decimal("111")), _position())

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "trailing_stop"


def test_exit_signal_holds_without_open_position() -> None:
    result = evaluate_exit_signal(_snapshot(), None)

    assert result.decision == "MANTER_POSICAO"
    assert result.reason_payload["code"] == "no_open_position"


def test_exit_signal_holds_when_atr_is_missing() -> None:
    result = evaluate_exit_signal(_snapshot(atr=None), _position())

    assert result.decision == "MANTER_POSICAO"
    assert result.reason_payload["code"] == "missing_atr"


def test_exit_signal_holds_when_price_is_above_all_stops() -> None:
    # entry=100, atr=3 → atr_stop=92.5, trailing_stop=111; close=118 above both
    result = evaluate_exit_signal(_snapshot(close_price=Decimal("118")), _position())

    assert result.decision == "MANTER_POSICAO"
    assert result.reason_payload["code"] == "exit_conditions_not_met"


def test_exit_signal_holds_when_regime_is_none() -> None:
    result = evaluate_exit_signal(_snapshot(), _position(), None)

    assert result.decision == "MANTER_POSICAO"


def _position() -> ExitPositionState:
    return ExitPositionState(
        quantity=Decimal("0.5"),
        entry_price=Decimal("100"),
        highest_price_since_entry=Decimal("120"),
    )


def _snapshot(
    *,
    close_price: Decimal = Decimal("118"),
    atr: Decimal | None = Decimal("3"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=Decimal("25"),
        sma_50=Decimal("110"),
        sma_200=Decimal("100"),
        rsi=Decimal("60"),
        atr=atr,
        atr_pct=Decimal("2.5") if atr is not None else None,
        average_volume=Decimal("20"),
        breakout_high_20=Decimal("119"),
        sma_long_prev=Decimal("95"),
        current_true_range=Decimal("4"),
    )
