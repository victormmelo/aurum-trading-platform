from __future__ import annotations

import argparse
from datetime import UTC, datetime

from app.core.config import get_settings
from app.db.session import build_session_factory
from app.market.binance import BinanceMarketClient
from app.market.importer import import_historical_candles


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Binance BTCUSDT candles into PostgreSQL.")
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--environment", default=None)
    parser.add_argument("--interval", action="append", dest="intervals")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    args = parser.parse_args()

    settings = get_settings()
    intervals = args.intervals or ["1h", "4h", "1d"]
    client = BinanceMarketClient(settings.binance_spot_base_url)
    session_factory = build_session_factory()

    with session_factory() as session:
        results = import_historical_candles(
            session,
            client,
            environment=args.environment or settings.aurum_environment,
            symbol=args.symbol or settings.trading_symbol,
            intervals=intervals,
            limit=args.limit,
            start_time=_parse_datetime(args.start_time),
            end_time=_parse_datetime(args.end_time),
        )

    for result in results:
        print(
            f"{result.interval}: fetched={result.fetched} inserted={result.inserted}",
            flush=True,
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


if __name__ == "__main__":
    main()
