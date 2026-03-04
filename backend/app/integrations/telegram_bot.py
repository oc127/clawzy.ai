"""Telegram Bot — 运维 Agent 的对话入口。

在 Telegram 上直接与运维 Agent 对话：
- "系统状态怎么样？"
- "帮我看看最近的错误日志"
- "备份一下数据库"

Setup:
1. Create bot via @BotFather → get token
2. Get your chat ID via @userinfobot
3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID in .env
"""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory conversation history (cleared on restart)
_chat_history: dict[str, list[dict]] = {}
MAX_HISTORY = 20

# Telegram Bot API base URL
_BOT_URL = ""


def _api(method: str) -> str:
    return f"{_BOT_URL}/{method}"


async def _send_message(chat_id: str, text: str) -> None:
    """Send a message via Telegram Bot API (handles 4096 char limit)."""
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(text), 4000):
            chunk = text[i:i + 4000]
            await client.post(_api("sendMessage"), json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
            })


async def _handle_update(update: dict) -> None:
    """Process a single Telegram update."""
    message = update.get("message")
    if not message or not message.get("text"):
        return

    chat_id = str(message["chat"]["id"])
    text = message["text"]

    # Auth: only respond to admin
    if chat_id != settings.telegram_admin_chat_id:
        await _send_message(chat_id, "Unauthorized.")
        return

    # Handle /clear command
    if text.strip() == "/clear":
        _chat_history.pop(chat_id, None)
        await _send_message(chat_id, "History cleared.")
        return

    # Handle /start command
    if text.strip() == "/start":
        await _send_message(chat_id, "Clawzy.ai Ops Agent ready. Ask me about system health, logs, metrics, etc.")
        return

    # Call ops agent
    from app.services.ops_chat_service import ops_chat

    history = _chat_history.get(chat_id, [])

    try:
        reply = await ops_chat(text, context=history)
    except Exception as e:
        logger.exception("Ops chat failed")
        reply = f"Error: {e}"

    # Update history
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    _chat_history[chat_id] = history[-MAX_HISTORY:]

    await _send_message(chat_id, reply)


async def start_polling() -> None:
    """Long-polling loop for Telegram updates. Runs as background task."""
    global _BOT_URL

    if not settings.telegram_bot_token:
        logger.info("Telegram bot not configured, skipping")
        return

    _BOT_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    logger.info("Starting Telegram bot polling...")

    offset = 0
    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            try:
                resp = await client.get(_api("getUpdates"), params={
                    "offset": offset,
                    "timeout": 30,
                })
                if resp.status_code != 200:
                    logger.error("Telegram getUpdates failed: %d", resp.status_code)
                    await asyncio.sleep(5)
                    continue

                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    try:
                        await _handle_update(update)
                    except Exception:
                        logger.exception("Error handling Telegram update")

            except httpx.TimeoutException:
                continue
            except Exception:
                logger.exception("Telegram polling error")
                await asyncio.sleep(5)
