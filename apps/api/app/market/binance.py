from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BinanceMarketError(RuntimeError):
    """Raised when a read-only Binance market data request fails."""


@dataclass(frozen=True)
class BinanceCandle:
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    quote_volume: Decimal | None
    trade_count: int | None
    source_payload: dict[str, Any]


class BinanceMarketClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_24h_ticker(self, symbol: str) -> dict[str, Any]:
        return self._get_json("/ticker/24hr", {"symbol": symbol.upper()})

    def get_klines(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 500,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[BinanceCandle]:
        params: dict[str, str | int] = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time is not None:
            params["startTime"] = _datetime_to_millis(start_time)
        if end_time is not None:
            params["endTime"] = _datetime_to_millis(end_time)

        payload = self._get_json("/klines", params)
        if not isinstance(payload, list):
            raise BinanceMarketError("Binance klines response is not a list")

        return [parse_kline(symbol.upper(), interval, row) for row in payload]

    def _get_json(self, path: str, params: dict[str, str | int]) -> Any:
        url = f"{self.base_url}{path}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "aurum-api/0.1.0"})

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise BinanceMarketError(f"Binance request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise BinanceMarketError(f"Binance request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise BinanceMarketError("Binance request timed out") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise BinanceMarketError("Binance response is not valid JSON") from exc


def parse_kline(symbol: str, interval: str, row: list[Any]) -> BinanceCandle:
    if len(row) < 9:
        raise BinanceMarketError("Binance kline row has fewer fields than expected")

    return BinanceCandle(
        symbol=symbol,
        interval=interval,
        open_time=_millis_to_datetime(row[0]),
        close_time=_millis_to_datetime(row[6]),
        open_price=Decimal(str(row[1])),
        high_price=Decimal(str(row[2])),
        low_price=Decimal(str(row[3])),
        close_price=Decimal(str(row[4])),
        volume=Decimal(str(row[5])),
        quote_volume=Decimal(str(row[7])) if row[7] is not None else None,
        trade_count=int(row[8]) if row[8] is not None else None,
        source_payload={"kline": row},
    )


def _millis_to_datetime(value: int | str) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def _datetime_to_millis(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)
