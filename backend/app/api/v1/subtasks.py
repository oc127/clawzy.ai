"""Sub-agent API — spawn subtasks that run against an agent."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent
from app.services.chat_service import run_subtask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subtasks", tags=["subtasks"])


class SubtaskRequest(BaseModel):
    agent_id: str
    task: str
    parent_conversation_id: str | None = None


class SubtaskResponse(BaseModel):
    result: str
    conversation_id: str | None = None


@router.post("", response_model=SubtaskResponse)
async def create_subtask(
    body: SubtaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, body.agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await run_subtask(
        db,
        user.id,
        agent,
        body.task,
        body.parent_conversation_id or "",
    )

    return SubtaskResponse(result=result)
