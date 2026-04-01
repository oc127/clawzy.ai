from datetime import datetime

from pydantic import BaseModel


class MCPServerCreate(BaseModel):
    name: str
    transport: str  # 'stdio' or 'http'
    command: str | None = None
    url: str | None = None
    config: dict | None = None


class MCPServerResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    transport: str | None = None
    command: str | None = None
    url: str | None = None
    config: dict | None = None
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
