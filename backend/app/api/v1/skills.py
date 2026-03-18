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
    SkillReviewCreateRequest,
    SkillReviewResponse,
    SkillReviewUpdateRequest,
    SkillSubmissionCreateRequest,
    SkillSubmissionResponse,
    SkillToggleRequest,
)
from app.services import skill_service

router = APIRouter(prefix="/skills", tags=["skills"])


# ─── Browsing ───


@router.get("", response_model=list[SkillBriefResponse])
async def list_skills(
    category: str | None = Query(None),
    search: str | None = Query(None),
    tag: str | None = Query(None),
    sort_by: str = Query("install_count", pattern="^(install_count|newest|featured|rating)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.list_skills(db, category, search, sort_by, tag, limit, offset)


@router.get("/categories", response_model=list[str])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_categories(db)


@router.get("/tags", response_model=list[str])
async def get_tags(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_all_tags(db)


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


@router.get("/{slug}/recommendations", response_model=list[SkillBriefResponse])
async def get_recommendations(
    slug: str,
    limit: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return await skill_service.get_recommended_skills(db, skill.id, limit)


# ─── Reviews ───


@router.get("/{slug}/reviews", response_model=list[SkillReviewResponse])
async def get_reviews(
    slug: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return await skill_service.get_skill_reviews(db, skill.id, limit, offset)


@router.get("/{slug}/reviews/mine", response_model=SkillReviewResponse | None)
async def get_my_review(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return await skill_service.get_user_review(db, skill.id, user.id)


@router.post("/{slug}/reviews", status_code=status.HTTP_201_CREATED, response_model=SkillReviewResponse)
async def create_review(
    slug: str,
    body: SkillReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    try:
        return await skill_service.create_review(db, skill.id, user.id, body.rating, body.title, body.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{slug}/reviews", response_model=SkillReviewResponse)
async def update_review(
    slug: str,
    body: SkillReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    try:
        return await skill_service.update_review(db, skill.id, user.id, body.rating, body.title, body.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{slug}/reviews", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = await skill_service.get_skill_by_slug(db, slug)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    try:
        await skill_service.delete_review(db, skill.id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Skill Submissions ───


@router.post("/submissions", status_code=status.HTTP_201_CREATED, response_model=SkillSubmissionResponse)
async def submit_skill(
    body: SkillSubmissionCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await skill_service.create_submission(
            db,
            user_id=user.id,
            name=body.name,
            slug=body.slug,
            summary=body.summary,
            description=body.description,
            category=body.category,
            tags=body.tags,
            version=body.version,
            source_url=body.source_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/submissions/mine", response_model=list[SkillSubmissionResponse])
async def get_my_submissions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await skill_service.get_user_submissions(db, user.id)


# ─── Agent skill management ───


@router.get("/agents/{agent_id}/installed", response_model=list[AgentSkillResponse])
async def get_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.agent_service import get_agent

    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
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
