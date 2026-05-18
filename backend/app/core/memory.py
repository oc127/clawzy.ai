"""Lucy's Memory — 工作记忆 + 长期记忆。

工作记忆：当前会话窗口、临时上下文。
长期记忆：跨会话事实、用户偏好、用户画像。

骨架阶段：实际存取仍走 app.services.memory_service；本模块负责给上层
提供一个统一、面向 Brain 的 API 表面，后续逐步把 memory_service 内化进来。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MemoryItem:
    content: str
    category: str  # "preference" | "fact" | "event" | "relationship" | ...
    importance: float = 0.5  # 0..1
    metadata: dict = field(default_factory=dict)


@dataclass
class UserProfile:
    """Aggregated view of who the user is, derived from long-term memory."""

    name: str | None = None
    interests: list[str] = field(default_factory=list)
    routines: list[str] = field(default_factory=list)
    relationship_stage: str = "new"  # "new" | "familiar" | "close"
    raw: dict = field(default_factory=dict)


class LucyMemory:
    """Read/write Lucy's memory for a given agent."""

    def __init__(self, db: AsyncSession, agent_id: str):
        self.db = db
        self.agent_id = agent_id

    async def remember(self, fact: str, category: str, importance: float = 0.5, **metadata) -> None:
        raise NotImplementedError

    async def recall(self, query: str, *, limit: int = 5, context: dict | None = None) -> list[MemoryItem]:
        raise NotImplementedError

    async def reflect_and_consolidate(self) -> None:
        """Merge duplicates, drop stale items, raise importance of recurring facts."""
        raise NotImplementedError

    async def build_user_profile(self) -> UserProfile:
        raise NotImplementedError
