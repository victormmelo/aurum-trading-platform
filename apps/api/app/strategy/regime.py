from __future__ import annotations

from decimal import Decimal

from app.strategy.types import IndicatorSnapshot, RegimeResult


def evaluate_regime(
    snapshot: IndicatorSnapshot | None,
    *,
    max_volatility_pct: Decimal = Decimal("8"),
) -> RegimeResult:
    if snapshot is None:
        return _blocked("Dados de regime insuficientes", "missing_snapshot", {})

    payload: dict[str, object] = {
        "close_price": str(snapshot.close_price),
        "sma_50": str(snapshot.sma_50) if snapshot.sma_50 is not None else None,
        "sma_200": str(snapshot.sma_200) if snapshot.sma_200 is not None else None,
        "atr_pct": str(snapshot.atr_pct) if snapshot.atr_pct is not None else None,
        "max_volatility_pct": str(max_volatility_pct),
    }

    if snapshot.sma_50 is None or snapshot.sma_200 is None:
        return _blocked(
            "Dados insuficientes para médias de regime",
            "missing_moving_average",
            payload,
        )

    if snapshot.close_price <= snapshot.sma_200:
        return _blocked("Preço abaixo da média de 200 períodos", "price_below_sma_200", payload)

    if snapshot.sma_50 <= snapshot.sma_200:
        return _blocked(
            "Média de 50 períodos abaixo da média de 200 períodos",
            "sma_50_below_sma_200",
            payload,
        )

    if snapshot.atr_pct is None:
        return _blocked(
            "Dados insuficientes para volatilidade de regime",
            "missing_volatility",
            payload,
        )

    if snapshot.atr_pct > max_volatility_pct:
        return _blocked("Volatilidade acima do limite permitido", "extreme_volatility", payload)

    return RegimeResult(
        allowed=True,
        reason="Regime positivo para operação long-only",
        reason_payload={"code": "regime_allowed", **payload},
    )


def _blocked(reason: str, code: str, payload: dict[str, object]) -> RegimeResult:
    return RegimeResult(
        allowed=False,
        reason=reason,
        reason_payload={"code": code, **payload},
    )
