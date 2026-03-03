from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    model_name: str = "deepseek-chat"


class AgentUpdate(BaseModel):
    name: str | None = None
    model_name: str | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    model_name: str
    status: str
    ws_port: int | None = None
    created_at: datetime
    last_active_at: datetime | None = None

    model_config = {"from_attributes": True}
