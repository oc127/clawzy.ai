"""Chat service — streams LLM responses via OpenClaw and manages conversations."""

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent import Agent
from app.models.chat import Conversation, Message, MessageRole
from app.services.credits_service import (
    deduct_credits,
    calculate_credits,
    InsufficientCreditsError,
)

logger = logging.getLogger(__name__)

# Minimum credits required to start a request (rough guard against zero-balance calls)
_MIN_CREDITS_GUARD = 1


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
    db: AsyncSession, conversation_id: str, limit: int = 100
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


def _build_openclaw_url(agent: Agent) -> str:
    """
    Resolve the OpenClaw HTTP endpoint to use for this agent.

    If the agent has its own running container with a ws_port, route to that
    dedicated instance. Otherwise fall back to the shared gateway.
    """
    from app.models.agent import AgentStatus

    if agent.status == AgentStatus.running and agent.ws_port:
        # Dedicated per-agent container (port mapped on host)
        return f"http://127.0.0.1:{agent.ws_port}"
    # Shared default gateway
    return settings.openclaw_url


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
    images: list[str] | None = None,
):
    """
    Stream a chat completion through OpenClaw (which proxies to LiteLLM).

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {"credits": N, "balance": M}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    # ── 1. Pre-flight credit check ──────────────────────────────────────────
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if user.credit_balance < _MIN_CREDITS_GUARD:
        yield json.dumps({
            "type": "error",
            "code": "insufficient_credits",
            "message": "Insufficient credits. Please top up to continue.",
        })
        return

    # ── 2. Save user message ────────────────────────────────────────────────
    await save_message(db, conversation_id, MessageRole.user, user_content or "[image]")
    await db.commit()

    # ── 3. Build message history ────────────────────────────────────────────
    history = await get_conversation_history(db, conversation_id)

    # Inject agent system prompt as the first message if present
    if agent.system_prompt:
        history = [{"role": "system", "content": agent.system_prompt}] + history

    # If images attached, replace last user message with multimodal content
    if images:
        model_to_use = "qwen-vl-plus"  # vision-capable model
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

    # ── 4. Route through OpenClaw ───────────────────────────────────────────
    openclaw_base = _build_openclaw_url(agent)
    url = f"{openclaw_base}/v1/chat/completions"
    # Per-agent containers have their own gateway token stored in agent.config
    gateway_token = (
        (agent.config or {}).get("gateway_token") or settings.openclaw_gateway_token
    )
    headers = {
        "Authorization": f"Bearer {gateway_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_to_use,
        "messages": history,
        "max_tokens": 8192,
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
                    logger.error("OpenClaw error %s: %s", response.status_code, body)
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
        tokens_input = len(str(history)) // 4
    if tokens_output == 0:
        tokens_output = len(full_content) // 4

    # ── 5. Deduct credits (post-completion) ────────────────────────────────
    credits_used = 0
    try:
        credits_used = await deduct_credits(
            db, user_id, agent.model_name,
            tokens_input, tokens_output, agent.id,
        )
    except InsufficientCreditsError:
        # Balance may have dropped during a long stream; warn but don't block
        yield json.dumps({
            "type": "error",
            "code": "insufficient_credits",
            "message": "Credits insufficient after response, please top up",
        })

    # ── 6. Persist assistant message ────────────────────────────────────────
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
