"""Lucy Events & Initiatives API — event sources, proactive messages, and webhook receivers."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.lucy_event import LucyEvent
from app.models.lucy_state import LucyState
from app.models.user import User
from app.schemas.events import EventCreate, EventResponse, EventUpdate, InitiativeResponse
from app.services.event_hub import list_events, register_event, remove_event
from app.services.proactive_engine import get_pending_initiatives, mark_delivered

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lucy/events", tags=["lucy-events"])

VALID_EVENT_TYPES = {"github_webhook", "health_check", "scheduled", "custom"}


async def _get_lucy_state(db: AsyncSession, user_id: str) -> LucyState:
    """Get LucyState for a user, raise 404 if not found."""
    result = await db.execute(select(LucyState).where(LucyState.user_id == user_id))
    state = result.scalar_one_or_none()
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lucy state not initialized")
    return state


# ─── Event source CRUD ───


@router.get("", response_model=list[EventResponse])
async def list_user_events(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all event sources configured for the current user."""
    events = await list_events(db, user.id)
    return events


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new event source."""
    if body.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"event_type must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}",
        )

    event = await register_event(db, user.id, body.event_type, body.name, body.config)
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an event source."""
    removed = await remove_event(db, user.id, event_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await db.commit()


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    body: EventUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an event source (name, config, enabled)."""
    result = await db.execute(
        select(LucyEvent).where(LucyEvent.id == event_id, LucyEvent.user_id == user.id)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if body.name is not None:
        event.name = body.name
    if body.config is not None:
        event.config = body.config
    if body.enabled is not None:
        event.enabled = body.enabled

    await db.commit()
    await db.refresh(event)
    return event


# ─── Initiatives ───


initiatives_router = APIRouter(prefix="/lucy/initiatives", tags=["lucy-events"])


@initiatives_router.get("", response_model=list[InitiativeResponse])
async def list_pending_initiatives(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending (undelivered) initiatives for the current user."""
    initiatives = await get_pending_initiatives(db, user.id)
    return initiatives


@initiatives_router.post("/{initiative_id}/delivered", status_code=status.HTTP_204_NO_CONTENT)
async def mark_initiative_delivered(
    initiative_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an initiative as delivered."""
    success = await mark_delivered(db, initiative_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Initiative not found")
    await db.commit()


# ─── Webhooks ───


webhooks_router = APIRouter(prefix="/lucy/webhooks", tags=["lucy-events"])


@webhooks_router.post("/github")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive GitHub webhook events and convert them to Lucy initiatives.

    The webhook URL should include the user_id as a query parameter:
      POST /api/v1/lucy/webhooks/github?user_id=<user_id>
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id query param required")

    event_type = request.headers.get("X-GitHub-Event", "unknown")
    payload: dict[str, Any] = await request.json()

    lucy_state = await _get_lucy_state(db, user_id)

    from app.services.event_hub import process_github_event

    initiative = await process_github_event(db, user_id, event_type, payload, lucy_state)
    await db.commit()

    return {
        "status": "processed",
        "event_type": event_type,
        "initiative_id": initiative.id if initiative else None,
    }
