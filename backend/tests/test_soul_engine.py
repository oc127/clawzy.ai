"""Tests for Soul Engine — prompt assembly, affection, and expression unlocks."""

import pytest

from app.models.lucy_state import LucyState
from app.services.soul_engine import (
    build_system_prompt,
    calculate_affection_delta,
    get_unlockable_expressions,
)


def _make_lucy_state(**overrides) -> LucyState:
    """Create a LucyState instance with sensible defaults, overridden by kwargs."""
    defaults = {
        "id": "test-state-id",
        "user_id": "test-user-id",
        "personality_type": "少女",
        "custom_personality_prompt": None,
        "mood": "neutral",
        "affection": 0,
        "interaction_streak": 0,
        "total_interactions": 0,
        "last_interaction_at": None,
        "unlocked_expressions": [],
        "soul_md": "",
        "persona_md": "",
        "taste_md": "",
        "user_level": "intermediate",
        "preferred_model": "deepseek-chat",
        "cultural_frame": "universal",
        "push_channels": ["websocket"],
        "line_user_id": None,
        "push_quiet_start": None,
        "push_quiet_end": None,
    }
    defaults.update(overrides)
    return LucyState(**defaults)


# ---------------------------------------------------------------------------
#  build_system_prompt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_system_prompt_default():
    """Build prompt with default LucyState, check it contains personality sections."""
    state = _make_lucy_state()
    prompt = build_system_prompt(state, memories=[], skills=[])

    # Should contain the default soul text
    assert "Lucy" in prompt
    # Should contain a persona template (少女 default)
    assert "energetic" in prompt or "curious" in prompt
    # Should contain mood effect (neutral)
    assert "calm" in prompt or "content" in prompt
    # Should contain an affection stage (new at 0)
    assert "just met" in prompt or "warm" in prompt


# ---------------------------------------------------------------------------
#  calculate_affection_delta
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calculate_affection_delta_chat():
    """Chat action returns a positive delta."""
    delta = calculate_affection_delta("chat", "neutral")
    assert delta > 0
    assert delta == 1  # base for chat is 1, neutral mood gives no bonus


@pytest.mark.asyncio
async def test_calculate_affection_delta_mood_boost():
    """Happy mood gives extra boost on positive interactions."""
    delta_neutral = calculate_affection_delta("chat", "neutral")
    delta_happy = calculate_affection_delta("chat", "happy")
    assert delta_happy > delta_neutral
    # Happy adds +1 to positive interactions
    assert delta_happy == delta_neutral + 1


# ---------------------------------------------------------------------------
#  get_unlockable_expressions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unlockable_expressions_low():
    """Affection 0 returns only the basic expressions."""
    expressions = get_unlockable_expressions(0)
    assert "neutral" in expressions
    assert "smile" in expressions
    # Should not include higher-tier expressions
    assert "kiss" not in expressions
    assert "love" not in expressions
    assert "shy" not in expressions


@pytest.mark.asyncio
async def test_get_unlockable_expressions_high():
    """Affection 100 returns all expressions from every tier."""
    expressions = get_unlockable_expressions(100)
    # Basic tier
    assert "neutral" in expressions
    assert "smile" in expressions
    # Mid tier
    assert "happy" in expressions
    assert "excited" in expressions
    assert "shy" in expressions
    # High tier
    assert "love" in expressions
    assert "blush" in expressions
    # Top tier
    assert "kiss" in expressions
    assert "heart_eyes" in expressions
    assert "special" in expressions
