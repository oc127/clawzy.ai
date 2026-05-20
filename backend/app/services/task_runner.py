"""Task Runner — executes background tasks for Lucy using LLM, keeping her in character.

Tasks run asynchronously so users can fire off multiple jobs (code review, research,
analysis, document generation) and Lucy works on them in parallel, reporting back
when each one completes.
"""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session
from app.models.lucy_state import LucyState
from app.models.lucy_task import LucyTask
from app.services.memory_service import get_relevant_memories
from app.services.soul_engine import build_system_prompt

logger = logging.getLogger(__name__)

# In-memory tracking of running asyncio tasks
_running_tasks: dict[str, asyncio.Task] = {}

# Prompt templates per task type — Lucy stays in character while working
_TASK_PROMPTS: dict[str, str] = {
    "code_review": (
        "The user has asked you to review code. Provide a thorough code review "
        "covering correctness, style, performance, and security. Format your "
        "review as markdown with sections. Be specific about line-level issues."
    ),
    "research": (
        "The user has asked you to research a topic. Provide a comprehensive "
        "research summary with key findings, organized with clear headings. "
        "Include relevant details, comparisons, and your own insights."
    ),
    "analysis": (
        "The user has asked you to analyze data or a situation. Provide a "
        "structured analysis with observations, patterns, conclusions, and "
        "actionable recommendations. Use markdown formatting."
    ),
    "generation": (
        "The user has asked you to generate a document or content. Produce "
        "high-quality, well-structured output in markdown format. Follow any "
        "specific instructions in the task description carefully."
    ),
    "custom": (
        "The user has given you a task. Complete it thoroughly and format "
        "your output as clean markdown. Follow all instructions carefully."
    ),
}


async def create_task(
    db: AsyncSession,
    user_id: str,
    title: str,
    description: str,
    task_type: str,
    metadata: dict | None = None,
) -> LucyTask:
    """Create a new task and start it running in the background."""
    task = LucyTask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        description=description,
        task_type=task_type,
        status="pending",
        progress=0,
        metadata_json=metadata,
    )
    db.add(task)
    await db.flush()
    await db.commit()
    await db.refresh(task)

    # Launch background execution
    bg_task = asyncio.create_task(_run_task_background(task.id, user_id))
    _running_tasks[task.id] = bg_task

    # Clean up reference when done
    bg_task.add_done_callback(lambda t: _running_tasks.pop(task.id, None))

    return task


async def _run_task_background(task_id: str, user_id: str) -> None:
    """Background wrapper that opens its own DB session for the task execution."""
    async with async_session() as db:
        try:
            await run_task(db, task_id, user_id)
        except Exception:
            logger.exception("Unhandled error in background task %s", task_id)
            # Mark as failed
            try:
                await db.execute(
                    update(LucyTask)
                    .where(LucyTask.id == task_id)
                    .values(
                        status="failed",
                        error="Internal error — task crashed unexpectedly.",
                        completed_at=datetime.now(UTC),
                    )
                )
                await db.commit()
            except Exception:
                logger.exception("Failed to mark task %s as failed", task_id)


async def run_task(db: AsyncSession, task_id: str, user_id: str) -> None:
    """Execute a task: build prompt, call LLM, store result.

    Updates progress as it goes. Lucy stays in character even for tasks.
    """
    # Load task
    result = await db.execute(select(LucyTask).where(LucyTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        logger.error("Task %s not found", task_id)
        return

    # Mark as running
    task.status = "running"
    task.started_at = datetime.now(UTC)
    task.progress = 5
    await db.commit()

    # Load Lucy state for this user
    result = await db.execute(select(LucyState).where(LucyState.user_id == user_id))
    lucy_state = result.scalar_one_or_none()
    if lucy_state is None:
        task.status = "failed"
        task.error = "No Lucy state found for user."
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return

    # Build the system prompt — Lucy stays in character
    memories = await get_relevant_memories(db, user_id)
    system_prompt = build_system_prompt(lucy_state, memories, skills=[])

    # Add task-specific instructions
    task_instruction = _TASK_PROMPTS.get(task.task_type, _TASK_PROMPTS["custom"])
    system_prompt += (
        f"\n\n--- TASK MODE ---\n"
        f"You are working on a background task. Stay in character as Lucy, but focus "
        f"on delivering excellent work.\n\n"
        f"{task_instruction}"
    )

    # Build the user message from task details
    user_message = f"# Task: {task.title}\n\n{task.description}"
    if task.metadata_json:
        user_message += f"\n\n## Additional context\n```json\n{json.dumps(task.metadata_json, indent=2)}\n```"

    task.progress = 10
    await db.commit()

    # Call LLM via gateway (same pattern as chat_service)
    if not (settings.openclaw_gateway_url and settings.openclaw_gateway_token):
        task.status = "failed"
        task.error = "Gateway not configured."
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return

    gateway_url = f"{settings.openclaw_gateway_url}/v1/chat/completions"
    gateway_auth = f"Bearer {settings.openclaw_gateway_token}"

    model = lucy_state.preferred_model or "deepseek-chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 8192,
        "stream": True,
    }

    headers = {
        "Authorization": gateway_auth,
        "Content-Type": "application/json",
    }

    full_content = ""
    try:
        task.progress = 20
        await db.commit()

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", gateway_url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error("LLM error for task %s: %s %s", task_id, response.status_code, body)
                    task.status = "failed"
                    task.error = f"Model returned HTTP {response.status_code}"
                    task.completed_at = datetime.now(UTC)
                    await db.commit()
                    return

                chunk_count = 0
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_content += content
                            chunk_count += 1

                            # Update progress periodically (20 -> 90 range)
                            if chunk_count % 20 == 0:
                                # Estimate progress based on content length
                                estimated_progress = min(90, 20 + int(len(full_content) / 100))
                                task.progress = estimated_progress
                                await db.commit()

    except httpx.ConnectError as exc:
        logger.error("Cannot connect to gateway for task %s: %s", task_id, exc)
        task.status = "failed"
        task.error = "Cannot connect to model service."
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return
    except httpx.TimeoutException:
        task.status = "failed"
        task.error = "Model request timed out."
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return
    except asyncio.CancelledError:
        task.status = "cancelled"
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return

    if not full_content:
        task.status = "failed"
        task.error = "Model returned empty response."
        task.completed_at = datetime.now(UTC)
        await db.commit()
        return

    # Success — store the result
    task.status = "completed"
    task.progress = 100
    task.result = full_content
    task.completed_at = datetime.now(UTC)
    await db.commit()

    logger.info("Task %s completed successfully (%d chars)", task_id, len(full_content))


async def cancel_task(db: AsyncSession, task_id: str, user_id: str) -> LucyTask | None:
    """Cancel a running task."""
    result = await db.execute(
        select(LucyTask).where(LucyTask.id == task_id, LucyTask.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None

    if task.status not in ("pending", "running"):
        return task  # Already finished, nothing to cancel

    # Cancel the asyncio task if it's running
    bg_task = _running_tasks.get(task_id)
    if bg_task and not bg_task.done():
        bg_task.cancel()

    task.status = "cancelled"
    task.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(task)
    return task


async def get_user_tasks(
    db: AsyncSession, user_id: str, status: str | None = None
) -> list[LucyTask]:
    """List tasks for a user, optionally filtered by status."""
    query = select(LucyTask).where(LucyTask.user_id == user_id)
    if status:
        query = query.where(LucyTask.status == status)
    query = query.order_by(LucyTask.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: str, user_id: str) -> LucyTask | None:
    """Get a single task by ID, scoped to user."""
    result = await db.execute(
        select(LucyTask).where(LucyTask.id == task_id, LucyTask.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def cleanup_stale_tasks(db: AsyncSession) -> int:
    """Mark tasks stuck in 'running' for >30min as failed.

    Returns the number of tasks cleaned up.
    """
    cutoff = datetime.now(UTC).replace(microsecond=0)
    # 30 minutes ago
    from datetime import timedelta

    cutoff = cutoff - timedelta(minutes=30)

    result = await db.execute(
        select(LucyTask).where(
            LucyTask.status == "running",
            LucyTask.started_at < cutoff,
        )
    )
    stale_tasks = list(result.scalars().all())

    for task in stale_tasks:
        # Cancel the asyncio task if still tracked
        bg_task = _running_tasks.pop(task.id, None)
        if bg_task and not bg_task.done():
            bg_task.cancel()

        task.status = "failed"
        task.error = "Task timed out after 30 minutes."
        task.completed_at = datetime.now(UTC)

    if stale_tasks:
        await db.commit()
        logger.warning("Cleaned up %d stale tasks", len(stale_tasks))

    return len(stale_tasks)
