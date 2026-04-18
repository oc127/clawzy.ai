from datetime import datetime

from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    triggers: list[str] | None = None
    content: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    triggers: list[str] | None = None
    content: str | None = None
    enabled: bool | None = None


class SkillToggle(BaseModel):
    enabled: bool


class SkillExtractRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": "..."}]


class SkillResponse(BaseModel):
    id: str
    agent_id: str
    slug: str
    name: str
    description: str | None = None
    triggers: list[str] | None = None
    source: str | None = None
    skill_content: str | None = None
    version: int = 1
    usage_count: int = 0
    success_rate: float = 1.0
    enabled: bool
    installed_at: datetime

    model_config = {"from_attributes": True}
