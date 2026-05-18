"""Lucy's Executor — 工具调用和能力执行。

把 search / code / schedule / shell / browser 等能力封装成一个
统一的执行表面，方便 Brain 决策后直接调用。

骨架阶段：内部仍委托现有 services（tool_service / scheduler_service / ...）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: Any
    error: str | None = None


class LucyExecutor:
    """Run tools on behalf of LucyBrain."""

    def __init__(self, db: AsyncSession, agent_id: str, container_id: str | None = None):
        self.db = db
        self.agent_id = agent_id
        self.container_id = container_id

    async def execute_tool(self, tool_name: str, params: dict) -> ToolResult:
        raise NotImplementedError

    async def search(self, query: str) -> ToolResult:
        raise NotImplementedError

    async def write_code(self, spec: str, language: str = "python") -> ToolResult:
        raise NotImplementedError

    async def manage_schedule(self, action: str, **kwargs) -> ToolResult:
        """action: 'create' | 'list' | 'cancel' | 'update'"""
        raise NotImplementedError
