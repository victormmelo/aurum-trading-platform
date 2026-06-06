from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from decimal import Decimal

import redis
import schedule
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.models import BotRuntimeState, DecisionLog, MarketCandle, MarketSnapshot
from app.db.session import get_session_factory
from app.execution.binance_private import BinanceCredentials, BinancePrivateClient
from app.market.binance import BinanceMarketClient
from app.market.importer import insert_market_candles
from app.market.refresh import refresh_market_data, save_market_snapshot_from_candles
from app.portfolio.reconciliation import BinancePortfolioReconciler
from app.strategy.signals import BUY, SELL
from app.worker.cycle import DEFAULT_CANDLE_LIMIT, MIN_SIGNAL_CANDLES, CycleResult, run_worker_cycle

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
    _start_report_scheduler(settings)
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
                _backfill_if_needed(session_factory, market_client, settings)
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
                        if result.decision in {BUY, SELL}:
                            _notify_trade_decision(session, result, settings)
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


def _backfill_if_needed(session_factory, market_client, settings) -> None:  # noqa: ANN001
    with session_factory() as session:
        deficient: list[tuple[str, int]] = []
        for interval in ["1h", "4h", "1d"]:
            count = session.scalar(
                select(func.count()).select_from(MarketCandle).where(
                    MarketCandle.environment == settings.aurum_environment,
                    MarketCandle.symbol == settings.trading_symbol,
                    MarketCandle.interval == interval,
                )
            ) or 0
            if count < MIN_SIGNAL_CANDLES:
                deficient.append((interval, count))

        if not deficient:
            return

        print(
            f"Aurum backfill: histórico insuficiente em {[i for i, _ in deficient]}, "
            f"buscando {DEFAULT_CANDLE_LIMIT} candles por intervalo",
            flush=True,
        )
        for interval, current_count in deficient:
            candles = market_client.get_klines(
                settings.trading_symbol, interval, limit=DEFAULT_CANDLE_LIMIT
            )
            inserted = insert_market_candles(
                session, environment=settings.aurum_environment, candles=candles
            )
            print(
                f"Aurum backfill: {interval} tinha {current_count}, "
                f"buscou {len(candles)}, inseriu {inserted}",
                flush=True,
            )
        session.commit()


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


def _notify_trade_decision(session, result: CycleResult, settings) -> None:  # noqa: ANN001
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        return
    try:
        from telegram_notifier import notify_buy_executed, notify_sell_executed  # noqa: PLC0415

        decision_log = session.get(DecisionLog, result.decision_id)
        if decision_log is None:
            return

        signal = (decision_log.indicators or {}).get("signal", {})
        order = decision_log.intended_order or {}
        portfolio = decision_log.portfolio_state or {}

        price = Decimal(signal["close_price"]) if signal.get("close_price") else Decimal("0")
        quantity = Decimal(order["quantity"]) if order.get("quantity") else Decimal("0")
        notional = (
            Decimal(order["quote_quantity"])
            if order.get("quote_quantity")
            else price * quantity
        )
        sma_short = Decimal(signal["sma_50"]) if signal.get("sma_50") else None
        sma_long = Decimal(signal["sma_200"]) if signal.get("sma_200") else None
        executed_at = decision_log.decided_at or datetime.now(UTC)

        if result.decision == BUY:
            notify_buy_executed(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
                price=price,
                quantity=quantity,
                notional=notional,
                sma_short=sma_short,
                sma_long=sma_long,
                executed_at=executed_at,
            )
        else:
            entry_price_str = portfolio.get("position_average_cost")
            entry_price = Decimal(entry_price_str) if entry_price_str else Decimal("0")
            notify_sell_executed(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
                price=price,
                quantity=quantity,
                notional=notional,
                entry_price=entry_price,
                sma_short=sma_short,
                sma_long=sma_long,
                executed_at=executed_at,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Aurum trade notification error: {exc}", flush=True)


def _start_report_scheduler(settings) -> None:  # noqa: ANN001
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        print("Aurum market report scheduler: Telegram not configured, skipping", flush=True)
        return

    from market_report import send_market_report  # noqa: PLC0415

    def _send_report() -> None:
        try:
            send_market_report(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                anthropic_api_key=settings.anthropic_api_key,
                news_api_key=settings.news_api_key,
                anthropic_model=settings.anthropic_model,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Aurum market report error: {exc}", flush=True)

    schedule.every().day.at(settings.report_time_morning).do(_send_report)
    schedule.every().day.at(settings.report_time_evening).do(_send_report)

    def _scheduler_loop() -> None:
        while True:
            schedule.run_pending()
            time.sleep(30)

    thread = threading.Thread(target=_scheduler_loop, daemon=True, name="report-scheduler")
    thread.start()
    print(
        f"Aurum market report scheduler started "
        f"morning={settings.report_time_morning} evening={settings.report_time_evening}",
        flush=True,
    )


if __name__ == "__main__":
    main()
