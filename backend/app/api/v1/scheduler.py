"""Scheduler API — manage agent scheduled tasks."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskRunResponse
from app.services.agent_service import get_agent
from app.services.scheduler_service import (
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    run_task,
    get_task_runs,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/tasks", tags=["scheduler"])


@router.get("", response_model=list[TaskResponse])
async def list_agent_tasks(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await list_tasks(db, agent_id)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_task(
    agent_id: str,
    body: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        return await create_task(
            db,
            agent_id=agent_id,
            cron_expression=body.cron_expression,
            prompt=body.prompt,
            description=body.description,
            webhook_url=body.webhook_url,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {exc}",
        )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_agent_task(
    agent_id: str,
    task_id: str,
    body: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    task = await update_task(
        db,
        task_id=task_id,
        cron_expression=body.cron_expression,
        prompt=body.prompt,
        description=body.description,
        enabled=body.enabled,
        webhook_url=body.webhook_url,
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_task(
    agent_id: str,
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    deleted = await delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@router.post("/{task_id}/run", response_model=TaskRunResponse)
async def trigger_agent_task(
    agent_id: str,
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    task = await get_task(db, task_id)
    if task is None or task.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return await run_task(db, task)


@router.get("/{task_id}/runs", response_model=list[TaskRunResponse])
async def list_task_runs(
    agent_id: str,
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    task = await get_task(db, task_id)
    if task is None or task.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return await get_task_runs(db, task_id)
