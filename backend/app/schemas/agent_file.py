from datetime import datetime
from pydantic import BaseModel


class AgentFileCreate(BaseModel):
    filename: str
    file_type: str | None = None
    file_size: int | None = None
    storage_path: str | None = None
    description: str | None = None
    agent_id: str | None = None
    created_by: str = "agent"


class AgentFileResponse(BaseModel):
    id: str
    agent_id: str | None
    user_id: str
    filename: str
    file_type: str | None
    file_size: int | None
    storage_path: str | None
    description: str | None
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}
