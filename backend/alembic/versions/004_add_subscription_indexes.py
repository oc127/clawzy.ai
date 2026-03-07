"""add subscription indexes

Revision ID: 004_add_subscription_indexes
Revises: 003_add_agent_gateway_token
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "004_add_subscription_indexes"
down_revision: Union[str, None] = "003_add_agent_gateway_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])


def downgrade() -> None:
    op.drop_index("ix_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
