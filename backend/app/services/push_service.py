"""Unified push notification service for Lucy.

Delivers messages to users through the best available channel:
WebSocket (in-app) > LINE (mobile) > Email (fallback).
"""

import json
import logging
import uuid
from email.message import EmailMessage
from enum import Enum

import aiosmtplib
import httpx
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session
from app.models.lucy_state import LucyState
from app.models.user import User

logger = logging.getLogger(__name__)

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


class PushChannel(str, Enum):
    WEBSOCKET = "websocket"
    LINE = "line"
    EMAIL = "email"


# ---- WebSocket connection registry ---------------------------------------- #

_active_connections: dict[str, set[WebSocket]] = {}


def register_connection(user_id: str, ws: WebSocket) -> None:
    """Register an active WebSocket connection for a user."""
    if user_id not in _active_connections:
        _active_connections[user_id] = set()
    _active_connections[user_id].add(ws)
    logger.debug("Registered WS connection for user=%s (total=%d)", user_id, len(_active_connections[user_id]))


def unregister_connection(user_id: str, ws: WebSocket) -> None:
    """Remove a WebSocket connection when it disconnects."""
    conns = _active_connections.get(user_id)
    if conns is None:
        return
    conns.discard(ws)
    if not conns:
        del _active_connections[user_id]
    logger.debug("Unregistered WS connection for user=%s", user_id)


def is_user_online(user_id: str) -> bool:
    """Check if user has any active WebSocket connections."""
    return bool(_active_connections.get(user_id))


# ---- Channel-specific delivery -------------------------------------------- #


async def push_via_websocket(user_id: str, message: str, initiative_type: str) -> bool:
    """Send via active WebSocket connections. Returns True if delivered to at least one."""
    conns = _active_connections.get(user_id)
    if not conns:
        return False

    payload = json.dumps({
        "type": "initiative",
        "initiative_type": initiative_type,
        "message": message,
        "initiative_id": str(uuid.uuid4()),
    })

    delivered = False
    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_text(payload)
            delivered = True
        except Exception:
            logger.warning("Failed to send WS push to user=%s, removing dead connection", user_id)
            dead.append(ws)

    # Clean up dead connections
    for ws in dead:
        conns.discard(ws)
    if not conns:
        _active_connections.pop(user_id, None)

    return delivered


async def push_via_line(user_id: str, message: str) -> bool:
    """Send via LINE Push Messaging API. Returns True if delivered."""
    if not settings.line_channel_access_token:
        logger.debug("LINE access token not configured, skipping LINE push")
        return False

    # Look up the user's LINE user ID from their LucyState
    async with async_session() as db:
        result = await db.execute(
            select(LucyState.line_user_id).where(LucyState.user_id == user_id)
        )
        line_user_id = result.scalar_one_or_none()

    if not line_user_id:
        logger.debug("No LINE user ID for user=%s, skipping LINE push", user_id)
        return False

    # LINE push messages have a 5000-char limit per text message, send up to 5 chunks
    chunks = [message[i:i + 4500] for i in range(0, len(message), 4500)]
    messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                LINE_PUSH_URL,
                headers={
                    "Authorization": f"Bearer {settings.line_channel_access_token}",
                    "Content-Type": "application/json",
                },
                json={"to": line_user_id, "messages": messages},
            )
            if resp.status_code == 200:
                logger.info("LINE push delivered to user=%s", user_id)
                return True
            else:
                logger.warning("LINE push failed for user=%s: %s %s", user_id, resp.status_code, resp.text)
                return False
    except Exception:
        logger.exception("LINE push error for user=%s", user_id)
        return False


async def push_via_email(user_id: str, message: str, subject: str | None = None) -> bool:
    """Send via email. Returns True if delivered."""
    if not settings.smtp_host:
        logger.debug("SMTP not configured, skipping email push")
        return False

    # Look up the user's email
    async with async_session() as db:
        result = await db.execute(
            select(User.email).where(User.id == user_id)
        )
        email = result.scalar_one_or_none()

    if not email:
        logger.debug("No email found for user=%s, skipping email push", user_id)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject or "Lucy - 新しいメッセージ / New Message"
    msg["From"] = settings.smtp_from_email
    msg["To"] = email
    msg.set_content(
        f"{message}\n\n"
        f"---\n"
        f"Lucyからのメッセージです。/ A message from Lucy.\n"
        f"{settings.frontend_url}"
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("Email push delivered to user=%s (%s)", user_id, email)
        return True
    except Exception:
        logger.exception("Email push failed for user=%s", user_id)
        return False


# ---- Main push dispatcher ------------------------------------------------- #


async def push_to_user(
    user_id: str,
    message: str,
    initiative_type: str = "general",
    channels: list[PushChannel] | None = None,
) -> None:
    """Push a message to a user through the best available channel.

    Priority order (unless *channels* restricts the set):
    1. WebSocket — instant, in-app
    2. LINE — mobile notification
    3. Email — always available

    If *channels* is specified, only those channels are attempted (still in
    priority order).  If one channel succeeds, no further channels are tried.
    """
    # Determine which channels to try and in what order
    priority = [PushChannel.WEBSOCKET, PushChannel.LINE, PushChannel.EMAIL]
    if channels is not None:
        priority = [ch for ch in priority if ch in channels]

    # Optionally filter by user's push_channels preference
    if channels is None:
        async with async_session() as db:
            result = await db.execute(
                select(LucyState.push_channels).where(LucyState.user_id == user_id)
            )
            user_channels = result.scalar_one_or_none()
        if user_channels:
            allowed = {PushChannel(ch) for ch in user_channels if ch in PushChannel.__members__.values()}
            priority = [ch for ch in priority if ch in allowed]

    for channel in priority:
        try:
            if channel == PushChannel.WEBSOCKET:
                if await push_via_websocket(user_id, message, initiative_type):
                    logger.info("Push delivered via WebSocket to user=%s", user_id)
                    return
            elif channel == PushChannel.LINE:
                if await push_via_line(user_id, message):
                    logger.info("Push delivered via LINE to user=%s", user_id)
                    return
            elif channel == PushChannel.EMAIL:
                if await push_via_email(user_id, message):
                    logger.info("Push delivered via email to user=%s", user_id)
                    return
        except Exception:
            logger.exception("Push via %s failed for user=%s, trying next channel", channel.value, user_id)

    logger.warning("All push channels exhausted for user=%s — message not delivered", user_id)


# ---- Broadcast structured events ------------------------------------------ #


async def broadcast_to_user(user_id: str, event_type: str, data: dict) -> None:
    """Broadcast a structured event to all of a user's WebSocket connections.

    Used for task progress updates, status changes, etc.
    """
    conns = _active_connections.get(user_id)
    if not conns:
        return

    payload = json.dumps({"type": event_type, **data})

    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    for ws in dead:
        conns.discard(ws)
    if not conns:
        _active_connections.pop(user_id, None)
