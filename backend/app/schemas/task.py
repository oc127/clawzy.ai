from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    cron_expression: str
    prompt: str
    description: str | None = None
    webhook_url: str | None = None


class TaskUpdate(BaseModel):
    cron_expression: str | None = None
    prompt: str | None = None
    description: str | None = None
    enabled: bool | None = None
    webhook_url: str | None = None


class TaskResponse(BaseModel):
    id: str
    agent_id: str
    cron_expression: str
    prompt: str
    description: str | None = None
    enabled: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    webhook_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskRunResponse(BaseModel):
    id: str
    task_id: str
    status: str
    output: str | None = None
    credits_used: int
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
