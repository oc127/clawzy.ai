"""Lucy's Brain — 感知 → 思考 → 行动 → 反思 循环。

统一的决策中心，替代 chat_service 的大杂烩模式。
目前为骨架，后续逐步把 chat_service / scheduler 中的决策点收敛到这里。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class Perception:
    """A single piece of input Lucy is aware of."""

    source: str  # "user_message" | "scheduler" | "event" | "internal"
    payload: Any
    context: dict = field(default_factory=dict)


@dataclass
class Decision:
    """What Lucy decided to do in response to a perception."""

    kind: str  # "reply" | "tool" | "proactive" | "wait" | "noop"
    detail: dict = field(default_factory=dict)


@dataclass
class ActionResult:
    """Outcome of executing a decision."""

    decision: Decision
    output: Any = None
    error: str | None = None


class LucyBrain:
    """Coordinates Lucy's perceive → think → act → reflect cycle."""

    def __init__(self, db: AsyncSession, agent_id: str, user_id: str | None = None):
        self.db = db
        self.agent_id = agent_id
        self.user_id = user_id

    async def perceive(self, source: str, payload: Any, **context) -> Perception:
        raise NotImplementedError

    async def think(self, perception: Perception) -> Decision:
        raise NotImplementedError

    async def act(self, decision: Decision) -> ActionResult:
        raise NotImplementedError

    async def reflect(self, result: ActionResult) -> None:
        raise NotImplementedError

    async def tick(self, source: str, payload: Any, **context) -> ActionResult:
        """One full cycle of the loop."""
        perception = await self.perceive(source, payload, **context)
        decision = await self.think(perception)
        result = await self.act(decision)
        await self.reflect(result)
        return result
