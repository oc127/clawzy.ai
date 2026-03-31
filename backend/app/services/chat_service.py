"""Chat service — streams LLM responses via OpenClaw → LiteLLM fallback."""

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

# How long to wait for OpenClaw to accept the connection before falling back
_OPENCLAW_CONNECT_TIMEOUT = 5.0


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


def _build_litellm_url() -> str:
    """Return the LiteLLM chat completions endpoint."""
    return f"{settings.litellm_url}/v1/chat/completions"


def _build_openclaw_url() -> str:
    """Return the OpenClaw chat completions endpoint."""
    return f"{settings.openclaw_url}/v1/chat/completions"


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
    images: list[str] | None = None,
):
    """
    Stream a chat completion through OpenClaw with automatic LiteLLM fallback.

    Primary channel:  OpenClaw  (http://clawzy-openclaw:18789/v1/chat/completions)
    Fallback channel: LiteLLM   (http://litellm:4000/v1/chat/completions)

    If OpenClaw is unreachable or times out on connect (5 s), the request is
    transparently retried against LiteLLM.  The fallback is logged at WARNING
    level as "[FALLBACK] OpenClaw unreachable, using LiteLLM directly".

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

    if agent.system_prompt:
        history = [{"role": "system", "content": agent.system_prompt}] + history

    if images:
        model_to_use = "qwen-vl-plus"
        content_parts: list = []
        if user_content:
            content_parts.append({"type": "text", "text": user_content})
        for img_url in images:
            content_parts.append({"type": "image_url", "image_url": {"url": img_url}})
        if history and history[-1]["role"] == "user":
            history[-1]["content"] = content_parts
        else:
            history.append({"role": "user", "content": content_parts})
    else:
        model_to_use = agent.model_name

    # ── 4. Dual-channel routing ─────────────────────────────────────────────
    # Build both endpoint configs.  Both use the LiteLLM master key — OpenClaw
    # proxies requests through to LiteLLM so the same key is accepted on both.
    shared_headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_to_use,
        "messages": history,
        "max_tokens": 8192,
        "stream": True,
    }

    openclaw_url = _build_openclaw_url()
    litellm_url = _build_litellm_url()

    # --- Attempt to connect to OpenClaw with a short connect timeout.
    # httpx establishes the TCP connection (and sends the request) when we
    # enter the stream() context manager.  Any ConnectError / TimeoutException
    # raised at that point means OpenClaw is down — switch to LiteLLM before
    # yielding a single byte to the client.
    openclaw_timeout = httpx.Timeout(
        connect=_OPENCLAW_CONNECT_TIMEOUT,
        read=120.0,
        write=30.0,
        pool=5.0,
    )
    litellm_timeout = httpx.Timeout(120.0)

    active_url = openclaw_url
    active_timeout = openclaw_timeout
    using_fallback = False

    # Try to establish the OpenClaw connection
    _probe_client = httpx.AsyncClient(timeout=openclaw_timeout)
    _stream_ctx = _probe_client.stream("POST", openclaw_url, headers=shared_headers, json=payload)
    try:
        _response = await _stream_ctx.__aenter__()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        # OpenClaw unreachable — clean up and switch to LiteLLM
        await _probe_client.aclose()
        logger.warning(
            "[FALLBACK] OpenClaw unreachable (%s), using LiteLLM directly", exc
        )
        using_fallback = True
        active_url = litellm_url
        active_timeout = litellm_timeout
        _probe_client = httpx.AsyncClient(timeout=litellm_timeout)
        _stream_ctx = _probe_client.stream("POST", litellm_url, headers=shared_headers, json=payload)
        try:
            _response = await _stream_ctx.__aenter__()
        except (httpx.ConnectError, httpx.TimeoutException):
            await _probe_client.aclose()
            yield json.dumps({
                "type": "error",
                "code": "connection_error",
                "message": "Cannot connect to model service",
            })
            return

    # ── 5. Stream from the active backend ──────────────────────────────────
    full_content = ""
    tokens_input = 0
    tokens_output = 0

    try:
        if _response.status_code != 200:
            body = await _response.aread()
            backend = "LiteLLM" if using_fallback else "OpenClaw"
            logger.error("%s error %s: %s", backend, _response.status_code, body)
            yield json.dumps({
                "type": "error",
                "code": "model_error",
                "message": f"Model returned HTTP {_response.status_code}",
            })
            return

        async for line in _response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    full_content += content
                    yield json.dumps({"type": "stream", "content": content})

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
    finally:
        await _stream_ctx.__aexit__(None, None, None)
        await _probe_client.aclose()

    if not full_content:
        yield json.dumps({
            "type": "error",
            "code": "empty_response",
            "message": "Model returned empty response",
        })
        return

    if tokens_input == 0:
        tokens_input = len(str(history)) // 4
    if tokens_output == 0:
        tokens_output = len(full_content) // 4

    # ── 6. Deduct credits (post-completion) ────────────────────────────────
    credits_used = 0
    try:
        credits_used = await deduct_credits(
            db, user_id, agent.model_name,
            tokens_input, tokens_output, agent.id,
        )
    except InsufficientCreditsError:
        yield json.dumps({
            "type": "error",
            "code": "insufficient_credits",
            "message": "Credits insufficient after response, please top up",
        })

    # ── 7. Persist assistant message ────────────────────────────────────────
    await save_message(
        db, conversation_id, MessageRole.assistant, full_content,
        model_name=agent.model_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )

    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv and conv.title == "New conversation":
        conv.title = user_content[:80]

    agent.last_active_at = datetime.now(timezone.utc)
    await db.commit()

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
