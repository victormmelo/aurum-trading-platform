from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MarketSnapshot, PortfolioSnapshot, Position
from app.execution.binance_private import BinancePrivateClient


@dataclass(frozen=True)
class PortfolioReconciliationResult:
    snapshot: PortfolioSnapshot
    position: Position


class BinancePortfolioReconciler:
    def __init__(self, client: BinancePrivateClient) -> None:
        self.client = client

    def reconcile(
        self,
        session: Session,
        *,
        environment: str,
        symbol: str,
        now: datetime | None = None,
    ) -> PortfolioReconciliationResult:
        captured_at = now or datetime.now(UTC)
        account = self.client.get_account()
        balances = _balances_by_asset(account)
        usdt_balance = balances.get("USDT", Decimal("0"))
        btc_balance = balances.get("BTC", Decimal("0"))
        price = _latest_price(session, environment=environment, symbol=symbol)
        btc_market_value = btc_balance * price
        total_equity = usdt_balance + btc_market_value

        position = _get_or_create_position(session, environment=environment, symbol=symbol)
        if btc_balance > 0:
            if position.quantity <= 0:
                position.average_cost = price
                position.remaining_cost = btc_market_value
            else:
                position.remaining_cost = position.average_cost * btc_balance
            position.quantity = btc_balance
        else:
            position.quantity = Decimal("0")
            position.remaining_cost = Decimal("0")
        position.last_reconciled_at = captured_at

        invested_value = position.remaining_cost
        average_cost = position.average_cost if btc_balance > 0 else Decimal("0")
        unrealized_pnl = btc_market_value - invested_value if btc_balance > 0 else Decimal("0")
        exposure_pct = (
            btc_market_value / total_equity * Decimal("100")
            if total_equity > 0
            else Decimal("0")
        )
        snapshot = PortfolioSnapshot(
            environment=environment,
            captured_at=captured_at,
            symbol=symbol,
            usdt_balance=usdt_balance,
            btc_balance=btc_balance,
            btc_market_price=price,
            btc_market_value=btc_market_value,
            invested_value=invested_value,
            average_cost=average_cost,
            total_equity=total_equity,
            exposure_pct=exposure_pct,
            realized_pnl=position.realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_fees_usdt=position.total_fees_usdt,
            source_payload={
                "source": "binance_spot_testnet_account",
                "accountType": account.get("accountType"),
                "permissions": account.get("permissions", []),
            },
        )
        session.add(position)
        session.add(snapshot)
        session.flush()
        return PortfolioReconciliationResult(snapshot=snapshot, position=position)


def _balances_by_asset(account: dict[str, Any]) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = {}
    for balance in account.get("balances", []):
        asset = str(balance.get("asset", "")).upper()
        if not asset:
            continue
        free = Decimal(str(balance.get("free", "0")))
        locked = Decimal(str(balance.get("locked", "0")))
        balances[asset] = free + locked
    return balances


def _latest_price(session: Session, *, environment: str, symbol: str) -> Decimal:
    snapshot = session.scalars(
        select(MarketSnapshot)
        .where(MarketSnapshot.environment == environment, MarketSnapshot.symbol == symbol)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(1)
    ).first()
    return snapshot.last_price if snapshot is not None else Decimal("0")


def _get_or_create_position(session: Session, *, environment: str, symbol: str) -> Position:
    position = session.scalars(
        select(Position).where(
            Position.environment == environment,
            Position.symbol == symbol,
            Position.asset == "BTC",
            Position.side == "LONG",
        )
    ).first()
    if position is not None:
        return position
    return Position(
        environment=environment,
        symbol=symbol,
        asset="BTC",
        side="LONG",
        quantity=Decimal("0"),
        average_cost=Decimal("0"),
        remaining_cost=Decimal("0"),
        realized_pnl=Decimal("0"),
        total_fees_usdt=Decimal("0"),
    )
