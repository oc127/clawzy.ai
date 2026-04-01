"""Tools API — manage agent tool availability."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent
from app.services.tool_service import get_tools_status, update_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/tools", tags=["tools"])


class ToolUpdate(BaseModel):
    enabled: bool | None = None
    requires_approval: bool | None = None


@router.get("")
async def list_agent_tools(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available tools with their enabled status."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    tools = await get_tools_status(db, agent_id)
    return {"tools": tools}


@router.patch("/{tool_name}")
async def update_agent_tool(
    agent_id: str,
    tool_name: str,
    body: ToolUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a tool or set requires_approval."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        result = await update_tool(db, agent_id, tool_name, body.enabled, body.requires_approval)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return result
