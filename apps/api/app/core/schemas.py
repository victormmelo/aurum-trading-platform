from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str


class BotStatusResponse(BaseModel):
    environment: str
    symbol: str
    status: str
    trading_mode: str
    last_cycle_at: datetime | None
    paused_at: datetime | None
    emergency_stopped_at: datetime | None
    reason: str | None


class BotCommandRequest(BaseModel):
    reason: str | None = None
