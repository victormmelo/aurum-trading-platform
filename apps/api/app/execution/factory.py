from __future__ import annotations

from app.core.config import Settings
from app.execution.adapters import (
    BinanceTestnetExecutionAdapter,
    BlockedMainnetExecutionAdapter,
    DryRunExecutionAdapter,
    ExecutionAdapter,
)
from app.execution.binance_private import BinanceCredentials, BinancePrivateClient


def execution_adapter_for_mode(settings: Settings, trading_mode: str) -> ExecutionAdapter:
    if trading_mode == "paper":
        return DryRunExecutionAdapter()
    if trading_mode == "testnet":
        if not settings.binance_api_key or not settings.binance_api_secret:
            raise RuntimeError(
                "BINANCE_API_KEY and BINANCE_API_SECRET are required for Testnet execution"
            )
        return BinanceTestnetExecutionAdapter(
            BinancePrivateClient(
                base_url=settings.binance_spot_base_url,
                credentials=BinanceCredentials(
                    api_key=settings.binance_api_key,
                    api_secret=settings.binance_api_secret,
                ),
                recv_window_ms=settings.binance_recv_window_ms,
            )
        )
    if trading_mode == "mainnet":
        return BlockedMainnetExecutionAdapter()
    raise RuntimeError(f"Unsupported trading mode: {trading_mode}")
