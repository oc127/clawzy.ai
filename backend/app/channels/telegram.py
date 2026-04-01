"""Telegram channel — Bot API helpers."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = settings.telegram_bot_api_url


async def send_message(bot_token: str, chat_id: int | str, text: str) -> bool:
    """Send a text message via Telegram Bot API."""
    url = f"{_BASE_URL}/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.error("Telegram sendMessage failed (chat_id=%s): %s", chat_id, exc)
        return False


def parse_update(payload: dict) -> tuple[int | None, str | None]:
    """
    Extract chat_id and text from a Telegram webhook update.

    Returns (chat_id, text) or (None, None) if not a text message.
    """
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return None, None

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")
    return chat_id, text
