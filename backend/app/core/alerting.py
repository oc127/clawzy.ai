"""Webhook 告警 — 支持 Slack/Discord/通用 webhook。

自动去重：同一条告警 5 分钟内不会重复发。
"""

import json
import time
import logging

import httpx

from app.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

ALERT_COOLDOWN_PREFIX = "clawzy:alert_cooldown"


async def send_alert(title: str, message: str, severity: str = "warning") -> bool:
    """异步发送告警。"""
    if not settings.alert_webhook_url:
        logger.warning("Alert suppressed (no webhook): %s — %s", title, message)
        return False

    r = await get_redis()
    alert_key = f"{ALERT_COOLDOWN_PREFIX}:{title}"
    if await r.exists(alert_key):
        return False

    await r.set(alert_key, "1", ex=settings.alert_cooldown_seconds)

    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "⚠️")
    payload = {
        "text": f"{emoji} *{title}*\n{message}\n_Clawzy.ai Self-Healing System_",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                settings.alert_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code < 300:
                logger.info("Alert sent: %s", title)
                return True
            else:
                logger.error("Alert webhook returned %d: %s", resp.status_code, resp.text[:200])
                return False
    except Exception:
        logger.exception("Failed to send alert: %s", title)
        return False


def send_alert_sync(title: str, message: str, severity: str = "warning") -> bool:
    """同步版本（Celery 任务用）。"""
    import redis as sync_redis_lib
    import requests

    if not settings.alert_webhook_url:
        return False

    r = sync_redis_lib.from_url(settings.redis_url)
    alert_key = f"{ALERT_COOLDOWN_PREFIX}:{title}"
    if r.exists(alert_key):
        return False

    r.set(alert_key, "1", ex=settings.alert_cooldown_seconds)

    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "⚠️")
    payload = {
        "text": f"{emoji} *{title}*\n{message}\n_Clawzy.ai Self-Healing System_",
    }

    try:
        resp = requests.post(settings.alert_webhook_url, json=payload, timeout=10)
        return resp.status_code < 300
    except Exception:
        logger.exception("Failed to send sync alert: %s", title)
        return False
