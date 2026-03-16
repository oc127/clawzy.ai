"""add skills and agent_skills tables

Revision ID: 001_add_skills
Revises:
Create Date: 2026-03-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_add_skills"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("clawhub_url", sa.String(500), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("install_count", sa.Integer(), nullable=False, default=0, index=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column(
            "skill_id", sa.String(36), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agent_id", "skill_id", name="uq_agent_skill"),
    )


def downgrade() -> None:
    op.drop_table("agent_skills")
    op.drop_table("skills")
