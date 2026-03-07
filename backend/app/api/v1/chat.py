import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session
from app.core.security import decode_token
from app.core.ws_relay import connect_to_container, relay
from app.deps import get_current_user
from app.i18n import parse_locale
from app.models.agent import AgentStatus
from app.models.user import User
from app.models.chat import Conversation, Message
from app.schemas.chat import ConversationResponse, MessageResponse
from app.services.agent_service import get_agent, start_agent
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# --------------------------------------------------------------------------- #
#  WebSocket — real-time chat (via OpenClaw container relay)
# --------------------------------------------------------------------------- #

@router.websocket("/ws/chat/{agent_id}")
async def ws_chat(websocket: WebSocket, agent_id: str):
    """
    WebSocket chat endpoint — 认证后直连 OpenClaw 容器。

    Connection: ws://host/api/v1/ws/chat/{agent_id}?token=<JWT>

    Client sends:
      {"type": "message", "content": "hello", "conversation_id": "optional-uuid"}
      {"type": "switch_model", "model": "claude-sonnet"}
      {"type": "ping"}

    Server sends (from OpenClaw container, with credits/persistence injected):
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {...}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    # --- 1. JWT 认证 ---
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]

    # --- 2. 验证用户和 Agent 所有权 ---
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            await websocket.close(code=4001, reason="User not found")
            return

        agent = await get_agent(db, agent_id, user_id)
        if agent is None:
            await websocket.close(code=4004, reason="Agent not found")
            return

        # --- 3. 自动唤醒龙虾（启动容器）---
        # Verify container is actually alive, not just DB status
        needs_start = agent.status != AgentStatus.running or not agent.container_id
        if not needs_start and agent.container_id:
            from app.core.docker_manager import docker_manager
            actual_status = docker_manager.get_container_status(agent.container_id)
            if actual_status != "running":
                logger.warning(
                    "Agent %s DB says running but container is %s, restarting",
                    agent_id, actual_status,
                )
                needs_start = True

        if needs_start:
            try:
                await websocket.accept()
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "agent_starting",
                }))
                agent = await start_agent(db, agent)
            except Exception as e:
                logger.exception("Failed to start agent %s", agent_id)
                # 如果还没 accept，先 accept 再发错误
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "code": "agent_start_failed",
                        "message": str(e),
                    }))
                except Exception:
                    pass
                await websocket.close(code=4003, reason="Agent start failed")
                return
            accepted = True
        else:
            accepted = False

        if not accepted:
            await websocket.accept()

        # --- 4. 连接到 OpenClaw 容器 ---
        gateway_token = agent.gateway_token or settings.litellm_master_key
        try:
            container_ws = await connect_to_container(agent.ws_port, gateway_token)
        except ConnectionError as e:
            logger.error("Cannot reach OpenClaw container: %s", e)
            await websocket.send_text(json.dumps({
                "type": "error",
                "code": "container_unreachable",
                "message": "Cannot connect to agent container",
            }))
            await websocket.close(code=4003, reason="Container unreachable")
            return

    # Parse locale
    locale = parse_locale(
        websocket.headers.get("accept-language"),
        websocket.query_params.get("locale"),
    )

    # --- 5. 开始双向中继：浏览器 ↔ 龙虾 ---
    try:
        async with async_session() as db:
            # Re-fetch agent in this session so it's attached
            agent = await get_agent(db, agent_id, user_id)
            conversation_id = websocket.query_params.get("conversation_id")

            await relay(
                client_ws=websocket,
                container_ws=container_ws,
                db=db,
                user_id=user_id,
                agent=agent,
                conversation_id=conversation_id,
                locale=locale,
            )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user=%s agent=%s", user_id, agent_id)
    finally:
        try:
            await container_ws.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- #
#  REST — conversation & message history
# --------------------------------------------------------------------------- #

@router.get("/agents/{agent_id}/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.agent_id == agent_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    agent = await get_agent(db, conv.agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
