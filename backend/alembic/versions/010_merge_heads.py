"""merge heads 008 and 009_knowledge_base

Revision ID: 010_merge_heads
Revises: 008, 009_knowledge_base
Create Date: 2026-05-16
"""

from collections.abc import Sequence

revision: str = "010_merge_heads"
down_revision: tuple[str, ...] = ("008", "009_knowledge_base")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
