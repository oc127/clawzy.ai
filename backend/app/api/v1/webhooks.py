"""Webhook endpoints for LINE, Discord, and Telegram.

These are public endpoints — authentication is done via platform-specific
signature verification, not JWT.
"""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.models.integration import Integration, Platform
from app.services.messaging_service import (
    process_platform_message,
    send_discord_message,
    send_line_reply,
    send_telegram_message,
    verify_line_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _get_integration(webhook_secret: str, platform: Platform) -> Integration | None:
    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(
                Integration.webhook_secret == webhook_secret,
                Integration.platform == platform,
                Integration.enabled.is_(True),
            )
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
#  LINE Webhook
# ---------------------------------------------------------------------------


@router.post("/line/{webhook_secret}")
async def line_webhook(webhook_secret: str, request: Request):
    """Handle LINE webhook events."""
    body = await request.body()

    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(
                Integration.webhook_secret == webhook_secret,
                Integration.platform == Platform.line,
                Integration.enabled.is_(True),
            )
        )
        integration = result.scalar_one_or_none()

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Verify LINE signature
    signature = request.headers.get("x-line-signature", "")
    if not integration.channel_secret or not verify_line_signature(body, signature, integration.channel_secret):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = payload.get("events", [])
    for event in events:
        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue

        text = event["message"]["text"]
        reply_token = event.get("replyToken")
        sender_id = event.get("source", {}).get("userId", "unknown")

        # Process in a new db session
        async with async_session() as db:
            # Re-fetch integration with agent loaded
            result = await db.execute(
                select(Integration)
                .options(selectinload(Integration.agent))
                .where(Integration.id == integration.id)
            )
            fresh = result.scalar_one()
            reply = await process_platform_message(db, fresh, sender_id, text)

        if reply and reply_token and integration.channel_access_token:
            await send_line_reply(reply_token, reply, integration.channel_access_token)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
#  Discord Webhook
# ---------------------------------------------------------------------------


@router.post("/discord/{webhook_secret}")
async def discord_webhook(webhook_secret: str, request: Request):
    """Handle Discord interaction/bot events."""
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Discord URL verification (ping)
    if payload.get("type") == 1:
        return {"type": 1}

    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(
                Integration.webhook_secret == webhook_secret,
                Integration.platform == Platform.discord,
                Integration.enabled.is_(True),
            )
        )
        integration = result.scalar_one_or_none()

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Handle MESSAGE_CREATE events from Discord gateway (bot mode)
    # For webhook-based bots, we process direct messages
    msg_content = payload.get("content") or payload.get("data", {}).get("options", [{}])[0].get("value", "")
    if not msg_content:
        return {"status": "ignored"}

    channel_id = payload.get("channel_id")
    author = payload.get("author", {})
    sender_id = author.get("id", "unknown")

    # Don't respond to bot messages
    if author.get("bot"):
        return {"status": "ignored"}

    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(Integration.id == integration.id)
        )
        fresh = result.scalar_one()
        reply = await process_platform_message(db, fresh, sender_id, msg_content)

    if reply and channel_id and integration.bot_token:
        await send_discord_message(channel_id, reply, integration.bot_token)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
#  Telegram Webhook
# ---------------------------------------------------------------------------


@router.post("/telegram/{webhook_secret}")
async def telegram_webhook(webhook_secret: str, request: Request):
    """Handle Telegram webhook updates."""
    body = await request.body()

    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(
                Integration.webhook_secret == webhook_secret,
                Integration.platform == Platform.telegram,
                Integration.enabled.is_(True),
            )
        )
        integration = result.scalar_one_or_none()

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle /message updates
    message = payload.get("message", {})
    text = message.get("text", "")
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    sender_id = str(message.get("from", {}).get("id", "unknown"))

    if not text or not chat_id:
        return {"status": "ignored"}

    # Skip bot commands except /ask
    if text.startswith("/") and not text.startswith("/ask"):
        return {"status": "ignored"}

    # Strip /ask prefix if present
    if text.startswith("/ask "):
        text = text[5:]

    async with async_session() as db:
        result = await db.execute(
            select(Integration)
            .options(selectinload(Integration.agent))
            .where(Integration.id == integration.id)
        )
        fresh = result.scalar_one()
        reply = await process_platform_message(db, fresh, sender_id, text)

    if reply and integration.bot_token:
        await send_telegram_message(chat_id, reply, integration.bot_token)

    return {"status": "ok"}
