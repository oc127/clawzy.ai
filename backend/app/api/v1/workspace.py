"""Workspace API — file operations inside agent containers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent
from app.services.workspace_service import (
    WORKSPACE_ROOT,
    list_files,
    read_file,
    write_file,
    delete_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/workspace", tags=["workspace"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_running_agent(agent_id: str, user: User, db: AsyncSession):
    """Return the agent if it exists, belongs to user, and has a container."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.container_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent container is not running")
    return agent


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class WriteFileBody(BaseModel):
    content: str


@router.get("")
async def list_workspace_files(
    agent_id: str,
    path: str = Query(default=WORKSPACE_ROOT, description="Directory path to list"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List files at the given path inside the agent workspace."""
    agent = await _get_running_agent(agent_id, user, db)
    try:
        entries = await list_files(agent.container_id, path)
    except Exception as exc:
        logger.error("list_files error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)[:300])
    return {"path": path, "entries": entries}


@router.get("/file")
async def read_workspace_file(
    agent_id: str,
    path: str = Query(..., description="File path to read"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Read a file from the agent workspace."""
    agent = await _get_running_agent(agent_id, user, db)
    try:
        content = await read_file(agent.container_id, path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    except Exception as exc:
        logger.error("read_file error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)[:300])
    return {"path": path, "content": content}


@router.put("/file")
async def write_workspace_file(
    agent_id: str,
    body: WriteFileBody,
    path: str = Query(..., description="File path to write"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Write content to a file in the agent workspace."""
    agent = await _get_running_agent(agent_id, user, db)
    try:
        await write_file(agent.container_id, path, body.content)
    except Exception as exc:
        logger.error("write_file error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)[:300])
    return {"path": path, "status": "written"}


@router.delete("/file")
async def delete_workspace_file(
    agent_id: str,
    path: str = Query(..., description="File path to delete"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file from the agent workspace."""
    agent = await _get_running_agent(agent_id, user, db)
    try:
        await delete_file(agent.container_id, path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("delete_file error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)[:300])
    return {"path": path, "status": "deleted"}
