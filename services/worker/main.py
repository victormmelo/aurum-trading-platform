from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import redis
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.models import BotRuntimeState, MarketCandle, MarketSnapshot
from app.db.session import get_session_factory
from app.execution.binance_private import BinanceCredentials, BinancePrivateClient
from app.market.binance import BinanceMarketClient
from app.market.refresh import refresh_market_data, save_market_snapshot_from_candles
from app.portfolio.reconciliation import BinancePortfolioReconciler
from app.worker.cycle import run_worker_cycle

MARKET_CHANNEL = "aurum:market:snapshots"


def main() -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    market_client = BinanceMarketClient(settings.binance_spot_base_url)
    private_client = (
        BinancePrivateClient(
            base_url=settings.binance_spot_base_url,
            credentials=BinanceCredentials(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret,
            ),
            recv_window_ms=settings.binance_recv_window_ms,
        )
        if settings.binance_api_key and settings.binance_api_secret
        else None
    )
    portfolio_reconciler = (
        BinancePortfolioReconciler(private_client) if private_client is not None else None
    )
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    last_worker_cycle_at = time.monotonic()

    print("Aurum worker started", flush=True)
    _log_startup_readiness(session_factory, settings)
    while True:
        cycle_started_at = time.monotonic()
        try:
            with session_factory() as session:
                market_result = refresh_market_data(
                    session,
                    market_client,
                    environment=settings.aurum_environment,
                    symbol=settings.trading_symbol,
                    limit=settings.market_backfill_limit,
                )
                if market_result.snapshot is not None:
                    _publish_snapshot(redis_client, market_result.snapshot)
                print(
                    "Aurum market refresh "
                    f"snapshot={market_result.snapshot.id if market_result.snapshot else None} "
                    f"fetched={market_result.fetched}",
                    flush=True,
                )

            now = time.monotonic()
            if now - last_worker_cycle_at >= settings.worker_cycle_seconds:
                with session_factory() as session:
                    runtime = session.scalars(
                        select(BotRuntimeState).where(
                            BotRuntimeState.environment == settings.aurum_environment
                        )
                    ).first()
                    if runtime is not None and runtime.status == "running":
                        if (
                            runtime.trading_mode == "testnet"
                            and settings.aurum_environment == "testnet"
                            and portfolio_reconciler is not None
                        ):
                            portfolio_reconciler.reconcile(
                                session,
                                environment=settings.aurum_environment,
                                symbol=settings.trading_symbol,
                            )
                        result = run_worker_cycle(
                            session,
                            environment=settings.aurum_environment,
                            symbol=settings.trading_symbol,
                        )
                        print(
                            "Aurum worker cycle "
                            f"status={result.status} decision={result.decision} "
                            f"reason={result.reason}",
                            flush=True,
                        )
                        snapshot = save_market_snapshot_from_candles(
                            session,
                            environment=settings.aurum_environment,
                            symbol=settings.trading_symbol,
                            captured_at=runtime.last_cycle_at or datetime.now(UTC),
                        )
                        session.commit()
                        if snapshot is not None:
                            _publish_snapshot(redis_client, snapshot)
                    else:
                        status = runtime.status if runtime is not None else "missing"
                        print(f"Aurum worker skipped decision cycle status={status}", flush=True)
                    last_worker_cycle_at = now
        except Exception as exc:  # noqa: BLE001
            print(f"Aurum worker loop error: {exc}", flush=True)

        elapsed = time.monotonic() - cycle_started_at
        time.sleep(max(1, settings.market_poll_seconds - elapsed))


def _log_startup_readiness(session_factory, settings) -> None:  # noqa: ANN001
    _MIN_CANDLES = 200  # noqa: N806
    intervals = ["1h", "4h", "1d"]
    try:
        with session_factory() as session:
            counts = {}
            for interval in intervals:
                counts[interval] = session.scalar(
                    select(func.count()).select_from(MarketCandle).where(
                        MarketCandle.environment == settings.aurum_environment,
                        MarketCandle.symbol == settings.trading_symbol,
                        MarketCandle.interval == interval,
                    )
                ) or 0
        is_ready = all(c >= _MIN_CANDLES for c in counts.values())
        mode = "operational" if is_ready else "collecting"
        print(
            f"Aurum data readiness candles={counts} min_required={_MIN_CANDLES} "
            f"ready={is_ready} mode={mode}",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Aurum data readiness check failed: {exc}", flush=True)


def _publish_snapshot(redis_client: redis.Redis, snapshot: MarketSnapshot) -> None:
    redis_client.publish(
        MARKET_CHANNEL,
        json.dumps(
            {
                "environment": snapshot.environment,
                "symbol": snapshot.symbol,
                "snapshot_id": str(snapshot.id),
                "captured_at": snapshot.captured_at.isoformat(),
            }
        ),
    )


if __name__ == "__main__":
    main()
