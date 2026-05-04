"""Persistent memory — extracts and retrieves facts across conversations."""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.memory import Memory

logger = logging.getLogger(__name__)

MAX_MEMORIES_PER_USER = 200
EXTRACT_PROMPT = """Extract 1-5 key facts worth remembering from this conversation.
Return a JSON array of short strings. Only include facts about the user's preferences,
project details, technical requirements, or important context.
If nothing worth remembering, return [].
Example: ["User prefers Python over JavaScript", "Working on an e-commerce project"]"""


async def extract_memories(
    db: AsyncSession,
    user_id: str,
    agent_id: str | None,
    conversation_id: str,
    messages: list[dict],
) -> list[str]:
    """Use a cheap model to extract memorable facts from a conversation."""
    if len(messages) < 4:
        return []

    recent = messages[-10:]
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": json.dumps(recent, ensure_ascii=False)},
        ],
        "max_tokens": 500,
        "temperature": 0,
    }

    try:
        url = f"{settings.openclaw_gateway_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openclaw_gateway_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return []
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            facts = json.loads(content)
            if not isinstance(facts, list):
                return []
    except Exception:
        logger.exception("Memory extraction failed")
        return []

    existing = await db.execute(
        select(Memory.fact).where(Memory.user_id == user_id)
    )
    existing_facts = {row[0].lower() for row in existing.all()}

    saved = []
    for fact in facts[:5]:
        if not isinstance(fact, str) or len(fact) < 5:
            continue
        if fact.lower() in existing_facts:
            continue
        mem = Memory(
            user_id=user_id,
            agent_id=agent_id,
            fact=fact,
            source_conversation_id=conversation_id,
        )
        db.add(mem)
        saved.append(fact)
        existing_facts.add(fact.lower())

    if saved:
        await db.commit()
        logger.info("Saved %d memories for user %s", len(saved), user_id)

    return saved


async def get_relevant_memories(
    db: AsyncSession,
    user_id: str,
    agent_id: str | None = None,
    limit: int = 10,
) -> list[str]:
    """Retrieve recent memories for a user, optionally filtered by agent."""
    q = select(Memory.fact).where(Memory.user_id == user_id)
    if agent_id:
        from sqlalchemy import or_
        q = q.where(or_(Memory.agent_id == agent_id, Memory.agent_id.is_(None)))
    q = q.order_by(Memory.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return [row[0] for row in result.all()]


async def list_user_memories(db: AsyncSession, user_id: str) -> list[Memory]:
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def delete_memory(db: AsyncSession, memory_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
    )
    mem = result.scalar_one_or_none()
    if mem is None:
        return False
    await db.delete(mem)
    await db.commit()
    return True
