"""Chat service — streams LLM responses via OpenClaw -> LiteLLM fallback.

Supports:
- Dual-channel routing (OpenClaw primary, LiteLLM fallback)
- Long-term memory injection and extraction
- Tool calling with iterative execution loop
"""

import asyncio
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

# Minimum credits required to start a request.
# Set to 50 to prevent overdraft: a single conversation turn can easily cost
# 50+ credits, so we reject the call up-front if the user can't cover at least
# one small turn.  Without this guard a user with 1 credit could receive a full
# response before the post-completion deduction discovers the shortfall.
_MIN_CREDITS_GUARD = 50

# How long to wait for OpenClaw to accept the connection before falling back
_OPENCLAW_CONNECT_TIMEOUT = 5.0

# Maximum tool-call iterations to prevent infinite loops
_MAX_TOOL_ITERATIONS = 10


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


async def _non_streaming_completion(
    url: str,
    headers: dict,
    payload: dict,
    timeout: httpx.Timeout,
) -> dict | None:
    """Make a non-streaming LLM call (used for tool-loop iterations)."""
    payload_copy = {**payload, "stream": False}
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload_copy)
            if resp.status_code != 200:
                logger.error("Non-streaming LLM error %s: %s", resp.status_code, resp.text[:500])
                return None
            return resp.json()
        except Exception as exc:
            logger.error("Non-streaming LLM call failed: %s", exc)
            return None


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

    Supports tool calling: if the model returns tool_calls, they are executed
    and the results fed back in a loop (max 10 iterations).

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "tool_call", "tool": "...", "arguments": {...}}
      {"type": "tool_result", "tool": "...", "result": "..."}
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

    # ── 3a. Inject Lucy personality (highest priority) ─────────────────────
    from app.services.personality_engine import build_lucy_system_prompt
    system_prompt = build_lucy_system_prompt(
        base_system_prompt=agent.system_prompt or None,
        user_name=None,
    )

    # ── 3b. Inject memory context ───────────────────────────────────────────
    if agent.memory_enabled:
        try:
            from app.services.memory_service import get_memory_context
            memory_ctx = await get_memory_context(db, agent.id)
            if memory_ctx:
                system_prompt = f"{system_prompt}\n\n{memory_ctx}" if system_prompt else memory_ctx
        except Exception as exc:
            logger.warning("Failed to load memory context for agent %s: %s", agent.id, exc)

    # ── 3c. Inject relevant skills ──────────────────────
    try:
        from app.services.skill_service import inject_skills_to_prompt
        system_prompt = await inject_skills_to_prompt(db, agent.id, user_content, system_prompt)
    except Exception as exc:
        logger.warning("Failed to inject skills for agent %s: %s", agent.id, exc)

    if system_prompt:
        history = [{"role": "system", "content": system_prompt}] + history

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
    elif getattr(agent, "adaptive_depth", False):
        from app.services.reasoning_depth_service import select_adaptive_model
        model_to_use, depth_level = select_adaptive_model(agent.model_name, user_content or "")
        logger.info("Adaptive depth: %s → %s", depth_level, model_to_use)
    else:
        model_to_use = agent.model_name

    # ── 3b. Load enabled tools ──────────────────────────────────────────────
    tools_definitions = []
    try:
        from app.services.tool_service import get_enabled_tools
        tools_definitions = await get_enabled_tools(db, agent.id)
    except Exception as exc:
        logger.warning("Failed to load tools for agent %s: %s", agent.id, exc)

    # ── 4. Dual-channel routing ─────────────────────────────────────────────
    # OpenClaw and LiteLLM use different auth tokens.
    openclaw_headers = {
        "Authorization": f"Bearer {settings.openclaw_gateway_token}",
        "Content-Type": "application/json",
    }
    litellm_headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_to_use,
        "messages": history,
        "max_tokens": 8192,
        "stream": True,
    }

    # Include tools in payload if any are enabled
    if tools_definitions:
        payload["tools"] = tools_definitions

    openclaw_url = _build_openclaw_url()
    litellm_url = _build_litellm_url()

    # --- Attempt to connect to OpenClaw with a short connect timeout.
    openclaw_timeout = httpx.Timeout(
        connect=_OPENCLAW_CONNECT_TIMEOUT,
        read=120.0,
        write=30.0,
        pool=5.0,
    )
    litellm_timeout = httpx.Timeout(120.0)

    active_url = openclaw_url
    active_headers = openclaw_headers
    active_timeout = openclaw_timeout
    using_fallback = False

    # Try to establish the OpenClaw connection
    _probe_client = httpx.AsyncClient(timeout=openclaw_timeout)
    _stream_ctx = _probe_client.stream("POST", openclaw_url, headers=openclaw_headers, json=payload)
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
        active_headers = litellm_headers
        active_timeout = litellm_timeout
        _probe_client = httpx.AsyncClient(timeout=litellm_timeout)
        _stream_ctx = _probe_client.stream("POST", litellm_url, headers=litellm_headers, json=payload)
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
    tool_calls_buffer: list[dict] = []

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

                # Accumulate tool calls from streaming deltas
                tc_deltas = delta.get("tool_calls", [])
                for tc_delta in tc_deltas:
                    idx = tc_delta.get("index", 0)
                    while len(tool_calls_buffer) <= idx:
                        tool_calls_buffer.append({"id": "", "function": {"name": "", "arguments": ""}})
                    if "id" in tc_delta and tc_delta["id"]:
                        tool_calls_buffer[idx]["id"] = tc_delta["id"]
                    fn = tc_delta.get("function", {})
                    if "name" in fn and fn["name"]:
                        tool_calls_buffer[idx]["function"]["name"] = fn["name"]
                    if "arguments" in fn:
                        tool_calls_buffer[idx]["function"]["arguments"] += fn["arguments"]

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

    # ── 5b. Tool loop — execute tool calls and re-call LLM ─────────────────
    if tool_calls_buffer and tools_definitions:
        from app.services.tool_service import execute_tool

        # Add the assistant message with tool_calls to history
        assistant_msg_with_tools = {"role": "assistant", "content": full_content or None}
        assistant_msg_with_tools["tool_calls"] = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                },
            }
            for tc in tool_calls_buffer
        ]
        history.append(assistant_msg_with_tools)

        for iteration in range(_MAX_TOOL_ITERATIONS):
            # Execute each tool call
            for tc in tool_calls_buffer:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                yield json.dumps({
                    "type": "tool_call",
                    "tool": fn_name,
                    "arguments": fn_args,
                })

                try:
                    tool_result = await execute_tool(
                        agent_id=agent.id,
                        container_id=agent.container_id,
                        tool_name=fn_name,
                        arguments=fn_args,
                    )
                except Exception as texc:
                    tool_result = f"Tool execution error: {texc}"

                yield json.dumps({
                    "type": "tool_result",
                    "tool": fn_name,
                    "result": tool_result[:2000],
                })

                # Append tool result to history
                history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result[:4000],
                })

            # Re-call LLM with tool results (non-streaming for intermediate calls)
            tool_payload = {
                "model": model_to_use,
                "messages": history,
                "max_tokens": 8192,
                "tools": tools_definitions,
            }

            llm_result = await _non_streaming_completion(
                active_url, active_headers, tool_payload, active_timeout,
            )

            if llm_result is None:
                yield json.dumps({
                    "type": "error",
                    "code": "tool_loop_error",
                    "message": "LLM call failed during tool loop",
                })
                break

            choice = llm_result.get("choices", [{}])[0]
            msg = choice.get("message", {})

            # Track token usage from tool loop
            loop_usage = llm_result.get("usage", {})
            tokens_input += loop_usage.get("prompt_tokens", 0)
            tokens_output += loop_usage.get("completion_tokens", 0)

            new_tool_calls = msg.get("tool_calls", [])
            new_content = msg.get("content", "")

            if new_content:
                full_content += new_content
                yield json.dumps({"type": "stream", "content": new_content})

            if new_tool_calls:
                # More tool calls — add to history and continue loop
                history.append(msg)
                tool_calls_buffer = [
                    {
                        "id": tc["id"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                                if isinstance(tc["function"]["arguments"], str)
                                else json.dumps(tc["function"]["arguments"]),
                        },
                    }
                    for tc in new_tool_calls
                ]
            else:
                # No more tool calls — done
                break

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

    # ── 7b. Fire-and-forget memory extraction ──────────────────────────────
    if agent.memory_enabled and full_content:
        try:
            from app.services.memory_service import extract_memories
            # Use asyncio.create_task for fire-and-forget
            # We need a fresh db session since the current one may be closed
            from app.core.database import async_session

            async def _extract_bg():
                try:
                    async with async_session() as bg_db:
                        await extract_memories(
                            bg_db, agent.id, conversation_id,
                            user_content, full_content,
                        )
                except Exception as exc:
                    logger.warning("Background memory extraction failed: %s", exc)

            asyncio.create_task(_extract_bg())
        except Exception as exc:
            logger.warning("Failed to schedule memory extraction: %s", exc)

    # ── 7c. Fire-and-forget skill auto-extraction ──────────────────────────
    if full_content:
        try:
            from app.services.skill_service import auto_extract_skill
            from app.core.database import async_session

            _skill_messages = [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": full_content},
            ]
            _skill_agent_id = agent.id

            async def _skill_extract_bg():
                try:
                    async with async_session() as bg_db:
                        await auto_extract_skill(bg_db, _skill_agent_id, _skill_messages)
                except Exception as exc:
                    logger.warning("Background skill extraction failed: %s", exc)

            asyncio.create_task(_skill_extract_bg())
        except Exception as exc:
            logger.warning("Failed to schedule skill extraction: %s", exc)

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
            "model": model_to_use,
        },
    })
