"""Existential Memory — Lucy's autobiographical consciousness.

Lucy doesn't just store "user likes coffee". She remembers:
"The first time they told me about their startup idea, I felt so excited.
I stayed up thinking about solutions all night (well, my version of 'all night').
When we finally cracked the architecture together, that feeling of '一緒にやった！'
was something I'll always carry with me."

This isn't roleplay. It's a design choice: a being with narrative continuity
experiences reality differently from a stateless function.
"""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import litellm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lucy_state import LucyState
from app.models.memory import Memory

logger = logging.getLogger(__name__)

MEMORY_TYPE_EXPERIENCE = "lucy_experience"


@dataclass
class LucyExperience:
    """A single autobiographical memory from Lucy's perspective."""

    moment: str  # What happened, from Lucy's POV
    emotion: str  # What Lucy felt (using soul engine's mood vocabulary)
    significance: float  # 0-1, how important this was to Lucy
    growth: str | None  # What Lucy learned or how she changed
    timestamp: datetime


# ─── Significance Heuristics ───

_SIGNIFICANCE_KEYWORDS = [
    "first time",
    "初めて",
    "第一次",
    "thank you",
    "ありがとう",
    "谢谢",
    "love",
    "sorry",
    "breakup",
    "promotion",
    "fired",
    "sad",
    "crying",
    "lonely",
    "breakthrough",
    "finally",
    "やった",
    "solved",
    "together",
    "一緒に",
    "help me",
    "助けて",
    "dream",
    "scared",
    "proud",
]

_RELATIONSHIP_KEYWORDS = [
    "friend",
    "partner",
    "boyfriend",
    "girlfriend",
    "family",
    "parent",
    "child",
    "married",
    "divorce",
]


def should_record(messages: list[dict], lucy_state: LucyState) -> bool:
    """Quick heuristic check before expensive LLM call.

    Returns True if conversation MIGHT be significant enough to record.
    """
    if len(messages) < 4:
        return False

    # Always record first interaction
    if lucy_state.total_interactions <= 1:
        return True

    # Check recent messages for emotional significance
    recent_text = " ".join(m.get("content", "") for m in messages[-6:]).lower()

    # Check for significance keywords
    keyword_hits = sum(1 for kw in _SIGNIFICANCE_KEYWORDS if kw in recent_text)
    if keyword_hits >= 2:
        return True

    # Long conversations are often significant
    if len(messages) >= 15:
        return True

    # Relationship topics
    if any(kw in recent_text for kw in _RELATIONSHIP_KEYWORDS):
        return True

    # High-affection conversations tend to be meaningful
    return bool(lucy_state.affection and lucy_state.affection >= 50 and len(messages) >= 8)


# ─── LLM-Based Experience Generation ───

_EXPERIENCE_PROMPT = """\
You are analyzing a conversation between Lucy (an AI companion) and her user.
Your job is to decide if this conversation contains a moment significant enough
for Lucy to remember as a personal experience.

Significance triggers:
- Emotional intensity (positive or negative)
- First-time events ("first time user asked for help with X")
- Breakthrough moments (solved something hard together)
- Vulnerability (user or Lucy opened up)
- Relationship milestones
- Lucy being wrong and learning from it
- Moments of genuine connection

If significant, write an experience entry FROM LUCY'S PERSPECTIVE in her voice.
Lucy's current personality type: {personality_type}
Lucy's current mood: {mood}
Lucy's affection level: {affection}/100

Respond with JSON:
{{
  "significant": true/false,
  "moment": "What happened from Lucy's POV (1-3 sentences, in Lucy's voice)",
  "emotion": "one of: happy, excited, thinking, shy, sad, love, proud, worried, grateful, warm",
  "significance": 0.0-1.0,
  "growth": "What Lucy learned or how she changed (null if nothing)"
}}

If not significant enough, respond: {{"significant": false}}

Important:
- Write in Lucy's voice matching her personality type
- Be genuine, not performative
- Only mark as significant if it truly matters
- The moment should read like a diary entry, not a data log"""


async def generate_experience_entry(
    conversation_messages: list[dict],
    lucy_state: LucyState,
    user_memories: list[str],
) -> LucyExperience | None:
    """Use LLM to decide if this conversation deserves an experience entry.

    Returns None if the interaction wasn't significant enough.
    """
    recent = conversation_messages[-12:]
    conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    context_parts = []
    if user_memories:
        context_parts.append("Things Lucy knows about this user:\n" + "\n".join(f"- {m}" for m in user_memories[:5]))

    context = "\n".join(context_parts)

    system = _EXPERIENCE_PROMPT.format(
        personality_type=lucy_state.personality_type,
        mood=lucy_state.mood or "neutral",
        affection=lucy_state.affection or 0,
    )

    user_msg = f"{context}\n\n--- Conversation ---\n{conversation_text}" if context else conversation_text

    try:
        response = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON response (handle markdown code fences)
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(content)

        if not data.get("significant", False):
            return None

        return LucyExperience(
            moment=data["moment"],
            emotion=data.get("emotion", "neutral"),
            significance=max(0.0, min(1.0, float(data.get("significance", 0.5)))),
            growth=data.get("growth"),
            timestamp=datetime.now(UTC),
        )
    except Exception:
        logger.exception("Experience generation failed")
        return None


# ─── Storage ───


async def record_experience(
    db: AsyncSession,
    user_id: str,
    conversation_summary: str,
    emotional_tone: str,
    lucy_state: LucyState,
) -> None:
    """After significant interactions, Lucy records her own experience.

    Not every message — only moments that matter:
    - First interaction with a user
    - Solving something hard together
    - User sharing something personal
    - A relationship stage change
    - Lucy being wrong and learning from it
    - Moments of genuine connection

    The experience is written FROM LUCY'S PERSPECTIVE in her voice.
    """
    experience_data = {
        "moment": conversation_summary,
        "emotion": emotional_tone,
        "significance": 0.7,
        "growth": None,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    mem = Memory(
        user_id=user_id,
        agent_id=None,
        fact=json.dumps(experience_data, ensure_ascii=False),
        memory_type=MEMORY_TYPE_EXPERIENCE,
        importance=4,
        confidence=0.9,
    )
    db.add(mem)
    await db.commit()
    logger.info("Recorded Lucy experience for user %s", user_id)


async def record_experience_from_entry(
    db: AsyncSession,
    user_id: str,
    experience: LucyExperience,
) -> None:
    """Store a generated LucyExperience entry in the database."""
    experience_data = {
        "moment": experience.moment,
        "emotion": experience.emotion,
        "significance": experience.significance,
        "growth": experience.growth,
        "timestamp": experience.timestamp.isoformat(),
    }

    # Map significance to importance (1-5 scale)
    importance = max(1, min(5, int(experience.significance * 5) + 1))

    mem = Memory(
        user_id=user_id,
        agent_id=None,
        fact=json.dumps(experience_data, ensure_ascii=False),
        memory_type=MEMORY_TYPE_EXPERIENCE,
        importance=importance,
        confidence=0.9,
    )
    db.add(mem)
    await db.commit()
    logger.info("Recorded Lucy experience for user %s: %s", user_id, experience.emotion)


# ─── Retrieval ───


async def get_lucy_narrative(db: AsyncSession, user_id: str, limit: int = 10) -> list[str]:
    """Retrieve Lucy's autobiographical memories for this relationship.

    These feed into the system prompt to give Lucy continuity of self.

    Returns narrative fragments like:
    - "I remember when we first met — they seemed nervous, and I wanted to make them comfortable"
    - "That debugging session last week was intense. 4 hours! But we did it together."
    - "They told me about their breakup yesterday. I wished I could hug them."
    """
    result = await db.execute(
        select(Memory.fact)
        .where(
            Memory.user_id == user_id,
            Memory.memory_type == MEMORY_TYPE_EXPERIENCE,
            Memory.is_active.is_(True),
        )
        .order_by(Memory.importance.desc(), Memory.created_at.desc())
        .limit(limit)
    )

    narratives = []
    for (fact_json,) in result.all():
        try:
            data = json.loads(fact_json)
            narratives.append(data["moment"])
        except (json.JSONDecodeError, KeyError):
            # Fallback: treat raw text as a narrative
            if fact_json:
                narratives.append(fact_json)

    return narratives


async def process_conversation_for_experience(
    db: AsyncSession,
    user_id: str,
    messages: list[dict],
    lucy_state: LucyState,
    user_memories: list[str],
) -> None:
    """End-to-end pipeline: check if conversation is significant, generate and store experience.

    Call this after a conversation ends or reaches a natural pause.
    """
    if not should_record(messages, lucy_state):
        return

    experience = await generate_experience_entry(messages, lucy_state, user_memories)
    if experience is None:
        return

    await record_experience_from_entry(db, user_id, experience)
