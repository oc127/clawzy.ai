"""Chat WebSocket — proxies frontend ↔ OpenClaw Gateway."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import websockets

from app.core.database import get_db, async_session
from app.core.security import decode_token
from app.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.schemas.chat import ConversationResponse, MessageResponse
from app.services.agent_service import get_agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# --------------------------------------------------------------------------- #
#  OpenClaw Gateway handshake helpers
# --------------------------------------------------------------------------- #

async def openclaw_handshake(oc_ws, gateway_token: str) -> bool:
    """
    Perform the OpenClaw Gateway WebSocket handshake.

    Flow:
      1. Server sends connect.challenge event
      2. Client sends connect request with auth token
      3. Server sends hello-ok response
    """
    try:
        # Step 1: Wait for connect.challenge
        raw = await asyncio.wait_for(oc_ws.recv(), timeout=10)
        challenge = json.loads(raw)
        logger.debug("OpenClaw challenge: %s", challenge)

        # Step 2: Send connect request
        connect_msg = {
            "type": "req",
            "id": str(uuid.uuid4()),
            "method": "connect",
            "params": {
                "protocol": {"min": 3, "max": 3},
                "auth": {"token": gateway_token},
                "role": "operator",
                "scopes": ["operator.chat", "operator.admin"],
                "client": {
                    "name": "clawzy-backend",
                    "version": "0.1.0",
                },
                "device": {
                    "id": f"clawzy-proxy-{uuid.uuid4().hex[:8]}",
                    "name": "clawzy-proxy",
                    "type": "api",
                },
            },
        }
        await oc_ws.send(json.dumps(connect_msg))

        # Step 3: Wait for hello-ok
        raw = await asyncio.wait_for(oc_ws.recv(), timeout=10)
        hello = json.loads(raw)
        logger.debug("OpenClaw hello: %s", hello)

        if hello.get("type") == "res" and hello.get("ok"):
            return True

        logger.error("OpenClaw handshake failed: %s", hello)
        return False

    except (asyncio.TimeoutError, Exception) as e:
        logger.error("OpenClaw handshake error: %s", e)
        return False


# --------------------------------------------------------------------------- #
#  WebSocket — real-time chat (proxied to OpenClaw)
# --------------------------------------------------------------------------- #

@router.websocket("/ws/chat/{agent_id}")
async def ws_chat(websocket: WebSocket, agent_id: str):
    """
    WebSocket chat endpoint that proxies to an OpenClaw Gateway container.

    Connection: ws://host/api/v1/ws/chat/{agent_id}?token=<JWT>

    Client sends:
      {"type": "message", "content": "hello"}

    Server sends:
      {"type": "stream", "content": "..."}
      {"type": "done"}
      {"type": "error", "code": "...", "message": "..."}
    """
    # --- Authenticate via query param token ---
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]

    # --- Verify agent ownership and get connection info ---
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

        if agent.status != "running":
            await websocket.close(code=4003, reason="Agent not running")
            return

        if not agent.ws_port or not agent.gateway_token:
            await websocket.close(code=4003, reason="Agent not provisioned")
            return

        ws_port = agent.ws_port
        gateway_token = agent.gateway_token

    await websocket.accept()

    # --- Connect to OpenClaw Gateway ---
    openclaw_url = f"ws://127.0.0.1:{ws_port}"
    oc_ws = None

    try:
        oc_ws = await asyncio.wait_for(
            websockets.connect(openclaw_url, max_size=25 * 1024 * 1024),
            timeout=15,
        )

        # Perform OpenClaw handshake
        if not await openclaw_handshake(oc_ws, gateway_token):
            await websocket.send_text(json.dumps({
                "type": "error",
                "code": "handshake_failed",
                "message": "Failed to connect to AI agent",
            }))
            await websocket.close()
            return

        # Send ready signal to frontend
        await websocket.send_text(json.dumps({"type": "ready"}))

        # --- Bidirectional proxy ---
        async def forward_client_to_openclaw():
            """Read from frontend, translate and send to OpenClaw."""
            try:
                while True:
                    raw = await websocket.receive_text()
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    msg_type = data.get("type")

                    if msg_type == "message":
                        content = data.get("content", "").strip()
                        if not content:
                            continue

                        # Translate to OpenClaw chat.send
                        oc_msg = {
                            "type": "req",
                            "id": str(uuid.uuid4()),
                            "method": "chat.send",
                            "params": {
                                "message": content,
                            },
                        }
                        await oc_ws.send(json.dumps(oc_msg))

                    elif msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))

            except WebSocketDisconnect:
                pass

        async def forward_openclaw_to_client():
            """Read from OpenClaw, translate and send to frontend."""
            try:
                async for raw in oc_ws:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    oc_type = data.get("type")

                    if oc_type == "event":
                        event_name = data.get("event", "")
                        event_payload = data.get("payload", {})

                        if event_name == "agent":
                            # Agent streaming content
                            content = event_payload.get("content") or event_payload.get("text", "")
                            if content:
                                await websocket.send_text(json.dumps({
                                    "type": "stream",
                                    "content": content,
                                }))

                    elif oc_type == "res":
                        # Response to a chat.send request
                        if data.get("ok"):
                            res_payload = data.get("payload", {})
                            status_val = res_payload.get("status", "ok")
                            if status_val == "error":
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "code": "agent_error",
                                    "message": res_payload.get("message", "Agent error"),
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "done",
                                    "conversation_id": res_payload.get("sessionKey", ""),
                                }))
                        else:
                            error = data.get("error", {})
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "code": error.get("code", "unknown"),
                                "message": error.get("message", "Unknown error"),
                            }))

            except websockets.ConnectionClosed:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "code": "agent_disconnected",
                    "message": "AI agent disconnected",
                }))

        # Run both directions concurrently
        client_task = asyncio.create_task(forward_client_to_openclaw())
        openclaw_task = asyncio.create_task(forward_openclaw_to_client())

        done, pending = await asyncio.wait(
            [client_task, openclaw_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

    except (asyncio.TimeoutError, OSError) as e:
        logger.error("Cannot connect to OpenClaw for agent %s: %s", agent_id, e)
        await websocket.send_text(json.dumps({
            "type": "error",
            "code": "connection_error",
            "message": "Cannot connect to AI agent. It may be starting up.",
        }))
    finally:
        if oc_ws:
            await oc_ws.close()
        logger.info("WebSocket closed: user=%s agent=%s", user_id, agent_id)


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
