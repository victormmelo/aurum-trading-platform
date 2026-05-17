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
    min_rsi: Decimal = Decimal("50"),
    max_rsi: Decimal = Decimal("75"),
) -> SignalResult:
    if not regime.allowed:
        return _no_trade("Regime bloqueia novas entradas", "regime_blocked", regime.reason_payload)

    if snapshot is None:
        return _no_trade("Dados de sinal insuficientes", "missing_snapshot", {})

    payload: dict[str, object] = {
        "close_price": str(snapshot.close_price),
        "current_volume": str(snapshot.current_volume),
        "breakout_high_20": str(snapshot.breakout_high_20)
        if snapshot.breakout_high_20 is not None
        else None,
        "average_volume": str(snapshot.average_volume)
        if snapshot.average_volume is not None
        else None,
        "rsi": str(snapshot.rsi) if snapshot.rsi is not None else None,
        "min_rsi": str(min_rsi),
        "max_rsi": str(max_rsi),
    }

    if snapshot.breakout_high_20 is None:
        return _no_trade("Dados insuficientes para breakout", "missing_breakout_high", payload)

    if snapshot.average_volume is None:
        return _no_trade(
            "Dados insuficientes para média de volume",
            "missing_average_volume",
            payload,
        )

    if snapshot.rsi is None:
        return _no_trade("Dados insuficientes para RSI", "missing_rsi", payload)

    if snapshot.close_price <= snapshot.breakout_high_20:
        return _no_trade(
            "Preço ainda não rompeu a máxima dos últimos 20 candles",
            "no_breakout",
            payload,
        )

    if snapshot.current_volume <= snapshot.average_volume:
        return _no_trade("Volume do rompimento abaixo da média recente", "weak_volume", payload)

    if snapshot.rsi < min_rsi or snapshot.rsi > max_rsi:
        return _no_trade("RSI fora da faixa permitida para entrada", "rsi_out_of_range", payload)

    return SignalResult(
        decision=BUY,
        reason="Breakout confirmado com regime, volume e RSI válidos",
        reason_payload={"code": "breakout_entry", **payload},
    )


def _no_trade(reason: str, code: str, payload: dict[str, object]) -> SignalResult:
    return SignalResult(
        decision=NO_TRADE,
        reason=reason,
        reason_payload={**payload, "code": code},
    )
