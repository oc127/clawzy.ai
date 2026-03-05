"""WebSocket 中继 — 后端 ↔ OpenClaw 容器双向转发。

后端只做三件事：
1. JWT 认证（在 chat.py 完成）
2. 消息持久化（拦截 user/assistant 消息存 DB）
3. 积分扣除（拦截 done 事件扣积分）

其余帧原样转发，让龙虾（OpenClaw）干活。
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import websockets
from websockets.exceptions import ConnectionClosed

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.chat import MessageRole
from app.services.chat_service import (
    get_or_create_conversation,
    save_message,
)
from app.services.credits_service import deduct_credits, InsufficientCreditsError
from app.services.fallback_service import get_fallback_reply
from app.i18n import DEFAULT_LOCALE

logger = logging.getLogger(__name__)

CONTAINER_CONNECT_TIMEOUT = 15  # 秒，等待容器就绪
CONTAINER_CONNECT_RETRY_INTERVAL = 1.0


async def connect_to_container(
    ws_port: int,
    gateway_token: str,
    timeout: float = CONTAINER_CONNECT_TIMEOUT,
) -> websockets.WebSocketClientProtocol:
    """连接到 OpenClaw 容器的 WebSocket，带重试（容器可能还在启动）。"""
    url = f"ws://127.0.0.1:{ws_port}"
    headers = {"Authorization": f"Bearer {gateway_token}"}
    deadline = asyncio.get_event_loop().time() + timeout

    last_error = None
    while asyncio.get_event_loop().time() < deadline:
        try:
            ws = await websockets.connect(
                url,
                additional_headers=headers,
                open_timeout=5,
                ping_interval=30,
                ping_timeout=10,
            )
            logger.info("Connected to OpenClaw container on port %d", ws_port)
            return ws
        except (OSError, ConnectionRefusedError, websockets.InvalidHandshake) as e:
            last_error = e
            await asyncio.sleep(CONTAINER_CONNECT_RETRY_INTERVAL)

    raise ConnectionError(
        f"Cannot connect to OpenClaw container on port {ws_port} "
        f"after {timeout}s: {last_error}"
    )


async def relay(
    client_ws,
    container_ws: websockets.WebSocketClientProtocol,
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str | None,
    locale: str = DEFAULT_LOCALE,
):
    """双向转发 + 消息拦截。

    - client_ws: 浏览器侧 FastAPI WebSocket
    - container_ws: OpenClaw 容器侧 websockets 连接
    """
    conv_id = conversation_id

    # 用于累积容器回复
    assistant_buffer = ""
    current_model = agent.model_name

    async def client_to_container():
        """浏览器 → 容器：拦截 message 存 DB，ping 本地处理，其余转发。"""
        nonlocal conv_id

        try:
            while True:
                raw = await asyncio.wait_for(client_ws.receive_text(), timeout=300)
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await client_ws.send_text(json.dumps({
                        "type": "error",
                        "code": "invalid_json",
                        "message": "Invalid JSON",
                    }))
                    continue

                msg_type = data.get("type")

                if msg_type == "ping":
                    await client_ws.send_text(json.dumps({"type": "pong"}))
                    continue

                if msg_type == "switch_model":
                    new_model = data.get("model", "").strip()
                    if new_model:
                        agent.model_name = new_model
                        await db.commit()
                        await client_ws.send_text(json.dumps({
                            "type": "model_switched",
                            "model": new_model,
                        }))
                    continue

                if msg_type == "message":
                    content = data.get("content", "").strip()
                    if not content:
                        continue

                    # 检查积分
                    from app.models.user import User
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one()
                    if user.credit_balance <= 0:
                        await client_ws.send_text(json.dumps({
                            "type": "error",
                            "code": "insufficient_credits",
                            "message": "No credits remaining",
                        }))
                        continue

                    # 确保有会话
                    if conv_id is None:
                        conv = await get_or_create_conversation(db, agent.id, None)
                        await db.commit()
                        conv_id = conv.id

                    # 存用户消息
                    await save_message(db, conv_id, MessageRole.user, content)
                    await db.commit()

                    # 转发给容器
                    await container_ws.send(json.dumps({
                        "type": "message",
                        "content": content,
                        "conversation_id": conv_id,
                    }))
                    continue

                # 其他消息类型直接转发
                await container_ws.send(raw)

        except asyncio.TimeoutError:
            logger.info("Client WebSocket idle timeout: user=%s agent=%s", user_id, agent.id)
        except Exception:
            pass  # 连接关闭由外层处理

    async def container_to_client():
        """容器 → 浏览器：拦截 stream 累积内容，done 时存 DB + 扣积分。"""
        nonlocal assistant_buffer, conv_id

        try:
            async for raw in container_ws:
                try:
                    data = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    # 非 JSON 帧直接转发
                    await client_ws.send_text(str(raw))
                    continue

                msg_type = data.get("type")

                if msg_type == "stream":
                    content = data.get("content", "")
                    assistant_buffer += content
                    await client_ws.send_text(raw if isinstance(raw, str) else json.dumps(data))

                elif msg_type == "done":
                    # 存助手消息
                    if conv_id and assistant_buffer:
                        usage = data.get("usage", {})
                        tokens_in = usage.get("tokens_input") or usage.get("prompt_tokens", 0)
                        tokens_out = usage.get("tokens_output") or usage.get("completion_tokens", 0)
                        model_used = usage.get("model", agent.model_name)

                        # 扣积分
                        credits_used = 0
                        try:
                            credits_used = await deduct_credits(
                                db, user_id, model_used,
                                tokens_in, tokens_out, agent.id,
                            )
                        except InsufficientCreditsError:
                            pass

                        await save_message(
                            db, conv_id, MessageRole.assistant, assistant_buffer,
                            model_name=model_used,
                            tokens_input=tokens_in,
                            tokens_output=tokens_out,
                            credits_used=credits_used,
                        )

                        # 更新对话标题 & agent 活跃时间
                        from app.models.chat import Conversation
                        result = await db.execute(
                            select(Conversation).where(Conversation.id == conv_id)
                        )
                        conv = result.scalar_one_or_none()
                        if conv and conv.title == "New conversation":
                            conv.title = assistant_buffer[:80]

                        agent.last_active_at = datetime.now(timezone.utc)
                        await db.commit()

                        # 查余额，注入到 done 事件
                        from app.models.user import User
                        result = await db.execute(select(User).where(User.id == user_id))
                        user = result.scalar_one()

                        data["conversation_id"] = conv_id
                        data.setdefault("usage", {})
                        data["usage"]["credits_used"] = credits_used
                        data["usage"]["balance"] = user.credit_balance

                    # 重置缓冲区
                    assistant_buffer = ""
                    await client_ws.send_text(json.dumps(data))

                else:
                    # error 或其他类型，直接转发
                    await client_ws.send_text(raw if isinstance(raw, str) else json.dumps(data))

        except ConnectionClosed:
            logger.info("Container WebSocket closed: agent=%s", agent.id)

    # 并行运行两个方向的转发
    client_task = asyncio.create_task(client_to_container())
    container_task = asyncio.create_task(container_to_client())

    try:
        done, pending = await asyncio.wait(
            [client_task, container_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        # 取消另一个方向
        for task in pending:
            task.cancel()
    finally:
        # 确保容器连接关闭
        try:
            await container_ws.close()
        except Exception:
            pass
