from datetime import UTC, datetime
from decimal import Decimal

from app.market.binance import BinanceCandle
from app.market.importer import import_historical_candles, insert_market_candles


class ExecuteResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class FakeSession:
    def __init__(self, rowcounts: list[int]) -> None:
        self.rowcounts = rowcounts
        self.executed = []
        self.commits = 0

    def execute(self, statement):  # noqa: ANN001
        self.executed.append(statement)
        return ExecuteResult(self.rowcounts.pop(0))

    def commit(self) -> None:
        self.commits += 1


class FakeClient:
    def __init__(self, candles_by_interval: dict[str, list[BinanceCandle]]) -> None:
        self.candles_by_interval = candles_by_interval
        self.calls = []

    def get_klines(  # noqa: ANN001
        self, symbol, interval, *, limit, start_time=None, end_time=None
    ):
        self.calls.append((symbol, interval, limit, start_time, end_time))
        return self.candles_by_interval[interval]


def test_insert_market_candles_uses_database_conflict_handling() -> None:
    session = FakeSession([1])

    inserted = insert_market_candles(
        session,  # type: ignore[arg-type]
        environment="testnet",
        candles=[_candle("1h")],
    )

    assert inserted == 1
    assert len(session.executed) == 1
    compiled = str(session.executed[0])
    assert "ON CONFLICT ON CONSTRAINT uq_market_candles_source_window DO NOTHING" in compiled


def test_import_historical_candles_reports_idempotent_second_insert() -> None:
    session = FakeSession([1, 0])
    client = FakeClient({"1h": [_candle("1h")], "4h": [_candle("4h")]})

    results = import_historical_candles(
        session,  # type: ignore[arg-type]
        client,  # type: ignore[arg-type]
        environment="testnet",
        symbol="BTCUSDT",
        intervals=["1h", "4h"],
        limit=10,
    )

    assert [(result.interval, result.fetched, result.inserted) for result in results] == [
        ("1h", 1, 1),
        ("4h", 1, 0),
    ]
    assert client.calls == [
        ("BTCUSDT", "1h", 10, None, None),
        ("BTCUSDT", "4h", 10, None, None),
    ]
    assert session.commits == 1


def _candle(interval: str) -> BinanceCandle:
    return BinanceCandle(
        symbol="BTCUSDT",
        interval=interval,
        open_time=datetime(2024, 3, 9, 16, 0, tzinfo=UTC),
        close_time=datetime(2024, 3, 9, 16, 59, 59, 999000, tzinfo=UTC),
        open_price=Decimal("100"),
        high_price=Decimal("110"),
        low_price=Decimal("90"),
        close_price=Decimal("105"),
        volume=Decimal("1.5"),
        quote_volume=Decimal("157.5"),
        trade_count=10,
        source_payload={"kline": []},
    )
