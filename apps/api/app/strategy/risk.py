from __future__ import annotations

from decimal import Decimal

from app.strategy.signals import BUY, NO_TRADE
from app.strategy.types import RiskConfig, RiskResult, RiskState, SignalResult

ONE_HUNDRED = Decimal("100")
ACTIVE_STATUSES = {"running"}
BLOCKING_STATUSES = {"paused", "emergency_stop"}


def evaluate_risk(
    candidate: SignalResult,
    state: RiskState,
    config: RiskConfig,
) -> RiskResult:
    payload: dict[str, object] = {
        "candidate_decision": candidate.decision,
        "bot_status": state.bot_status,
        "daily_pnl_pct": str(state.daily_pnl_pct),
        "daily_loss_limit_pct": str(config.daily_loss_limit_pct),
        "current_exposure_pct": str(state.current_exposure_pct),
        "projected_order_notional": str(state.projected_order_notional),
        "total_equity": str(state.total_equity),
        "max_exposure_pct": str(config.max_exposure_pct),
    }

    if state.bot_status in BLOCKING_STATUSES:
        return _blocked(
            NO_TRADE,
            "Robô pausado ou em parada de emergência",
            "bot_not_running",
            payload,
        )

    if state.bot_status not in ACTIVE_STATUSES:
        return _blocked(
            NO_TRADE,
            "Estado operacional do robô não permite operar",
            "unknown_bot_status",
            payload,
        )

    if candidate.decision != BUY:
        return RiskResult(
            allowed=True,
            decision=candidate.decision,
            reason="Decisão não abre nova exposição",
            reason_payload={"code": "no_new_exposure", **payload},
        )

    if state.daily_pnl_pct <= -config.daily_loss_limit_pct:
        return _blocked(
            NO_TRADE,
            "Limite de perda diária atingido",
            "daily_loss_limit_reached",
            payload,
        )

    if state.total_equity <= 0:
        return _blocked(
            NO_TRADE,
            "Patrimônio total inválido para cálculo de risco",
            "invalid_equity",
            payload,
        )

    projected_exposure_pct = state.current_exposure_pct + (
        state.projected_order_notional / state.total_equity * ONE_HUNDRED
    )
    payload["projected_exposure_pct"] = str(projected_exposure_pct)

    if projected_exposure_pct > config.max_exposure_pct:
        return _blocked(
            NO_TRADE,
            "Exposição projetada acima do limite máximo",
            "max_exposure_exceeded",
            payload,
        )

    return RiskResult(
        allowed=True,
        decision=candidate.decision,
        reason="Risco permite nova compra",
        reason_payload={"code": "risk_allowed", **payload},
    )


def _blocked(
    decision: str,
    reason: str,
    code: str,
    payload: dict[str, object],
) -> RiskResult:
    return RiskResult(
        allowed=False,
        decision=decision,
        reason=reason,
        reason_payload={"code": code, **payload},
    )
