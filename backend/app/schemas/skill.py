from datetime import datetime

from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    slug: str | None = None
    content: str | None = None


class SkillToggle(BaseModel):
    enabled: bool


class SkillResponse(BaseModel):
    id: str
    agent_id: str
    slug: str
    name: str
    source: str | None = None
    skill_content: str | None = None
    enabled: bool
    installed_at: datetime

    model_config = {"from_attributes": True}
