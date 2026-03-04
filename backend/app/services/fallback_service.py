"""断线 fallback 服务 — 龙虾不在时的友好回复。

当 LiteLLM/模型 API 不可用、容器崩溃、或其他异常时，
不要让用户看到冷冰冰的错误，而是用预设的友好回复保持对话。
"""

import json
import random
from pathlib import Path
from functools import lru_cache

from app.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES

_MESSAGES_DIR = Path(__file__).parent.parent / "i18n" / "messages"


@lru_cache(maxsize=4)
def _load_fallback(locale: str) -> dict:
    loc = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    path = _MESSAGES_DIR / f"{loc}.json"
    if not path.exists():
        path = _MESSAGES_DIR / f"{DEFAULT_LOCALE}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("fallback", {})


def get_fallback_reply(error_type: str, locale: str = DEFAULT_LOCALE) -> str:
    """根据错误类型返回一条友好的 fallback 回复。"""
    fb = _load_fallback(locale)
    pool_map = {
        "model_error": "modelUnavailable",
        "timeout": "modelUnavailable",
        "connection_error": "networkError",
        "empty_response": "modelUnavailable",
        "agent_down": "agentDown",
        "insufficient_credits": "noCredits",
        "rate_limited": "rateLimited",
    }
    key = pool_map.get(error_type, "modelUnavailable")
    pool = fb.get(key, fb.get("modelUnavailable", ["Sorry, please try again later."]))
    return random.choice(pool)


def get_model_switched_message(locale: str = DEFAULT_LOCALE) -> str:
    """当自动切换到备用模型时的友好通知。"""
    fb = _load_fallback(locale)
    pool = fb.get("modelSwitched", ["Switched to backup model."])
    return random.choice(pool)


def get_reconnecting_message(locale: str = DEFAULT_LOCALE) -> str:
    """WebSocket 断线后重连时发给用户的第一条消息。"""
    fb = _load_fallback(locale)
    pool = fb.get("reconnected", ["Reconnected!"])
    return random.choice(pool)
