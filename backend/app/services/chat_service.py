"""Chat service — streams LLM responses via LiteLLM and manages conversations.

当模型不可用时，自动切换到 fallback 客服模式，用友好的预设回复代替冷冰冰的错误。
"""

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
from app.services.fallback_service import get_fallback_reply

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


async def _send_fallback_reply(
    db: AsyncSession,
    conversation_id: str,
    error_type: str,
):
    """当模型不可用时，发送友好的 fallback 回复（不扣积分）。

    龙虾不是"报错"，而是像客服一样告诉用户情况。
    """
    reply = get_fallback_reply(error_type)

    # 保存 fallback 回复到对话历史（标记为 system 回复，不扣积分）
    await save_message(
        db, conversation_id, MessageRole.assistant, reply,
        model_name="fallback",  # 标记为 fallback，不是真实模型
        credits_used=0,
    )
    await db.commit()

    # 先流式发送 fallback 内容，让用户看到"龙虾在说话"而不是一个错误弹窗
    yield json.dumps({"type": "stream", "content": reply})
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "usage": {
            "credits_used": 0,
            "balance": None,  # 前端会处理 null
            "model": "fallback",
        },
        "is_fallback": True,  # 告诉前端这是 fallback 回复
    })


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
):
    """
    Stream a chat completion from LiteLLM.

    当模型不可用时自动降级到 fallback 客服模式：
    - 超时 → 友好提示 + 不扣积分
    - 连接失败 → 友好提示 + 不扣积分
    - 空回复 → 友好提示 + 不扣积分
    - 积分不足 → 友好提示引导充值

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {...}, "conversation_id": "..."}
    """
    # Save user message
    await save_message(db, conversation_id, MessageRole.user, user_content)
    await db.commit()

    # Build message history for context
    history = await get_conversation_history(db, conversation_id)

    # Call LiteLLM streaming endpoint
    url = f"{settings.litellm_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": agent.model_name,
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
                    # 降级到 fallback 客服模式
                    async for event in _send_fallback_reply(db, conversation_id, "model_error"):
                        yield event
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
        logger.warning("LiteLLM timeout for agent %s", agent.id)
        async for event in _send_fallback_reply(db, conversation_id, "timeout"):
            yield event
        return

    except httpx.ConnectError:
        logger.error("Cannot connect to LiteLLM for agent %s", agent.id)
        async for event in _send_fallback_reply(db, conversation_id, "connection_error"):
            yield event
        return

    except Exception:
        logger.exception("Unexpected error in stream_chat_completion")
        async for event in _send_fallback_reply(db, conversation_id, "model_error"):
            yield event
        return

    if not full_content:
        async for event in _send_fallback_reply(db, conversation_id, "empty_response"):
            yield event
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
        # 已经产生了回复，保存但用 fallback 友好提示
        credits_used = 0
        # 仍然保存回复内容，但额外发一条 fallback 提示
        yield json.dumps({
            "type": "stream",
            "content": "\n\n---\n" + get_fallback_reply("insufficient_credits"),
        })
        full_content += "\n\n---\n" + get_fallback_reply("insufficient_credits")

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
