import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session
from app.core.security import decode_token
from app.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.schemas.chat import ConversationResponse, MessageResponse
from app.services.agent_service import get_agent
from app.services.chat_service import (
    get_or_create_conversation,
    stream_chat_completion,
)
from app.services.credits_service import check_daily_limit, DailyLimitExceededError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# --------------------------------------------------------------------------- #
#  WebSocket — real-time chat
# --------------------------------------------------------------------------- #

@router.websocket("/ws/chat/{agent_id}")
async def ws_chat(websocket: WebSocket, agent_id: str):
    """
    WebSocket chat endpoint.

    Connection: ws://host/api/v1/ws/chat/{agent_id}?token=<JWT>

    Client sends:
      {"type": "message", "content": "hello", "conversation_id": "optional-uuid"}
      {"type": "switch_model", "model": "claude-sonnet"}

    Server sends:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {...}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]

    # Verify agent ownership
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

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "code": "invalid_json",
                    "message": "Invalid JSON",
                }))
                continue

            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue
                if len(content) > 20000:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "code": "message_too_long",
                        "message": "Message exceeds 20,000 character limit",
                    }))
                    continue

                conversation_id = data.get("conversation_id")

                async with async_session() as db:
                    # Re-fetch agent to get latest model_name
                    agent = await get_agent(db, agent_id, user_id)
                    if agent is None:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "agent_not_found",
                            "message": "Agent no longer exists",
                        }))
                        break

                    # Check credits
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user is None:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "user_not_found",
                            "message": "User no longer exists",
                        }))
                        break
                    if user.credit_balance <= 0:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "insufficient_credits",
                            "message": "No credits remaining",
                        }))
                        continue

                    # Check daily credit limit
                    try:
                        await check_daily_limit(db, user)
                    except DailyLimitExceededError as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "daily_limit_exceeded",
                            "message": str(e),
                        }))
                        continue

                    try:
                        conv = await get_or_create_conversation(db, agent_id, conversation_id)
                        await db.commit()
                    except Exception:
                        logger.exception("Failed to get/create conversation")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "conversation_error",
                            "message": "Failed to create conversation",
                        }))
                        continue
                    conv_id = conv.id

                    async for event in stream_chat_completion(
                        db, user_id, agent, conv_id, content
                    ):
                        await websocket.send_text(event)

            elif msg_type == "switch_model":
                new_model = data.get("model", "").strip()
                if new_model:
                    from app.services.credits_service import CREDIT_RATES
                    if new_model not in CREDIT_RATES:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "invalid_model",
                            "message": f"Unknown model: {new_model}",
                        }))
                        continue
                    async with async_session() as db:
                        agent = await get_agent(db, agent_id, user_id)
                        if agent:
                            agent.model_name = new_model
                            await db.commit()
                            await websocket.send_text(json.dumps({
                                "type": "model_switched",
                                "model": new_model,
                            }))

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user=%s agent=%s", user_id, agent_id)


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
