"""Integration management endpoints — configure LINE/Discord/Telegram per agent."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.deps import get_current_user
from app.models.integration import Integration, Platform
from app.models.user import User
from app.schemas.integration import IntegrationCreate, IntegrationResponse, IntegrationUpdate
from app.services.agent_service import get_agent
from app.services.messaging_service import delete_telegram_webhook, set_telegram_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _build_webhook_url(integration: Integration) -> str:
    base = settings.oauth_redirect_base_url or "https://clawzy.ai"
    return f"{base}/api/v1/webhooks/{integration.platform.value}/{integration.webhook_secret}"


def _to_response(integration: Integration) -> IntegrationResponse:
    return IntegrationResponse(
        id=integration.id,
        agent_id=integration.agent_id,
        platform=integration.platform.value,
        enabled=integration.enabled,
        webhook_url=_build_webhook_url(integration),
        has_bot_token=bool(integration.bot_token),
        has_channel_secret=bool(integration.channel_secret),
        has_channel_access_token=bool(integration.channel_access_token),
        created_at=integration.created_at.isoformat(),
        updated_at=integration.updated_at.isoformat(),
    )


@router.get("/agents/{agent_id}", response_model=list[IntegrationResponse])
async def list_integrations(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(select(Integration).where(Integration.agent_id == agent_id))
    return [_to_response(i) for i in result.scalars().all()]


@router.post("/agents/{agent_id}", response_model=IntegrationResponse, status_code=201)
async def create_integration(
    agent_id: str,
    body: IntegrationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check for existing integration on this platform
    result = await db.execute(
        select(Integration).where(
            Integration.agent_id == agent_id,
            Integration.platform == Platform(body.platform),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"{body.platform} integration already exists for this agent")

    # Validate required fields per platform
    if body.platform == "line":
        if not body.channel_secret or not body.channel_access_token:
            raise HTTPException(status_code=422, detail="LINE requires channel_secret and channel_access_token")
    elif body.platform == "discord":
        if not body.bot_token:
            raise HTTPException(status_code=422, detail="Discord requires bot_token")
    elif body.platform == "telegram" and not body.bot_token:
        raise HTTPException(status_code=422, detail="Telegram requires bot_token")

    integration = Integration(
        agent_id=agent_id,
        user_id=user.id,
        platform=Platform(body.platform),
        bot_token=body.bot_token,
        channel_secret=body.channel_secret,
        channel_access_token=body.channel_access_token,
    )
    db.add(integration)
    await db.flush()

    # Auto-register Telegram webhook
    if body.platform == "telegram" and body.bot_token:
        webhook_url = _build_webhook_url(integration)
        try:
            ok = await set_telegram_webhook(body.bot_token, webhook_url)
            if not ok:
                logger.warning("Failed to set Telegram webhook for integration %s", integration.id)
        except Exception:
            logger.exception("Error setting Telegram webhook")

    await db.commit()
    await db.refresh(integration)
    return _to_response(integration)


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    body: IntegrationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.user_id == user.id,
        )
    )
    integration = result.scalar_one_or_none()
    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    if body.bot_token is not None:
        integration.bot_token = body.bot_token
    if body.channel_secret is not None:
        integration.channel_secret = body.channel_secret
    if body.channel_access_token is not None:
        integration.channel_access_token = body.channel_access_token
    if body.enabled is not None:
        integration.enabled = body.enabled

    # Re-register Telegram webhook if token changed
    if integration.platform == Platform.telegram and body.bot_token:
        webhook_url = _build_webhook_url(integration)
        try:
            await set_telegram_webhook(body.bot_token, webhook_url)
        except Exception:
            logger.exception("Error updating Telegram webhook")

    await db.commit()
    await db.refresh(integration)
    return _to_response(integration)


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.user_id == user.id,
        )
    )
    integration = result.scalar_one_or_none()
    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Unregister Telegram webhook
    if integration.platform == Platform.telegram and integration.bot_token:
        try:
            await delete_telegram_webhook(integration.bot_token)
        except Exception:
            logger.exception("Error deleting Telegram webhook")

    await db.delete(integration)
    await db.commit()
