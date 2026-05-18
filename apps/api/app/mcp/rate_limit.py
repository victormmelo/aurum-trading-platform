from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

MCP_RATE_LIMIT_PER_MINUTE = 60
MCP_RATE_LIMIT_WINDOW_SECONDS = 60


class McpRateLimitExceededError(Exception):
    def __init__(self, decision: McpRateLimitDecision) -> None:
        super().__init__(
            "Rate limit MCP excedido para token e recurso. "
            f"Tente novamente após {decision.reset_at.isoformat()}."
        )
        self.decision = decision


class McpRateLimitStore(Protocol):
    def increment(self, key: str, *, ttl_seconds: int) -> int: ...


@dataclass(frozen=True)
class McpRateLimitDecision:
    allowed: bool
    key: str
    limit: int
    remaining: int
    reset_at: datetime
    count: int


class RedisMcpRateLimitStore:
    def __init__(self, redis: Any) -> None:
        self.redis = redis

    def increment(self, key: str, *, ttl_seconds: int) -> int:
        count = int(self.redis.incr(key))
        if count == 1:
            self.redis.expire(key, ttl_seconds)
        return count


def create_redis_rate_limit_store(redis_url: str) -> RedisMcpRateLimitStore:
    from redis import Redis

    return RedisMcpRateLimitStore(Redis.from_url(redis_url, decode_responses=True))


def check_mcp_rate_limit(
    store: McpRateLimitStore,
    *,
    environment: str,
    token_id: uuid.UUID,
    resource: str,
    now: datetime | None = None,
    limit: int = MCP_RATE_LIMIT_PER_MINUTE,
    window_seconds: int = MCP_RATE_LIMIT_WINDOW_SECONDS,
) -> McpRateLimitDecision:
    checked_at = now or datetime.now(UTC)
    timestamp = checked_at.timestamp()
    window_epoch = int(timestamp // window_seconds * window_seconds)
    reset_epoch = window_epoch + window_seconds
    reset_at = datetime.fromtimestamp(reset_epoch, tz=UTC)
    ttl_seconds = max(1, math.ceil(reset_epoch - timestamp))
    key = f"mcp:rate:{environment}:{token_id}:{resource}:{window_epoch}"
    count = store.increment(key, ttl_seconds=ttl_seconds)
    remaining = max(0, limit - count)
    decision = McpRateLimitDecision(
        allowed=count <= limit,
        key=key,
        limit=limit,
        remaining=remaining,
        reset_at=reset_at,
        count=count,
    )
    if not decision.allowed:
        raise McpRateLimitExceededError(decision)
    return decision
