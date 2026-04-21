"""create task_pipelines and pipeline_steps tables

Revision ID: 007
Revises: 006
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_pipelines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planning"),
        sa.Column("original_prompt", sa.Text(), nullable=True),
        sa.Column("plan", sa.JSON(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_task_pipelines_user_id", "task_pipelines", ["user_id"])

    op.create_table(
        "pipeline_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pipeline_id",
            sa.String(36),
            sa.ForeignKey("task_pipelines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.String(36),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("agent_role", sa.String(50), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("evaluation_score", sa.Float(), nullable=True),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("depends_on", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_pipeline_steps_pipeline_id", "pipeline_steps", ["pipeline_id"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_steps_pipeline_id", table_name="pipeline_steps")
    op.drop_table("pipeline_steps")
    op.drop_index("ix_task_pipelines_user_id", table_name="task_pipelines")
    op.drop_table("task_pipelines")
