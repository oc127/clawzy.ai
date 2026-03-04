"""Lightweight i18n for backend user-facing messages."""

import json
from pathlib import Path
from functools import lru_cache

SUPPORTED_LOCALES = ("zh", "en", "ja", "ko")
DEFAULT_LOCALE = "zh"

_MESSAGES_DIR = Path(__file__).parent / "messages"


@lru_cache(maxsize=4)
def _load_messages(locale: str) -> dict:
    path = _MESSAGES_DIR / f"{locale}.json"
    if not path.exists():
        path = _MESSAGES_DIR / f"{DEFAULT_LOCALE}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    """Translate a dotted key like 'auth.loginFailed'.

    Falls back to the key itself if not found.
    Supports {placeholder} interpolation via kwargs.
    """
    loc = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    messages = _load_messages(loc)
    value = messages
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return key
        if value is None:
            return key
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return value if isinstance(value, str) else key


def parse_locale(accept_language: str | None, cookie_locale: str | None = None) -> str:
    """Determine locale from cookie or Accept-Language header."""
    # Cookie takes priority
    if cookie_locale and cookie_locale in SUPPORTED_LOCALES:
        return cookie_locale

    if not accept_language:
        return DEFAULT_LOCALE

    # Parse Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().lower()
        # Match exact or prefix
        if lang in SUPPORTED_LOCALES:
            return lang
        prefix = lang.split("-")[0]
        if prefix in SUPPORTED_LOCALES:
            return prefix

    return DEFAULT_LOCALE
