"""mcp tokens and access logs

Revision ID: 20260517_0002
Revises: 20260517_0001
Create Date: 2026-05-17 00:02:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260517_0002"
down_revision: str | None = "20260517_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)
jsonb_type = postgresql.JSONB(astext_type=sa.Text())


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "mcp_tokens",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes", jsonb_type, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('active', 'revoked', 'expired')",
            name=op.f("ck_mcp_tokens_mcp_tokens_status"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mcp_tokens")),
        sa.UniqueConstraint("token_hash", name="uq_mcp_tokens_token_hash"),
    )

    op.create_table(
        "mcp_access_logs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("token_id", uuid_type, nullable=True),
        sa.Column("agent_name", sa.String(length=120), nullable=True),
        sa.Column("resource", sa.String(length=120), nullable=False),
        sa.Column("arguments", jsonb_type, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["token_id"],
            ["mcp_tokens.id"],
            name=op.f("fk_mcp_access_logs_token_id_mcp_tokens"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mcp_access_logs")),
    )


def downgrade() -> None:
    op.drop_table("mcp_access_logs")
    op.drop_table("mcp_tokens")
