"""add lucy_events and lucy_initiatives tables

Revision ID: 006_proactive_engine
Revises: 005_conv_user_id
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_proactive_engine"
down_revision: str | None = "005_conv_user_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lucy_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "lucy_initiatives",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("initiative_type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("context", sa.JSON, nullable=True),
        sa.Column("delivered", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Index for fetching pending initiatives efficiently
    op.create_index("ix_lucy_initiatives_user_delivered", "lucy_initiatives", ["user_id", "delivered"])

    # Add push notification fields to lucy_states
    op.add_column("lucy_states", sa.Column("push_channels", sa.JSON, nullable=True, server_default='["websocket"]'))
    op.add_column("lucy_states", sa.Column("line_user_id", sa.String(255), nullable=True))
    op.add_column("lucy_states", sa.Column("push_quiet_start", sa.Integer, nullable=True))
    op.add_column("lucy_states", sa.Column("push_quiet_end", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("lucy_states", "push_quiet_end")
    op.drop_column("lucy_states", "push_quiet_start")
    op.drop_column("lucy_states", "line_user_id")
    op.drop_column("lucy_states", "push_channels")
    op.drop_index("ix_lucy_initiatives_user_delivered", "lucy_initiatives")
    op.drop_table("lucy_initiatives")
    op.drop_table("lucy_events")
