"""Seed the skills table with initial ClawHub data.

Usage: python -m app.data.seed_skills
"""
import asyncio
import logging

from sqlalchemy import select

from app.core.database import async_session
from app.models.skill import Skill
from app.data.skills_seed import SKILL_SEEDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed():
    async with async_session() as db:
        for data in SKILL_SEEDS:
            # Skip if already exists
            result = await db.execute(select(Skill).where(Skill.slug == data["slug"]))
            if result.scalar_one_or_none():
                logger.info("Skill '%s' already exists, skipping", data["slug"])
                continue

            skill = Skill(**data)
            db.add(skill)
            logger.info("Added skill: %s", data["name"])

        await db.commit()
        logger.info("Seeding complete. %d skills processed.", len(SKILL_SEEDS))


if __name__ == "__main__":
    asyncio.run(seed())
