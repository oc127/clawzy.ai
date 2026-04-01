"""Scheduler service — asyncio-based cron task runner (no Celery)."""

import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session
from app.models.task import ScheduledTask, TaskRun

logger = logging.getLogger(__name__)

# Background task handle
_scheduler_task: asyncio.Task | None = None


def calculate_next_run(cron_expression: str) -> datetime:
    """Calculate the next fire time from a cron expression."""
    cron = croniter(cron_expression, datetime.now(timezone.utc))
    return cron.get_next(datetime).replace(tzinfo=timezone.utc)


async def create_task(
    db: AsyncSession,
    agent_id: str,
    cron_expression: str,
    prompt: str,
    description: str | None = None,
    webhook_url: str | None = None,
) -> ScheduledTask:
    """Create a scheduled task with computed next_run_at."""
    next_run = calculate_next_run(cron_expression)
    task = ScheduledTask(
        agent_id=agent_id,
        cron_expression=cron_expression,
        prompt=prompt,
        description=description,
        webhook_url=webhook_url,
        next_run_at=next_run,
        enabled=True,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    logger.info("Created scheduled task %s for agent %s (next_run=%s)", task.id, agent_id, next_run)
    return task


async def run_task(db: AsyncSession, task: ScheduledTask) -> TaskRun:
    """Execute a scheduled task: call LiteLLM non-interactively and record output."""
    run = TaskRun(
        task_id=task.id,
        status="running",
    )
    db.add(run)
    await db.flush()

    try:
        # Non-interactive LLM call via LiteLLM
        from app.models.agent import Agent

        result = await db.execute(
            select(Agent).where(Agent.id == task.agent_id)
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            run.status = "failed"
            run.output = "Agent not found"
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return run

        messages = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        messages.append({"role": "user", "content": task.prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.litellm_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.litellm_master_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": agent.model_name,
                    "messages": messages,
                    "max_tokens": 4096,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})

        run.status = "completed"
        run.output = content
        run.credits_used = usage.get("total_tokens", 0) // 10  # rough credit estimate
        run.completed_at = datetime.now(timezone.utc)

        # Fire webhook if configured
        if task.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as wh_client:
                    await wh_client.post(
                        task.webhook_url,
                        json={
                            "task_id": task.id,
                            "run_id": run.id,
                            "status": run.status,
                            "output": content[:2000],
                        },
                    )
            except Exception as wh_exc:
                logger.warning("Webhook delivery failed for task %s: %s", task.id, wh_exc)

    except Exception as exc:
        logger.error("Task %s execution failed: %s", task.id, exc)
        run.status = "failed"
        run.output = str(exc)[:2000]
        run.completed_at = datetime.now(timezone.utc)

    # Update task timestamps and compute next run
    task.last_run_at = datetime.now(timezone.utc)
    task.next_run_at = calculate_next_run(task.cron_expression)

    await db.commit()
    await db.refresh(run)
    return run


async def _scheduler_loop():
    """Background loop: check for due tasks every 60 seconds."""
    logger.info("Scheduler background loop started")
    while True:
        try:
            async with async_session() as db:
                now = datetime.now(timezone.utc)
                result = await db.execute(
                    select(ScheduledTask).where(
                        ScheduledTask.enabled.is_(True),
                        ScheduledTask.next_run_at <= now,
                    )
                )
                due_tasks = list(result.scalars().all())

                for task in due_tasks:
                    logger.info("Running due task %s (agent=%s)", task.id, task.agent_id)
                    try:
                        await run_task(db, task)
                    except Exception as exc:
                        logger.error("Scheduler failed to run task %s: %s", task.id, exc)

        except Exception as exc:
            logger.error("Scheduler loop error: %s", exc)

        await asyncio.sleep(60)


def start_scheduler():
    """Start the scheduler background task. Call from FastAPI startup event."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Scheduler background task created")


async def list_tasks(db: AsyncSession, agent_id: str) -> list[ScheduledTask]:
    """List all scheduled tasks for an agent."""
    result = await db.execute(
        select(ScheduledTask)
        .where(ScheduledTask.agent_id == agent_id)
        .order_by(ScheduledTask.created_at.desc())
    )
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: str) -> ScheduledTask | None:
    """Get a single task by ID."""
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    return result.scalar_one_or_none()


async def update_task(
    db: AsyncSession,
    task_id: str,
    cron_expression: str | None = None,
    prompt: str | None = None,
    description: str | None = None,
    enabled: bool | None = None,
    webhook_url: str | None = None,
) -> ScheduledTask | None:
    """Update a scheduled task."""
    task = await get_task(db, task_id)
    if task is None:
        return None
    if cron_expression is not None:
        task.cron_expression = cron_expression
        task.next_run_at = calculate_next_run(cron_expression)
    if prompt is not None:
        task.prompt = prompt
    if description is not None:
        task.description = description
    if enabled is not None:
        task.enabled = enabled
    if webhook_url is not None:
        task.webhook_url = webhook_url
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    """Delete a scheduled task."""
    task = await get_task(db, task_id)
    if task is None:
        return False
    await db.delete(task)
    await db.commit()
    return True


async def get_task_runs(
    db: AsyncSession, task_id: str, limit: int = 50
) -> list[TaskRun]:
    """Get execution history for a task."""
    result = await db.execute(
        select(TaskRun)
        .where(TaskRun.task_id == task_id)
        .order_by(TaskRun.started_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
