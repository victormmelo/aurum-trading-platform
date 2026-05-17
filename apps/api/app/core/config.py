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
    database_url: str = Field(
        default="postgresql+psycopg://aurum:aurum_dev_password@localhost:5432/aurum",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
