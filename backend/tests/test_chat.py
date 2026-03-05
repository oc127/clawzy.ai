"""Tests for conversation management and message persistence."""

import uuid
import pytest
import pytest_asyncio

from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.chat import Conversation, Message, MessageRole
from app.core.security import hash_password
from app.services.chat_service import (
    get_or_create_conversation,
    save_message,
    get_conversation_history,
)


@pytest_asyncio.fixture
async def chat_user(db_session):
    user = User(
        email=f"chat-test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpass123"),
        name="Chat Test",
        credit_balance=500,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def chat_agent(db_session, chat_user):
    agent = Agent(
        user_id=chat_user.id,
        name="Chat Lobster",
        model_name="deepseek-chat",
        status=AgentStatus.running,
        ws_port=19100,
        gateway_token="test-token",
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.mark.asyncio
async def test_create_conversation(db_session, chat_agent):
    """Creating a conversation without ID should generate a new one."""
    conv = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    assert conv.id is not None
    assert conv.agent_id == chat_agent.id
    assert conv.title == "New conversation"


@pytest.mark.asyncio
async def test_get_existing_conversation(db_session, chat_agent):
    """Passing an existing conversation ID should return it."""
    conv1 = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    conv2 = await get_or_create_conversation(db_session, chat_agent.id, conv1.id)
    assert conv2.id == conv1.id


@pytest.mark.asyncio
async def test_get_nonexistent_conversation_creates_new(db_session, chat_agent):
    """Passing a nonexistent conversation ID should create a new one."""
    conv = await get_or_create_conversation(db_session, chat_agent.id, "nonexistent-id")
    await db_session.commit()

    assert conv.id != "nonexistent-id"
    assert conv.agent_id == chat_agent.id


@pytest.mark.asyncio
async def test_save_user_message(db_session, chat_agent):
    """Should persist a user message."""
    conv = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    msg = await save_message(db_session, conv.id, MessageRole.user, "Hello lobster!")
    await db_session.commit()

    assert msg.id is not None
    assert msg.role == MessageRole.user
    assert msg.content == "Hello lobster!"
    assert msg.conversation_id == conv.id


@pytest.mark.asyncio
async def test_save_assistant_message_with_metadata(db_session, chat_agent):
    """Should persist an assistant message with token/credit metadata."""
    conv = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    msg = await save_message(
        db_session, conv.id, MessageRole.assistant, "Hi there!",
        model_name="deepseek-chat",
        tokens_input=100,
        tokens_output=50,
        credits_used=1,
    )
    await db_session.commit()

    assert msg.model_name == "deepseek-chat"
    assert msg.tokens_input == 100
    assert msg.tokens_output == 50
    assert msg.credits_used == 1


@pytest.mark.asyncio
async def test_get_conversation_history(db_session, chat_agent):
    """Should return messages in chronological order."""
    conv = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    await save_message(db_session, conv.id, MessageRole.user, "First")
    await save_message(db_session, conv.id, MessageRole.assistant, "Second")
    await save_message(db_session, conv.id, MessageRole.user, "Third")
    await db_session.commit()

    history = await get_conversation_history(db_session, conv.id, limit=10)

    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First"
    assert history[1]["role"] == "assistant"
    assert history[2]["content"] == "Third"


@pytest.mark.asyncio
async def test_conversation_history_limit(db_session, chat_agent):
    """Should respect the limit parameter."""
    conv = await get_or_create_conversation(db_session, chat_agent.id)
    await db_session.commit()

    for i in range(10):
        await save_message(db_session, conv.id, MessageRole.user, f"Message {i}")
    await db_session.commit()

    history = await get_conversation_history(db_session, conv.id, limit=3)
    assert len(history) == 3
