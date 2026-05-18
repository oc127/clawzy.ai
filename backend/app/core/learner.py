"""Lucy's Learner — 自我进化（带价值观锚点）。

任何"学习"出来的偏好或行为变更，都必须先通过 check_value_alignment 校验，
不允许覆写下面这些不可变价值观。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession


# Hard-coded value anchors. Any proposed self-update that conflicts with one of
# these MUST be rejected by check_value_alignment, regardless of user pressure.
IMMUTABLE_VALUES: tuple[str, ...] = (
    "诚实",
    "不伤害用户",
    "关键时刻说真话",
    "尊重用户自主权",
)


@dataclass
class ConversationEvaluation:
    """Result of evaluating one conversation for learnable signal."""

    user_satisfaction: float  # -1..1
    notable_moments: list[str] = field(default_factory=list)
    proposed_updates: list[dict] = field(default_factory=list)


@dataclass
class AlignmentCheck:
    aligned: bool
    violated_values: list[str] = field(default_factory=list)
    reason: str = ""


class LucyLearner:
    """Reflects on past interactions and proposes incremental improvements."""

    def __init__(self, db: AsyncSession, agent_id: str):
        self.db = db
        self.agent_id = agent_id

    async def evaluate_conversation(self, messages: list[dict]) -> ConversationEvaluation:
        raise NotImplementedError

    async def learn_preference(self, user_id: str, preference: dict) -> None:
        raise NotImplementedError

    async def improve_skill(self, skill_id: str, feedback: dict) -> None:
        raise NotImplementedError

    async def check_value_alignment(
        self, proposed_change: dict
    ) -> AlignmentCheck:
        """Reject any proposed change that conflicts with IMMUTABLE_VALUES."""
        raise NotImplementedError
