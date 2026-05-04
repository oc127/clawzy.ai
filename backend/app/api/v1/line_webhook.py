"""LINE Messaging API webhook — bridges LINE messages to Clawzy agents."""

import hashlib
import hmac
import base64
import json
import logging

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.services.chat_service import get_or_create_conversation, stream_chat_completion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line", tags=["line"])

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook signature."""
    if not settings.line_channel_secret:
        return False
    mac = hmac.new(
        settings.line_channel_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    )
    return hmac.compare_digest(base64.b64encode(mac.digest()).decode("utf-8"), signature)


async def reply_to_line(reply_token: str, text: str) -> None:
    """Send a reply message via LINE Messaging API."""
    if not settings.line_channel_access_token:
        logger.warning("LINE access token not configured")
        return

    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
    messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            LINE_REPLY_URL,
            headers={
                "Authorization": f"Bearer {settings.line_channel_access_token}",
                "Content-Type": "application/json",
            },
            json={"replyToken": reply_token, "messages": messages},
        )


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None),
):
    body = await request.body()

    if x_line_signature and not verify_signature(body, x_line_signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    events = data.get("events", [])

    for event in events:
        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue

        reply_token = event.get("replyToken")
        user_text = event["message"]["text"]
        line_user_id = event.get("source", {}).get("userId", "")

        if not reply_token or not line_user_id:
            continue

        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.email == f"line_{line_user_id}@clawzy.ai")
            )
            user = result.scalar_one_or_none()

            if user is None:
                await reply_to_line(reply_token, "Please link your Clawzy account first at our website.")
                continue

            result = await db.execute(
                select(Agent)
                .where(Agent.user_id == user.id, Agent.status == AgentStatus.running)
                .order_by(Agent.last_active_at.desc())
                .limit(1)
            )
            agent = result.scalar_one_or_none()

            if agent is None:
                await reply_to_line(reply_token, "No active agent found. Please start an agent on the dashboard.")
                continue

            conv = await get_or_create_conversation(db, agent.id, None)
            await db.commit()

            full_response = ""
            async for event_str in stream_chat_completion(db, user.id, agent, conv.id, user_text):
                event_data = json.loads(event_str)
                if event_data["type"] == "stream":
                    full_response += event_data["content"]
                elif event_data["type"] == "error":
                    full_response = f"Error: {event_data['message']}"
                    break

            if full_response:
                await reply_to_line(reply_token, full_response)

    return {"ok": True}
