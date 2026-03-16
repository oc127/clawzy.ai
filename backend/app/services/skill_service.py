import json
import logging
import os

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.agent import Agent
from app.models.skill import AgentSkill, Skill, SkillReview, SkillSubmission

logger = logging.getLogger(__name__)


# ─── Skill Browsing ───


async def list_skills(
    db: AsyncSession,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "install_count",
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Skill]:
    query = select(Skill)

    if category:
        query = query.where(Skill.category == category)
    if search:
        pattern = f"%{search}%"
        query = query.where(Skill.name.ilike(pattern) | Skill.summary.ilike(pattern))
    if tag:
        # JSON contains for tag filtering
        query = query.where(Skill.tags.contains([tag]))

    if sort_by == "install_count":
        query = query.order_by(Skill.install_count.desc())
    elif sort_by == "newest":
        query = query.order_by(Skill.created_at.desc())
    elif sort_by == "featured":
        query = query.order_by(Skill.is_featured.desc(), Skill.install_count.desc())
    elif sort_by == "rating":
        query = query.order_by(Skill.avg_rating.desc(), Skill.review_count.desc())
    else:
        query = query.order_by(Skill.install_count.desc())

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_skill_by_id(db: AsyncSession, skill_id: str) -> Skill | None:
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    return result.scalar_one_or_none()


async def get_skill_by_slug(db: AsyncSession, slug: str) -> Skill | None:
    result = await db.execute(select(Skill).where(Skill.slug == slug))
    return result.scalar_one_or_none()


async def get_categories(db: AsyncSession) -> list[str]:
    result = await db.execute(select(Skill.category).distinct().order_by(Skill.category))
    return list(result.scalars().all())


async def get_all_tags(db: AsyncSession) -> list[str]:
    """Get all unique tags across all skills."""
    result = await db.execute(select(Skill.tags).where(Skill.tags.isnot(None)))
    tag_set: set[str] = set()
    for (tags,) in result:
        if tags:
            tag_set.update(tags)
    return sorted(tag_set)


async def get_trending_skills(db: AsyncSession, limit: int = 10) -> list[Skill]:
    result = await db.execute(select(Skill).order_by(Skill.install_count.desc()).limit(limit))
    return list(result.scalars().all())


async def get_recommended_skills(db: AsyncSession, skill_id: str, limit: int = 6) -> list[Skill]:
    """Get recommended skills based on same category + overlapping tags."""
    skill = await get_skill_by_id(db, skill_id)
    if skill is None:
        return []

    query = select(Skill).where(Skill.id != skill_id)

    # Same category first, then by install count
    query = query.where(Skill.category == skill.category)
    query = query.order_by(Skill.avg_rating.desc(), Skill.install_count.desc())
    query = query.limit(limit)

    result = await db.execute(query)
    recommendations = list(result.scalars().all())

    # If not enough from same category, fill from top-rated overall
    if len(recommendations) < limit:
        remaining = limit - len(recommendations)
        existing_ids = {r.id for r in recommendations} | {skill_id}
        fill_query = (
            select(Skill)
            .where(Skill.id.notin_(existing_ids))
            .order_by(Skill.avg_rating.desc(), Skill.install_count.desc())
            .limit(remaining)
        )
        fill_result = await db.execute(fill_query)
        recommendations.extend(fill_result.scalars().all())

    return recommendations


# ─── Agent Skill Install / Uninstall ───


async def install_skill(db: AsyncSession, agent_id: str, skill_id: str, user_id: str) -> AgentSkill:
    # Verify agent belongs to user
    agent = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id))
    agent = agent.scalar_one_or_none()
    if agent is None:
        raise ValueError("Agent not found")

    # Verify skill exists
    skill = await get_skill_by_id(db, skill_id)
    if skill is None:
        raise ValueError("Skill not found")

    # Check if already installed
    existing = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Skill already installed on this agent")

    # Create the association
    agent_skill = AgentSkill(agent_id=agent_id, skill_id=skill_id)
    db.add(agent_skill)

    # Increment install count
    skill.install_count += 1

    await db.commit()
    await db.refresh(agent_skill)

    # Update agent's OpenClaw config
    await _sync_agent_skills_config(db, agent_id)

    return agent_skill


async def uninstall_skill(db: AsyncSession, agent_id: str, skill_id: str, user_id: str) -> None:
    # Verify agent belongs to user
    agent = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id))
    if agent.scalar_one_or_none() is None:
        raise ValueError("Agent not found")

    result = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )
    agent_skill = result.scalar_one_or_none()
    if agent_skill is None:
        raise ValueError("Skill not installed on this agent")

    # Decrement install count
    skill = await get_skill_by_id(db, skill_id)
    if skill and skill.install_count > 0:
        skill.install_count -= 1

    await db.delete(agent_skill)
    await db.commit()

    # Update agent's OpenClaw config
    await _sync_agent_skills_config(db, agent_id)


async def toggle_skill(db: AsyncSession, agent_id: str, skill_id: str, user_id: str, enabled: bool) -> AgentSkill:
    # Verify agent belongs to user
    agent = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id))
    if agent.scalar_one_or_none() is None:
        raise ValueError("Agent not found")

    result = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )
    agent_skill = result.scalar_one_or_none()
    if agent_skill is None:
        raise ValueError("Skill not installed on this agent")

    agent_skill.enabled = enabled
    await db.commit()
    await db.refresh(agent_skill)

    # Update agent's OpenClaw config
    await _sync_agent_skills_config(db, agent_id)

    return agent_skill


async def get_agent_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id)
        .options(selectinload(AgentSkill.skill))
        .order_by(AgentSkill.installed_at.desc())
    )
    return list(result.scalars().all())


# ─── Reviews ───


async def get_skill_reviews(
    db: AsyncSession, skill_id: str, limit: int = 50, offset: int = 0
) -> list[SkillReview]:
    result = await db.execute(
        select(SkillReview)
        .where(SkillReview.skill_id == skill_id)
        .options(selectinload(SkillReview.user))
        .order_by(SkillReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_user_review(db: AsyncSession, skill_id: str, user_id: str) -> SkillReview | None:
    result = await db.execute(
        select(SkillReview)
        .where(SkillReview.skill_id == skill_id, SkillReview.user_id == user_id)
        .options(selectinload(SkillReview.user))
    )
    return result.scalar_one_or_none()


async def create_review(
    db: AsyncSession, skill_id: str, user_id: str, rating: int, title: str | None, content: str | None
) -> SkillReview:
    skill = await get_skill_by_id(db, skill_id)
    if skill is None:
        raise ValueError("Skill not found")

    existing = await get_user_review(db, skill_id, user_id)
    if existing:
        raise ValueError("You have already reviewed this skill")

    review = SkillReview(
        skill_id=skill_id,
        user_id=user_id,
        rating=rating,
        title=title,
        content=content,
    )
    db.add(review)

    # Update skill avg rating
    await _recalculate_skill_rating(db, skill)

    await db.commit()
    await db.refresh(review)

    # Reload with user relationship
    return await get_user_review(db, skill_id, user_id)  # type: ignore[return-value]


async def update_review(
    db: AsyncSession,
    skill_id: str,
    user_id: str,
    rating: int | None,
    title: str | None,
    content: str | None,
) -> SkillReview:
    review = await get_user_review(db, skill_id, user_id)
    if review is None:
        raise ValueError("Review not found")

    if rating is not None:
        review.rating = rating
    if title is not None:
        review.title = title
    if content is not None:
        review.content = content

    skill = await get_skill_by_id(db, skill_id)
    if skill:
        await _recalculate_skill_rating(db, skill)

    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, skill_id: str, user_id: str) -> None:
    review = await get_user_review(db, skill_id, user_id)
    if review is None:
        raise ValueError("Review not found")

    await db.delete(review)

    skill = await get_skill_by_id(db, skill_id)
    if skill:
        await _recalculate_skill_rating(db, skill)

    await db.commit()


async def _recalculate_skill_rating(db: AsyncSession, skill: Skill) -> None:
    """Recalculate the average rating and review count for a skill."""
    result = await db.execute(
        select(func.avg(SkillReview.rating), func.count(SkillReview.id)).where(
            SkillReview.skill_id == skill.id
        )
    )
    row = result.one()
    skill.avg_rating = round(float(row[0] or 0), 2)
    skill.review_count = int(row[1] or 0)


# ─── Skill Submissions ───


async def create_submission(
    db: AsyncSession,
    user_id: str,
    name: str,
    slug: str,
    summary: str,
    description: str,
    category: str,
    tags: list[str] | None,
    version: str | None,
    source_url: str | None,
) -> SkillSubmission:
    # Check slug uniqueness against existing skills
    existing = await get_skill_by_slug(db, slug)
    if existing:
        raise ValueError("A skill with this slug already exists")

    # Check for pending submission with same slug
    pending = await db.execute(
        select(SkillSubmission).where(SkillSubmission.slug == slug, SkillSubmission.status == "pending")
    )
    if pending.scalar_one_or_none():
        raise ValueError("A submission with this slug is already pending review")

    submission = SkillSubmission(
        user_id=user_id,
        name=name,
        slug=slug,
        summary=summary,
        description=description,
        category=category,
        tags=tags,
        version=version,
        source_url=source_url,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_user_submissions(db: AsyncSession, user_id: str) -> list[SkillSubmission]:
    result = await db.execute(
        select(SkillSubmission)
        .where(SkillSubmission.user_id == user_id)
        .order_by(SkillSubmission.created_at.desc())
    )
    return list(result.scalars().all())


async def get_submission_by_id(db: AsyncSession, submission_id: str) -> SkillSubmission | None:
    result = await db.execute(select(SkillSubmission).where(SkillSubmission.id == submission_id))
    return result.scalar_one_or_none()


# ─── Agent Config Sync ───


async def _sync_agent_skills_config(db: AsyncSession, agent_id: str) -> None:
    """Regenerate the agent's openclaw.json with current skills config.

    OpenClaw's file watcher detects the change and hot-reloads automatically.
    """
    # Get the agent
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        return

    # Get enabled skills
    skills_result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id, AgentSkill.enabled == True)  # noqa: E712
        .options(selectinload(AgentSkill.skill))
    )
    agent_skills = list(skills_result.scalars().all())

    # Build the config
    from app.core.docker_manager import docker_manager

    skill_slugs = [as_.skill.slug for as_ in agent_skills]
    config = docker_manager.generate_agent_config(
        model_name=agent.model_name,
        litellm_key=settings.litellm_master_key,
        skill_slugs=skill_slugs,
    )

    # Write to the agent's config directory
    config_dir = os.path.join(settings.openclaw_agent_config_dir, agent_id)
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "openclaw.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    logger.info("Updated skills config for agent %s: %s", agent_id, skill_slugs)
