"""add lucy_states table and new memory fields

Revision ID: 004_add_lucy_state
Revises: 003_add_password_reset
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_add_lucy_state"
down_revision: str | None = "003_add_password_reset"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create lucy_states table
    op.create_table(
        "lucy_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("personality_type", sa.String(20), nullable=False, server_default="少女"),
        sa.Column("custom_personality_prompt", sa.Text, nullable=True),
        sa.Column("mood", sa.String(20), nullable=False, server_default="neutral"),
        sa.Column("affection", sa.Integer, nullable=False, server_default="0"),
        sa.Column("interaction_streak", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_interactions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unlocked_expressions", sa.JSON, nullable=True),
        sa.Column("soul_md", sa.Text, nullable=False, server_default=""),
        sa.Column("persona_md", sa.Text, nullable=False, server_default=""),
        sa.Column("taste_md", sa.Text, nullable=False, server_default=""),
        sa.Column("preferred_model", sa.String(100), nullable=False, server_default="deepseek-chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lucy_states_user_id", "lucy_states", ["user_id"], unique=True)

    # Add new columns to memories table
    op.add_column("memories", sa.Column("memory_type", sa.String(20), nullable=False, server_default="episode"))
    op.add_column("memories", sa.Column("importance", sa.Integer, nullable=False, server_default="3"))
    op.add_column("memories", sa.Column("confidence", sa.Float, nullable=False, server_default="0.8"))
    op.add_column("memories", sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()))


def downgrade() -> None:
    # Remove new columns from memories table
    op.drop_column("memories", "is_active")
    op.drop_column("memories", "confidence")
    op.drop_column("memories", "importance")
    op.drop_column("memories", "memory_type")

    # Drop lucy_states table
    op.drop_index("ix_lucy_states_user_id", "lucy_states")
    op.drop_table("lucy_states")
