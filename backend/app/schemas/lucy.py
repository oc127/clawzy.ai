from datetime import datetime

from pydantic import BaseModel


class LucyStateResponse(BaseModel):
    personality_type: str
    mood: str
    affection: int
    relationship_stage: str
    interaction_streak: int
    total_interactions: int
    unlocked_expressions: list[str]
    preferred_model: str
    last_interaction_at: datetime | None = None

    model_config = {"from_attributes": True}


class PersonalityUpdate(BaseModel):
    personality_type: str
    custom_personality_prompt: str | None = None


class ModelUpdate(BaseModel):
    model_name: str


class SoulResponse(BaseModel):
    soul_md: str
    persona_md: str
    taste_md: str


class SoulUpdate(BaseModel):
    soul_md: str | None = None
    persona_md: str | None = None
    taste_md: str | None = None


class ExpressionsResponse(BaseModel):
    unlocked: list[str]
    locked: list[str]
    next_unlock_at: int


class PushChannelsResponse(BaseModel):
    push_channels: list[str]
    line_user_id: str | None = None
    push_quiet_start: int | None = None
    push_quiet_end: int | None = None


class PushChannelsUpdate(BaseModel):
    push_channels: list[str] | None = None
    push_quiet_start: int | None = None
    push_quiet_end: int | None = None
