"""add adaptive_depth to agents

Revision ID: 008
Revises: 007
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("adaptive_depth", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("agents", "adaptive_depth")
