"""Schedule API — manage agent task items (todos/schedule)."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.agent_task import AgentTask
from app.models.user import User
from app.schemas.agent_task import AgentTaskCreate, AgentTaskUpdate, AgentTaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("", response_model=list[AgentTaskResponse])
async def list_tasks(
    agent_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(AgentTask).where(AgentTask.user_id == user.id)
    if agent_id:
        q = q.where(AgentTask.agent_id == agent_id)
    if status_filter:
        q = q.where(AgentTask.status == status_filter)
    q = q.order_by(AgentTask.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: AgentTaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = AgentTask(user_id=user.id, **body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=AgentTaskResponse)
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=AgentTaskResponse)
async def update_task(
    task_id: str,
    body: AgentTaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    if body.status == "completed" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await db.delete(task)
    await db.commit()
