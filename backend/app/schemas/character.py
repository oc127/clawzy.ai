from datetime import datetime

from pydantic import BaseModel


class CharacterCreate(BaseModel):
    name: str
    name_reading: str | None = None
    age: int | None = None
    occupation: str | None = None
    personality_type: str | None = None
    personality_traits: list[str] | None = None
    speaking_style: str | None = None
    catchphrase: str | None = None
    interests: list[str] | None = None
    backstory: str | None = None
    system_prompt: str
    greeting_message: str | None = None
    sample_dialogues: list[dict] | None = None
    avatar_color: str | None = None
    category: str = "healing"


class CharacterResponse(BaseModel):
    id: str
    name: str
    name_reading: str | None
    age: int | None
    occupation: str | None
    personality_type: str | None
    personality_traits: list | None
    speaking_style: str | None
    catchphrase: str | None
    interests: list | None
    backstory: str | None
    system_prompt: str
    greeting_message: str | None
    sample_dialogues: list | None
    avatar_color: str | None
    category: str
    is_preset: bool
    creator_id: str | None
    usage_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentFromCharacterResponse(BaseModel):
    agent_id: str
    character_id: str
    character_name: str
