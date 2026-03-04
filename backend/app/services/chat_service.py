"""Chat service — 带自动修复的 LLM 流式对话。

自愈层级：
1. 临时错误（超时、429、5xx）→ 重试 2 次，指数退避
2. 主模型持续失败 → 熔断器打开 → 自动切备用模型
3. 所有模型都挂 → 友好的客服 fallback 回复（不扣积分）
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.circuit_breaker import circuit_breaker
from app.core.model_fallback import get_fallback_models
from app.models.agent import Agent
from app.models.chat import Conversation, Message, MessageRole
from app.services.credits_service import deduct_credits, InsufficientCreditsError
from app.services.fallback_service import get_fallback_reply
from app.i18n import t, DEFAULT_LOCALE

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 1.0


# ------------------------------------------------------------------ #
#  对话管理（不变）
# ------------------------------------------------------------------ #

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


# ------------------------------------------------------------------ #
#  Fallback 客服回复
# ------------------------------------------------------------------ #

async def _send_fallback_reply(
    db: AsyncSession,
    conversation_id: str,
    error_type: str,
    locale: str = DEFAULT_LOCALE,
):
    """当所有模型都不可用时，发送友好的 fallback 回复（不扣积分）。"""
    reply = get_fallback_reply(error_type, locale=locale)

    await save_message(
        db, conversation_id, MessageRole.assistant, reply,
        model_name="fallback",
        credits_used=0,
    )
    await db.commit()

    yield json.dumps({"type": "stream", "content": reply})
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "usage": {
            "credits_used": 0,
            "balance": None,
            "model": "fallback",
        },
        "is_fallback": True,
    })


# ------------------------------------------------------------------ #
#  LiteLLM 调用（带重试）
# ------------------------------------------------------------------ #

async def _call_litellm_with_retry(
    model_name: str,
    history: list[dict],
    max_retries: int = MAX_RETRIES,
) -> tuple[str, int, int, str | None]:
    """尝试调用 LiteLLM，临时错误自动重试。

    Returns: (full_content, tokens_input, tokens_output, error_type_or_none)
    error_type 非 None 表示最终失败。
    """
    url = f"{settings.litellm_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": history,
        "max_tokens": 4096,
        "stream": True,
    }

    last_error_type = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.info("Retry %d/%d for model %s after %.1fs", attempt, max_retries, model_name, delay)
            await asyncio.sleep(delay)

        try:
            full_content = ""
            tokens_input = 0
            tokens_output = 0

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 429:
                        last_error_type = "rate_limited"
                        logger.warning("Model %s rate limited (attempt %d)", model_name, attempt + 1)
                        continue

                    if response.status_code >= 500:
                        last_error_type = "model_error"
                        body = await response.aread()
                        logger.warning("Model %s server error %d (attempt %d): %s",
                                       model_name, response.status_code, attempt + 1, body[:200])
                        continue

                    if response.status_code != 200:
                        body = await response.aread()
                        logger.error("Model %s client error %d: %s", model_name, response.status_code, body[:200])
                        return "", 0, 0, "model_error"

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

                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                full_content += content

                        usage = chunk.get("usage")
                        if usage:
                            tokens_input = usage.get("prompt_tokens", 0)
                            tokens_output = usage.get("completion_tokens", 0)

            if not full_content:
                last_error_type = "empty_response"
                continue

            return full_content, tokens_input, tokens_output, None

        except httpx.TimeoutException:
            last_error_type = "timeout"
            logger.warning("Model %s timeout (attempt %d)", model_name, attempt + 1)
            continue

        except httpx.ConnectError:
            last_error_type = "connection_error"
            logger.error("Cannot connect to LiteLLM for model %s (attempt %d)", model_name, attempt + 1)
            continue

        except Exception:
            last_error_type = "model_error"
            logger.exception("Unexpected error calling model %s (attempt %d)", model_name, attempt + 1)
            continue

    return "", 0, 0, last_error_type


# ------------------------------------------------------------------ #
#  主入口：带自愈的流式聊天
# ------------------------------------------------------------------ #

async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
    locale: str = DEFAULT_LOCALE,
):
    """
    流式聊天 + 自动修复：
    1. 检查主模型熔断状态
    2. 临时错误重试 2 次
    3. 主模型失败 → 尝试备用模型链
    4. 全部失败 → 客服 fallback 回复
    """
    await save_message(db, conversation_id, MessageRole.user, user_content)
    await db.commit()

    history = await get_conversation_history(db, conversation_id)

    # 构建模型尝试链：主模型 + 备用模型
    models_to_try = [agent.model_name] + get_fallback_models(agent.model_name)

    actual_model_used = None
    full_content = ""
    tokens_input = 0
    tokens_output = 0

    for model_name in models_to_try:
        # 检查熔断器
        if not await circuit_breaker.can_request(model_name):
            logger.info("Circuit breaker OPEN for %s, skipping", model_name)
            continue

        # 带重试的调用
        content, t_in, t_out, error_type = await _call_litellm_with_retry(model_name, history)

        if error_type is None:
            await circuit_breaker.record_success(model_name)
            actual_model_used = model_name
            full_content = content
            tokens_input = t_in
            tokens_output = t_out
            break
        else:
            await circuit_breaker.record_failure(model_name)
            logger.warning("Model %s failed (%s), trying next fallback...", model_name, error_type)
            continue

    # 全部失败 → 客服回复
    if actual_model_used is None:
        async for event in _send_fallback_reply(db, conversation_id, "model_error", locale=locale):
            yield event
        return

    # 成功 → 流式发送内容
    yield json.dumps({"type": "stream", "content": full_content})

    # 如果用了备用模型，告诉用户
    used_fallback = actual_model_used != agent.model_name
    if used_fallback:
        notice = "\n\n" + t("chat.backupModelNotice", locale)
        yield json.dumps({"type": "stream", "content": notice})
        full_content += notice
        yield json.dumps({"type": "model_switched", "content": actual_model_used, "is_fallback": True})

    # 估算 token 数
    if tokens_input == 0:
        tokens_input = len(str(history)) // 4
    if tokens_output == 0:
        tokens_output = len(full_content) // 4

    # 扣积分
    try:
        credits_used = await deduct_credits(
            db, user_id, actual_model_used,
            tokens_input, tokens_output, agent.id,
        )
    except InsufficientCreditsError:
        credits_used = 0
        credits_msg = get_fallback_reply("insufficient_credits", locale=locale)
        yield json.dumps({
            "type": "stream",
            "content": "\n\n---\n" + credits_msg,
        })
        full_content += "\n\n---\n" + credits_msg

    # 保存 assistant 消息
    await save_message(
        db, conversation_id, MessageRole.assistant, full_content,
        model_name=actual_model_used,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )

    # 更新对话标题
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv and conv.title == "New conversation":
        conv.title = user_content[:80]

    # 更新 agent 最后活跃时间
    agent.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    # 查余额
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
            "model": actual_model_used,
        },
    })
