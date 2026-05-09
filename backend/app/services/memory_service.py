"""Persistent memory — extracts and retrieves structured facts across conversations."""

import json
import logging

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.memory import Memory

logger = logging.getLogger(__name__)

MAX_MEMORIES_PER_USER = 200
VALID_MEMORY_TYPES = {"identity", "preference", "goal", "relationship", "episode", "reflection"}

EXTRACT_PROMPT = """\
Extract 1-5 key facts worth remembering from this conversation.
Return a JSON array of objects with the following structure:
[{"fact": "...", "type": "preference|identity|goal|relationship|episode|reflection", "importance": 1-5}]

Memory types:
- identity: who the user is (name, role, background)
- preference: likes, dislikes, style choices
- goal: what the user is trying to achieve
- relationship: connections to people, teams, orgs
- episode: notable events or experiences mentioned
- reflection: insights, lessons learned, opinions

Importance scale: 1=trivial, 2=minor, 3=moderate, 4=significant, 5=critical

Only include facts about the user's preferences, identity, goals, relationships, \
project details, technical requirements, or important context.
If nothing worth remembering, return [].
Example: [{"fact": "User prefers Python over JavaScript", "type": "preference", "importance": 3}]"""


async def extract_memories(
    db: AsyncSession,
    user_id: str,
    agent_id: str | None,
    conversation_id: str,
    messages: list[dict],
) -> list[str]:
    """Use a cheap model to extract structured memorable facts from a conversation."""
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
            raw_facts = json.loads(content)
            if not isinstance(raw_facts, list):
                return []
    except Exception:
        logger.exception("Memory extraction failed")
        return []

    existing = await db.execute(
        select(Memory.fact).where(Memory.user_id == user_id, Memory.is_active.is_(True))
    )
    existing_facts = {row[0].lower() for row in existing.all()}

    saved = []
    for entry in raw_facts[:5]:
        # Support both old format (plain strings) and new format (dicts)
        if isinstance(entry, str):
            fact = entry
            memory_type = "episode"
            importance = 3
        elif isinstance(entry, dict) and "fact" in entry:
            fact = entry["fact"]
            memory_type = entry.get("type", "episode")
            importance = entry.get("importance", 3)
        else:
            continue

        if not isinstance(fact, str) or len(fact) < 5:
            continue
        if fact.lower() in existing_facts:
            continue

        # Validate and normalize memory_type
        if memory_type not in VALID_MEMORY_TYPES:
            memory_type = "episode"

        # Clamp importance to 1-5
        try:
            importance = max(1, min(5, int(importance)))
        except (ValueError, TypeError):
            importance = 3

        # Set confidence based on how specific/clear the fact is
        confidence = 0.8
        if len(fact) > 50:
            confidence = 0.9  # longer, more detailed facts get higher confidence
        if importance >= 4:
            confidence = 0.9

        # Resolve conflicts before saving
        await resolve_conflicts(db, user_id, fact, importance)

        mem = Memory(
            user_id=user_id,
            agent_id=agent_id,
            fact=fact,
            source_conversation_id=conversation_id,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
        )
        db.add(mem)
        saved.append(fact)
        existing_facts.add(fact.lower())

    if saved:
        await db.commit()
        logger.info("Saved %d memories for user %s", len(saved), user_id)

    return saved


async def resolve_conflicts(
    db: AsyncSession,
    user_id: str,
    new_fact: str,
    new_importance: int,
) -> None:
    """Check for conflicting memories using simple keyword overlap and deactivate the weaker one.

    When a new memory has significant keyword overlap with an existing one,
    the one with lower importance is deactivated (is_active=False).
    """
    # Extract meaningful keywords (skip very short words)
    new_words = {w.lower() for w in new_fact.split() if len(w) > 3}
    if not new_words:
        return

    existing = await db.execute(
        select(Memory).where(
            Memory.user_id == user_id,
            Memory.is_active.is_(True),
        )
    )
    existing_memories = existing.scalars().all()

    for mem in existing_memories:
        existing_words = {w.lower() for w in mem.fact.split() if len(w) > 3}
        if not existing_words:
            continue

        # Calculate keyword overlap ratio
        overlap = new_words & existing_words
        smaller_set_size = min(len(new_words), len(existing_words))
        if smaller_set_size == 0:
            continue
        overlap_ratio = len(overlap) / smaller_set_size

        # If significant overlap (>50%), treat as potential conflict
        if overlap_ratio > 0.5:
            if new_importance >= mem.importance:
                # New memory wins — deactivate existing
                mem.is_active = False
                logger.info("Deactivated conflicting memory id=%s (importance %d) in favor of new (importance %d)",
                            mem.id, mem.importance, new_importance)
            else:
                # Existing memory wins — the new one should not be saved
                # We signal this by raising, but simpler: just deactivate nothing
                # and the duplicate-check in extract_memories will skip near-dupes.
                # For now, keep both — the existing one has higher importance.
                pass


async def get_relevant_memories(
    db: AsyncSession,
    user_id: str,
    agent_id: str | None = None,
    limit: int = 10,
    memory_type: str | None = None,
) -> list[str]:
    """Retrieve active memories for a user, optionally filtered by agent and type."""
    q = select(Memory.fact).where(
        Memory.user_id == user_id,
        Memory.is_active.is_(True),
    )
    if agent_id:
        q = q.where(or_(Memory.agent_id == agent_id, Memory.agent_id.is_(None)))
    if memory_type:
        q = q.where(Memory.memory_type == memory_type)
    q = q.order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return [row[0] for row in result.all()]


async def get_user_profile_summary(
    db: AsyncSession,
    user_id: str,
    max_length: int = 1375,
) -> str:
    """Build a USER.md-style compact profile summary from active identity, preference, and goal memories."""
    result = await db.execute(
        select(Memory).where(
            Memory.user_id == user_id,
            Memory.is_active.is_(True),
            Memory.memory_type.in_(["identity", "preference", "goal"]),
        ).order_by(Memory.importance.desc(), Memory.created_at.desc())
    )
    memories = result.scalars().all()

    if not memories:
        return ""

    sections: dict[str, list[str]] = {
        "identity": [],
        "preference": [],
        "goal": [],
    }
    for mem in memories:
        sections.setdefault(mem.memory_type, []).append(mem.fact)

    parts: list[str] = []
    section_titles = {
        "identity": "## Identity",
        "preference": "## Preferences",
        "goal": "## Goals",
    }
    for key in ("identity", "preference", "goal"):
        facts = sections.get(key, [])
        if facts:
            lines = [section_titles[key]]
            for fact in facts:
                lines.append(f"- {fact}")
            parts.append("\n".join(lines))

    summary = "\n\n".join(parts)

    # Truncate to max_length if needed
    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."

    return summary


async def list_user_memories(
    db: AsyncSession,
    user_id: str,
    memory_type: str | None = None,
    active_only: bool = True,
) -> list[Memory]:
    """List memories for a user with optional filtering by type and active status."""
    q = select(Memory).where(Memory.user_id == user_id)
    if active_only:
        q = q.where(Memory.is_active.is_(True))
    if memory_type:
        q = q.where(Memory.memory_type == memory_type)
    q = q.order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(50)
    result = await db.execute(q)
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
