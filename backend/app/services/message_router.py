"""Message router — unified inbound handler for external channels."""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent import Agent

logger = logging.getLogger(__name__)


async def route_inbound(
    db: AsyncSession,
    agent_id: str,
    user_text: str,
    metadata: dict | None = None,
) -> str:
    """
    Unified entry point for all external channel messages.

    Calls LiteLLM non-interactively and returns the response text.
    """
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        logger.warning("Inbound message for unknown agent %s", agent_id)
        return "Agent not found."

    messages = []
    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})
    messages.append({"role": "user", "content": user_text})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.litellm_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.litellm_master_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": agent.model_name,
                    "messages": messages,
                    "max_tokens": 4096,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return "I'm sorry, I couldn't generate a response."
        return content

    except httpx.TimeoutException:
        logger.error("LiteLLM timeout for agent %s", agent_id)
        return "Sorry, the request timed out. Please try again."
    except Exception as exc:
        logger.error("Message routing failed for agent %s: %s", agent_id, exc)
        return "An error occurred processing your message."
