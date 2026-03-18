"""Messaging service — bridges LINE/Discord/Telegram messages to the agent chat system."""

import hashlib
import hmac
import json
import logging
from base64 import b64decode, b64encode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.chat import Conversation, MessageRole
from app.models.integration import Integration, Platform
from app.models.user import User
from app.services.chat_service import (
    get_or_create_conversation,
    save_message,
    stream_chat_completion,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Core: process incoming message from any platform
# ---------------------------------------------------------------------------


async def process_platform_message(
    db: AsyncSession,
    integration: Integration,
    sender_id: str,
    text: str,
) -> str:
    """
    Process an incoming message from a messaging platform.
    Returns the assistant's reply text.
    """
    if not text.strip():
        return ""

    # Truncate to same limit as WebSocket chat
    if len(text) > 20000:
        text = text[:20000]

    agent = integration.agent
    user = await _get_user(db, integration.user_id)
    if user is None:
        return "Account error. Please reconfigure this integration."

    if user.credit_balance <= 0:
        return "No credits remaining. Please top up at clawzy.ai."

    # Use sender_id as a pseudo-conversation key so each platform user gets a thread
    conv_key = f"{integration.platform.value}:{sender_id}"
    conv = await _get_or_create_platform_conversation(db, agent.id, conv_key)
    await db.commit()

    # Stream the full response (collect all chunks)
    full_response = ""
    async for event_str in stream_chat_completion(db, user.id, agent, conv.id, text):
        event = json.loads(event_str)
        if event["type"] == "stream":
            full_response += event["content"]
        elif event["type"] == "error":
            logger.warning("Chat error for integration %s: %s", integration.id, event.get("message"))
            return event.get("message", "Sorry, something went wrong.")

    return full_response or "Sorry, I could not generate a response."


async def _get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_or_create_platform_conversation(
    db: AsyncSession, agent_id: str, conv_key: str
) -> Conversation:
    """Find or create a conversation using a platform-specific key stored in the title."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.agent_id == agent_id,
            Conversation.title == conv_key,
        )
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv
    conv = Conversation(agent_id=agent_id, title=conv_key)
    db.add(conv)
    await db.flush()
    return conv


# ---------------------------------------------------------------------------
#  LINE Messaging API
# ---------------------------------------------------------------------------


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """Verify LINE webhook signature."""
    mac = hmac.new(channel_secret.encode(), body, hashlib.sha256)
    expected = b64encode(mac.digest()).decode()
    return hmac.compare_digest(expected, signature)


async def send_line_reply(reply_token: str, text: str, channel_access_token: str) -> None:
    """Send a reply message via LINE Messaging API."""
    # LINE has a 5000 char limit per text message
    if len(text) > 5000:
        text = text[:4997] + "..."

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Authorization": f"Bearer {channel_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": text}],
            },
        )


async def send_line_push(user_id: str, text: str, channel_access_token: str) -> None:
    """Push a message to a LINE user (for cases without reply token)."""
    if len(text) > 5000:
        text = text[:4997] + "..."

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {channel_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "to": user_id,
                "messages": [{"type": "text", "text": text}],
            },
        )


# ---------------------------------------------------------------------------
#  Discord Bot
# ---------------------------------------------------------------------------


async def send_discord_message(channel_id: str, text: str, bot_token: str) -> None:
    """Send a message to a Discord channel."""
    # Discord has 2000 char limit
    if len(text) > 2000:
        text = text[:1997] + "..."

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
            },
            json={"content": text},
        )


def verify_discord_signature(body: bytes, signature: str, timestamp: str, public_key: str) -> bool:
    """Verify Discord interaction signature using Ed25519."""
    try:
        from nacl.signing import VerifyKey
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
#  Telegram Bot API
# ---------------------------------------------------------------------------


async def send_telegram_message(chat_id: str, text: str, bot_token: str) -> None:
    """Send a message via Telegram Bot API."""
    # Telegram has 4096 char limit
    if len(text) > 4096:
        text = text[:4093] + "..."

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )


async def set_telegram_webhook(bot_token: str, webhook_url: str) -> bool:
    """Register webhook URL with Telegram."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={"url": webhook_url},
        )
        data = resp.json()
        return data.get("ok", False)


async def delete_telegram_webhook(bot_token: str) -> bool:
    """Remove webhook from Telegram."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
        )
        data = resp.json()
        return data.get("ok", False)
