"""009 - conversation_evaluations table

Revision ID: 009
Revises: 008
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("coherence_score", sa.Float, nullable=True),
        sa.Column("helpfulness_score", sa.Float, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("patterns_found", sa.JSON, nullable=True),
        sa.Column("improvement_suggestions", sa.JSON, nullable=True),
        sa.Column("skill_extracted", sa.Boolean, default=False, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("conversation_evaluations")
