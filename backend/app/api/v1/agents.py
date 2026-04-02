import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.docker_manager import docker_manager
from app.deps import get_current_user
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent_service import (
    create_agent,
    list_agents,
    get_agent,
    update_agent,
    delete_agent,
    start_agent,
    stop_agent,
    AgentLimitError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_my_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_agents(db, user.id)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_my_agent(
    body: AgentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = await create_agent(db, user.id, body.name, body.model_name, body.system_prompt)
    except AgentLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # Auto-start the agent container after creation
    try:
        agent = await start_agent(db, agent)
    except Exception as exc:
        logger.warning("Auto-start failed for agent %s: %s", agent.id, exc)

    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_my_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_my_agent(
    agent_id: str,
    body: AgentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await update_agent(db, agent, body.name, body.model_name)


@router.post("/{agent_id}/start", response_model=AgentResponse)
async def start_my_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await start_agent(db, agent)


@router.post("/{agent_id}/stop", response_model=AgentResponse)
async def stop_my_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await stop_agent(db, agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    await delete_agent(db, agent)


# ---------------------------------------------------------------------------
# Plugin management
# ---------------------------------------------------------------------------

@router.get("/{agent_id}/plugins")
async def list_agent_plugins(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List installed ClawHub plugins inside the agent container."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.container_id:
        return {"plugins": []}

    try:
        exit_code, output_bytes = await docker_manager.exec_in_container(
            agent.container_id, ["openclaw", "plugins", "list", "--json"]
        )
    except Exception as exc:
        logger.error("Docker exec error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=f"Container exec error: {str(exc)[:300]}")

    output = (output_bytes or b"").decode("utf-8", errors="replace")
    plugins: list = []
    try:
        data = json.loads(output)
        if isinstance(data, list):
            plugins = data
        elif isinstance(data, dict) and "plugins" in data:
            plugins = data["plugins"]
    except (json.JSONDecodeError, ValueError):
        for line in output.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("@", 1)
                plugins.append({"slug": parts[0], "version": parts[1] if len(parts) > 1 else "unknown"})

    return {"plugins": plugins}


@router.delete("/{agent_id}/plugins/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_agent_plugin(
    agent_id: str,
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uninstall a ClawHub plugin from an agent's container."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.container_id:
        raise HTTPException(status_code=400, detail="Agent container is not running")

    try:
        exit_code, output_bytes = await docker_manager.exec_in_container(
            agent.container_id, ["openclaw", "plugins", "uninstall", f"clawhub:{slug}"]
        )
    except Exception as exc:
        logger.error("Docker exec error for agent %s: %s", agent_id, exc)
        raise HTTPException(status_code=500, detail=f"Container exec error: {str(exc)[:300]}")

    output = (output_bytes or b"").decode("utf-8", errors="replace")[:500]
    if exit_code != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Plugin uninstall failed (exit {exit_code}): {output}",
        )
