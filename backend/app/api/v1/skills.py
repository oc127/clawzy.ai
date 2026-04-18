"""Skills API — manage agent skills and browse built-in skill library."""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillUpdate, SkillToggle, SkillExtractRequest, SkillResponse
from app.services.agent_service import get_agent
from app.services.skill_service import (
    install_skill,
    update_skill,
    list_skills,
    get_skill,
    toggle_skill,
    delete_skill,
    auto_extract_skill,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/skills", tags=["skills"])

# ── Built-in skill library (no agent/auth scope) ───────────────────────────
builtin_router = APIRouter(prefix="/skills/builtin", tags=["builtin-skills"])


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
        description=body.description,
        triggers=body.triggers,
    )


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_agent_skill(
    agent_id: str,
    skill_id: str,
    body: SkillUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    skill = await get_skill(db, skill_id)
    if skill is None or skill.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    updated = await update_skill(
        db,
        skill_id=skill_id,
        name=body.name,
        description=body.description,
        triggers=body.triggers,
        content=body.content,
        enabled=body.enabled,
    )
    return updated


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


@router.post("/extract", response_model=SkillResponse | None, status_code=status.HTTP_200_OK)
async def extract_skill_from_conversation(
    agent_id: str,
    body: SkillExtractRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger skill extraction from a conversation history.

    Returns the created skill if a reusable pattern was found, or null if not.
    """
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    skill = await auto_extract_skill(db, agent_id, body.messages)
    return skill


# ── Built-in skill library endpoints ──────────────────────────────────────

@builtin_router.get("", summary="List all built-in skills (compact index)")
async def list_builtin_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    user: User = Depends(get_current_user),
):
    """Return compact metadata for all built-in disk-based skills."""
    from app.services.skill_loader import list_all_skills

    skills = list_all_skills()
    if category:
        skills = [s for s in skills if s.category == category]

    return [
        {
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "tags": s.tags,
            "triggers": s.triggers,
            "version": s.version,
            "platform": s.platform,
        }
        for s in skills
    ]


@builtin_router.get("/search", summary="Search built-in skills")
async def search_builtin_skills(
    q: str = Query(..., min_length=1, description="Search query"),
    user: User = Depends(get_current_user),
):
    """Search built-in skills by name, description, tags, or triggers."""
    from app.services.skill_loader import search_skills

    results = search_skills(q)
    return [
        {
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "tags": s.tags,
            "triggers": s.triggers,
        }
        for s in results
    ]


@builtin_router.get("/{name}", summary="Get full content of a built-in skill")
async def get_builtin_skill(
    name: str,
    user: User = Depends(get_current_user),
):
    """Return full SKILL.md content for a specific built-in skill."""
    from app.services.skill_loader import get_skill as load_skill

    skill = load_skill(name)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Built-in skill '{name}' not found")

    return {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "tags": skill.tags,
        "triggers": skill.triggers,
        "version": skill.version,
        "platform": skill.platform,
        "content": skill.content,
    }
