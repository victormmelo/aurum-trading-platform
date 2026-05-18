from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.mcp.rate_limit import McpRateLimitExceededError, check_mcp_rate_limit

NOW = datetime(2026, 5, 17, 20, 0, 5, tzinfo=UTC)


def test_mcp_rate_limit_allows_sixty_calls_per_token_resource_window() -> None:
    store = FakeRateLimitStore()
    token_id = uuid.uuid4()

    for _ in range(60):
        decision = check_mcp_rate_limit(
            store,
            environment="testnet",
            token_id=token_id,
            resource="get_market_summary",
            now=NOW,
        )

    assert decision.allowed is True
    assert decision.count == 60
    assert decision.remaining == 0
    assert decision.reset_at == datetime(2026, 5, 17, 20, 1, tzinfo=UTC)
    assert store.ttls == {decision.key: 55}


def test_mcp_rate_limit_blocks_sixty_first_call() -> None:
    store = FakeRateLimitStore()
    token_id = uuid.uuid4()

    for _ in range(60):
        check_mcp_rate_limit(
            store,
            environment="testnet",
            token_id=token_id,
            resource="get_market_summary",
            now=NOW,
        )

    with pytest.raises(McpRateLimitExceededError) as exc_info:
        check_mcp_rate_limit(
            store,
            environment="testnet",
            token_id=token_id,
            resource="get_market_summary",
            now=NOW,
        )

    assert exc_info.value.decision.allowed is False
    assert exc_info.value.decision.count == 61
    assert exc_info.value.decision.remaining == 0


def test_mcp_rate_limit_isolates_tokens_and_resources() -> None:
    store = FakeRateLimitStore()
    token_id = uuid.uuid4()

    for _ in range(60):
        check_mcp_rate_limit(
            store,
            environment="testnet",
            token_id=token_id,
            resource="get_market_summary",
            now=NOW,
        )

    other_resource = check_mcp_rate_limit(
        store,
        environment="testnet",
        token_id=token_id,
        resource="get_portfolio_status",
        now=NOW,
    )
    other_token = check_mcp_rate_limit(
        store,
        environment="testnet",
        token_id=uuid.uuid4(),
        resource="get_market_summary",
        now=NOW,
    )

    assert other_resource.count == 1
    assert other_token.count == 1


class FakeRateLimitStore:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    def increment(self, key: str, *, ttl_seconds: int) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        if self.counts[key] == 1:
            self.ttls[key] = ttl_seconds
        return self.counts[key]
