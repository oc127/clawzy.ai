"""Subtask API — spawn subtasks that run against the user's Lucy companion."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.lucy_state import LucyState
from app.models.user import User
from app.services.chat_service import run_subtask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subtasks", tags=["subtasks"])


class SubtaskRequest(BaseModel):
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
    result = await db.execute(
        select(LucyState).where(LucyState.user_id == user.id)
    )
    lucy_state = result.scalar_one_or_none()
    if lucy_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Lucy state found. Please create an account at thelucy.ai first.",
        )

    result = await run_subtask(
        db,
        user.id,
        lucy_state,
        body.task,
        body.parent_conversation_id or "",
    )

    return SubtaskResponse(result=result)
