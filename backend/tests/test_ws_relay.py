"""Tests for WebSocket relay module — message interception, credits, and forwarding."""

import json
import uuid
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.chat import MessageRole
from app.core.security import hash_password


@pytest_asyncio.fixture
async def relay_user(db_session):
    user = User(
        email=f"relay-test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpass123"),
        name="Relay Test",
        credit_balance=500,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def relay_agent(db_session, relay_user):
    agent = Agent(
        user_id=relay_user.id,
        name="Relay Lobster",
        model_name="deepseek-chat",
        status=AgentStatus.running,
        ws_port=19200,
        gateway_token="relay-test-token",
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.mark.asyncio
async def test_connect_to_container_success():
    """Should connect when container is reachable."""
    from app.core.ws_relay import connect_to_container

    mock_ws = MagicMock()

    async def mock_connect(*args, **kwargs):
        return mock_ws

    with patch("app.core.ws_relay.websockets.connect", side_effect=mock_connect):
        ws = await connect_to_container(19200, "test-token", timeout=2)
        assert ws == mock_ws


@pytest.mark.asyncio
async def test_connect_to_container_retry():
    """Should retry on connection failure then succeed."""
    from app.core.ws_relay import connect_to_container

    mock_ws = MagicMock()
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionRefusedError("not ready")
        return mock_ws

    with patch("app.core.ws_relay.websockets.connect", side_effect=side_effect):
        ws = await connect_to_container(19200, "test-token", timeout=10)
        assert ws == mock_ws
        assert call_count == 3


@pytest.mark.asyncio
async def test_connect_to_container_timeout():
    """Should raise ConnectionError after timeout."""
    from app.core.ws_relay import connect_to_container

    async def always_fail(*args, **kwargs):
        raise ConnectionRefusedError("never ready")

    with patch("app.core.ws_relay.websockets.connect", side_effect=always_fail):
        with pytest.raises(ConnectionError, match="Cannot connect"):
            await connect_to_container(19200, "test-token", timeout=2)


class FakeContainerWS:
    """Fake async-iterable WebSocket that yields predefined messages then waits."""
    def __init__(self, items, wait_after=2.0):
        self._items = list(items)
        self._closed = False
        self._wait_after = wait_after

    def __aiter__(self):
        return self._aiter_impl()

    async def _aiter_impl(self):
        for item in self._items:
            yield item
        # Wait so the client task can finish first
        await asyncio.sleep(self._wait_after)

    async def send(self, data):
        pass

    async def close(self):
        self._closed = True


@pytest.mark.asyncio
async def test_relay_ping_handled_locally(db_session, relay_user, relay_agent):
    """Ping messages should be answered locally, not forwarded to container."""
    from app.core.ws_relay import relay

    client_ws = AsyncMock()
    container_ws = FakeContainerWS([])

    # Client sends ping, then raises to end the loop
    client_ws.receive_text = AsyncMock(
        side_effect=[
            json.dumps({"type": "ping"}),
            asyncio.TimeoutError(),
        ]
    )

    await relay(
        client_ws=client_ws,
        container_ws=container_ws,
        db=db_session,
        user_id=relay_user.id,
        agent=relay_agent,
        conversation_id=None,
    )

    # Should have sent pong to client
    pong_calls = [
        call for call in client_ws.send_text.call_args_list
        if "pong" in str(call)
    ]
    assert len(pong_calls) >= 1


@pytest.mark.asyncio
async def test_relay_stream_forwarded(db_session, relay_user, relay_agent):
    """Stream messages from container should be forwarded to client."""
    from app.core.ws_relay import relay

    # Container sends stream + done
    stream_msg = json.dumps({"type": "stream", "content": "Hello"})
    done_msg = json.dumps({
        "type": "done",
        "usage": {"tokens_input": 10, "tokens_output": 5, "model": "deepseek-chat"},
    })

    client_ws = AsyncMock()
    container_ws = FakeContainerWS([stream_msg, done_msg])

    # Client does nothing (timeout immediately)
    client_ws.receive_text = AsyncMock(side_effect=asyncio.TimeoutError())

    await relay(
        client_ws=client_ws,
        container_ws=container_ws,
        db=db_session,
        user_id=relay_user.id,
        agent=relay_agent,
        conversation_id=None,
    )

    # Client should have received the stream message
    forwarded = [str(call) for call in client_ws.send_text.call_args_list]
    assert any("stream" in f for f in forwarded)


@pytest.mark.asyncio
async def test_relay_insufficient_credits(db_session, relay_user, relay_agent):
    """User with 0 credits should get error when sending message."""
    from app.core.ws_relay import relay

    relay_user.credit_balance = 0
    await db_session.commit()

    client_ws = AsyncMock()
    container_ws = FakeContainerWS([])

    client_ws.receive_text = AsyncMock(
        side_effect=[
            json.dumps({"type": "message", "content": "Hi"}),
            asyncio.TimeoutError(),
        ]
    )

    await relay(
        client_ws=client_ws,
        container_ws=container_ws,
        db=db_session,
        user_id=relay_user.id,
        agent=relay_agent,
        conversation_id=None,
    )

    # Should have sent insufficient_credits error
    error_calls = [
        str(call) for call in client_ws.send_text.call_args_list
        if "insufficient_credits" in str(call)
    ]
    assert len(error_calls) >= 1
