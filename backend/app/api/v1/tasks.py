"""Tasks API — create and manage background tasks for Lucy."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.tasks import TaskCreateRequest, TaskListResponse, TaskResponse, TaskStatus
from app.services.task_runner import cancel_task, create_task, get_task, get_user_tasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lucy/tasks", tags=["lucy-tasks"])

VALID_TASK_TYPES = {"code_review", "research", "analysis", "generation", "custom"}


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    body: TaskCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new background task for Lucy to work on."""
    if body.task_type not in VALID_TASK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"task_type must be one of: {', '.join(sorted(VALID_TASK_TYPES))}",
        )

    task = await create_task(
        db=db,
        user_id=user.id,
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        metadata=body.metadata_json,
    )
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: TaskStatus | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's tasks, optionally filtered by status."""
    tasks = await get_user_tasks(db, user.id, status=status_filter)
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_detail(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task's details and result."""
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_running_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending or running task."""
    task = await cancel_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a completed, failed, or cancelled task."""
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    if task.status in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a task that is still pending or running. Cancel it first.",
        )
    await db.delete(task)
    await db.commit()
