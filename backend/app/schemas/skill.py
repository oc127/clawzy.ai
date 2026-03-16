from datetime import datetime

from pydantic import BaseModel, Field


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
    avg_rating: float = 0.0
    review_count: int = 0
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
    avg_rating: float = 0.0
    review_count: int = 0

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


# --- Reviews ---


class ReviewUserResponse(BaseModel):
    id: str
    name: str | None = None

    model_config = {"from_attributes": True}


class SkillReviewResponse(BaseModel):
    id: str
    skill_id: str
    user: ReviewUserResponse
    rating: int
    title: str | None = None
    content: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillReviewCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, max_length=2000)


class SkillReviewUpdateRequest(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, max_length=2000)


# --- Skill Submission ---


class SkillSubmissionCreateRequest(BaseModel):
    name: str = Field(max_length=200)
    slug: str = Field(max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    summary: str = Field(max_length=500)
    description: str = Field(max_length=10000)
    category: str = Field(max_length=50)
    tags: list[str] | None = None
    version: str | None = Field(None, max_length=50)
    source_url: str | None = Field(None, max_length=500)


class SkillSubmissionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    summary: str
    description: str
    category: str
    tags: list[str] | None = None
    version: str | None = None
    source_url: str | None = None
    status: str
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
