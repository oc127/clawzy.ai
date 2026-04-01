"""Skills API — manage agent skills."""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillToggle, SkillResponse
from app.services.agent_service import get_agent
from app.services.skill_service import (
    install_skill,
    list_skills,
    toggle_skill,
    delete_skill,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/skills", tags=["skills"])


def _slugify(name: str) -> str:
    """Generate a slug from a skill name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "custom-skill"


@router.get("", response_model=list[SkillResponse])
async def list_agent_skills(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await list_skills(db, agent_id)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_skill(
    agent_id: str,
    body: SkillCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    slug = body.slug or _slugify(body.name)
    return await install_skill(
        db,
        agent_id=agent_id,
        slug=slug,
        name=body.name,
        source="custom",
        content=body.content,
    )


@router.patch("/{skill_id}", response_model=SkillResponse)
async def toggle_agent_skill(
    agent_id: str,
    skill_id: str,
    body: SkillToggle,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    skill = await toggle_skill(db, skill_id, body.enabled)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_skill(
    agent_id: str,
    skill_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    deleted = await delete_skill(db, skill_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
