from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "Aurum API"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_version: str = Field(default="0.1.0", alias="API_VERSION")
    aurum_environment: str = Field(default="testnet", alias="AURUM_ENVIRONMENT")
    trading_symbol: str = Field(default="BTCUSDT", alias="TRADING_SYMBOL")
    binance_spot_base_url: str = Field(
        default="https://testnet.binance.vision/api/v3",
        alias="BINANCE_SPOT_BASE_URL",
    )
    binance_api_key: str | None = Field(default=None, alias="BINANCE_API_KEY")
    binance_api_secret: str | None = Field(default=None, alias="BINANCE_API_SECRET")
    binance_recv_window_ms: int = Field(default=5000, alias="BINANCE_RECV_WINDOW_MS")
    market_stale_after_seconds: int = Field(default=300, alias="MARKET_STALE_AFTER_SECONDS")
    market_poll_seconds: int = Field(default=30, alias="MARKET_POLL_SECONDS")
    worker_cycle_seconds: int = Field(default=60, alias="WORKER_CYCLE_SECONDS")
    market_backfill_limit: int = Field(default=500, alias="MARKET_BACKFILL_LIMIT")
    database_url: str = Field(
        default="postgresql+psycopg://aurum:aurum_dev_password@localhost:5432/aurum",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
