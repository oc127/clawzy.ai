"""Add agent_memories, agent_tools tables and memory_enabled column

Revision ID: 002_memory_tools
Revises: 001_clawhub_templates
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002_memory_tools"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add memory_enabled column to agents table
    op.add_column(
        "agents",
        sa.Column("memory_enabled", sa.Boolean(), server_default="1", nullable=False),
    )

    # Create agent_memories table
    op.create_table(
        "agent_memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "agent_id",
            sa.String(36),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(20), nullable=True, server_default="fact"),
        sa.Column("source_conversation_id", sa.String(36), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create agent_tools table
    op.create_table(
        "agent_tools",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "agent_id",
            sa.String(36),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_tools")
    op.drop_table("agent_memories")
    op.drop_column("agents", "memory_enabled")
