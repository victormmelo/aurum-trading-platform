from __future__ import annotations

from app.strategy.types import IndicatorSnapshot, RegimeResult


def evaluate_regime(snapshot: IndicatorSnapshot | None) -> RegimeResult:
    if snapshot is None:
        return _blocked("Dados de regime insuficientes", "missing_snapshot", {})

    payload: dict[str, object] = {
        "close_price": str(snapshot.close_price),
        "sma_200": str(snapshot.sma_200) if snapshot.sma_200 is not None else None,
        "sma_long_prev": str(snapshot.sma_long_prev)
        if snapshot.sma_long_prev is not None
        else None,
    }

    if snapshot.sma_200 is None:
        return _blocked("Dados insuficientes para SMA-200", "missing_sma_200", payload)

    if snapshot.close_price <= snapshot.sma_200:
        return _blocked("Preço abaixo da SMA-200", "price_below_sma_200", payload)

    if snapshot.sma_long_prev is None:
        return _blocked(
            "Dados insuficientes para inclinação da SMA-200",
            "missing_sma_slope",
            payload,
        )

    if snapshot.sma_200 <= snapshot.sma_long_prev:
        return _blocked("SMA-200 sem inclinação positiva", "sma_200_slope_negative", payload)

    return RegimeResult(
        allowed=True,
        reason="Regime positivo: preço acima da SMA-200 com inclinação positiva",
        reason_payload={"code": "regime_allowed", **payload},
    )


def _blocked(reason: str, code: str, payload: dict[str, object]) -> RegimeResult:
    return RegimeResult(
        allowed=False,
        reason=reason,
        reason_payload={"code": code, **payload},
    )
