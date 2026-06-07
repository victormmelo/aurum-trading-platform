from __future__ import annotations

from decimal import Decimal

from app.strategy.types import IndicatorSnapshot, RegimeResult, SignalResult

BUY = "COMPRA"
SELL = "VENDA"
HOLD = "MANTER_POSICAO"
NO_TRADE = "NAO_OPERAR"


def evaluate_breakout_entry_signal(
    snapshot: IndicatorSnapshot | None,
    regime: RegimeResult,
    *,
    atr_stop_multiplier: Decimal = Decimal("2.5"),
) -> SignalResult:
    if not regime.allowed:
        return _no_trade("Regime bloqueia novas entradas", "regime_blocked", regime.reason_payload)

    if snapshot is None:
        return _no_trade("Dados de sinal insuficientes", "missing_snapshot", {})

    payload: dict[str, object] = {
        "close_price": str(snapshot.close_price),
        "breakout_high_20": str(snapshot.breakout_high_20)
        if snapshot.breakout_high_20 is not None
        else None,
        "atr": str(snapshot.atr) if snapshot.atr is not None else None,
        "current_true_range": str(snapshot.current_true_range)
        if snapshot.current_true_range is not None
        else None,
        "atr_stop_multiplier": str(atr_stop_multiplier),
    }

    if snapshot.breakout_high_20 is None:
        return _no_trade("Dados insuficientes para breakout", "missing_breakout_high", payload)

    if snapshot.close_price <= snapshot.breakout_high_20:
        return _no_trade(
            "Preço ainda não rompeu a máxima dos últimos 20 candles",
            "no_breakout",
            payload,
        )

    if (
        snapshot.current_true_range is not None
        and snapshot.atr is not None
        and snapshot.atr > 0
        and snapshot.current_true_range > snapshot.atr * atr_stop_multiplier
    ):
        return _no_trade("Candle de exaustão detectado no breakout", "exhaustion_candle", payload)

    return SignalResult(
        decision=BUY,
        reason="Breakout confirmado com regime válido e sem exaustão",
        reason_payload={"code": "breakout_entry", **payload},
    )


def _no_trade(reason: str, code: str, payload: dict[str, object]) -> SignalResult:
    return SignalResult(
        decision=NO_TRADE,
        reason=reason,
        reason_payload={**payload, "code": code},
    )
