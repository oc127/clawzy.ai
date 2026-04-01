"""LINE channel — Messaging API helpers."""

import hashlib
import hmac
import base64
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = settings.line_api_url


async def send_message(channel_access_token: str, reply_token: str, text: str) -> bool:
    """Reply to a LINE message using the Messaging API."""
    url = f"{_BASE_URL}/bot/message/reply"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {channel_access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": text}],
                },
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.error("LINE reply failed: %s", exc)
        return False


def verify_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """Verify the LINE webhook signature."""
    mac = hmac.new(
        channel_secret.encode("utf-8"),
        body,
        digestmod=hashlib.sha256,
    )
    expected = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(signature, expected)


def parse_event(payload: dict) -> list[tuple[str | None, str | None]]:
    """
    Parse LINE webhook events.

    Returns list of (reply_token, text) tuples for message events.
    """
    events = payload.get("events", [])
    results = []
    for event in events:
        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue
        reply_token = event.get("replyToken")
        text = message.get("text")
        results.append((reply_token, text))
    return results
