from decimal import Decimal

from app.strategy.risk import evaluate_risk
from app.strategy.types import RiskConfig, RiskState, SignalResult


def test_risk_allows_buy_within_limits() -> None:
    result = evaluate_risk(_candidate("COMPRA"), _state(), _config())

    assert result.allowed is True
    assert result.decision == "COMPRA"
    assert result.reason_payload["code"] == "risk_allowed"


def test_risk_blocks_daily_loss_limit() -> None:
    result = evaluate_risk(
        _candidate("COMPRA"),
        _state(daily_pnl_pct=Decimal("-2")),
        _config(),
    )

    assert result.allowed is False
    assert result.decision == "NAO_OPERAR"
    assert result.reason_payload["code"] == "daily_loss_limit_reached"


def test_risk_blocks_projected_exposure_above_limit() -> None:
    result = evaluate_risk(
        _candidate("COMPRA"),
        _state(current_exposure_pct=Decimal("45"), projected_order_notional=Decimal("1000")),
        _config(max_exposure_pct=Decimal("50")),
    )

    assert result.allowed is False
    assert result.reason_payload["code"] == "max_exposure_exceeded"


def test_risk_blocks_when_bot_is_paused() -> None:
    result = evaluate_risk(_candidate("COMPRA"), _state(bot_status="paused"), _config())

    assert result.allowed is False
    assert result.reason_payload["code"] == "bot_not_running"


def test_risk_preserves_non_buy_decisions() -> None:
    result = evaluate_risk(_candidate("VENDA"), _state(), _config())

    assert result.allowed is True
    assert result.decision == "VENDA"
    assert result.reason_payload["code"] == "no_new_exposure"


def _candidate(decision: str) -> SignalResult:
    return SignalResult(decision=decision, reason="candidate", reason_payload={"code": "candidate"})


def _state(
    *,
    bot_status: str = "running",
    daily_pnl_pct: Decimal = Decimal("0"),
    current_exposure_pct: Decimal = Decimal("0"),
    projected_order_notional: Decimal = Decimal("1000"),
    total_equity: Decimal = Decimal("10000"),
) -> RiskState:
    return RiskState(
        bot_status=bot_status,
        daily_pnl_pct=daily_pnl_pct,
        current_exposure_pct=current_exposure_pct,
        projected_order_notional=projected_order_notional,
        total_equity=total_equity,
    )


def _config(
    *,
    risk_per_trade_pct: Decimal = Decimal("1"),
    daily_loss_limit_pct: Decimal = Decimal("2"),
    max_exposure_pct: Decimal = Decimal("50"),
) -> RiskConfig:
    return RiskConfig(
        risk_per_trade_pct=risk_per_trade_pct,
        daily_loss_limit_pct=daily_loss_limit_pct,
        max_exposure_pct=max_exposure_pct,
    )
