"""WebSocket 中继 — 后端 ↔ OpenClaw 容器双向转发。

后端只做三件事：
1. JWT 认证（在 chat.py 完成）
2. 消息持久化（拦截 user/assistant 消息存 DB）
3. 积分扣除（拦截 done 事件，通过 Redis 去重扣积分）

扣费优先级：LiteLLM callback（精确）> ws_relay（兜底）。
两者通过 Redis SETNX 去重，保证同一 call_id 只扣一次。
"""

import asyncio
import collections
import json
import logging
import time
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
from app.api.v1.usage_callback import try_dedup_charge
from app.services.fallback_service import get_fallback_reply
from app.i18n import DEFAULT_LOCALE

logger = logging.getLogger(__name__)

CONTAINER_CONNECT_TIMEOUT = 15  # 秒，等待容器就绪
CONTAINER_CONNECT_RETRY_INTERVAL = 1.0
WS_MSG_RATE_LIMIT = 30  # 每用户每分钟最大消息数
WS_RATE_WINDOW = 60  # 滑动窗口（秒）
MAX_RELAY_RECONNECTS = 2  # 中继断开后最大自动重连次数


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
        msg_timestamps: collections.deque[float] = collections.deque()

        try:
            while True:
                raw = await asyncio.wait_for(client_ws.receive_text(), timeout=300)

                # 消息级限流：滑动窗口
                now = time.monotonic()
                while msg_timestamps and now - msg_timestamps[0] > WS_RATE_WINDOW:
                    msg_timestamps.popleft()
                if len(msg_timestamps) >= WS_MSG_RATE_LIMIT:
                    await client_ws.send_text(json.dumps({
                        "type": "error",
                        "code": "rate_limited",
                        "message": "Too many messages, please slow down",
                    }))
                    continue
                msg_timestamps.append(now)

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
                        call_id = (
                            usage.get("call_id")
                            or usage.get("litellm_call_id")
                            or data.get("call_id", "")
                        )

                        # 去重扣积分：如果 LiteLLM callback 已扣过则跳过
                        credits_used = 0
                        if call_id:
                            result_charge = await try_dedup_charge(
                                call_id, user_id, model_used,
                                tokens_in, tokens_out, agent.id,
                            )
                            if result_charge is not None:
                                credits_used = result_charge
                        else:
                            # 无 call_id 降级到直接扣费
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
            raise  # Propagate to outer loop for reconnection

    # 带自动重连的中继循环
    reconnect_count = 0

    while True:
        client_task = asyncio.create_task(client_to_container())
        container_task = asyncio.create_task(container_to_client())

        done_tasks, pending = await asyncio.wait(
            [client_task, container_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

        # Check if container side died (not client side)
        container_died = container_task in done_tasks
        client_died = client_task in done_tasks

        if client_died or not container_died:
            # Client disconnected or both done — normal exit
            break

        if reconnect_count >= MAX_RELAY_RECONNECTS:
            break

        reconnect_count += 1
        logger.warning(
            "Container WebSocket dropped during relay (agent=%s), "
            "attempting reconnect %d/%d",
            agent.id, reconnect_count, MAX_RELAY_RECONNECTS,
        )

        # Notify client
        try:
            await client_ws.send_text(json.dumps({
                "type": "agent_status",
                "status": "reconnecting",
                "content": "Agent connection lost, reconnecting...",
            }))
        except Exception:
            break  # Client also gone

        # Close old container ws
        try:
            await container_ws.close()
        except Exception:
            pass

        # Exponential backoff: 1s, 2s
        await asyncio.sleep(1.0 * reconnect_count)

        # Attempt to reconnect to container
        try:
            from app.config import settings as _settings
            gateway_token = agent.gateway_token or _settings.litellm_master_key
            container_ws = await connect_to_container(
                agent.ws_port, gateway_token,
            )

            await client_ws.send_text(json.dumps({
                "type": "reconnected",
                "content": "Connection restored",
            }))
            logger.info("Reconnected to container for agent=%s", agent.id)
            continue  # Restart relay loop
        except ConnectionError:
            logger.error(
                "Failed to reconnect to container for agent=%s", agent.id,
            )
            try:
                await client_ws.send_text(json.dumps({
                    "type": "error",
                    "code": "container_unreachable",
                    "message": "Cannot reconnect to agent container",
                }))
            except Exception:
                pass
            break

    # 确保容器连接关闭
    try:
        await container_ws.close()
    except Exception:
        pass
