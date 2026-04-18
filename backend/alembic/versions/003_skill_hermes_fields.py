"""Add Hermes-style fields to agent_skills table

Revision ID: 003_skill_hermes
Revises: 002_memory_tools
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003_skill_hermes"
down_revision = "002_memory_tools"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_skills",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "agent_skills",
        sa.Column("triggers", sa.JSON(), nullable=True),
    )
    op.add_column(
        "agent_skills",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "agent_skills",
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "agent_skills",
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "agent_skills",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_skills", "updated_at")
    op.drop_column("agent_skills", "success_rate")
    op.drop_column("agent_skills", "usage_count")
    op.drop_column("agent_skills", "version")
    op.drop_column("agent_skills", "triggers")
    op.drop_column("agent_skills", "description")
