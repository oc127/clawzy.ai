"""Connectors API — validate and connect messaging platform integrations.

Endpoints:
  POST /api/v1/connectors/telegram/validate  — verify Telegram Bot Token via getMe
  POST /api/v1/connectors/telegram/connect   — save token to openclaw.json + confirm
  POST /api/v1/connectors/line/validate      — verify LINE Channel Access Token via bot/info
  POST /api/v1/connectors/line/connect       — save LINE config to openclaw.json + confirm
"""

import json
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.http_client import get_shared_client
from app.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["connectors"])


# ── Shared response schema ────────────────────────────────────────────────────

class ValidateResponse(BaseModel):
    valid: bool
    detail: str


# ── Telegram ──────────────────────────────────────────────────────────────────

class TelegramValidateRequest(BaseModel):
    bot_token: str


class TelegramConnectRequest(BaseModel):
    bot_token: str


@router.post("/telegram/validate", response_model=ValidateResponse)
async def validate_telegram(
    body: TelegramValidateRequest,
    user: User = Depends(get_current_user),
) -> ValidateResponse:
    """Validate a Telegram Bot Token by calling the getMe API."""
    url = f"{settings.telegram_bot_api_url}/bot{body.bot_token}/getMe"
    client = get_shared_client()
    try:
        resp = await client.get(url, timeout=10.0)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Network error: {exc}")

    if resp.status_code == 200:
        username = resp.json().get("result", {}).get("username", "")
        return ValidateResponse(valid=True, detail=f"Bot @{username} is valid")

    return ValidateResponse(valid=False, detail="Invalid bot token")


@router.post("/telegram/connect", response_model=ValidateResponse)
async def connect_telegram(
    body: TelegramConnectRequest,
    user: User = Depends(get_current_user),
) -> ValidateResponse:
    """Validate and save Telegram bot token to openclaw.json channels config."""
    url = f"{settings.telegram_bot_api_url}/bot{body.bot_token}/getMe"
    client = get_shared_client()
    try:
        resp = await client.get(url, timeout=10.0)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Network error: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid bot token")

    username = resp.json().get("result", {}).get("username", "")
    _update_openclaw_config("telegram", {"bot_token": body.bot_token, "enabled": True})
    return ValidateResponse(valid=True, detail=f"Telegram bot @{username} connected successfully")


# ── LINE ──────────────────────────────────────────────────────────────────────

class LineValidateRequest(BaseModel):
    channel_access_token: str


class LineConnectRequest(BaseModel):
    channel_access_token: str
    channel_secret: str
    webhook_path: str = "/webhooks/line"


@router.post("/line/validate", response_model=ValidateResponse)
async def validate_line(
    body: LineValidateRequest,
    user: User = Depends(get_current_user),
) -> ValidateResponse:
    """Validate a LINE Channel Access Token by calling the bot/info API."""
    url = f"{settings.line_api_url}/bot/info"
    client = get_shared_client()
    try:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {body.channel_access_token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Network error: {exc}")

    if resp.status_code == 200:
        display_name = resp.json().get("displayName", "LINE Bot")
        return ValidateResponse(valid=True, detail=f"Bot '{display_name}' is valid")

    return ValidateResponse(valid=False, detail="Invalid channel access token")


@router.post("/line/connect", response_model=ValidateResponse)
async def connect_line(
    body: LineConnectRequest,
    user: User = Depends(get_current_user),
) -> ValidateResponse:
    """Validate and save LINE channel config to openclaw.json channels config."""
    url = f"{settings.line_api_url}/bot/info"
    client = get_shared_client()
    try:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {body.channel_access_token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Network error: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid channel access token")

    display_name = resp.json().get("displayName", "LINE Bot")
    _update_openclaw_config("line", {
        "channel_access_token": body.channel_access_token,
        "channel_secret": body.channel_secret,
        "webhook_path": body.webhook_path,
        "enabled": True,
    })
    return ValidateResponse(valid=True, detail=f"LINE bot '{display_name}' connected successfully")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _update_openclaw_config(channel: str, config: dict) -> None:
    """Write channel config into openclaw.json under a 'channels' key."""
    config_path = _find_openclaw_config()
    if config_path is None:
        logger.warning("openclaw.json not found; skipping config write for channel=%s", channel)
        return

    try:
        with open(config_path) as f:
            data = json.load(f)
        data.setdefault("channels", {})[channel] = config
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Updated openclaw.json channels.%s", channel)
    except Exception as exc:
        logger.error("Failed to update openclaw.json: %s", exc)


def _find_openclaw_config() -> Path | None:
    """Locate openclaw.json by checking common mount paths."""
    candidates = [
        Path("/app/openclaw/openclaw.json"),
        Path("openclaw/openclaw.json"),
        Path("../openclaw/openclaw.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None
