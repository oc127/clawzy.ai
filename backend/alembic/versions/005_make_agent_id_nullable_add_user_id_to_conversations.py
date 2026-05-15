"""make agent_id nullable and add user_id to conversations

Revision ID: 005_conv_user_id
Revises: 004_add_lucy_state
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_conv_user_id"
down_revision: str | None = "004_add_lucy_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Make agent_id nullable
    op.alter_column(
        "conversations",
        "agent_id",
        existing_type=sa.String(36),
        nullable=True,
    )

    # Add user_id column
    op.add_column(
        "conversations",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_conversations_user_id", "conversations")
    op.drop_column("conversations", "user_id")

    op.alter_column(
        "conversations",
        "agent_id",
        existing_type=sa.String(36),
        nullable=False,
    )
