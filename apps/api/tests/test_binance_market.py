from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.market.binance import BinanceMarketError, BinanceMarketClient, parse_kline


def test_parse_kline_normalizes_binance_payload() -> None:
    candle = parse_kline(
        "BTCUSDT",
        "1h",
        [
            1710000000000,
            "100.10",
            "110.20",
            "99.90",
            "105.50",
            "12.345",
            1710003599999,
            "1300.50",
            42,
            "0",
            "0",
            "0",
        ],
    )

    assert candle.symbol == "BTCUSDT"
    assert candle.interval == "1h"
    assert candle.open_time == datetime(2024, 3, 9, 16, 0, tzinfo=timezone.utc)
    assert candle.close_time == datetime(2024, 3, 9, 16, 59, 59, 999000, tzinfo=timezone.utc)
    assert candle.open_price == Decimal("100.10")
    assert candle.high_price == Decimal("110.20")
    assert candle.low_price == Decimal("99.90")
    assert candle.close_price == Decimal("105.50")
    assert candle.volume == Decimal("12.345")
    assert candle.quote_volume == Decimal("1300.50")
    assert candle.trade_count == 42
    assert candle.source_payload["kline"][0] == 1710000000000


def test_parse_kline_rejects_short_payload() -> None:
    with pytest.raises(BinanceMarketError, match="fewer fields"):
        parse_kline("BTCUSDT", "1h", [1710000000000])


def test_client_builds_read_only_kline_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_urls: list[str] = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self) -> bytes:
            return (
                b"[[1710000000000,\"100\",\"110\",\"90\",\"105\",\"1\","
                b"1710003599999,\"105\",10,\"0\",\"0\",\"0\"]]"
            )

    def fake_urlopen(request, timeout):  # noqa: ANN001
        seen_urls.append(request.full_url)
        assert timeout == 10.0
        return Response()

    monkeypatch.setattr("app.market.binance.urlopen", fake_urlopen)

    client = BinanceMarketClient("https://testnet.binance.vision/api/v3")
    candles = client.get_klines("btcusdt", "1h", limit=1)

    assert len(candles) == 1
    assert candles[0].symbol == "BTCUSDT"
    assert seen_urls == [
        "https://testnet.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1"
    ]


def test_client_rejects_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self) -> bytes:
            return b"not-json"

    monkeypatch.setattr("app.market.binance.urlopen", lambda request, timeout: Response())

    client = BinanceMarketClient("https://testnet.binance.vision/api/v3")

    with pytest.raises(BinanceMarketError, match="valid JSON"):
        client.get_24h_ticker("BTCUSDT")
