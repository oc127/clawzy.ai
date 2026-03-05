"""Chat service — 消息持久化与会话管理。

聊天流式对话现在由 OpenClaw 容器处理（通过 ws_relay 中继）。
此模块保留会话管理和消息持久化函数，供中继层调用。
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


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


