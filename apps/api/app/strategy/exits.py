from __future__ import annotations

from decimal import Decimal

from app.strategy.signals import HOLD, SELL
from app.strategy.types import ExitPositionState, IndicatorSnapshot, SignalResult


def evaluate_exit_signal(
    snapshot: IndicatorSnapshot | None,
    position: ExitPositionState | None,
    *,
    atr_stop_multiplier: Decimal = Decimal("2"),
    trailing_stop_multiplier: Decimal = Decimal("3"),
) -> SignalResult:
    if position is None or position.quantity <= 0:
        return _hold("Sem posição long aberta para gerenciar", "no_open_position", {})

    payload: dict[str, object] = {
        "entry_price": str(position.entry_price),
        "quantity": str(position.quantity),
        "highest_price_since_entry": str(position.highest_price_since_entry),
        "atr_stop_multiplier": str(atr_stop_multiplier),
        "trailing_stop_multiplier": str(trailing_stop_multiplier),
    }

    if snapshot is None:
        return _hold("Dados de saída insuficientes", "missing_snapshot", payload)

    payload.update(
        {
            "close_price": str(snapshot.close_price),
            "sma_50": str(snapshot.sma_50) if snapshot.sma_50 is not None else None,
            "sma_200": str(snapshot.sma_200) if snapshot.sma_200 is not None else None,
            "atr": str(snapshot.atr) if snapshot.atr is not None else None,
        }
    )

    if snapshot.sma_50 is None or snapshot.sma_200 is None:
        return _hold(
            "Dados insuficientes para avaliar perda de tendência",
            "missing_trend",
            payload,
        )

    if snapshot.close_price <= snapshot.sma_200:
        return _sell(
            "Preço perdeu a média de 200 períodos",
            "trend_exit_price_below_sma_200",
            payload,
        )

    if snapshot.sma_50 <= snapshot.sma_200:
        return _sell(
            "Média de 50 períodos perdeu a média de 200 períodos",
            "trend_exit_sma_cross",
            payload,
        )

    if snapshot.atr is None or snapshot.atr <= 0:
        return _hold("Dados insuficientes para stops por ATR", "missing_atr", payload)

    atr_stop_price = position.entry_price - (snapshot.atr * atr_stop_multiplier)
    payload["atr_stop_price"] = str(atr_stop_price)
    if snapshot.close_price <= atr_stop_price:
        return _sell("Stop por ATR atingido", "atr_stop", payload)

    trailing_stop_price = position.highest_price_since_entry - (
        snapshot.atr * trailing_stop_multiplier
    )
    payload["trailing_stop_price"] = str(trailing_stop_price)
    if snapshot.close_price <= trailing_stop_price:
        return _sell("Trailing stop por ATR atingido", "trailing_stop", payload)

    return _hold("Posição long mantida", "exit_conditions_not_met", payload)


def _sell(reason: str, code: str, payload: dict[str, object]) -> SignalResult:
    return SignalResult(decision=SELL, reason=reason, reason_payload={"code": code, **payload})


def _hold(reason: str, code: str, payload: dict[str, object]) -> SignalResult:
    return SignalResult(decision=HOLD, reason=reason, reason_payload={"code": code, **payload})
