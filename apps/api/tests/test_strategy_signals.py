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


def test_breakout_signal_blocks_weak_volume() -> None:
    result = evaluate_breakout_entry_signal(
        _snapshot(current_volume=Decimal("19")),
        _allowed_regime(),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "weak_volume"


def test_breakout_signal_blocks_rsi_out_of_range() -> None:
    result = evaluate_breakout_entry_signal(_snapshot(rsi=Decimal("80")), _allowed_regime())

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "rsi_out_of_range"


def test_breakout_signal_blocks_when_regime_is_blocked() -> None:
    result = evaluate_breakout_entry_signal(
        _snapshot(),
        RegimeResult(False, "blocked", {"code": "price_below_sma_200"}),
    )

    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "regime_blocked"


def _allowed_regime() -> RegimeResult:
    return RegimeResult(True, "allowed", {"code": "regime_allowed"})


def _snapshot(
    *,
    close_price: Decimal = Decimal("120"),
    current_volume: Decimal = Decimal("25"),
    rsi: Decimal | None = Decimal("60"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=current_volume,
        sma_50=Decimal("110"),
        sma_200=Decimal("100"),
        rsi=rsi,
        atr=Decimal("3"),
        atr_pct=Decimal("2.5"),
        average_volume=Decimal("20"),
        breakout_high_20=Decimal("119"),
    )

