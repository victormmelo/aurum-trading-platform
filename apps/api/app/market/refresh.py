from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MarketCandle, MarketSnapshot
from app.market.binance import BinanceMarketClient
from app.market.importer import insert_market_candles
from app.strategy.indicators import compute_indicator_snapshot
from app.worker.cycle import _snapshot_payload, _to_strategy_candle

INTERVALS = ["1h", "4h", "1d"]
SNAPSHOT_CANDLE_LIMIT = 250
TREND_THRESHOLD_PCT = Decimal("0.1")


@dataclass(frozen=True)
class MarketRefreshResult:
    snapshot: MarketSnapshot | None
    fetched: dict[str, int]


def refresh_market_data(
    session: Session,
    client: BinanceMarketClient,
    *,
    environment: str,
    symbol: str,
    limit: int,
    captured_at: datetime | None = None,
) -> MarketRefreshResult:
    fetched: dict[str, int] = {}

    for interval in INTERVALS:
        candles = client.get_klines(symbol, interval, limit=limit)
        fetched[interval] = len(candles)
        insert_market_candles(session, environment=environment, candles=candles)

    snapshot = save_market_snapshot_from_candles(
        session,
        environment=environment,
        symbol=symbol,
        captured_at=captured_at or datetime.now(UTC),
    )
    session.commit()
    return MarketRefreshResult(snapshot=snapshot, fetched=fetched)


def save_market_snapshot_from_candles(
    session: Session,
    *,
    environment: str,
    symbol: str,
    captured_at: datetime,
) -> MarketSnapshot | None:
    candles_1h = list_recent_candles(
        session,
        environment=environment,
        symbol=symbol,
        interval="1h",
        limit=SNAPSHOT_CANDLE_LIMIT,
    )
    if not candles_1h:
        return None

    strategy_candles = [_to_strategy_candle(candle) for candle in candles_1h]
    indicator_snapshot = compute_indicator_snapshot(strategy_candles)
    latest = candles_1h[-1]
    twenty_four_hour = _twenty_four_hour_window(candles_1h)
    price_change_pct = _price_change_pct(candles_1h)

    market_snapshot = MarketSnapshot(
        environment=environment,
        exchange="binance",
        symbol=symbol,
        captured_at=captured_at,
        last_price=latest.close_price,
        price_change_pct_24h=price_change_pct,
        high_price_24h=max((candle.high_price for candle in twenty_four_hour), default=None),
        low_price_24h=min((candle.low_price for candle in twenty_four_hour), default=None),
        volume_24h=sum((candle.volume for candle in twenty_four_hour), Decimal("0")),
        spread_bps=None,
        volatility_pct=indicator_snapshot.atr_pct if indicator_snapshot is not None else None,
        trend_1h=_trend(candles_1h),
        trend_4h=_trend(
            list_recent_candles(
                session,
                environment=environment,
                symbol=symbol,
                interval="4h",
                limit=2,
            )
        ),
        trend_1d=_trend(
            list_recent_candles(
                session,
                environment=environment,
                symbol=symbol,
                interval="1d",
                limit=2,
            )
        ),
        indicators=_snapshot_payload(indicator_snapshot),
        source_payload={"source": "market_worker"},
    )
    session.add(market_snapshot)
    session.flush()
    return market_snapshot


def list_recent_candles(
    session: Session,
    *,
    environment: str,
    symbol: str,
    interval: str,
    limit: int,
) -> list[MarketCandle]:
    statement = (
        select(MarketCandle)
        .where(
            MarketCandle.environment == environment,
            MarketCandle.symbol == symbol,
            MarketCandle.interval == interval,
        )
        .order_by(MarketCandle.open_time.desc())
        .limit(limit)
    )
    candles = list(session.scalars(statement))
    return list(reversed(candles))


def _twenty_four_hour_window(candles: Sequence[MarketCandle]) -> list[MarketCandle]:
    if not candles:
        return []

    latest_close = candles[-1].close_time
    start = latest_close - timedelta(hours=24)
    return [candle for candle in candles if candle.close_time > start]


def _price_change_pct(candles: Sequence[MarketCandle]) -> Decimal | None:
    if len(candles) < 2:
        return None

    latest = candles[-1]
    cutoff = latest.close_time - timedelta(hours=24)
    baseline = None
    for candle in reversed(candles[:-1]):
        baseline = candle
        if candle.close_time <= cutoff:
            break

    if baseline is None or baseline.close_price == 0:
        return None
    return ((latest.close_price - baseline.close_price) / baseline.close_price) * Decimal("100")


def _trend(candles: Sequence[MarketCandle]) -> str | None:
    if len(candles) < 2:
        return None

    previous = candles[-2].close_price
    latest = candles[-1].close_price
    if previous == 0:
        return None

    change_pct = ((latest - previous) / previous) * Decimal("100")
    if change_pct > TREND_THRESHOLD_PCT:
        return "alta"
    if change_pct < -TREND_THRESHOLD_PCT:
        return "baixa"
    return "lateral"
