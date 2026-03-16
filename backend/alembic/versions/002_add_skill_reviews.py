"""add skill_reviews table and avg_rating to skills

Revision ID: 002_add_skill_reviews
Revises: 001_add_skills
Create Date: 2026-03-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_add_skill_reviews"
down_revision: str = "001_add_skills"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add rating columns to skills
    op.add_column("skills", sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0"))
    op.add_column("skills", sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("skills", sa.Column("security_status", sa.String(20), nullable=False, server_default="unreviewed"))

    # Skill reviews / ratings
    op.create_table(
        "skill_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "skill_id", sa.String(36), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("rating", sa.Integer(), nullable=False),  # 1-5
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("skill_id", "user_id", name="uq_skill_user_review"),
    )

    # Skill submissions
    op.create_table(
        "skill_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),  # GitHub URL or similar
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, approved, rejected
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("skill_submissions")
    op.drop_table("skill_reviews")
    op.drop_column("skills", "security_status")
    op.drop_column("skills", "review_count")
    op.drop_column("skills", "avg_rating")
