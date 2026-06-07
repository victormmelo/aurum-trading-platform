from decimal import Decimal

from app.strategy.regime import evaluate_regime
from app.strategy.types import IndicatorSnapshot


def test_regime_allows_when_price_above_sma_200_with_positive_slope() -> None:
    result = evaluate_regime(_snapshot())

    assert result.allowed is True
    assert result.reason_payload["code"] == "regime_allowed"


def test_regime_blocks_when_price_is_below_sma_200() -> None:
    result = evaluate_regime(_snapshot(close_price=Decimal("95")))

    assert result.allowed is False
    assert result.reason_payload["code"] == "price_below_sma_200"


def test_regime_blocks_when_sma_200_slope_is_negative() -> None:
    # sma_200 (100) <= sma_long_prev (105) → slope negative
    result = evaluate_regime(_snapshot(sma_200=Decimal("100"), sma_long_prev=Decimal("105")))

    assert result.allowed is False
    assert result.reason_payload["code"] == "sma_200_slope_negative"


def test_regime_blocks_when_sma_200_slope_is_flat() -> None:
    result = evaluate_regime(_snapshot(sma_200=Decimal("100"), sma_long_prev=Decimal("100")))

    assert result.allowed is False
    assert result.reason_payload["code"] == "sma_200_slope_negative"


def test_regime_blocks_when_sma_slope_data_is_missing() -> None:
    result = evaluate_regime(_snapshot(sma_long_prev=None))

    assert result.allowed is False
    assert result.reason_payload["code"] == "missing_sma_slope"


def test_regime_blocks_when_sma_200_is_missing() -> None:
    result = evaluate_regime(_snapshot(sma_200=None))

    assert result.allowed is False
    assert result.reason_payload["code"] == "missing_sma_200"


def test_regime_blocks_when_snapshot_is_none() -> None:
    result = evaluate_regime(None)

    assert result.allowed is False
    assert result.reason_payload["code"] == "missing_snapshot"


def _snapshot(
    *,
    close_price: Decimal = Decimal("120"),
    sma_200: Decimal | None = Decimal("100"),
    sma_long_prev: Decimal | None = Decimal("95"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=Decimal("25"),
        sma_50=Decimal("110"),
        sma_200=sma_200,
        rsi=Decimal("60"),
        atr=Decimal("3"),
        atr_pct=Decimal("2.5"),
        average_volume=Decimal("20"),
        breakout_high_20=Decimal("119"),
        sma_long_prev=sma_long_prev,
        current_true_range=Decimal("4"),
    )
