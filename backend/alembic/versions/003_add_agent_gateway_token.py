"""add gateway_token to agents

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agents", sa.Column("gateway_token", sa.String(64), nullable=True))


def downgrade():
    op.drop_column("agents", "gateway_token")
