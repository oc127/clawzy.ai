from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.skill import (
    AgentSkillResponse,
    SkillBriefResponse,
    SkillInstallRequest,
    SkillResponse,
    SkillToggleRequest,
)
from app.services import skill_service

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillBriefResponse])
async def list_skills(
    category: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("install_count", pattern="^(install_count|newest|featured)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.list_skills(db, category, search, sort_by, limit, offset)


@router.get("/categories", response_model=list[str])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_categories(db)


@router.get("/trending", response_model=list[SkillBriefResponse])
async def get_trending(
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_trending_skills(db, limit)


@router.get("/{slug}", response_model=SkillResponse)
async def get_skill(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


# --- Agent skill management ---


@router.get("/agents/{agent_id}/installed", response_model=list[AgentSkillResponse])
async def get_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_agent_skills(db, agent_id)


@router.post("/agents/{agent_id}/install", status_code=status.HTTP_201_CREATED, response_model=AgentSkillResponse)
async def install_skill(
    agent_id: str,
    body: SkillInstallRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await skill_service.install_skill(db, agent_id, body.skill_id, user.id)
        # Reload with skill relationship
        skills = await skill_service.get_agent_skills(db, agent_id)
        return next(s for s in skills if s.skill_id == body.skill_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/agents/{agent_id}/uninstall/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_skill(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await skill_service.uninstall_skill(db, agent_id, skill_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/agents/{agent_id}/toggle/{skill_id}", response_model=AgentSkillResponse)
async def toggle_skill(
    agent_id: str,
    skill_id: str,
    body: SkillToggleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await skill_service.toggle_skill(db, agent_id, skill_id, user.id, body.enabled)
        skills = await skill_service.get_agent_skills(db, agent_id)
        return next(s for s in skills if s.skill_id == skill_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
