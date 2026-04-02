"""Memory service — long-term memory for agents via LLM extraction."""

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.memory import AgentMemory

logger = logging.getLogger(__name__)

# Prompt for extracting memories from conversations
_EXTRACT_PROMPT = """You are a memory extraction system. Analyze the following conversation exchange and extract key facts, preferences, or important information that should be remembered long-term.

User message: {user_msg}
Assistant response: {assistant_msg}

Extract 0-3 discrete facts/memories. Each memory should be a single, concise sentence.
If there's nothing worth remembering (e.g. casual greetings, simple Q&A), return an empty list.

Respond ONLY with a JSON array of objects, each with "content" (string) and "importance" (1-10 integer).
Example: [{"content": "User prefers Python over JavaScript", "importance": 7}]
If nothing to extract: []"""

_SYNTHESIZE_PROMPT = """You are a memory consolidation system. Below are daily memories from an AI agent's conversations. Synthesize them into a concise long-term summary that preserves the most important information.

Daily memories:
{memories}

Create a single paragraph summary (max 200 words) capturing the key facts, preferences, and patterns. Focus on information that would be useful for future conversations.

Respond with ONLY the summary text, no JSON or formatting."""


async def _call_llm(prompt: str) -> str:
    """Make a non-streaming LLM call via shared LiteLLM client."""
    from app.core.http_client import get_litellm_client

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    client = get_litellm_client()
    resp = await client.post("/v1/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def extract_memories(
    db: AsyncSession,
    agent_id: str,
    conversation_id: str,
    user_msg: str,
    assistant_msg: str,
) -> list[AgentMemory]:
    """Use LLM to extract key facts/memories from a conversation exchange."""
    try:
        prompt = _EXTRACT_PROMPT.format(user_msg=user_msg, assistant_msg=assistant_msg)
        raw = await _call_llm(prompt)

        # Parse JSON from LLM response
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        memories_data = json.loads(cleaned)
        if not isinstance(memories_data, list):
            return []

        created = []
        for item in memories_data[:3]:  # Max 3 per exchange
            if not isinstance(item, dict) or "content" not in item:
                continue
            memory = AgentMemory(
                agent_id=agent_id,
                content=item["content"],
                memory_type="fact",
                source_conversation_id=conversation_id,
                importance=min(max(int(item.get("importance", 5)), 1), 10),
            )
            db.add(memory)
            created.append(memory)

        if created:
            await db.commit()
            logger.info("Extracted %d memories for agent %s", len(created), agent_id)

        return created

    except Exception as exc:
        logger.warning("Memory extraction failed for agent %s: %s", agent_id, exc)
        return []


async def get_memory_context(db: AsyncSession, agent_id: str, limit: int = 20) -> str:
    """Fetch recent memories formatted as a context string for the system prompt."""
    result = await db.execute(
        select(AgentMemory)
        .where(AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.importance.desc(), AgentMemory.created_at.desc())
        .limit(limit)
    )
    memories = result.scalars().all()

    if not memories:
        return ""

    lines = ["[Long-term Memory]"]
    for m in memories:
        lines.append(f"- {m.content}")
    lines.append("[End Memory]")
    return "\n".join(lines)


async def synthesize_daily(db: AsyncSession, agent_id: str) -> AgentMemory | None:
    """Compress daily 'fact' memories into a single long-term summary."""
    try:
        result = await db.execute(
            select(AgentMemory)
            .where(
                AgentMemory.agent_id == agent_id,
                AgentMemory.memory_type == "fact",
            )
            .order_by(AgentMemory.created_at.desc())
            .limit(50)
        )
        facts = list(result.scalars().all())

        if len(facts) < 5:
            # Not enough to synthesize
            return None

        memories_text = "\n".join(f"- {m.content}" for m in facts)
        prompt = _SYNTHESIZE_PROMPT.format(memories=memories_text)
        summary = await _call_llm(prompt)

        # Create long-term memory
        long_term = AgentMemory(
            agent_id=agent_id,
            content=summary.strip(),
            memory_type="long_term",
            importance=8,
        )
        db.add(long_term)

        # Delete the synthesized fact memories
        fact_ids = [m.id for m in facts]
        await db.execute(
            delete(AgentMemory).where(AgentMemory.id.in_(fact_ids))
        )

        await db.commit()
        logger.info("Synthesized %d facts into long-term memory for agent %s", len(facts), agent_id)
        return long_term

    except Exception as exc:
        logger.warning("Memory synthesis failed for agent %s: %s", agent_id, exc)
        return None


async def list_memories(
    db: AsyncSession, agent_id: str, offset: int = 0, limit: int = 50
) -> list[AgentMemory]:
    """List memories for an agent, paginated."""
    result = await db.execute(
        select(AgentMemory)
        .where(AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_memory(db: AsyncSession, memory_id: str) -> bool:
    """Delete a specific memory."""
    result = await db.execute(
        select(AgentMemory).where(AgentMemory.id == memory_id)
    )
    memory = result.scalar_one_or_none()
    if memory is None:
        return False
    await db.delete(memory)
    await db.commit()
    return True
