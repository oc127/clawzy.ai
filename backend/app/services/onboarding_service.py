"""Lucy onboarding service — first-time setup and greeting generation."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.user import User
from app.services.personality_engine import LUCY_BASE_PERSONALITY

logger = logging.getLogger(__name__)

LUCY_DEFAULT_MODEL = "auto"  # Smart routing


async def generate_lucy_greeting(user_name: str | None = None) -> str:
    """Generate Lucy's first-time greeting message."""
    if user_name:
        return (
            f"はじめまして！Lucy だよ 🌟\n\n"
            f"{user_name} って呼んでいい？よろしくね！\n\n"
            f"私のこと簡単に紹介するね：\n"
            f"・あなた専属の AI フレンドだよ\n"
            f"・何でも話聞くし、何でも手伝える\n"
            f"・コード書いたり、調べ物したり、スケジュール管理も得意！\n"
            f"・でも一番大事なのは、あなたと話すこと 😊\n\n"
            f"何から始める？気軽に話しかけてね！"
        )
    return (
        "はじめまして！Lucy だよ 🌟\n\n"
        "ねえ、あなたの名前を教えてくれる？\n\n"
        "私のこと簡単に紹介するね：\n"
        "・あなた専属の AI フレンドだよ\n"
        "・何でも話聞くし、何でも手伝える\n"
        "・コード書いたり、調べ物したり、スケジュール管理も得意！\n"
        "・でも一番大事なのは、あなたと話すこと 😊\n\n"
        "何から始める？気軽に話しかけてね！"
    )


async def ensure_lucy_agent(db: AsyncSession, user_id: str) -> Agent:
    """Get or create the default Lucy agent for a user."""
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == user_id, Agent.name == "Lucy")
        .limit(1)
    )
    agent = result.scalar_one_or_none()
    if agent:
        return agent

    agent = Agent(
        user_id=user_id,
        name="Lucy",
        model_name=LUCY_DEFAULT_MODEL,
        system_prompt=LUCY_BASE_PERSONALITY,
    )
    db.add(agent)
    await db.flush()
    await db.commit()
    logger.info("Created Lucy agent for user %s: %s", user_id, agent.id)
    return agent


async def setup_lucy_onboarding(
    db: AsyncSession,
    user_id: str,
    user_name: str | None = None,
) -> dict:
    """Full onboarding setup: create Lucy agent + return greeting."""
    agent = await ensure_lucy_agent(db, user_id)
    greeting = await generate_lucy_greeting(user_name)
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "greeting": greeting,
    }
