from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
        agent = await create_agent(db, user.id, body.name, body.model_name)
    except AgentLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
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
