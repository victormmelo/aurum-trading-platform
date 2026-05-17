from decimal import Decimal

from app.strategy.regime import evaluate_regime
from app.strategy.types import IndicatorSnapshot


def test_regime_allows_positive_trend_with_acceptable_volatility() -> None:
    result = evaluate_regime(_snapshot())

    assert result.allowed is True
    assert result.reason_payload["code"] == "regime_allowed"


def test_regime_blocks_when_price_is_below_sma_200() -> None:
    result = evaluate_regime(_snapshot(close_price=Decimal("95")))

    assert result.allowed is False
    assert result.reason_payload["code"] == "price_below_sma_200"


def test_regime_blocks_extreme_volatility() -> None:
    result = evaluate_regime(_snapshot(atr_pct=Decimal("9")))

    assert result.allowed is False
    assert result.reason_payload["code"] == "extreme_volatility"


def test_regime_blocks_missing_indicator_data() -> None:
    result = evaluate_regime(_snapshot(sma_50=None))

    assert result.allowed is False
    assert result.reason_payload["code"] == "missing_moving_average"


def _snapshot(
    *,
    close_price: Decimal = Decimal("120"),
    sma_50: Decimal | None = Decimal("110"),
    sma_200: Decimal | None = Decimal("100"),
    atr_pct: Decimal | None = Decimal("2.5"),
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        close_price=close_price,
        current_volume=Decimal("25"),
        sma_50=sma_50,
        sma_200=sma_200,
        rsi=Decimal("60"),
        atr=Decimal("3"),
        atr_pct=atr_pct,
        average_volume=Decimal("20"),
        breakout_high_20=Decimal("119"),
    )

