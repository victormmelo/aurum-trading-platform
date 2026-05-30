from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.db.models import MarketSnapshot, PortfolioSnapshot, Position
from app.portfolio.reconciliation import BinancePortfolioReconciler

NOW = datetime(2026, 5, 30, 12, 0, tzinfo=UTC)


def test_reconciler_reads_binance_balances_and_writes_snapshot_and_position() -> None:
    session = FakeSession(
        scalars=[
            MarketSnapshot(
                environment="testnet",
                symbol="BTCUSDT",
                captured_at=NOW,
                last_price=Decimal("100000"),
                indicators={},
                source_payload={},
            ),
            None,
        ]
    )
    client = FakeClient(
        {
            "accountType": "SPOT",
            "permissions": ["SPOT"],
            "balances": [
                {"asset": "BTC", "free": "0.01000000", "locked": "0.00200000"},
                {"asset": "USDT", "free": "500", "locked": "25"},
            ],
        }
    )

    result = BinancePortfolioReconciler(client).reconcile(
        session,
        environment="testnet",
        symbol="BTCUSDT",
        now=NOW,
    )

    assert isinstance(result.snapshot, PortfolioSnapshot)
    assert isinstance(result.position, Position)
    assert result.snapshot.usdt_balance == Decimal("525")
    assert result.snapshot.btc_balance == Decimal("0.01200000")
    assert result.snapshot.btc_market_value == Decimal("1200.00000000")
    assert result.snapshot.total_equity == Decimal("1725.00000000")
    assert result.snapshot.source_payload["source"] == "binance_spot_testnet_account"
    assert result.position.quantity == Decimal("0.01200000")
    assert result.position.average_cost == Decimal("100000")
    assert len(session.added) == 2


class FakeClient:
    def __init__(self, account: dict) -> None:
        self.account = account

    def get_account(self) -> dict:
        return self.account


class FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def first(self):  # noqa: ANN201
        return self.value


class FakeSession:
    def __init__(self, *, scalars: list) -> None:
        self._scalars = scalars
        self.added = []
        self.flushes = 0

    def scalars(self, statement):  # noqa: ANN001, ANN201, ARG002
        return FakeScalarResult(self._scalars.pop(0))

    def add(self, value) -> None:  # noqa: ANN001
        self.added.append(value)

    def flush(self) -> None:
        self.flushes += 1
