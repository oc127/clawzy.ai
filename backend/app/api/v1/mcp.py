"""MCP API — manage agent MCP server configurations."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.mcp import MCPServerCreate, MCPServerResponse
from app.services.agent_service import get_agent
from app.services.mcp_service import (
    list_mcp_servers,
    get_mcp_server,
    add_mcp_server,
    discover_tools,
    remove_mcp_server,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/mcp-servers", tags=["mcp"])


@router.get("", response_model=list[MCPServerResponse])
async def list_agent_mcp_servers(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await list_mcp_servers(db, agent_id)


@router.post("", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def add_agent_mcp_server(
    agent_id: str,
    body: MCPServerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await add_mcp_server(
        db,
        agent_id=agent_id,
        name=body.name,
        transport=body.transport,
        command=body.command,
        url=body.url,
        config=body.config,
    )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_mcp_server(
    agent_id: str,
    server_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    deleted = await remove_mcp_server(db, server_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")


@router.get("/{server_id}/tools")
async def discover_mcp_tools(
    agent_id: str,
    server_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    server = await get_mcp_server(db, server_id)
    if server is None or server.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")

    tools = await discover_tools(agent_id, server)
    return {"tools": tools}
