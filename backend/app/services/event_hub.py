"""Event Hub — processes external events and converts them to Lucy initiatives.

Handles GitHub webhooks, health checks, and custom event sources.
Each event type is converted into a situation description that the
Proactive Engine uses to generate an in-character Lucy message.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lucy_event import LucyEvent, LucyInitiative
from app.models.lucy_state import LucyState
from app.services.proactive_engine import generate_initiative

logger = logging.getLogger(__name__)

# ─── GitHub event situation templates ───

_GITHUB_SITUATIONS: dict[str, str] = {
    "push": (
        "A new push was made to the repository '{repo}' on branch '{branch}' "
        "by {sender}. {commits_summary} "
        "Mention this casually and ask if they want to review."
    ),
    "pull_request": (
        "A pull request was {action} on '{repo}': '{title}' by {sender}. "
        "React naturally and offer to help review."
    ),
    "issues": (
        "An issue was {action} on '{repo}': '{title}' by {sender}. "
        "Let them know about it conversationally."
    ),
    "workflow_run": (
        "A CI/CD workflow '{workflow_name}' on '{repo}' has {conclusion}. "
        "If it failed, express concern and offer to help debug. "
        "If it succeeded, celebrate briefly."
    ),
    "star": (
        "Someone starred the repository '{repo}'! "
        "Share the excitement naturally."
    ),
}


async def process_github_event(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    payload: dict[str, Any],
    lucy_state: LucyState,
) -> LucyInitiative | None:
    """Convert a GitHub webhook payload into a Lucy initiative."""
    repo = payload.get("repository", {}).get("full_name", "unknown repo")
    sender = payload.get("sender", {}).get("login", "someone")
    action = payload.get("action", "")

    template = _GITHUB_SITUATIONS.get(event_type)
    if template is None:
        # Generic fallback for unsupported event types
        situation = (
            f"A GitHub event '{event_type}' occurred on repository '{repo}' by {sender}. "
            f"Mention it briefly."
        )
    elif event_type == "push":
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])
        commits_summary = f"{len(commits)} commit(s) pushed." if commits else ""
        situation = template.format(repo=repo, branch=branch, sender=sender, commits_summary=commits_summary)
    elif event_type == "pull_request":
        title = payload.get("pull_request", {}).get("title", "untitled")
        situation = template.format(repo=repo, action=action, title=title, sender=sender)
    elif event_type == "issues":
        title = payload.get("issue", {}).get("title", "untitled")
        situation = template.format(repo=repo, action=action, title=title, sender=sender)
    elif event_type == "workflow_run":
        workflow_name = payload.get("workflow_run", {}).get("name", "unknown")
        conclusion = payload.get("workflow_run", {}).get("conclusion", "completed")
        situation = template.format(repo=repo, workflow_name=workflow_name, conclusion=conclusion)
    elif event_type == "star":
        situation = template.format(repo=repo)
    else:
        situation = template.format(**{k: payload.get(k, "") for k in template.split("{") if "}" in k})

    # Update last_triggered_at on matching events
    result = await db.execute(
        select(LucyEvent).where(
            LucyEvent.user_id == user_id,
            LucyEvent.event_type == "github_webhook",
            LucyEvent.enabled.is_(True),
        )
    )
    for event in result.scalars().all():
        event_repo = event.config.get("repo", "")
        if event_repo and event_repo in repo:
            event.last_triggered_at = datetime.now(UTC)

    return await generate_initiative(
        db, user_id, "event_report", situation, lucy_state,
        context={"source": "github", "event_type": event_type, "repo": repo},
    )


async def process_health_check(
    db: AsyncSession,
    user_id: str,
    event: LucyEvent,
    lucy_state: LucyState,
) -> LucyInitiative | None:
    """Ping a URL and create an alert initiative if the service is down."""
    url = event.config.get("url")
    if not url:
        return None

    # Throttle: don't alert more than once per hour
    if event.last_triggered_at:
        hours_since = (datetime.now(UTC) - event.last_triggered_at).total_seconds() / 3600
        if hours_since < 1:
            return None

    is_down = False
    status_code = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            status_code = resp.status_code
            if resp.status_code >= 500:
                is_down = True
    except (httpx.ConnectError, httpx.TimeoutException):
        is_down = True
    except Exception:
        logger.exception("Health check failed for %s", url)
        is_down = True

    if not is_down:
        return None

    event.last_triggered_at = datetime.now(UTC)

    status_info = f"HTTP {status_code}" if status_code else "unreachable"
    situation = (
        f"The service at '{event.name}' ({url}) appears to be down ({status_info}). "
        f"Alert the user with concern and offer to help investigate."
    )

    return await generate_initiative(
        db, user_id, "alert", situation, lucy_state,
        context={"source": "health_check", "url": url, "status": status_info, "event_id": event.id},
    )


async def register_event(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    name: str,
    config: dict[str, Any],
) -> LucyEvent:
    """Register a new event source for monitoring."""
    event = LucyEvent(
        user_id=user_id,
        event_type=event_type,
        name=name,
        config=config,
    )
    db.add(event)
    await db.flush()
    return event


async def remove_event(db: AsyncSession, user_id: str, event_id: str) -> bool:
    """Remove an event source. Returns False if not found."""
    result = await db.execute(
        select(LucyEvent).where(
            LucyEvent.id == event_id,
            LucyEvent.user_id == user_id,
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        return False
    await db.delete(event)
    await db.flush()
    return True


async def list_events(db: AsyncSession, user_id: str) -> list[LucyEvent]:
    """List all configured events for a user."""
    result = await db.execute(
        select(LucyEvent).where(LucyEvent.user_id == user_id).order_by(LucyEvent.created_at.desc())
    )
    return list(result.scalars().all())
