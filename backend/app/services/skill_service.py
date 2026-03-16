import json
import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.agent import Agent
from app.models.skill import AgentSkill, Skill

logger = logging.getLogger(__name__)


async def list_skills(
    db: AsyncSession,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "install_count",
    limit: int = 50,
    offset: int = 0,
) -> list[Skill]:
    query = select(Skill)

    if category:
        query = query.where(Skill.category == category)
    if search:
        pattern = f"%{search}%"
        query = query.where(Skill.name.ilike(pattern) | Skill.summary.ilike(pattern))

    if sort_by == "install_count":
        query = query.order_by(Skill.install_count.desc())
    elif sort_by == "newest":
        query = query.order_by(Skill.created_at.desc())
    elif sort_by == "featured":
        query = query.order_by(Skill.is_featured.desc(), Skill.install_count.desc())
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


async def get_trending_skills(db: AsyncSession, limit: int = 10) -> list[Skill]:
    result = await db.execute(select(Skill).order_by(Skill.install_count.desc()).limit(limit))
    return list(result.scalars().all())


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
        .where(AgentSkill.agent_id == agent_id, AgentSkill.enabled == True)
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
