import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.agent import Agent
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me", status_code=204)
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the current user's account and all associated data.

    Required by Apple App Store guidelines for account deletion.
    Cleans up Docker containers for agents, then deletes the user
    (CASCADE handles agents, conversations, messages, credit transactions).
    """
    from app.core.docker_manager import docker_manager

    # 1. Stop and remove all agent containers
    result = await db.execute(
        select(Agent).where(Agent.user_id == user.id)
    )
    agents = result.scalars().all()

    for agent in agents:
        if agent.container_id:
            try:
                await docker_manager.stop_container(agent.container_id)
                await docker_manager.remove_container(agent.container_id)
            except Exception:
                logger.warning(
                    "Failed to remove container %s for agent %s during account deletion",
                    agent.container_id,
                    agent.id,
                )

    # 2. Delete user (CASCADE removes agents, conversations, messages, credits)
    await db.delete(user)
    await db.commit()

    logger.info("Account deleted: user_id=%s, agents_cleaned=%d", user.id, len(agents))
    return Response(status_code=204)
