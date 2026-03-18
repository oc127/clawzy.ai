from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    model_name: str = Field(default="deepseek-chat", max_length=50)


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    model_name: str | None = Field(None, max_length=50)


class AgentResponse(BaseModel):
    id: str
    name: str
    model_name: str
    status: str
    ws_port: int | None = None
    created_at: datetime
    last_active_at: datetime | None = None

    model_config = {"from_attributes": True}
