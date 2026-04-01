from datetime import datetime

from pydantic import BaseModel


class ChannelCreate(BaseModel):
    channel_type: str  # 'telegram', 'line', 'discord'
    config: dict


class ChannelUpdate(BaseModel):
    config: dict | None = None
    enabled: bool | None = None


class ChannelResponse(BaseModel):
    id: str
    agent_id: str
    channel_type: str
    config: dict
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
