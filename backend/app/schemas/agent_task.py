from datetime import datetime
from pydantic import BaseModel


class AgentTaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"
    category: str | None = None
    agent_id: str | None = None
    created_by: str = "user"


class AgentTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    priority: str | None = None
    status: str | None = None
    category: str | None = None


class AgentTaskResponse(BaseModel):
    id: str
    agent_id: str | None
    user_id: str
    title: str
    description: str | None
    due_date: datetime | None
    priority: str
    status: str
    category: str | None
    created_by: str
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
