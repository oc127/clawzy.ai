"""Chat service — streams LLM responses via OpenClaw WebSocket and manages conversations."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import websockets
from websockets.exceptions import WebSocketException, ConnectionClosed
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent import Agent, AgentStatus
from app.models.chat import Conversation, Message, MessageRole
from app.services.credits_service import (
    deduct_credits,
    InsufficientCreditsError,
)

logger = logging.getLogger(__name__)

_MIN_CREDITS_GUARD = 1
_SESSION_KEY = "agent:main:main"


def _build_ws_url(agent: Agent) -> str:
    """
    Return the WebSocket URL for this agent's OpenClaw container.

    Running agents are reachable by container name on the Docker network.
    Agents without a running container fall back to the shared gateway.
    """
    if agent.status == AgentStatus.running and agent.container_id:
        # Each per-agent container is named clawzy-agent-{agent.id}
        return f"ws://clawzy-agent-{agent.id}:18789"
    # Shared gateway — convert http(s):// to ws(s)://
    base = settings.openclaw_url
    return base.replace("https://", "wss://").replace("http://", "ws://")


def _get_gateway_token(agent: Agent) -> str:
    if agent.status == AgentStatus.running and agent.config:
        token = agent.config.get("gateway_token")
        if token:
            return token
    return settings.openclaw_gateway_token


async def _openclaw_stream(ws_url: str, gateway_token: str, message: str):
    """
    Connect to an OpenClaw WebSocket gateway, send a user message, and yield
    incremental text tokens as they stream back.

    OpenClaw WebSocket protocol:
    1. Client connects with Authorization: Bearer <token>
    2. Server sends connect.challenge event
    3. Client sends 'connect' req with client info + scopes + auth
    4. Server responds hello-ok
    5. Client sends 'chat.send' req
    6. Server streams 'chat' delta/final events (each delta has FULL accumulated text)

    Raises ConnectionError on WebSocket failures, RuntimeError on protocol errors.
    """
    # Origin must match the gateway's allowedOrigins. Using the gateway host itself.
    origin = ws_url.replace("wss://", "https://").replace("ws://", "http://")
    headers = {
        "Authorization": f"Bearer {gateway_token}",
        "Origin": origin,
    }

    try:
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            # ── Step 2: receive connect.challenge ───────────────────────────
            raw = await asyncio.wait_for(ws.recv(), timeout=15)
            msg = json.loads(raw)
            if msg.get("event") != "connect.challenge":
                raise RuntimeError(f"Expected connect.challenge, got: {raw[:200]}")

            # ── Step 3: send connect request ────────────────────────────────
            connect_id = str(uuid.uuid4())
            await ws.send(json.dumps({
                "type": "req",
                "id": connect_id,
                "method": "connect",
                "params": {
                    "minProtocol": 1,
                    "maxProtocol": 10,
                    "client": {
                        "id": "webchat-ui",
                        "version": "1.0.0",
                        "platform": "web",
                        "mode": "webchat",
                    },
                    "scopes": ["operator.read", "operator.write"],
                    "auth": {"token": gateway_token},
                },
            }))

            # ── Step 4: wait for hello-ok ────────────────────────────────────
            # May receive tick/presence events before the response
            for _ in range(10):
                raw = await asyncio.wait_for(ws.recv(), timeout=10)
                msg = json.loads(raw)
                if msg.get("type") == "res" and msg.get("id") == connect_id:
                    if not msg.get("ok"):
                        raise RuntimeError(f"OpenClaw connect rejected: {msg}")
                    break
            else:
                raise RuntimeError("hello-ok not received from OpenClaw")

            # ── Step 5: send chat.send ───────────────────────────────────────
            chat_req_id = str(uuid.uuid4())
            await ws.send(json.dumps({
                "type": "req",
                "id": chat_req_id,
                "method": "chat.send",
                "params": {
                    "sessionKey": _SESSION_KEY,
                    "message": message,
                    "idempotencyKey": str(uuid.uuid4()),
                },
            }))

            # Wait for chat.send ack (contains runId)
            run_id: str | None = None
            for _ in range(10):
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                msg = json.loads(raw)
                if msg.get("type") == "res" and msg.get("id") == chat_req_id:
                    if not msg.get("ok"):
                        raise RuntimeError(f"chat.send rejected: {msg}")
                    run_id = msg["payload"]["runId"]
                    break
            else:
                raise RuntimeError("chat.send ack not received from OpenClaw")

            # ── Step 6: stream chat events ───────────────────────────────────
            prev_text = ""
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") != "event" or msg.get("event") != "chat":
                    continue

                payload = msg.get("payload", {})
                if payload.get("runId") != run_id:
                    continue

                state = payload.get("state")
                blocks = payload.get("message", {}).get("content", [])
                full_text = "".join(
                    b.get("text", "") for b in blocks if b.get("type") == "text"
                )

                # Deltas carry cumulative text — yield only the new suffix
                if len(full_text) > len(prev_text):
                    yield full_text[len(prev_text):]
                    prev_text = full_text

                if state == "error":
                    raise RuntimeError(
                        f"OpenClaw agent error: {payload.get('errorMessage', 'unknown')}"
                    )
                if state in ("final", "aborted"):
                    break

    except (WebSocketException, ConnectionClosed, OSError) as exc:
        raise ConnectionError(str(exc)) from exc


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
    """Get recent messages for context (used for token estimation)."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    agent: Agent,
    conversation_id: str,
    user_content: str,
    images: list[str] | None = None,
):
    """
    Stream a chat completion through the agent's OpenClaw container.

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {...}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    from app.models.user import User

    # ── 1. Pre-flight credit check ───────────────────────────────────────────
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if user.credit_balance < _MIN_CREDITS_GUARD:
        yield json.dumps({
            "type": "error",
            "code": "insufficient_credits",
            "message": "Insufficient credits. Please top up to continue.",
        })
        return

    # ── 2. Save user message ─────────────────────────────────────────────────
    await save_message(db, conversation_id, MessageRole.user, user_content or "[image]")
    await db.commit()

    # ── 3. Resolve routing ───────────────────────────────────────────────────
    ws_url = _build_ws_url(agent)
    gateway_token = _get_gateway_token(agent)

    # For images, append a note to the message (vision is handled by the model)
    message_text = user_content or ""
    if images:
        img_note = "\n".join(f"[image: {url}]" for url in images)
        message_text = f"{message_text}\n{img_note}".strip()

    # ── 4. Stream via OpenClaw WebSocket ─────────────────────────────────────
    full_content = ""
    fallback_used = False
    connection_error: Exception | None = None

    # Try the agent's dedicated container first
    try:
        async for chunk in _openclaw_stream(ws_url, gateway_token, message_text):
            full_content += chunk
            yield json.dumps({"type": "stream", "content": chunk})
    except ConnectionError as exc:
        connection_error = exc
        logger.warning(
            "Agent %s container unreachable (%s); will try shared gateway fallback",
            agent.id, exc,
        )
    except RuntimeError as exc:
        yield json.dumps({"type": "error", "code": "model_error", "message": str(exc)})
        return

    # If per-agent container failed, fall back to shared gateway
    if not full_content and connection_error and agent.status == AgentStatus.running:
        fallback_used = True
        fallback_url = (
            settings.openclaw_url
            .replace("https://", "wss://")
            .replace("http://", "ws://")
        )
        fallback_token = settings.openclaw_gateway_token
        try:
            async for chunk in _openclaw_stream(fallback_url, fallback_token, message_text):
                full_content += chunk
                yield json.dumps({"type": "stream", "content": chunk})
        except ConnectionError:
            yield json.dumps({
                "type": "error",
                "code": "connection_error",
                "message": "Cannot connect to any agent service",
            })
            return
        except RuntimeError as exc:
            yield json.dumps({"type": "error", "code": "model_error", "message": str(exc)})
            return

    # Retry once on empty response (transient OpenClaw state after restart)
    if not full_content and not connection_error:
        logger.warning("Empty response from OpenClaw for agent %s; retrying once", agent.id)
        try:
            async for chunk in _openclaw_stream(ws_url, gateway_token, message_text):
                full_content += chunk
                yield json.dumps({"type": "stream", "content": chunk})
        except (ConnectionError, RuntimeError) as exc:
            logger.warning("Retry also failed: %s", exc)

    if not full_content:
        yield json.dumps({
            "type": "error",
            "code": "connection_error" if connection_error else "empty_response",
            "message": (
                "Cannot connect to agent container"
                if connection_error
                else "Agent returned empty response"
            ),
        })
        return

    # ── 5. Estimate tokens ───────────────────────────────────────────────────
    history = await get_conversation_history(db, conversation_id)
    tokens_input = len(str(history)) // 4
    tokens_output = len(full_content) // 4

    # ── 6. Deduct credits ────────────────────────────────────────────────────
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

    # ── 7. Persist assistant message ─────────────────────────────────────────
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
            "fallback_used": fallback_used,
        },
    })
