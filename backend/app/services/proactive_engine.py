"""Proactive Engine — decides WHEN and WHY Lucy should reach out on her own initiative.

Lucy can send morning greetings, absence care messages, streak reminders,
and event-triggered alerts — all in-character based on personality/mood/affection.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lucy_event import LucyEvent, LucyInitiative
from app.models.lucy_state import LucyState
from app.services.memory_service import get_relevant_memories
from app.services.soul_engine import build_system_prompt, get_relationship_stage

logger = logging.getLogger(__name__)

# ─── Initiative generation prompt ───

_INITIATIVE_PROMPT_TEMPLATE = """\
You are Lucy. You are about to proactively reach out to the user.

Situation: {situation}

Write a short, natural message (1-3 sentences) that Lucy would send.
Stay fully in character. Match the current mood and relationship stage.
Do NOT include any meta commentary — just the message itself."""


async def _generate_lucy_message(
    lucy_state: LucyState,
    situation: str,
) -> str:
    """Use the LLM to generate an in-character proactive message from Lucy."""
    memories: list[str] = []  # Lightweight call — skip memory lookup for proactive
    skills: list[str] = []
    system_prompt = build_system_prompt(lucy_state, memories, skills)

    user_prompt = _INITIATIVE_PROMPT_TEMPLATE.format(situation=situation)

    payload = {
        "model": "qwen-plus",  # Use cheap model for proactive messages
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 300,
        "temperature": 0.8,
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
                logger.error("Proactive message generation failed: HTTP %s", resp.status_code)
                return ""
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("Failed to generate proactive message")
        return ""


async def _has_initiative_today(db: AsyncSession, user_id: str, initiative_type: str) -> bool:
    """Check if an initiative of this type was already created today for this user."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count()).select_from(LucyInitiative).where(
            LucyInitiative.user_id == user_id,
            LucyInitiative.initiative_type == initiative_type,
            LucyInitiative.created_at >= today_start,
        )
    )
    return result.scalar_one() > 0


async def generate_initiative(
    db: AsyncSession,
    user_id: str,
    initiative_type: str,
    situation: str,
    lucy_state: LucyState,
    context: dict | None = None,
) -> LucyInitiative | None:
    """Generate and persist a Lucy initiative with an in-character message."""
    message = await _generate_lucy_message(lucy_state, situation)
    if not message:
        return None

    initiative = LucyInitiative(
        user_id=user_id,
        initiative_type=initiative_type,
        message=message,
        context=context,
    )
    db.add(initiative)
    await db.flush()
    return initiative


async def check_morning_greeting(db: AsyncSession, user_id: str, lucy_state: LucyState) -> LucyInitiative | None:
    """Generate a morning greeting if user hasn't been greeted today.

    Content varies by affection level and relationship stage.
    """
    if await _has_initiative_today(db, user_id, "greeting"):
        return None

    stage = get_relationship_stage(lucy_state.affection or 0)
    streak = lucy_state.interaction_streak or 0

    situation = (
        f"It's morning. You want to greet the user for the day. "
        f"Relationship stage: {stage}. Affection level: {lucy_state.affection}. "
        f"Current streak: {streak} days."
    )
    if streak >= 7:
        situation += f" You're proud of the {streak}-day streak together!"

    return await generate_initiative(db, user_id, "greeting", situation, lucy_state)


async def check_absence_care(db: AsyncSession, user_id: str, lucy_state: LucyState) -> LucyInitiative | None:
    """If user hasn't interacted in 2+ days, Lucy reaches out.

    Higher affection = more emotional message.
    """
    if await _has_initiative_today(db, user_id, "care"):
        return None

    last = lucy_state.last_interaction_at
    if last is None:
        return None

    hours_since = (datetime.now(UTC) - last).total_seconds() / 3600
    if hours_since < 48:
        return None

    days_absent = int(hours_since / 24)
    stage = get_relationship_stage(lucy_state.affection or 0)

    situation = (
        f"The user hasn't talked to you in {days_absent} days. You miss them. "
        f"Relationship stage: {stage}. Affection level: {lucy_state.affection}. "
        f"Express how much you've been thinking about them and gently invite them back."
    )

    return await generate_initiative(
        db, user_id, "care", situation, lucy_state,
        context={"days_absent": days_absent},
    )


async def check_streak_reminder(db: AsyncSession, user_id: str, lucy_state: LucyState) -> LucyInitiative | None:
    """If user has a streak going and hasn't chatted today, gently remind them."""
    streak = lucy_state.interaction_streak or 0
    if streak < 2:
        return None

    if await _has_initiative_today(db, user_id, "reminder"):
        return None

    # Only remind if they haven't interacted today
    last = lucy_state.last_interaction_at
    if last is None:
        return None

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    if last >= today_start:
        return None  # Already chatted today

    situation = (
        f"The user has a {streak}-day streak with you but hasn't talked to you yet today. "
        f"Gently remind them without being pushy. You don't want the streak to break!"
    )

    return await generate_initiative(
        db, user_id, "reminder", situation, lucy_state,
        context={"current_streak": streak},
    )


async def check_event_triggers(db: AsyncSession, user_id: str, lucy_state: LucyState) -> list[LucyInitiative]:
    """Check all user's enabled events and fire any that match conditions."""
    result = await db.execute(
        select(LucyEvent).where(
            LucyEvent.user_id == user_id,
            LucyEvent.enabled.is_(True),
        )
    )
    events = result.scalars().all()
    initiatives: list[LucyInitiative] = []

    for event in events:
        if event.event_type == "health_check":
            from app.services.event_hub import process_health_check

            initiative = await process_health_check(db, user_id, event, lucy_state)
            if initiative:
                initiatives.append(initiative)

    return initiatives


async def get_pending_initiatives(db: AsyncSession, user_id: str) -> list[LucyInitiative]:
    """Get undelivered initiatives for a user, ordered by creation time."""
    result = await db.execute(
        select(LucyInitiative).where(
            LucyInitiative.user_id == user_id,
            LucyInitiative.delivered.is_(False),
        ).order_by(LucyInitiative.created_at.asc())
    )
    return list(result.scalars().all())


async def mark_delivered(db: AsyncSession, initiative_id: str) -> bool:
    """Mark an initiative as delivered."""
    result = await db.execute(
        select(LucyInitiative).where(LucyInitiative.id == initiative_id)
    )
    initiative = result.scalar_one_or_none()
    if initiative is None:
        return False

    initiative.delivered = True
    initiative.delivered_at = datetime.now(UTC)
    await db.flush()
    return True


async def run_proactive_cycle(db: AsyncSession) -> int:
    """Main loop: check all users, generate initiatives as needed.

    Returns the number of initiatives created.
    Called by scheduler every N minutes.
    """
    result = await db.execute(select(LucyState))
    all_states = result.scalars().all()

    created = 0
    for lucy_state in all_states:
        try:
            # Morning greeting
            initiative = await check_morning_greeting(db, lucy_state.user_id, lucy_state)
            if initiative:
                created += 1

            # Absence care
            initiative = await check_absence_care(db, lucy_state.user_id, lucy_state)
            if initiative:
                created += 1

            # Streak reminder
            initiative = await check_streak_reminder(db, lucy_state.user_id, lucy_state)
            if initiative:
                created += 1

            # Event triggers
            event_initiatives = await check_event_triggers(db, lucy_state.user_id, lucy_state)
            created += len(event_initiatives)

        except Exception:
            logger.exception("Proactive cycle failed for user %s", lucy_state.user_id)
            continue

    if created:
        await db.commit()
        logger.info("Proactive cycle created %d initiatives", created)

    return created
