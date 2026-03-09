"""Tool Store API — browse catalog, install/uninstall tools on agents."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.i18n import DEFAULT_LOCALE
from app.models.user import User
from app.schemas.toolstore import ToolInstallRequest, ToolInstallResponse
from app.services.agent_service import get_agent
from app.services.toolstore_service import (
    get_catalog,
    get_popular,
    get_agent_tools,
    install_tool,
    uninstall_tool,
    ToolNotFoundError,
)

router = APIRouter(prefix="/toolstore", tags=["toolstore"])


def _locale(request: Request) -> str:
    return getattr(request.state, "locale", DEFAULT_LOCALE)


# --- Public endpoints (no auth required) ---

@router.get("/catalog")
async def catalog(
    request: Request,
    category: str | None = None,
    search: str | None = None,
):
    """Browse the tool catalog. Supports filtering by category and search."""
    locale = _locale(request)
    return get_catalog(category=category, search=search, locale=locale)


@router.get("/popular")
async def popular(request: Request):
    """Top 10 most popular tools."""
    locale = _locale(request)
    return {"tools": get_popular(limit=10, locale=locale)}


# --- Agent tool management (auth required) ---

@router.get("/agents/{agent_id}/tools")
async def agent_tools(
    agent_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tools installed on a specific agent."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    locale = _locale(request)
    return {"tools": get_agent_tools(agent, locale=locale)}


@router.post("/agents/{agent_id}/tools", response_model=ToolInstallResponse)
async def install_agent_tool(
    agent_id: str,
    body: ToolInstallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Install a tool on an agent."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        result = await install_tool(db, agent, body.tool_id)
    except ToolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return result


@router.delete("/agents/{agent_id}/tools/{tool_id}")
async def uninstall_agent_tool(
    agent_id: str,
    tool_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uninstall a tool from an agent."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        result = await uninstall_tool(db, agent, tool_id)
    except ToolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return result
