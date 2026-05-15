"""add user_level and cultural_frame to lucy_states

Revision ID: 008_apeiron_fields
Revises: 007_lucy_tasks
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_apeiron_fields"
down_revision: str | None = "007_lucy_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lucy_states", sa.Column("user_level", sa.String(20), nullable=True, server_default="intermediate"))
    op.add_column("lucy_states", sa.Column("cultural_frame", sa.String(20), nullable=True, server_default="universal"))


def downgrade() -> None:
    op.drop_column("lucy_states", "cultural_frame")
    op.drop_column("lucy_states", "user_level")
