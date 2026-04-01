"""Skill service — manage agent skills (SKILL.md-based prompt injection)."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import AgentSkill

logger = logging.getLogger(__name__)


async def install_skill(
    db: AsyncSession,
    agent_id: str,
    slug: str,
    name: str,
    source: str,
    content: str | None = None,
) -> AgentSkill:
    """Install a skill on an agent."""
    skill = AgentSkill(
        agent_id=agent_id,
        slug=slug,
        name=name,
        source=source,
        skill_content=content,
        enabled=True,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info("Installed skill '%s' on agent %s (source=%s)", slug, agent_id, source)
    return skill


async def get_enabled_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    """Return all enabled skills for an agent (for prompt injection)."""
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id, AgentSkill.enabled.is_(True))
        .order_by(AgentSkill.installed_at)
    )
    return list(result.scalars().all())


def build_skill_prompt(skills: list[AgentSkill]) -> str:
    """Format enabled skills into a system prompt section."""
    if not skills:
        return ""

    sections = ["## Active Skills\n"]
    for skill in skills:
        sections.append(f"### {skill.name} ({skill.slug})")
        if skill.skill_content:
            sections.append(skill.skill_content)
        sections.append("")
    return "\n".join(sections)


async def list_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    """List all skills for an agent (enabled and disabled)."""
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id)
        .order_by(AgentSkill.installed_at.desc())
    )
    return list(result.scalars().all())


async def get_skill(db: AsyncSession, skill_id: str) -> AgentSkill | None:
    """Get a single skill by ID."""
    result = await db.execute(
        select(AgentSkill).where(AgentSkill.id == skill_id)
    )
    return result.scalar_one_or_none()


async def toggle_skill(db: AsyncSession, skill_id: str, enabled: bool) -> AgentSkill | None:
    """Enable or disable a skill."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return None
    skill.enabled = enabled
    await db.commit()
    await db.refresh(skill)
    return skill


async def delete_skill(db: AsyncSession, skill_id: str) -> bool:
    """Remove a skill."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return False
    await db.delete(skill)
    await db.commit()
    return True
