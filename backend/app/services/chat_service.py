"""Chat service — streams LLM responses via LiteLLM and manages conversations."""

import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent import Agent
from app.models.chat import Conversation, Message, MessageRole
from app.services.credits_service import deduct_credits, InsufficientCreditsError

logger = logging.getLogger(__name__)


async def get_or_create_conversation(
    db: AsyncSession, agent_id: str, conversation_id: str | None = None
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.agent_id == agent_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    conv = Conversation(agent_id=agent_id)
    db.add(conv)
    await db.flush()
    return conv


async def save_message(
    db: AsyncSession,
    conversation_id: str,
    role: MessageRole,
    content: str,
    model_name: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    credits_used: int | None = None,
) -> Message:
    """Persist a message to the database."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model_name=model_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_conversation_history(
    db: AsyncSession, conversation_id: str, limit: int = 20
) -> list[dict]:
    """Get recent messages for context."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
    images: list[str] | None = None,
):
    """
    Stream a chat completion from LiteLLM.

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {"credits": N, "balance": M}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    # Save user message (text only in DB)
    await save_message(db, conversation_id, MessageRole.user, user_content or "[image]")
    await db.commit()

    # Build message history for context
    history = await get_conversation_history(db, conversation_id)

    # If images attached, replace last user message with multimodal content
    if images:
        model_to_use = "qwen-vl-plus"   # vision-capable model
        content_parts: list = []
        if user_content:
            content_parts.append({"type": "text", "text": user_content})
        for img_url in images:
            content_parts.append({"type": "image_url", "image_url": {"url": img_url}})
        # Replace last history entry (the user text message we just saved)
        if history and history[-1]["role"] == "user":
            history[-1]["content"] = content_parts
        else:
            history.append({"role": "user", "content": content_parts})
    else:
        model_to_use = agent.model_name

    # Call LiteLLM streaming endpoint
    url = f"{settings.litellm_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_to_use,
        "messages": history,
        "max_tokens": 4096,
        "stream": True,
    }

    full_content = ""
    tokens_input = 0
    tokens_output = 0

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error("LiteLLM error %s: %s", response.status_code, body)
                    yield json.dumps({
                        "type": "error",
                        "code": "model_error",
                        "message": f"Model returned HTTP {response.status_code}",
                    })
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Extract content delta
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_content += content
                            yield json.dumps({"type": "stream", "content": content})

                    # Extract usage if present (final chunk)
                    usage = chunk.get("usage")
                    if usage:
                        tokens_input = usage.get("prompt_tokens", 0)
                        tokens_output = usage.get("completion_tokens", 0)

    except httpx.TimeoutException:
        yield json.dumps({
            "type": "error",
            "code": "timeout",
            "message": "Model request timed out",
        })
        return
    except httpx.ConnectError:
        yield json.dumps({
            "type": "error",
            "code": "connection_error",
            "message": "Cannot connect to model service",
        })
        return

    if not full_content:
        yield json.dumps({
            "type": "error",
            "code": "empty_response",
            "message": "Model returned empty response",
        })
        return

    # Estimate tokens if not provided by API
    if tokens_input == 0:
        tokens_input = len(str(history)) // 4  # rough estimate
    if tokens_output == 0:
        tokens_output = len(full_content) // 4

    # Deduct credits
    try:
        credits_used = await deduct_credits(
            db, user_id, agent.model_name,
            tokens_input, tokens_output, agent.id,
        )
    except InsufficientCreditsError:
        # Still save the message but warn user
        credits_used = 0
        yield json.dumps({
            "type": "error",
            "code": "insufficient_credits",
            "message": "Credits insufficient, please top up",
        })

    # Save assistant message
    await save_message(
        db, conversation_id, MessageRole.assistant, full_content,
        model_name=agent.model_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )

    # Update conversation title from first message
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv and conv.title == "New conversation":
        conv.title = user_content[:80]

    # Update agent last_active_at
    agent.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    # Refresh user balance
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "usage": {
            "credits_used": credits_used,
            "balance": user.credit_balance,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "model": agent.model_name,
        },
    })
