"""Tests for Agent CRUD, start/stop, port allocation, and gateway token."""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email=f"agent-test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpass123"),
        name="Agent Test",
        credit_balance=500,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_agent(db_session, test_user):
    """Agent creation should allocate port and generate gateway token."""
    from app.services.agent_service import create_agent

    agent = await create_agent(db_session, test_user.id, "My Lobster", "deepseek-chat")

    assert agent.name == "My Lobster"
    assert agent.model_name == "deepseek-chat"
    assert agent.user_id == test_user.id
    assert agent.status == AgentStatus.stopped
    assert agent.ws_port is not None
    assert agent.ws_port >= 19000
    assert agent.gateway_token is not None
    assert len(agent.gateway_token) > 20


@pytest.mark.asyncio
async def test_create_agent_limit(db_session, test_user):
    """Free plan should only allow 1 agent."""
    from app.services.agent_service import create_agent, AgentLimitError

    await create_agent(db_session, test_user.id, "Lobster 1", "deepseek-chat")

    with pytest.raises(AgentLimitError):
        await create_agent(db_session, test_user.id, "Lobster 2", "deepseek-chat")


@pytest.mark.asyncio
async def test_list_agents(db_session, test_user):
    """Should list only the user's agents."""
    from app.services.agent_service import list_agents, create_agent

    await create_agent(db_session, test_user.id, "My Agent", "deepseek-chat")

    agents = await list_agents(db_session, test_user.id)
    assert len(agents) >= 1
    assert all(a.user_id == test_user.id for a in agents)


@pytest.mark.asyncio
async def test_get_agent(db_session, test_user):
    """get_agent should return agent for valid owner, None for others."""
    from app.services.agent_service import create_agent, get_agent

    agent = await create_agent(db_session, test_user.id, "Test", "deepseek-chat")

    found = await get_agent(db_session, agent.id, test_user.id)
    assert found is not None
    assert found.id == agent.id

    not_found = await get_agent(db_session, agent.id, "nonexistent-user-id")
    assert not_found is None


@pytest.mark.asyncio
async def test_delete_agent(db_session, test_user):
    """Deleting an agent should remove it from DB."""
    from app.services.agent_service import create_agent, get_agent, delete_agent

    agent = await create_agent(db_session, test_user.id, "To Delete", "deepseek-chat")
    agent_id = agent.id

    await delete_agent(db_session, agent)

    found = await get_agent(db_session, agent_id, test_user.id)
    assert found is None


@pytest.mark.asyncio
async def test_start_agent(db_session, test_user):
    """Starting an agent should create container and set status to running."""
    from app.services.agent_service import create_agent, start_agent

    agent = await create_agent(db_session, test_user.id, "Startable", "deepseek-chat")
    assert agent.status == AgentStatus.stopped

    with patch("app.services.agent_service.docker_manager") as mock_dm:
        mock_dm.create_agent_container.return_value = "container-123"
        mock_dm.get_container_status.return_value = "running"

        started = await start_agent(db_session, agent)

    assert started.status == AgentStatus.running
    assert started.container_id == "container-123"


@pytest.mark.asyncio
async def test_stop_agent(db_session, test_user):
    """Stopping an agent should set status to stopped."""
    from app.services.agent_service import create_agent, start_agent, stop_agent

    agent = await create_agent(db_session, test_user.id, "Stoppable", "deepseek-chat")

    with patch("app.services.agent_service.docker_manager") as mock_dm:
        mock_dm.create_agent_container.return_value = "container-456"
        mock_dm.get_container_status.return_value = "running"
        agent = await start_agent(db_session, agent)

    with patch("app.services.agent_service.docker_manager") as mock_dm:
        stopped = await stop_agent(db_session, agent)

    assert stopped.status == AgentStatus.stopped


@pytest.mark.asyncio
async def test_port_allocation_increments(db_session, test_user):
    """Each new agent should get a different port."""
    from app.services.agent_service import create_agent

    # Create two agents under same user — need pro plan for >1 agent
    with patch("app.services.agent_service.get_user_plan", return_value="pro"):
        a1 = await create_agent(db_session, test_user.id, "A1", "deepseek-chat")
        a2 = await create_agent(db_session, test_user.id, "A2", "deepseek-chat")

    assert a1.ws_port != a2.ws_port
    assert a2.ws_port == a1.ws_port + 1


@pytest.mark.asyncio
async def test_gateway_token_unique(db_session, test_user):
    """Each agent should have a unique gateway token."""
    from app.services.agent_service import create_agent

    with patch("app.services.agent_service.get_user_plan", return_value="pro"):
        a1 = await create_agent(db_session, test_user.id, "T1", "deepseek-chat")
        a2 = await create_agent(db_session, test_user.id, "T2", "deepseek-chat")

    assert a1.gateway_token != a2.gateway_token
