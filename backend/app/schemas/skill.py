from datetime import datetime

from pydantic import BaseModel


class SkillResponse(BaseModel):
    id: str
    slug: str
    name: str
    summary: str
    description: str
    category: str
    tags: list[str] | None = None
    icon_url: str | None = None
    clawhub_url: str | None = None
    author: str | None = None
    version: str | None = None
    install_count: int = 0
    is_featured: bool = False
    security_status: str = "unreviewed"
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillBriefResponse(BaseModel):
    """Compact skill info for list views."""
    id: str
    slug: str
    name: str
    summary: str
    category: str
    tags: list[str] | None = None
    icon_url: str | None = None
    install_count: int = 0
    is_featured: bool = False
    security_status: str = "unreviewed"

    model_config = {"from_attributes": True}


class AgentSkillResponse(BaseModel):
    id: str
    skill: SkillBriefResponse
    enabled: bool
    installed_at: datetime

    model_config = {"from_attributes": True}


class SkillInstallRequest(BaseModel):
    skill_id: str


class SkillToggleRequest(BaseModel):
    enabled: bool
