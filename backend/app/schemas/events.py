from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Event source schemas ──

class EventCreate(BaseModel):
    event_type: str  # "github_webhook", "health_check", "scheduled", "custom"
    name: str
    config: dict[str, Any] = {}


class EventUpdate(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    enabled: bool | None = None


class EventResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    name: str
    config: dict[str, Any]
    enabled: bool
    last_triggered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Initiative schemas ──

class InitiativeResponse(BaseModel):
    id: str
    user_id: str
    initiative_type: str
    message: str
    context: dict[str, Any] | None = None
    delivered: bool
    delivered_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Webhook schemas ──

class GitHubWebhookPayload(BaseModel):
    """Minimal GitHub webhook payload — we accept the full payload as dict."""
    pass
