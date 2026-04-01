from datetime import datetime

from pydantic import BaseModel


class ApprovalResolve(BaseModel):
    decision: str  # 'approved' or 'denied'


class ApprovalResponse(BaseModel):
    id: str
    agent_id: str
    user_id: str
    tool_name: str
    tool_args: dict | None = None
    status: str
    conversation_id: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}
