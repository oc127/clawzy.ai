from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    code_review = "code_review"
    research = "research"
    analysis = "analysis"
    generation = "generation"
    custom = "custom"


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    task_type: TaskType = TaskType.custom
    metadata_json: dict | None = None


class TaskResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    task_type: str
    status: str
    progress: int
    result: str | None = None
    error: str | None = None
    metadata_json: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
