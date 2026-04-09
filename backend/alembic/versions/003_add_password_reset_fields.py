"""add password reset fields to users

Revision ID: 003_add_password_reset
Revises: 002_add_skill_reviews
Create Date: 2026-04-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_password_reset"
down_revision: str | None = "002_add_skill_reviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_reset_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"])


def downgrade() -> None:
    op.drop_index("ix_users_password_reset_token", "users")
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
