from __future__ import annotations

from decimal import Decimal

from app.strategy.types import PositionSizingInput, PositionSizingResult, RiskConfig

ONE_HUNDRED = Decimal("100")


def calculate_position_size(
    sizing_input: PositionSizingInput,
    config: RiskConfig,
    *,
    atr_stop_multiplier: Decimal = Decimal("2"),
) -> PositionSizingResult:
    payload: dict[str, object] = {
        "entry_price": str(sizing_input.entry_price),
        "atr": str(sizing_input.atr) if sizing_input.atr is not None else None,
        "available_cash": str(sizing_input.available_cash),
        "total_equity": str(sizing_input.total_equity),
        "current_exposure_notional": str(sizing_input.current_exposure_notional),
        "risk_per_trade_pct": str(config.risk_per_trade_pct),
        "max_exposure_pct": str(config.max_exposure_pct),
        "atr_stop_multiplier": str(atr_stop_multiplier),
    }

    if sizing_input.entry_price <= 0:
        return _zero("Preço de entrada inválido", "invalid_entry_price", payload)

    if sizing_input.atr is None or sizing_input.atr <= 0:
        return _zero("ATR inválido ou ausente para sizing", "invalid_atr", payload)

    if sizing_input.available_cash <= 0:
        return _zero("Caixa disponível insuficiente", "insufficient_cash", payload)

    if sizing_input.total_equity <= 0:
        return _zero("Patrimônio total inválido", "invalid_equity", payload)

    stop_distance = sizing_input.atr * atr_stop_multiplier
    risk_budget = sizing_input.total_equity * config.risk_per_trade_pct / ONE_HUNDRED
    max_quantity_by_risk = risk_budget / stop_distance
    max_notional_by_risk = max_quantity_by_risk * sizing_input.entry_price
    max_exposure_notional = sizing_input.total_equity * config.max_exposure_pct / ONE_HUNDRED
    remaining_exposure_notional = max_exposure_notional - sizing_input.current_exposure_notional

    payload.update(
        {
            "stop_distance": str(stop_distance),
            "risk_budget": str(risk_budget),
            "max_notional_by_risk": str(max_notional_by_risk),
            "remaining_exposure_notional": str(remaining_exposure_notional),
        }
    )

    if remaining_exposure_notional <= 0:
        return _zero("Exposição máxima já atingida", "max_exposure_reached", payload)

    notional = min(
        max_notional_by_risk,
        sizing_input.available_cash,
        remaining_exposure_notional,
    )
    if notional <= 0:
        return _zero("Sizing resultou em notional zero", "zero_notional", payload)

    quantity = notional / sizing_input.entry_price
    payload.update({"notional": str(notional), "quantity": str(quantity)})
    return PositionSizingResult(
        quantity=quantity,
        notional=notional,
        reason="Tamanho de posição calculado",
        reason_payload={"code": "position_size_calculated", **payload},
    )


def _zero(reason: str, code: str, payload: dict[str, object]) -> PositionSizingResult:
    return PositionSizingResult(
        quantity=Decimal("0"),
        notional=Decimal("0"),
        reason=reason,
        reason_payload={"code": code, **payload},
    )
