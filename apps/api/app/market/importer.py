from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.orm import Session

from app.db.models import MarketCandle
from app.market.binance import BinanceCandle, BinanceMarketClient


@dataclass(frozen=True)
class CandleImportResult:
    interval: str
    fetched: int
    inserted: int
    last_close_time: datetime | None


def import_historical_candles(
    session: Session,
    client: BinanceMarketClient,
    *,
    environment: str,
    symbol: str,
    intervals: list[str],
    limit: int,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> list[CandleImportResult]:
    results: list[CandleImportResult] = []

    for interval in intervals:
        candles = client.get_klines(
            symbol,
            interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
        inserted = insert_market_candles(session, environment=environment, candles=candles)
        last_close = candles[-1].close_time if candles else None
        results.append(
            CandleImportResult(
                interval=interval,
                fetched=len(candles),
                inserted=inserted,
                last_close_time=last_close,
            )
        )

    session.commit()
    return results


def insert_market_candles(
    session: Session,
    *,
    environment: str,
    candles: list[BinanceCandle],
) -> int:
    if not candles:
        return 0

    rows = [
        {
            "environment": environment,
            "exchange": "binance",
            "symbol": candle.symbol,
            "interval": candle.interval,
            "open_time": candle.open_time,
            "close_time": candle.close_time,
            "open_price": candle.open_price,
            "high_price": candle.high_price,
            "low_price": candle.low_price,
            "close_price": candle.close_price,
            "volume": candle.volume,
            "quote_volume": candle.quote_volume,
            "trade_count": candle.trade_count,
            "source_payload": candle.source_payload,
        }
        for candle in candles
    ]

    statement = (
        postgres_insert(MarketCandle)
        .values(rows)
        .on_conflict_do_nothing(
            constraint="uq_market_candles_source_window",
        )
    )
    result = session.execute(statement)
    return int(result.rowcount or 0)
