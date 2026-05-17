from decimal import Decimal

from app.strategy.sizing import calculate_position_size
from app.strategy.types import PositionSizingInput, RiskConfig


def test_position_sizing_limits_by_risk_budget() -> None:
    result = calculate_position_size(_sizing_input(), _config(risk_per_trade_pct=Decimal("1")))

    assert result.notional == Decimal("5000")
    assert result.quantity == Decimal("0.5")
    assert result.reason_payload["code"] == "position_size_calculated"


def test_position_sizing_limits_by_available_cash() -> None:
    result = calculate_position_size(
        _sizing_input(available_cash=Decimal("2000")),
        _config(),
    )

    assert result.notional == Decimal("2000")
    assert result.quantity == Decimal("0.2")


def test_position_sizing_limits_by_remaining_exposure() -> None:
    result = calculate_position_size(
        _sizing_input(current_exposure_notional=Decimal("4500")),
        _config(max_exposure_pct=Decimal("50")),
    )

    assert result.notional == Decimal("500")
    assert result.quantity == Decimal("0.05")


def test_position_sizing_returns_zero_for_missing_atr() -> None:
    result = calculate_position_size(_sizing_input(atr=None), _config())

    assert result.notional == Decimal("0")
    assert result.quantity == Decimal("0")
    assert result.reason_payload["code"] == "invalid_atr"


def test_position_sizing_returns_zero_when_exposure_is_full() -> None:
    result = calculate_position_size(
        _sizing_input(current_exposure_notional=Decimal("5000")),
        _config(max_exposure_pct=Decimal("50")),
    )

    assert result.notional == Decimal("0")
    assert result.reason_payload["code"] == "max_exposure_reached"


def _sizing_input(
    *,
    entry_price: Decimal = Decimal("10000"),
    atr: Decimal | None = Decimal("100"),
    available_cash: Decimal = Decimal("10000"),
    total_equity: Decimal = Decimal("10000"),
    current_exposure_notional: Decimal = Decimal("0"),
) -> PositionSizingInput:
    return PositionSizingInput(
        entry_price=entry_price,
        atr=atr,
        available_cash=available_cash,
        total_equity=total_equity,
        current_exposure_notional=current_exposure_notional,
    )


def _config(
    *,
    risk_per_trade_pct: Decimal = Decimal("10"),
    daily_loss_limit_pct: Decimal = Decimal("2"),
    max_exposure_pct: Decimal = Decimal("100"),
) -> RiskConfig:
    return RiskConfig(
        risk_per_trade_pct=risk_per_trade_pct,
        daily_loss_limit_pct=daily_loss_limit_pct,
        max_exposure_pct=max_exposure_pct,
    )
