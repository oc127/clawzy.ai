"""Webhooks API — receive inbound messages from Telegram, LINE, etc."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from fastapi import Depends
from app.models.channel import AgentChannel
from app.channels.telegram import parse_update as telegram_parse, send_message as telegram_send
from app.channels.line import parse_event as line_parse, send_message as line_send, verify_signature
from app.services.message_router import route_inbound

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/telegram/{agent_id}")
async def telegram_webhook(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Telegram webhook updates."""
    # Verify Telegram webhook secret (prevents forged requests)
    secret_token = request.headers.get("x-telegram-bot-api-secret-token", "")

    payload = await request.json()

    # Find the Telegram channel config for this agent
    result = await db.execute(
        select(AgentChannel).where(
            AgentChannel.agent_id == agent_id,
            AgentChannel.channel_type == "telegram",
            AgentChannel.enabled.is_(True),
        )
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram channel not configured for this agent",
        )

    # Verify webhook secret if configured
    expected_secret = channel.config.get("webhook_secret", "")
    if expected_secret and secret_token != expected_secret:
        logger.warning("Telegram webhook rejected: invalid secret for agent %s", agent_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    chat_id, text = telegram_parse(payload)
    if chat_id is None or not text:
        return {"ok": True}  # Ignore non-text messages

    # Route message through LLM
    response_text = await route_inbound(db, agent_id, text, metadata={"chat_id": chat_id})

    # Send reply
    bot_token = channel.config.get("bot_token", "")
    if bot_token:
        await telegram_send(bot_token, chat_id, response_text)

    return {"ok": True}


@router.post("/line/{agent_id}")
async def line_webhook(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive LINE webhook events."""
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")

    # Find the LINE channel config for this agent
    result = await db.execute(
        select(AgentChannel).where(
            AgentChannel.agent_id == agent_id,
            AgentChannel.channel_type == "line",
            AgentChannel.enabled.is_(True),
        )
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LINE channel not configured for this agent",
        )

    # Verify signature
    channel_secret = channel.config.get("channel_secret", "")
    if channel_secret and not verify_signature(body, signature, channel_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE signature",
        )

    payload = await request.json()
    events = line_parse(payload)

    channel_access_token = channel.config.get("channel_access_token", "")

    for reply_token, text in events:
        if not reply_token or not text:
            continue

        response_text = await route_inbound(db, agent_id, text, metadata={"reply_token": reply_token})

        if channel_access_token:
            await line_send(channel_access_token, reply_token, response_text)

    return {"ok": True}
