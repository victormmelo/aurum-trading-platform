"""seed strategy v2 config

Revision ID: 20260607_0004
Revises: 20260606_0003
Create Date: 2026-06-07 00:04:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260607_0004"
down_revision: str | None = "20260606_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text("""
        INSERT INTO strategy_configs (
            id,
            environment,
            version,
            name,
            symbol,
            signal_timeframe,
            regime_timeframe_primary,
            regime_timeframe_secondary,
            parameters,
            is_active,
            created_by,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            'testnet',
            2,
            'Regime 1d + Breakout 4h v2',
            'BTCUSDT',
            '4h',
            '1d',
            '1d',
            (
                '{"breakout_lookback": 20, "atr_period": 14, "atr_stop_multiplier": 2.5,'
                ' "trailing_stop_multiplier": 3.0, "sma_long_period": 200,'
                ' "sma_slope_lookback": 20}'::jsonb
            ),
            false,
            'system',
            now(),
            now()
        )
        ON CONFLICT ON CONSTRAINT uq_strategy_configs_environment_version DO NOTHING
        """)
    )


def downgrade() -> None:
    op.execute(
        sa.text("""
        DELETE FROM strategy_configs
        WHERE environment = 'testnet' AND version = 2
          AND name = 'Regime 1d + Breakout 4h v2'
        """)
    )
