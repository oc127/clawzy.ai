"""Channels API — manage agent multi-channel configurations."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.channel import AgentChannel
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse
from app.services.agent_service import get_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/channels", tags=["channels"])


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await db.execute(
        select(AgentChannel)
        .where(AgentChannel.agent_id == agent_id)
        .order_by(AgentChannel.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def add_channel(
    agent_id: str,
    body: ChannelCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    channel = AgentChannel(
        agent_id=agent_id,
        channel_type=body.channel_type,
        config=body.config,
        enabled=True,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    agent_id: str,
    channel_id: str,
    body: ChannelUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await db.execute(
        select(AgentChannel).where(
            AgentChannel.id == channel_id,
            AgentChannel.agent_id == agent_id,
        )
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    if body.config is not None:
        channel.config = body.config
    if body.enabled is not None:
        channel.enabled = body.enabled
    await db.commit()
    await db.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel(
    agent_id: str,
    channel_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await db.execute(
        select(AgentChannel).where(
            AgentChannel.id == channel_id,
            AgentChannel.agent_id == agent_id,
        )
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    await db.delete(channel)
    await db.commit()
