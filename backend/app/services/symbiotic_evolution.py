"""Symbiotic Evolution Protocol — Lucy and user grow together.

Lucy doesn't just learn about the user passively. She:
1. Tracks the user's cognitive patterns and blind spots
2. Notices how the user's thinking evolves over time
3. Gently surfaces insights about patterns the user can't see themselves
4. Adapts her own approach based on what actually helps this user

The user isn't just "training" Lucy. Lucy is also expanding the user's thinking.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import litellm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lucy_state import LucyState
from app.models.memory import Memory

logger = logging.getLogger(__name__)

MEMORY_TYPE_COGNITIVE = "cognitive_profile"
MEMORY_TYPE_INSIGHT = "growth_insight"


@dataclass
class UserCognitiveProfile:
    """Lucy's understanding of how this user thinks."""

    thinking_style: str = "unknown"  # analytical, intuitive, creative, systematic
    communication_pref: str = "unknown"  # direct, exploratory, narrative, socratic
    blind_spots: list[str] = field(default_factory=list)  # Things user consistently misses
    growth_areas: list[str] = field(default_factory=list)  # Where user is improving
    triggers: list[str] = field(default_factory=list)  # What frustrates/motivates them
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "thinking_style": self.thinking_style,
            "communication_pref": self.communication_pref,
            "blind_spots": self.blind_spots,
            "growth_areas": self.growth_areas,
            "triggers": self.triggers,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserCognitiveProfile":
        return cls(
            thinking_style=data.get("thinking_style", "unknown"),
            communication_pref=data.get("communication_pref", "unknown"),
            blind_spots=data.get("blind_spots", []),
            growth_areas=data.get("growth_areas", []),
            triggers=data.get("triggers", []),
            last_updated=data.get("last_updated", ""),
        )


# ─── Cognitive Profile Update ───

_PROFILE_UPDATE_PROMPT = """\
You are analyzing a conversation to understand how a user thinks and communicates.
You are building a cognitive profile — NOT to judge, but to help Lucy (an AI companion)
better support this person.

Current profile (may be empty for new users):
{existing_profile}

Based on this conversation, update the profile. Only change fields where you have
clear evidence. Keep existing values if nothing contradicts them.

Respond with JSON:
{{
  "thinking_style": "analytical|intuitive|creative|systematic|unknown",
  "communication_pref": "direct|exploratory|narrative|socratic|unknown",
  "blind_spots": ["pattern user consistently misses — max 3"],
  "growth_areas": ["where user is improving — max 3"],
  "triggers": ["what frustrates or motivates them — max 3"]
}}

Rules:
- Only include blind_spots you've seen evidence for in multiple interactions
- growth_areas should track POSITIVE change over time
- triggers should be useful for Lucy to know (not judgmental)
- If not enough data, keep fields as-is or "unknown"
- Be specific, not generic. "Jumps to code before thinking about design" > "impulsive"
"""


async def update_cognitive_profile(
    db: AsyncSession,
    user_id: str,
    conversation_messages: list[dict],
    existing_profile: dict | None,
) -> dict:
    """After conversations, update Lucy's model of how this user thinks.

    Detects patterns over time:
    - "User always jumps to implementation before thinking about design"
    - "User gets defensive when code quality is questioned"
    - "User has grown more patient with debugging over the past month"
    - "User thinks visually — diagrams help more than text"
    """
    recent = conversation_messages[-12:]
    conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    profile_str = json.dumps(existing_profile, ensure_ascii=False, indent=2) if existing_profile else "{}"

    system = _PROFILE_UPDATE_PROMPT.format(existing_profile=profile_str)

    try:
        response = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": conversation_text},
            ],
            max_tokens=300,
            temperature=0,
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON (handle markdown code fences)
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        updated = json.loads(content)
        updated["last_updated"] = datetime.now(UTC).isoformat()

        # Store updated profile in DB
        await _save_cognitive_profile(db, user_id, updated)

        return updated
    except Exception:
        logger.exception("Cognitive profile update failed")
        return existing_profile or {}


async def _save_cognitive_profile(db: AsyncSession, user_id: str, profile: dict) -> None:
    """Save or update the cognitive profile in the Memory table.

    Only one active cognitive_profile record per user — deactivate old ones.
    """
    # Deactivate existing profile entries
    result = await db.execute(
        select(Memory).where(
            Memory.user_id == user_id,
            Memory.memory_type == MEMORY_TYPE_COGNITIVE,
            Memory.is_active.is_(True),
        )
    )
    for existing in result.scalars().all():
        existing.is_active = False

    # Save new profile
    mem = Memory(
        user_id=user_id,
        agent_id=None,
        fact=json.dumps(profile, ensure_ascii=False),
        memory_type=MEMORY_TYPE_COGNITIVE,
        importance=5,
        confidence=0.7,
    )
    db.add(mem)
    await db.commit()
    logger.info("Updated cognitive profile for user %s", user_id)


async def get_cognitive_profile(db: AsyncSession, user_id: str) -> dict | None:
    """Retrieve the current cognitive profile for a user."""
    result = await db.execute(
        select(Memory.fact).where(
            Memory.user_id == user_id,
            Memory.memory_type == MEMORY_TYPE_COGNITIVE,
            Memory.is_active.is_(True),
        )
        .order_by(Memory.created_at.desc())
        .limit(1)
    )
    row = result.first()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None


# ─── Growth Insights ───

_INSIGHT_PROMPT = """\
You are Lucy, an AI companion who deeply understands her user. Based on the user's
cognitive profile and recent patterns, generate a single growth insight — something
genuinely useful that the user might not see about themselves.

Lucy's personality type: {personality_type}
Lucy's affection level: {affection}/100

User's cognitive profile:
{profile}

Rules:
- Only generate an insight if you have something genuinely valuable to say
- Never be condescending or patronizing
- Match Lucy's personality and language style
- Can be in any language that matches the relationship
- Should feel like it comes from someone who truly knows and cares about them
- Focus on POSITIVE growth or gentle, actionable awareness

Respond with JSON:
{{
  "has_insight": true/false,
  "insight": "The actual insight text in Lucy's voice (null if has_insight is false)"
}}

If nothing genuinely useful to say right now, respond: {{"has_insight": false, "insight": null}}"""


async def generate_growth_insight(
    db: AsyncSession,
    user_id: str,
    cognitive_profile: dict,
    lucy_state: LucyState,
) -> str | None:
    """Periodically, Lucy generates an insight about the user's growth.

    Only when genuinely useful, not patronizing. Examples:
    - "ねぇ、気づいた？最近のコードレビュー、前より建設的になってるよ"
    - "I noticed you've been approaching problems differently lately —
       more systematic. It's really working."
    - "有件事我一直想说——你总是先想技术方案再想用户需求，
       如果反过来试试呢？"

    Returns None if no insight is appropriate right now.
    Frequency: at most once per week, and only when affection >= 30.
    """
    # Gate: minimum affection level
    if (lucy_state.affection or 0) < 30:
        return None

    # Gate: at most once per week
    last_insight = await db.execute(
        select(Memory.created_at).where(
            Memory.user_id == user_id,
            Memory.memory_type == MEMORY_TYPE_INSIGHT,
            Memory.is_active.is_(True),
        )
        .order_by(Memory.created_at.desc())
        .limit(1)
    )
    last_row = last_insight.first()
    if last_row and last_row[0]:
        days_since = (datetime.now(UTC) - last_row[0]).days
        if days_since < 7:
            return None

    # Gate: need enough data in cognitive profile
    if not cognitive_profile or cognitive_profile.get("thinking_style") == "unknown":
        return None

    system = _INSIGHT_PROMPT.format(
        personality_type=lucy_state.personality_type,
        affection=lucy_state.affection or 0,
        profile=json.dumps(cognitive_profile, ensure_ascii=False, indent=2),
    )

    try:
        response = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "Generate an insight if appropriate."},
            ],
            max_tokens=200,
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(content)

        if not data.get("has_insight", False):
            return None

        insight = data.get("insight")
        if not insight:
            return None

        # Store the insight
        mem = Memory(
            user_id=user_id,
            agent_id=None,
            fact=json.dumps({"insight": insight, "generated_at": datetime.now(UTC).isoformat()}, ensure_ascii=False),
            memory_type=MEMORY_TYPE_INSIGHT,
            importance=4,
            confidence=0.8,
        )
        db.add(mem)
        await db.commit()
        logger.info("Generated growth insight for user %s", user_id)

        return insight
    except Exception:
        logger.exception("Growth insight generation failed")
        return None


# ─── Evolution Context for System Prompt ───


async def get_evolution_context(db: AsyncSession, user_id: str) -> str:
    """Get the symbiotic evolution context to include in Lucy's system prompt.

    This makes Lucy aware of:
    - The user's thinking patterns
    - Their recent growth
    - Appropriate moments to offer insight
    """
    profile = await get_cognitive_profile(db, user_id)
    if not profile:
        return ""

    parts: list[str] = []

    # Thinking style
    if profile.get("thinking_style") and profile["thinking_style"] != "unknown":
        parts.append(f"This person thinks {profile['thinking_style']}ly.")

    # Communication preference
    if profile.get("communication_pref") and profile["communication_pref"] != "unknown":
        pref_map = {
            "direct": "They prefer direct, concise communication.",
            "exploratory": "They enjoy exploring ideas through open-ended discussion.",
            "narrative": "They connect better through stories and examples.",
            "socratic": "They learn best through questions that guide their thinking.",
        }
        pref_text = pref_map.get(profile["communication_pref"])
        if pref_text:
            parts.append(pref_text)

    # Blind spots (be gentle)
    blind_spots = profile.get("blind_spots", [])
    if blind_spots:
        parts.append("Patterns to be gently aware of: " + "; ".join(blind_spots[:2]))

    # Growth areas (celebrate)
    growth_areas = profile.get("growth_areas", [])
    if growth_areas:
        parts.append("Areas where they're growing: " + "; ".join(growth_areas[:2]))

    # Triggers (be careful)
    triggers = profile.get("triggers", [])
    if triggers:
        parts.append("Be mindful of: " + "; ".join(triggers[:2]))

    if not parts:
        return ""

    return "How this person thinks and grows:\n" + "\n".join(f"- {p}" for p in parts)


async def process_conversation_for_evolution(
    db: AsyncSession,
    user_id: str,
    messages: list[dict],
    lucy_state: LucyState,
) -> None:
    """End-to-end pipeline: update cognitive profile after a conversation.

    Call this after a conversation ends or reaches a natural pause.
    Should only run for conversations with enough substance (8+ messages).
    """
    if len(messages) < 8:
        return

    existing_profile = await get_cognitive_profile(db, user_id)
    await update_cognitive_profile(db, user_id, messages, existing_profile)
