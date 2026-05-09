import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.lucy_state import LucyState
from app.models.user import User
from app.schemas.lucy import (
    ExpressionsResponse,
    LucyStateResponse,
    ModelUpdate,
    PersonalityUpdate,
    SoulResponse,
    SoulUpdate,
)
from app.services.soul_engine import get_relationship_stage, get_unlockable_expressions

router = APIRouter(prefix="/lucy", tags=["lucy"])

VALID_PERSONALITY_TYPES = {"少女", "御姐", "custom"}

ALL_EXPRESSIONS = [
    "smile",
    "shy",
    "angry",
    "sad",
    "excited",
    "thinking",
    "love",
    "surprised",
    "sleepy",
    "confident",
]

# Affection thresholds for unlocking expressions
EXPRESSION_UNLOCK_THRESHOLDS = {
    "smile": 0,
    "shy": 10,
    "thinking": 20,
    "excited": 30,
    "sad": 40,
    "angry": 50,
    "surprised": 60,
    "love": 70,
    "sleepy": 80,
    "confident": 90,
}


async def _get_or_create_lucy_state(db: AsyncSession, user_id: str) -> LucyState:
    """Get existing LucyState for user, or create one with defaults."""
    result = await db.execute(
        select(LucyState).where(LucyState.user_id == user_id)
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = LucyState(
            id=str(uuid.uuid4()),
            user_id=user_id,
            unlocked_expressions=["smile"],
        )
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


@router.get("/state", response_model=LucyStateResponse)
async def get_lucy_state(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's Lucy state."""
    state = await _get_or_create_lucy_state(db, user.id)
    return LucyStateResponse(
        personality_type=state.personality_type,
        mood=state.mood,
        affection=state.affection,
        relationship_stage=get_relationship_stage(state.affection),
        interaction_streak=state.interaction_streak,
        total_interactions=state.total_interactions,
        unlocked_expressions=state.unlocked_expressions or [],
        preferred_model=state.preferred_model,
        last_interaction_at=state.last_interaction_at,
    )


@router.patch("/personality", response_model=LucyStateResponse)
async def update_personality(
    body: PersonalityUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update Lucy's personality type."""
    if body.personality_type not in VALID_PERSONALITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"personality_type must be one of: {', '.join(VALID_PERSONALITY_TYPES)}",
        )

    if body.personality_type == "custom" and not body.custom_personality_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="custom_personality_prompt is required when personality_type is 'custom'",
        )

    state = await _get_or_create_lucy_state(db, user.id)
    state.personality_type = body.personality_type
    state.custom_personality_prompt = body.custom_personality_prompt
    await db.commit()
    await db.refresh(state)
    return state


@router.patch("/model", response_model=LucyStateResponse)
async def update_model(
    body: ModelUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update Lucy's preferred model."""
    state = await _get_or_create_lucy_state(db, user.id)
    state.preferred_model = body.model_name
    await db.commit()
    await db.refresh(state)
    return state


@router.get("/soul", response_model=SoulResponse)
async def get_soul(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Lucy's soul files content."""
    state = await _get_or_create_lucy_state(db, user.id)
    return SoulResponse(
        soul_md=state.soul_md,
        persona_md=state.persona_md,
        taste_md=state.taste_md,
    )


@router.patch("/soul", response_model=SoulResponse)
async def update_soul(
    body: SoulUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update soul files (advanced users). User-edited fields are pinned against auto-overwrite."""
    state = await _get_or_create_lucy_state(db, user.id)

    if body.soul_md is not None:
        state.soul_md = body.soul_md
    if body.persona_md is not None:
        state.persona_md = body.persona_md
    if body.taste_md is not None:
        state.taste_md = body.taste_md

    await db.commit()
    await db.refresh(state)
    return SoulResponse(
        soul_md=state.soul_md,
        persona_md=state.persona_md,
        taste_md=state.taste_md,
    )


@router.post("/interaction", response_model=LucyStateResponse)
async def record_interaction(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an interaction (called after chat). Updates streak, affection, and counters."""
    state = await _get_or_create_lucy_state(db, user.id)
    now = datetime.now(UTC)

    # Update interaction streak
    if state.last_interaction_at is not None:
        last = state.last_interaction_at
        # Check if the last interaction was yesterday (consecutive day)
        yesterday = now.date() - timedelta(days=1)
        if last.date() == yesterday:
            state.interaction_streak += 1
        elif last.date() != now.date():
            # Streak broken (missed a day or more)
            state.interaction_streak = 1
        # Same day: streak stays unchanged
    else:
        state.interaction_streak = 1

    # Update counters
    state.total_interactions += 1
    state.last_interaction_at = now

    # Affection adjustment: small bump per interaction, bonus for streaks
    affection_gain = 1
    if state.interaction_streak >= 7:
        affection_gain = 3
    elif state.interaction_streak >= 3:
        affection_gain = 2
    state.affection = min(100, state.affection + affection_gain)

    # Check for new expression unlocks
    unlocked = set(state.unlocked_expressions or [])
    for expression, threshold in EXPRESSION_UNLOCK_THRESHOLDS.items():
        if state.affection >= threshold:
            unlocked.add(expression)
    state.unlocked_expressions = sorted(unlocked)

    await db.commit()
    await db.refresh(state)
    return state


@router.get("/expressions", response_model=ExpressionsResponse)
async def get_expressions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get available and locked expressions."""
    state = await _get_or_create_lucy_state(db, user.id)

    unlocked = set(state.unlocked_expressions or [])
    locked = [e for e in ALL_EXPRESSIONS if e not in unlocked]

    # Find the next unlock threshold
    next_unlock_at = 100
    for expression, threshold in sorted(EXPRESSION_UNLOCK_THRESHOLDS.items(), key=lambda x: x[1]):
        if expression not in unlocked:
            next_unlock_at = threshold
            break

    return ExpressionsResponse(
        unlocked=sorted(unlocked),
        locked=locked,
        next_unlock_at=next_unlock_at,
    )
