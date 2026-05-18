"""Lucy's Personality — 性格 / 情绪 / 关系阶段。

骨架阶段：复用 services.personality_engine 里的 LUCY_PERSONALITY 字符串与
情绪推断函数，后续把"关系阶段（new/familiar/close）"和"情绪状态机"
从纯文本约束升级为可观测的状态。
"""

from __future__ import annotations

from dataclasses import dataclass


# Mood the rest of the system can react to.
# Keep this list short — it must be a closed set.
MOODS = ("normal", "caring", "excited", "supportive", "concerned", "playful")
RELATIONSHIP_STAGES = ("new", "familiar", "close")


@dataclass
class PersonalityState:
    mood: str = "normal"
    relationship_stage: str = "new"
    last_interaction_at: str | None = None  # ISO-8601


class LucyPersonality:
    """Holds Lucy's current affective state for one agent/user pair."""

    def __init__(self, agent_id: str, user_id: str | None = None):
        self.agent_id = agent_id
        self.user_id = user_id
        self.state = PersonalityState()

    async def get_current_mood(self, recent_messages: list[dict]) -> str:
        raise NotImplementedError

    async def apply_personality(self, raw_response: str) -> str:
        """Re-shape a raw LLM response so it sounds like Lucy.

        In practice the LUCY_PERSONALITY system prompt does most of this work;
        this hook is for post-processing (trim markdown, enforce no-emoji-spam,
        soften tone when mood == 'caring', etc.).
        """
        raise NotImplementedError

    async def update_relationship_stage(self, interaction_count: int, days_known: int) -> str:
        raise NotImplementedError
