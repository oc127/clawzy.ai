"""add lucy_tasks table

Revision ID: 007_lucy_tasks
Revises: 006_proactive_engine
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_lucy_tasks"
down_revision: str | None = "006_proactive_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lucy_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("result", sa.Text, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Index for listing tasks by status
    op.create_index("ix_lucy_tasks_user_status", "lucy_tasks", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_lucy_tasks_user_status", "lucy_tasks")
    op.drop_table("lucy_tasks")
