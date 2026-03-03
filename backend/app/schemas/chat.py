from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: str
    agent_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    credits_used: int | None = None
    model_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
