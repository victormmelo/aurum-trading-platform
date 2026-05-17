from decimal import Decimal

from app.strategy.exits import evaluate_exit_signal
from app.strategy.types import ExitPositionState, IndicatorSnapshot


def test_exit_signal_sells_when_price_loses_sma_200() -> None:
    result = evaluate_exit_signal(_snapshot(close_price=Decimal("99")), _position())

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "trend_exit_price_below_sma_200"


def test_exit_signal_sells_when_sma_50_loses_sma_200() -> None:
    result = evaluate_exit_signal(_snapshot(sma_50=Decimal("98")), _position())

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "trend_exit_sma_cross"


def test_exit_signal_sells_when_atr_stop_is_hit() -> None:
    result = evaluate_exit_signal(
        _snapshot(close_price=Decimal("94"), sma_200=Decimal("90")),
        _position(),
    )

    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "atr_stop"


def test_exit_signal_sells_when_trailing_stop_is_hit() -> None:
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


def _position() -> ExitPositionState:
    return ExitPositionState(
        quantity=Decimal("0.5"),
        entry_price=Decimal("100"),
        highest_price_since_entry=Decimal("120"),
    )


def _snapshot(
    *,
    close_price: Decimal = Decimal("118"),
    sma_50: Decimal | None = Decimal("110"),
    sma_200: Decimal | None = Decimal("100"),
    atr: Decimal | None = Decimal("3"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=Decimal("25"),
        sma_50=sma_50,
        sma_200=sma_200,
        rsi=Decimal("60"),
        atr=atr,
        atr_pct=Decimal("2.5") if atr is not None else None,
        average_volume=Decimal("20"),
        breakout_high_20=Decimal("119"),
    )
