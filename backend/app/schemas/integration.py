from pydantic import BaseModel, Field


class IntegrationCreate(BaseModel):
    platform: str = Field(pattern=r"^(line|discord|telegram)$")
    bot_token: str | None = Field(None, max_length=500)
    channel_secret: str | None = Field(None, max_length=500)
    channel_access_token: str | None = Field(None, max_length=500)


class IntegrationUpdate(BaseModel):
    bot_token: str | None = Field(None, max_length=500)
    channel_secret: str | None = Field(None, max_length=500)
    channel_access_token: str | None = Field(None, max_length=500)
    enabled: bool | None = None


class IntegrationResponse(BaseModel):
    id: str
    agent_id: str
    platform: str
    enabled: bool
    webhook_url: str | None = None
    has_bot_token: bool = False
    has_channel_secret: bool = False
    has_channel_access_token: bool = False
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
